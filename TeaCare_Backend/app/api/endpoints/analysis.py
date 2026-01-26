from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
import uuid
import os
import cv2
import numpy as np
import io
import csv
import reverse_geocoder as rg
import pycountry
from PIL import Image
import tensorflow as tf
from skimage.feature import graycomatrix, graycoprops
import random

from app.core.database import get_db
from app.models.sql_models import DiseaseReport, DiseaseInfo, Treatment, SystemLog
from app.schemas.dtos import LocationUpdate, FeedbackRequest
from app.services.ai_service import ai_manager
from app.services.pdf_service import pdf_manager
from typing import Optional, List

router = APIRouter()

# --- HELPER: LOGGING ---
def log_event(db: Session, level: str, source: str, message: str):
    try:
        new_log = SystemLog(level=level, source=source, message=message)
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Logging failed: {e}")

# --- HELPER: Computer Vision Forensics (Local) ---
def analyze_lesions_advanced(image_path):
    try:
        # 1. Load & Preprocess
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. VEGETATION INDEX (Green Leaf Index - GLI)
        # GLI = (2G - R - B) / (2G + R + B)
        # We calculate the mean GLI for the whole leaf
        R, G, B = cv2.split(img_rgb)
        # Avoid division by zero
        denom = (2.0 * G + R + B) + 0.00001
        gli_matrix = (2.0 * G - R - B) / denom
        avg_gli = np.mean(gli_matrix)

        # 3. TEXTURE ANALYSIS (Entropy & Contrast)
        # Entropy = measure of randomness (high for fungal textures)
        # Contrast = measure of local intensity variation
        from skimage.feature import graycomatrix, graycoprops
        # Calculate GLCM (Gray Level Co-occurrence Matrix)
        # We downscale slightly for speed if needed, but 224x224 is fast enough
        glcm = graycomatrix(gray, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
        texture_contrast = graycoprops(glcm, 'contrast')[0, 0]
        texture_homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
        
        # 4. MORPHOLOGY (Lesion Shapes)
        # Mask for disease (same logic as before)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        disease_mask = cv2.bitwise_and(thresh, cv2.bitwise_not(green_mask))
        
        # Find contours of spots
        contours, _ = cv2.findContours(disease_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        lesion_count = len(contours)
        avg_circularity = 0
        avg_area = 0
        
        valid_spots = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 10: # Ignore tiny noise
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    # Circularity = 4 * pi * Area / (Perimeter^2)
                    # 1.0 = Perfect Circle, < 0.5 = Irregular/Splotchy
                    circularity = (4 * np.pi * area) / (perimeter * perimeter)
                    avg_circularity += circularity
                    avg_area += area
                    valid_spots += 1
        
        if valid_spots > 0:
            avg_circularity /= valid_spots
            avg_area /= valid_spots

        # 5. Generate Heatmap (Same as before)
        heatmap = img.copy()
        heatmap[disease_mask > 0] = [0, 0, 255] # Red BGR
        blended = cv2.addWeighted(img, 0.7, heatmap, 0.3, 0)
        filename = os.path.basename(image_path)
        heatmap_path = f"uploads/heatmap_{filename}"
        cv2.imwrite(heatmap_path, blended)

        return {
            "gli_index": round(avg_gli, 3),          # Green Leaf Index (-1 to 1)
            "texture_contrast": round(texture_contrast, 1), # High = Rough
            "texture_homogeneity": round(texture_homogeneity, 2), # High = Smooth
            "lesion_count": lesion_count,
            "avg_spot_area_px": round(avg_area, 0),
            "avg_circularity": round(avg_circularity, 2), # 1.0 = Circle
            "heatmap_url": heatmap_path,
            "severity": round((cv2.countNonZero(disease_mask)/cv2.countNonZero(thresh))*100, 2) if cv2.countNonZero(thresh) > 0 else 0
        }

    except Exception as e:
        print(f"CV Error: {e}")
        return {}

# ==========================================
# 1. PREDICTION ENDPOINTS
# ==========================================

@router.post("/predict")
async def predict_disease(
    user_id: int = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    if not ai_manager.model:
        return {"error": "AI Model offline", "confidence": "0%"}

    try:
        contents = await file.read()
        
        if ai_manager.is_blurry(contents):
            return {"error": "Image is too blurry", "blur_score": "Low"}

        # Save File
        ext = os.path.splitext(file.filename)[1]
        file_location = f"uploads/{uuid.uuid4()}{ext}"
        with open(file_location, "wb") as buffer:
            buffer.write(contents)

        # Predict
        disease_name, confidence = ai_manager.predict_image(contents)
        
        # Low Confidence Logic
        symptoms, causes, treatment_list = [], [], []
        if confidence < 50:
            disease_name = "Unknown / Unclear"
            symptoms = ["The AI is not sure. The image might be unclear."]
        else:
            # Fetch Info from DB
            clean_name = disease_name.split(". ", 1)[1] if ". " in disease_name else disease_name
            disease_name = clean_name
            
            d_info = db.query(DiseaseInfo).filter(DiseaseInfo.name.ilike(clean_name)).first()
            if d_info:
                symptoms = d_info.symptoms
                causes = d_info.causes
                treatments = db.query(Treatment).filter(Treatment.disease_id == d_info.disease_id).all()
                treatment_list = [{"type": t.type, "title": t.title, "instruction": t.instruction, "safety_tip": t.safety_tip} for t in treatments]

        # Auto-Verify Logic
        initial_status = "Auto-Verified" if confidence > 85.0 and disease_name != "Unknown / Unclear" else "Pending"
        initial_correctness = "Yes" if initial_status == "Auto-Verified" else "Unknown"

        # Save Report
        new_report = DiseaseReport(
            user_id=user_id,
            disease_name=disease_name,
            confidence=f"{confidence:.1f}%",
            image_url=file_location,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            verification_status=initial_status,
            is_correct=initial_correctness
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        return {
            "report_id": new_report.report_id,
            "disease_name": disease_name,
            "confidence": f"{confidence:.2f}%",
            "symptoms": symptoms,
            "causes": causes,
            "treatments": treatment_list,
            "image_url": file_location
        }
    except Exception as e:
        print(f"Prediction Error: {e}")
        raise HTTPException(status_code=500, detail="Server Error")

@router.post("/predict/advanced")
async def predict_advanced(
    user_id: int = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Use ai_manager to check model status
    if not ai_manager.model:
        raise HTTPException(status_code=503, detail="AI Model is offline")

    try:
        # 1. Read & Save Original
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1]
        file_location = f"uploads/{uuid.uuid4()}{ext}"
        
        # Ensure uploads directory exists (from reference code)
        os.makedirs("uploads", exist_ok=True) 
        
        with open(file_location, "wb") as buffer:
            buffer.write(contents)

        # 2. RUN AI MODEL (Classification)
        # Standardize image processing (from reference code)
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        image = image.resize((224, 224))
        img_array = np.asarray(image)
        batch = np.array([img_array])

        # Use ai_manager.model for prediction
        predictions = ai_manager.model.predict(batch)
        scores = tf.nn.softmax(predictions[0]).numpy()
        
        class_probs = []
        for i, score in enumerate(scores):
            # Use ai_manager.class_names
            raw_name = ai_manager.class_names[i]
            clean_name = raw_name
            
            # Logic to clean the name (remove numbering like "3. Gray Blight")
            if ". " in raw_name and raw_name.split(". ")[0].isdigit():
                clean_name = raw_name.split(". ", 1)[1]

            class_probs.append({
                "disease": clean_name, 
                "probability": float(score) * 100
            })
            
        class_probs.sort(key=lambda x: x["probability"], reverse=True)
        top_result = class_probs[0]

        # 3. RUN COMPUTER VISION (Quantification)
        cv_metrics = analyze_lesions_advanced(file_location)

        # Fallback values if CV fails (from reference code)
        if not cv_metrics:
            cv_metrics = {
                "severity": 0,
                "lesion_count": 0,
                "heatmap_url": "",
                "gli_index": 0,
                "texture_contrast": 0,
                "texture_homogeneity": 0,
                "avg_circularity": 0,
                "avg_spot_area_px": 0
            }

        initial_status = "Auto-Verified" if top_result['probability'] > 85.0 else "Pending"
        initial_correctness = "Yes" if initial_status == "Auto-Verified" else "Unknown"

        # 4. Save Report
        new_report = DiseaseReport(
            user_id=user_id,
            disease_name=top_result["disease"],
            confidence=f"{top_result['probability']:.1f}%",
            image_url=file_location,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            verification_status=initial_status, 
            is_correct=initial_correctness
        )
        db.add(new_report)
        db.commit()

        # 5. Return Advanced Data (Detailed structure from reference code)
        return {
            "report_id": new_report.report_id,
            "top_diagnosis": top_result,
            "full_spectrum": class_probs[:5],
            "image_url": file_location,
            "telemetry": cv_metrics,
            
            # Scientific Metrics (Safe Access)
            "severity_metrics": {
                "score": cv_metrics.get("severity", 0),
                "lesion_count": cv_metrics.get("lesion_count", 0),
                "heatmap_url": cv_metrics.get("heatmap_url", "")
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc() # Prints real error to terminal for debugging
        print(f"Advanced Scan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 2. REPORT MANAGEMENT
# ==========================================

@router.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_db)):
    return db.query(DiseaseReport).filter(DiseaseReport.user_id == user_id).order_by(DiseaseReport.report_id.desc()).all()

@router.patch("/history/{report_id}/location")
def update_location(report_id: int, loc: LocationUpdate, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.latitude = loc.latitude
    report.longitude = loc.longitude
    db.commit()
    return {"message": "Location saved"}

@router.post("/history/{report_id}/feedback")
def submit_feedback(report_id: int, feedback: FeedbackRequest, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.is_correct = "Yes" if feedback.is_correct else "No"
    
    if not feedback.is_correct:
        report.user_correction = feedback.correct_disease
        report.verification_status = "Pending" 
        log_event(db, "WARNING", "Triage", f"Report #{report_id} FLAGGED by User Feedback")
    
    db.commit()
    return {"message": "Feedback received"}

@router.get("/reports/locations")
def get_public_reports(db: Session = Depends(get_db)):
    """Public map data endpoint."""
    return db.query(DiseaseReport).filter(DiseaseReport.latitude != None).all()

@router.get("/api/reports/{report_id}/export")
def export_report_pdf(report_id: int, db: Session = Depends(get_db)):
    report = db.query(DiseaseReport).filter(DiseaseReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Re-run Advanced Analysis for the PDF
    cv_metrics = analyze_lesions_advanced(report.image_url)
    
    # Re-calculate Confusion Spectrum (simplified)
    # Ideally, we store this in DB, but re-calculating ensures fresh data
    confusion_spectrum = [{"name": report.disease_name, "prob": float(report.confidence.strip('%'))}]
    
    pdf_path = pdf_manager.generate_disease_report(report, cv_metrics, confusion_spectrum)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=f"TeaCare_Report_{report_id}.pdf")

# ==========================================
# 3. ANALYTICS (TEMPORAL & GEO)
# ==========================================

def get_country_name(code):
    try:
        return pycountry.countries.get(alpha_2=code).name
    except:
        return code 

@router.get("/api/analytics/temporal")
def get_temporal_analytics(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    country: Optional[str] = "All",
    region: Optional[str] = "All", 
    disease: Optional[str] = "All",
    db: Session = Depends(get_db)
):
    # --- 1. Date Logic ---
    try:
        if start_date and end_date:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            e_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            e_dt = datetime.now()
            s_dt = e_dt - timedelta(days=30)
            
        # Convert to String for Database Comparison
        s_str = s_dt.strftime("%Y-%m-%d %H:%M")
        e_str = e_dt.strftime("%Y-%m-%d %H:%M")
        
    except ValueError:
        # Fallback
        e_dt = datetime.now()
        s_dt = e_dt - timedelta(days=30)
        s_str = s_dt.strftime("%Y-%m-%d %H:%M")
        e_str = e_dt.strftime("%Y-%m-%d %H:%M")
    
    # --- 2. Query Data ---
    query = db.query(DiseaseReport).filter(
        DiseaseReport.timestamp >= s_str,
        DiseaseReport.timestamp <= e_str
    )
    
    if disease and disease != "All":
        query = query.filter(DiseaseReport.disease_name == disease)

    all_reports = query.all()
    filtered_reports = []

    # --- 3. Dynamic Geo-Filtering ---
    if (country and country != "All") or (region and region != "All"):
        valid_reports = []
        coords_to_check = []
        for r in all_reports:
            if r.latitude and r.longitude:
                try:
                    coords_to_check.append((float(r.latitude), float(r.longitude)))
                    valid_reports.append(r)
                except: continue
        
        if coords_to_check:
            geo_results = rg.search(coords_to_check)
            for idx, geo in enumerate(geo_results):
                r_country = get_country_name(geo.get('cc'))
                r_region = geo.get('admin1')
                country_match = (country == "All") or (r_country == country)
                region_match = (region == "All") or (r_region == region)
                if country_match and region_match:
                    filtered_reports.append(valid_reports[idx])
    else:
        filtered_reports = all_reports

    # --- 4. Data Aggregation ---
    data_map = {}
    composition_map = {}
    disease_totals = {} 
    seasonality_map = {i: 0 for i in range(1, 13)}
    
    # Fill Timeline
    current = s_dt
    while current <= e_dt:
        key = current.strftime("%Y-%m-%d")
        data_map[key] = { "date": key, "disease_count": 0 }
        composition_map[key] = { "date": key }
        current += timedelta(days=1)

    for r in filtered_reports:
        try:
            # Handle variable timestamp formats safely
            ts_str = str(r.timestamp)
            if "T" in ts_str: dt = datetime.strptime(ts_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            else: dt = datetime.strptime(ts_str[:16], "%Y-%m-%d %H:%M")
            
            d_key = dt.strftime("%Y-%m-%d")
            d_name = r.disease_name
            
            if d_key in data_map:
                data_map[d_key]["disease_count"] += 1
                composition_map[d_key][d_name] = composition_map[d_key].get(d_name, 0) + 1
                disease_totals[d_name] = disease_totals.get(d_name, 0) + 1
                seasonality_map[dt.month] += 1
        except Exception as e: 
            # print(f"Skipping row: {e}")
            continue

    # Fill zeros
    all_diseases = list(disease_totals.keys())
    for day in composition_map.values():
        for d in all_diseases:
            if d not in day: day[d] = 0

    timeline = sorted(data_map.values(), key=lambda x: x['date'])
    composition_timeline = sorted(composition_map.values(), key=lambda x: x['date'])

    # --- 5. Statistics ---
    counts = [t["disease_count"] for t in timeline]
    
    # Trend
    trend = []
    window = 3
    for i in range(len(counts)):
        s = max(0, i - window + 1)
        chunk = counts[s : i + 1]
        trend.append(round(sum(chunk) / len(chunk), 2))

    # Anomalies
    anomalies = []
    if len(counts) > 0:
        mean = sum(counts) / len(counts)
        variance = sum([((x - mean) ** 2) for x in counts]) / len(counts)
        std_dev = variance ** 0.5
        threshold = mean + (1.5 * std_dev)
        for t in timeline:
            if t["disease_count"] > threshold and t["disease_count"] > 0:
                anomalies.append(t)

    # Forecast
    forecast = []
    if counts:
        last_avg = sum(counts[-5:]) / 5 if len(counts) >= 5 else counts[-1]
        momentum = (counts[-1] - counts[0]) / len(counts) if len(counts) > 1 else 0
        for i in range(1, 8):
            f_date = (e_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            val = max(0, last_avg + (momentum * i) + random.uniform(-0.5, 0.5))
            forecast.append({
                "date": f_date,
                "predicted": round(val, 1),
                "confidence_high": round(val * 1.25, 1)
            })

    # Seasonal Profile
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    seasonal_profile = [{"month": month_names[i-1], "cases": seasonality_map[i]} for i in range(1, 13)]

    # Growth Rate
    mid = len(counts) // 2
    first_half = sum(counts[:mid])
    last_half = sum(counts[mid:])
    growth_rate = 0
    if first_half > 0:
        growth_rate = ((last_half - first_half) / first_half) * 100

    return {
        "timeline": timeline,
        "composition": composition_timeline,
        "disease_breakdown": [{"name": k, "value": v} for k, v in disease_totals.items()],
        "trend_line": trend,
        "forecast": forecast,
        "anomalies": anomalies,
        "seasonality": seasonal_profile,
        "statistics": {
            "total_cases": sum(counts),
            "peak_day": max(counts) if counts else 0,
            "growth_rate": round(growth_rate, 1),
            "active_region": region if region != "All" else country,
            "anomaly_count": len(anomalies)
        }
    }

@router.get("/api/analytics/map")
def get_map_data(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    country: Optional[str] = "All",
    region: Optional[str] = "All", 
    disease: Optional[str] = "All",
    db: Session = Depends(get_db)
):
    """Returns filtered reports with geo-coordinates and resolved locations for the heatmap."""
    
    # 1. Date Logic
    try:
        if start_date and end_date:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            e_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            e_dt = datetime.now()
            s_dt = e_dt - timedelta(days=30)
        
        # Convert to String for Database Comparison
        s_str = s_dt.strftime("%Y-%m-%d %H:%M")
        e_str = e_dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return []

    # 2. Base Query (Only fetch valid coords)
    query = db.query(DiseaseReport).filter(
        DiseaseReport.timestamp >= s_str,
        DiseaseReport.timestamp <= e_str,
        DiseaseReport.latitude.isnot(None),
        DiseaseReport.longitude.isnot(None)
    )
    
    if disease and disease != "All":
        query = query.filter(DiseaseReport.disease_name == disease)

    reports = query.all()
    map_points = []

    # 3. Geo-Filtering (Batch Processing)
    coords_to_check = []
    valid_reports = []
    
    for r in reports:
        try:
            coords_to_check.append((float(r.latitude), float(r.longitude)))
            valid_reports.append(r)
        except: continue

    if coords_to_check:
        geo_results = rg.search(coords_to_check)
        
        for idx, geo in enumerate(geo_results):
            r = valid_reports[idx]
            
            # Resolve Location
            r_country = get_country_name(geo.get('cc'))
            r_region = geo.get('admin1')
            
            # Apply Filter
            country_match = (country == "All") or (r_country == country)
            region_match = (region == "All") or (r_region == region)
            
            if country_match and region_match:
                map_points.append({
                    "id": r.report_id,
                    "lat": float(r.latitude),
                    "lng": float(r.longitude),
                    "disease": r.disease_name,
                    "confidence": r.confidence,
                    "date": str(r.timestamp).split(" ")[0],
                    "location": f"{geo.get('name')}, {r_region}",
                    "image_url": r.image_url 
                })

    return map_points

@router.get("/api/analytics/filters")
def get_dynamic_filters(db: Session = Depends(get_db)):
    """Returns available Countries, Regions, and Diseases for the UI filters."""
    try:
        unique_diseases = db.query(DiseaseReport.disease_name).distinct().all()
        diseases = sorted([d[0] for d in unique_diseases if d[0]])

        coords_raw = db.query(DiseaseReport.latitude, DiseaseReport.longitude).filter(
            DiseaseReport.latitude.isnot(None), 
            DiseaseReport.longitude.isnot(None)
        ).all()

        unique_coords = list(set([(float(c[0]), float(c[1])) for c in coords_raw if c[0] and c[1]]))
        locations = {} 
        
        if unique_coords:
            results = rg.search(unique_coords)
            for res in results:
                cc = res.get('cc', 'Unknown')
                country_name = get_country_name(cc)
                region = res.get('admin1', 'Unknown') 
                
                if country_name not in locations:
                    locations[country_name] = set()
                locations[country_name].add(region)

        formatted_locations = {k: sorted(list(v)) for k, v in locations.items()}
        return {"diseases": diseases, "locations": formatted_locations}
    except Exception as e:
        return {"diseases": [], "locations": {}}

@router.get("/api/analytics/export")
def export_raw_data(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    country: Optional[str] = "All",
    region: Optional[str] = "All", 
    disease: Optional[str] = "All",
    db: Session = Depends(get_db)
):
    """Exports filtered report data as CSV with geo-enriched locations."""
    
    # 1. Date Logic
    try:
        if start_date and end_date:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            e_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            e_dt = datetime.now()
            s_dt = e_dt - timedelta(days=30)
        
        # Convert to string for DB comparison
        s_str = s_dt.strftime("%Y-%m-%d %H:%M")
        e_str = e_dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # 2. Base Query
    query = db.query(DiseaseReport).filter(
        DiseaseReport.timestamp >= s_str,
        DiseaseReport.timestamp <= e_str
    )
    
    if disease and disease != "All":
        query = query.filter(DiseaseReport.disease_name == disease)

    all_reports = query.all()
    export_rows = []

    # 3. Geo-Enrichment & Filtering
    valid_reports = []
    coords_to_check = []
    
    for r in all_reports:
        if r.latitude and r.longitude:
            try:
                coords_to_check.append((float(r.latitude), float(r.longitude)))
                valid_reports.append(r)
            except: continue
    
    if coords_to_check:
        geo_results = rg.search(coords_to_check)
        
        for idx, geo in enumerate(geo_results):
            r = valid_reports[idx]
            
            # Resolve Names
            r_country_code = geo.get('cc', 'Unknown')
            r_country = get_country_name(r_country_code)
            r_region = geo.get('admin1', 'Unknown')
            r_city = geo.get('name', 'Unknown')

            # Apply Filter
            country_match = (country == "All") or (r_country == country)
            region_match = (region == "All") or (r_region == region)
            
            if country_match and region_match:
                # Add to Export List
                export_rows.append([
                    r.report_id,
                    r.timestamp,
                    r.disease_name,
                    r.confidence,
                    r.latitude,
                    r.longitude,
                    r_city,
                    r_region,
                    r_country,
                    r.user_id
                ])

    # 4. Generate CSV Stream
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Report ID", "Timestamp", "Disease", "AI Confidence", 
        "Latitude", "Longitude", "Detected City", "Detected Region", "Detected Country", 
        "User ID"
    ])
    
    # Rows
    writer.writerows(export_rows)
    
    output.seek(0)
    
    filename = f"teacare_export_{start_date or '30d'}_to_{end_date or 'now'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
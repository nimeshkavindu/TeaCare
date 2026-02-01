# TeaCare: AI-Powered Tea Plant Disease Identification System 🌱📱

![TeaCare Banner](assets/banner.png)
[![Flutter](https://img.shields.io/badge/Flutter-3.0%2B-blue?logo=flutter)](https://flutter.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-yellow?logo=python)](https://www.python.org/)
[![AI Model](https://img.shields.io/badge/Model-ConvNeXt%20%7C%20Qwen--0.5B-orange)]()

## 📖 Overview

**TeaCare** is a "Digital Doctor" mobile application designed to assist tea farmers in Sri Lanka by identifying plant diseases instantly and providing expert management advice[cite: 28]. 

The tea industry suffers from significant yield losses due to diseases, exacerbated by a scarcity of agronomists and delayed manual diagnosis [cite: 13-16]. [cite_start]TeaCare bridges this gap by deploying lightweight, low-latency AI models directly on standard mobile hardware, connecting smallholder farmers with expert-level agronomy knowledge[cite: 62].

---

## ✨ Key Features

### 1. 🍃 Instant Disease Diagnosis (The "Digital Doctor")
* **Function:** Identifies 7 distinct classes of tea leaf conditions in under 2 seconds[cite: 29, 52].
* **Classes Detected:** Tea Algal Leaf Spot, Brown Blight, Gray Blight, Helopeltis, Red Spider, Green Mirid Bug, and Healthy Leaf[cite: 45].
* **Tech:** Powered by a transfer-learning optimized **ConvNeXtTiny** model[cite: 38].

![Disease Diagnosis Screenshot](assets/scanner_demo.png)
### 2. 🤖 AI Expert Chatbot
* **Function:** Farmers can ask "How do I fix this?" and receive safe, verified answers sourced from official technical manuals[cite: 30].
* **Tech:** Runs on a quantized **Qwen-0.5B** Small Language Model (SLM) optimized for CPU inference[cite: 39].

![Chatbot Screenshot](assets/chatbot_demo.png)
### 3. 🗺️ Live Disease Geo-Heatmap
* **Function:** A real-time geospatial map that tracks disease outbreaks across regions to help researchers and authorities monitor spread patterns[cite: 31].

![Heatmap Screenshot](assets/heatmap_demo.png)
### 4. 🌦️ Weather-Based Risk Alerts
* **Function:** A logic-based engine that correlates real-time weather data (humidity, temperature) to forecast fungal disease risks before they spread[cite: 32].

---

## 🏗️ System Architecture

TeaCare is architected for performance on low-end devices, ensuring accessibility for all farmers.

### Tech Stack
* **Frontend (Mobile):** [Flutter (Dart)](https://flutter.dev/) - Selected for cross-platform consistency and native performance[cite: 34].
* **Backend:** [FastAPI (Python)](https://fastapi.tiangolo.com/) - Handles asynchronous inference requests and database orchestration[cite: 36].
* **AI Engine:**
    * **Visual:** ConvNeXtTiny (Transfer Learning)[cite: 38].
    * **NLP:** Qwen-0.5B (Quantized)[cite: 39].
* **Web Dashboard:** Next.js (for administrative analytics).

---

## 📊 Performance & Results

The system achieved an **Overall Accuracy of 88%** across all test classes[cite: 41].

| Metric | Value | Significance |
| :--- | :--- | :--- |
| **Overall Accuracy** | **88%** | ]Reliable identification across 7 classes[cite: 41]. |
| **Healthy Leaf Recall** | **0.99** | Near-perfect reliability in identifying healthy plants, preventing unnecessary chemical usage [cite: 43-44]. |
| **Inference Time** | **< 2s** | Real-time performance suitable for field use[cite: 52]. |

![Confusion Matrix](assets/confusion_matrix.png)
---

## 🚀 Getting Started

Follow these instructions to set up the project locally.

### Prerequisites
* Flutter SDK (Latest Stable)
* Python 3.9+
* Node.js (for Web Dashboard)

### 1. Backend Setup
```bash
# Clone the repository
git clone [https://github.com/nimeshkavindu/TeaCare.git](https://github.com/nimeshkavindu/TeaCare.git)
cd TeaCare/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --reload
```

## 2. Mobile App Setup

To get the mobile application up and running, follow these steps:

```bash
# Navigate to the mobile app directory
cd ../mobile_app

# Get dependencies
flutter pub get

# Configure API URL
# Go to lib/core/constants.dart and set BASE_URL to your local IP

# Run the app
flutter run
```
## 📂 Project Structure
To maintain the alignment of the directory tree, I have placed the structure inside a plaintext code block. This ensures that the lines and spacing remain consistent across different screens.

```bash
TeaCare/
├── mobile_app/      # Flutter Application
│   ├── lib/
│   ├── assets/
│   └── pubspec.yaml
├── backend/         # FastAPI Server & AI Models
│   ├── app/
│   ├── models/      # ConvNeXt and Qwen model files
│   └── main.py
├── web_dashboard/   # Next.js Analytics Dashboard
└── README.md
```
## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

import 'package:flutter/material.dart';
import 'dart:io';
import 'treatment_screen.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:latlong2/latlong.dart'; 
import 'location_picker_screen.dart';

class DiagnosisScreen extends StatefulWidget {
  final int reportId;
  final String diseaseName;
  final String confidence;
  final String imagePath;
  final List<dynamic> symptoms;
  final List<dynamic> causes;
  final List<dynamic> treatments;

  const DiagnosisScreen({
    super.key,
    required this.reportId,
    required this.diseaseName,
    required this.confidence,
    required this.imagePath,
    required this.symptoms,
    required this.causes,
    required this.treatments,
  });

  @override
  State<DiagnosisScreen> createState() => _DiagnosisScreenState();
}

class _DiagnosisScreenState extends State<DiagnosisScreen> {
  // Update with your IP
  final String baseUrl = "http://192.168.8.122:8000";

  void _markLocation() async {
    final LatLng? result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const LocationPickerScreen()),
    );

    if (result != null) {
      _sendLocation(result.latitude, result.longitude);
    }
  }

  Future<void> _sendLocation(double lat, double lng) async {
    try {
      await http.patch(
        Uri.parse("$baseUrl/history/${widget.reportId}/location"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"latitude": lat, "longitude": lng}),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Location Saved!"),
            backgroundColor: Color.fromARGB(255, 76, 175, 80),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Failed to save location"),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _reportIncorrect() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Help us improve"),
        content: const Text("What is the correct disease?"),
        actions: [
          TextButton(
            child: const Text("Cancel"),
            onPressed: () => Navigator.pop(context),
          ),
          TextButton(
            child: const Text("Submit"),
            onPressed: () => _sendFeedback("Corrected by User"),
          ),
        ],
      ),
    );
  }

  Future<void> _sendFeedback(String correctDisease) async {
    Navigator.pop(context);
    try {
      await http.post(
        Uri.parse("$baseUrl/history/${widget.reportId}/feedback"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "is_correct": false,
          "correct_disease": correctDisease,
        }),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Feedback Sent!"),
            backgroundColor: Colors.blue,
          ),
        );
      }
    } catch (e) {
      print(e);
    }
  }

  // --- UI BUILDER ---
  @override
  Widget build(BuildContext context) {
    // 1. Determine Status Colors
    bool isHealthy = widget.diseaseName.toLowerCase().contains("healthy");

    // Healthy = Green Theme, Disease = Red Theme
    Color statusColor = isHealthy
        ? Colors.green
        : const Color(0xFFD32F2F); // Red
    Color statusBg = isHealthy
        ? const Color(0xFFE8F5E9)
        : const Color(0xFFFFEBEE); // Light Red
    IconData statusIcon = isHealthy
        ? Icons.check_circle
        : Icons.warning_amber_rounded;

    return Scaffold(
      backgroundColor: const Color(0xFFF3F4F6), // Light Gray Background
      appBar: AppBar(
        backgroundColor: const Color(0xFF4E7C46), // Dark Green Header
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.eco, color: Colors.white),
            SizedBox(width: 8),
            Text(
              "TeaCare",
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share, color: Colors.white),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // --- HEADER ALERT CARD ---
            Container(
              width: double.infinity,
              color: const Color(0xFF4E7C46), // Match Header
              padding: const EdgeInsets.only(bottom: 24),
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 20),
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.1),
                      blurRadius: 10,
                      offset: const Offset(0, 5),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    // Icon Bubble
                    Container(
                      width: 50,
                      height: 50,
                      decoration: BoxDecoration(
                        color: statusBg,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(statusIcon, color: statusColor, size: 28),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      isHealthy ? "Healthy Plant" : "Disease Detected",
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      widget.diseaseName,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                        color: statusColor,
                      ),
                    ),
                    const SizedBox(height: 12),
                    // Confidence Pill
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(
                          0xFFE8F5E9,
                        ), // Always light green for confidence
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.check_circle,
                            size: 16,
                            color: Color(0xFF2E7D32),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            "${widget.confidence} Confidence",
                            style: const TextStyle(
                              color: Color(0xFF2E7D32),
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  // --- SCANNED IMAGE ---
                  Stack(
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(20),
                        child: Image.file(
                          File(widget.imagePath),
                          width: double.infinity,
                          height: 220,
                          fit: BoxFit.cover,
                        ),
                      ),
                      Positioned(
                        top: 12,
                        right: 12,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 5,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.6),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Text(
                            "Scanned Image",
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // --- SYMPTOMS CARD ---
                  if (widget.symptoms.isNotEmpty)
                    _buildInfoCard(
                      "Symptoms",
                      Icons.visibility,
                      Colors.orange.shade100,
                      const Color(0xFFFF9800),
                      widget.symptoms,
                    ),
                  const SizedBox(height: 16),

                  // --- CAUSES CARD ---
                  if (widget.causes.isNotEmpty)
                    _buildInfoCard(
                      "Causes",
                      Icons.search,
                      Colors.blue.shade100,
                      const Color(0xFF2196F3),
                      widget.causes,
                    ),

                  const SizedBox(height: 24),

                  // --- ACTION BUTTONS ---

                  // 1. Treatment (Primary)
                  if (!isHealthy)
                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: ElevatedButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => TreatmentScreen(
                                diseaseName: widget.diseaseName,
                                treatments: widget.treatments,
                              ),
                            ),
                          );
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF4E7C46), // Green
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          elevation: 4,
                          shadowColor: const Color(0xFF4E7C46).withOpacity(0.4),
                        ),
                        child: const Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              "Treatment Recommendation",
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            Icon(
                              Icons.arrow_forward_ios,
                              color: Colors.white,
                              size: 18,
                            ),
                          ],
                        ),
                      ),
                    ),
                  const SizedBox(height: 12),

                  // 2. Save Location (Secondary)
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: _markLocation,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black87,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                          side: BorderSide(color: Colors.grey.shade300),
                        ),
                        elevation: 0,
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.location_on,
                            color: Color(0xFF4E7C46),
                          ), // Green Icon
                          SizedBox(width: 8),
                          Text(
                            "Save Location",
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 3. Feedback Link
                  GestureDetector(
                    onTap: _reportIncorrect,
                    child: const Text(
                      "Wrong diagnosis? Give feedback",
                      style: TextStyle(
                        color: Colors.grey,
                        decoration: TextDecoration.underline,
                        decorationStyle: TextDecorationStyle.dotted,
                        fontSize: 13,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // --- HELPER: Info Card Builder (Updated Design) ---
  Widget _buildInfoCard(
    String title,
    IconData icon,
    Color bgCol,
    Color iconCol,
    List<dynamic> items,
  ) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 15,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: bgCol.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: iconCol, size: 22),
              ),
              const SizedBox(width: 12),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Icon(Icons.circle, size: 8, color: iconCol),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      item.toString(),
                      style: const TextStyle(
                        color: Colors.black54,
                        height: 1.5,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

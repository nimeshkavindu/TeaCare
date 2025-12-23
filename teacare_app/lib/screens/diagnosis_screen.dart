import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';

class DiagnosisScreen extends StatefulWidget {
  final int reportId; // NEW: Need ID to update location/feedback
  final String diseaseName;
  final String confidence;
  final String imagePath;
  final List<dynamic> symptoms;
  final String treatment;

  const DiagnosisScreen({
    super.key,
    required this.reportId,
    required this.diseaseName,
    required this.confidence,
    required this.imagePath,
    required this.symptoms,
    required this.treatment,
  });

  @override
  State<DiagnosisScreen> createState() => _DiagnosisScreenState();
}

class _DiagnosisScreenState extends State<DiagnosisScreen> {
  // Update with your IP
  final String baseUrl = "http://192.168.8.122:8000"; 

  void _markLocation() {
    // In a real app, open Google Maps picker here.
    // For now, we simulate sending coordinates.
    _sendLocation(6.9271, 79.8612); // Example: Colombo
  }

  Future<void> _sendLocation(double lat, double lng) async {
    try {
      await http.patch(
        Uri.parse("$baseUrl/history/${widget.reportId}/location"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"latitude": lat, "longitude": lng}),
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Location Saved to Map!"), backgroundColor: Colors.green),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Failed to save location"), backgroundColor: Colors.red),
      );
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
            child: const Text("Healthy Leaf"),
            onPressed: () => _sendFeedback("Healthy Leaf"),
          ),
           TextButton(
            child: const Text("Blister Blight"),
            onPressed: () => _sendFeedback("Blister Blight"),
          ),
        ],
      ),
    );
  }

  Future<void> _sendFeedback(String correctDisease) async {
    Navigator.pop(context); // Close dialog
    try {
      await http.post(
        Uri.parse("$baseUrl/history/${widget.reportId}/feedback"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"is_correct": false, "correct_disease": correctDisease}),
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Thank you! Use this to retrain later."), backgroundColor: Colors.blue),
      );
    } catch (e) {
      print(e);
    }
  }

  @override
  Widget build(BuildContext context) {
    bool isBlurry = widget.diseaseName == "Unknown" && widget.confidence == "0.00%";

    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(title: const Text("Diagnosis Result"), backgroundColor: Colors.transparent, elevation: 0, foregroundColor: Colors.black),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.file(File(widget.imagePath), width: double.infinity, height: 250, fit: BoxFit.cover),
            ),
            const SizedBox(height: 24),

            if (isBlurry)
              Container(
                padding: const EdgeInsets.all(16),
                color: Colors.red.withOpacity(0.1),
                child: const Row(
                  children: [
                    Icon(Icons.error, color: Colors.red),
                    SizedBox(width: 10),
                    Expanded(child: Text("Image is too blurry. Please retake.")),
                  ],
                ),
              )
            else ...[
              // RESULT CARD
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.green.withOpacity(0.3))),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle, color: Colors.green, size: 40),
                    const SizedBox(width: 16),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(widget.diseaseName, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.black)),
                        Text("Confidence: ${widget.confidence}", style: const TextStyle(color: Colors.grey)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              
              // TREATMENT
              const Text("Treatment:", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text(widget.treatment, style: const TextStyle(fontSize: 16)),
              const SizedBox(height: 30),

              // ACTION BUTTONS
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _markLocation,
                      icon: const Icon(Icons.location_on),
                      label: const Text("Save Location"),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _reportIncorrect,
                      child: const Text("Wrong Diagnosis?"),
                    ),
                  ),
                ],
              ),
            ]
          ],
        ),
      ),
    );
  }
}
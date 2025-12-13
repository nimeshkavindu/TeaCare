import 'package:flutter/material.dart';
import 'dart:io';

class DiagnosisScreen extends StatelessWidget {
  final String diseaseName;
  final String confidence;
  final String imagePath;
  final List<dynamic> symptoms;
  final String treatment;

  const DiagnosisScreen({
    super.key,
    required this.diseaseName,
    required this.confidence,
    required this.imagePath,
    required this.symptoms,
    required this.treatment,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: const Text(
          "Diagnosis Result",
          style: TextStyle(color: Colors.black),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // display photo
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.file(
                File(imagePath),
                width: double.infinity,
                height: 250,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(height: 24),

            // disease name and confidance score
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.red.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.warning_amber_rounded,
                    color: Colors.red,
                    size: 40,
                  ),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        diseaseName,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.red,
                        ),
                      ),
                      Text(
                        "Confidence: $confidence",
                        style: const TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // symptoms
            const Text(
              "Symptoms Detected:",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ...symptoms.map(
              (s) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    const Icon(Icons.circle, size: 8, color: Colors.green),
                    const SizedBox(width: 8),
                    Expanded(child: Text(s)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Treatment
            const Text(
              "Recommended Treatment:",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                treatment,
                style: const TextStyle(fontSize: 16, color: Colors.black87),
              ),
            ),

            const SizedBox(height: 30),

            // 5. Done Button
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF11D452),
                ),
                child: const Text(
                  "Scan Another",
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

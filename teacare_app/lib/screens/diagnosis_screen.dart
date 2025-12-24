import 'package:flutter/material.dart';
import 'dart:io';
import 'treatment_screen.dart'; // We will create this next

class DiagnosisScreen extends StatefulWidget {
  final int reportId;
  final String diseaseName;
  final String confidence;
  final String imagePath;
  final List<dynamic> symptoms;
  final List<dynamic> causes; // Received from backend
  final List<dynamic> treatments; // Received from backend

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
  // ... (Keep your existing _markLocation and _reportIncorrect functions here) ...

  @override
  Widget build(BuildContext context) {
    // Check if healthy to change colors
    bool isHealthy = widget.diseaseName.toLowerCase().contains("healthy");
    Color statusColor = isHealthy ? Colors.green : Colors.red;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("TeaCare", style: TextStyle(color: Colors.white)),
        backgroundColor: const Color(0xFF3B5E3C), // Dark Green Header
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // 1. HEADER SECTION
            Container(
              width: double.infinity,
              padding: const EdgeInsets.only(bottom: 20, left: 20, right: 20),
              decoration: const BoxDecoration(
                color: Color(0xFF3B5E3C),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(30),
                  bottomRight: Radius.circular(30),
                ),
              ),
              child: Column(
                children: [
                  CircleAvatar(
                    backgroundColor: Colors.white.withOpacity(0.2),
                    radius: 30,
                    child: Icon(
                      isHealthy ? Icons.check : Icons.warning_amber_rounded,
                      color: statusColor,
                      size: 30,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    isHealthy ? "Healthy Leaf" : "Disease Detected",
                    style: const TextStyle(color: Colors.white70, fontSize: 16),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    widget.diseaseName,
                    style: TextStyle(
                      color: isHealthy
                          ? Colors.greenAccent
                          : const Color(0xFFFF5252),
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.9),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      "${widget.confidence} Confidence",
                      style: const TextStyle(
                        color: Colors.black87,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 2. SCANNED IMAGE
                  Stack(
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(15),
                        child: Image.file(
                          File(widget.imagePath),
                          width: double.infinity,
                          height: 200,
                          fit: BoxFit.cover,
                        ),
                      ),
                      Positioned(
                        top: 10,
                        right: 10,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.black54,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Text(
                            "Scanned Image",
                            style: TextStyle(color: Colors.white, fontSize: 12),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // 3. SYMPTOMS CARD
                  if (widget.symptoms.isNotEmpty)
                    _buildInfoCard(
                      "Symptoms",
                      Icons.remove_red_eye,
                      Colors.orange.shade100,
                      Colors.orange.shade900,
                      widget.symptoms,
                    ),

                  const SizedBox(height: 15),

                  // 4. CAUSES CARD
                  if (widget.causes.isNotEmpty)
                    _buildInfoCard(
                      "Causes",
                      Icons.search,
                      Colors.blue.shade50,
                      Colors.blue.shade900,
                      widget.causes,
                    ),

                  const SizedBox(height: 25),

                  // 5. TREATMENT BUTTON
                  if (!isHealthy)
                    SizedBox(
                      width: double.infinity,
                      height: 55,
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
                          backgroundColor: const Color(
                            0xFF437649,
                          ), // Nice Forest Green
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          elevation: 4,
                        ),
                        child: const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              "Treatment Recommendation",
                              style: TextStyle(
                                fontSize: 18,
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            SizedBox(width: 8),
                            Icon(
                              Icons.arrow_forward_ios,
                              color: Colors.white,
                              size: 18,
                            ),
                          ],
                        ),
                      ),
                    ),

                  const SizedBox(height: 20),

                  // 6. ACTION BUTTONS (Save & Wrong)
                  Row(
                    children: [
                      Expanded(
                        child: _buildActionButton(
                          "Save Location",
                          Icons.location_on,
                          Colors.blue,
                          () {},
                        ),
                      ), // Call _markLocation
                      const SizedBox(width: 15),
                      Expanded(
                        child: _buildActionButton(
                          "Wrong Diagnosis?",
                          Icons.flag,
                          Colors.grey,
                          () {},
                        ),
                      ), // Call _reportIncorrect
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard(
    String title,
    IconData icon,
    Color bgCol,
    Color iconCol,
    List<dynamic> items,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.shade100,
            blurRadius: 5,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: bgCol,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: iconCol, size: 20),
              ),
              const SizedBox(width: 10),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ...items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.circle, size: 8, color: iconCol),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      item.toString(),
                      style: const TextStyle(
                        color: Colors.black87,
                        height: 1.4,
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

  Widget _buildActionButton(
    String label,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, color: color, size: 20),
      label: Text(label, style: TextStyle(color: color)),
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 12),
        side: BorderSide(color: color.withOpacity(0.5)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }
}

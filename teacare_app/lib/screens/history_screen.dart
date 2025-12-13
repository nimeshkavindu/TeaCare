import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class HistoryScreen extends StatefulWidget {
  final int userId;
  const HistoryScreen({super.key, required this.userId});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<dynamic> _reports = [];
  bool _isLoading = true;

  final String serverUrl = "http://192.168.8.122:8000";

  @override
  void initState() {
    super.initState();
    _fetchHistory();
  }

  Future<void> _fetchHistory() async {
    try {
      final response = await http.get(
        Uri.parse("$serverUrl/history/${widget.userId}"),
      );

      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _reports = jsonDecode(response.body);
            _isLoading = false;
          });
        }
      } else {
        print("Server Error: ${response.statusCode}");
        if (mounted) setState(() => _isLoading = false);
      }
    } catch (e) {
      print("Connection Error: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: const Text(
          "Disease Reports",
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF11D452)),
            )
          : _reports.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.history, size: 64, color: Colors.grey[300]),
                  const SizedBox(height: 16),
                  const Text(
                    "No reports found",
                    style: TextStyle(color: Colors.grey, fontSize: 18),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _reports.length,
              itemBuilder: (context, index) {
                final report = _reports[index];
                final isHealthy = report['disease_name'] == "Healthy Leaf";

                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 5,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      // --- ICON ---
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: isHealthy
                              ? const Color(0xFFDCFCE7)
                              : const Color(0xFFFEE2E2),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.spa,
                          color: isHealthy
                              ? const Color(0xFF15803D)
                              : Colors.red,
                          size: 28,
                        ),
                      ),
                      const SizedBox(width: 16),

                      // --- TEXT DETAILS ---
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              report['disease_name'],
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                                color: Color(0xFF1F2937),
                              ),
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                Icon(
                                  Icons.analytics_outlined,
                                  size: 14,
                                  color: Colors.grey[500],
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  "Confidence: ${report['confidence']}",
                                  style: TextStyle(
                                    color: Colors.grey[600],
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 2),
                            Row(
                              children: [
                                Icon(
                                  Icons.calendar_today_outlined,
                                  size: 14,
                                  color: Colors.grey[500],
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  report['timestamp'],
                                  style: TextStyle(
                                    color: Colors.grey[600],
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'diagnosis_screen.dart';
import 'history_screen.dart';
import 'weather_screen.dart';
import 'community_screen.dart';

class HomeScreen extends StatefulWidget {
  final String userName;
  final int userId;
  const HomeScreen({super.key, required this.userName, required this.userId});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ImagePicker _picker = ImagePicker();
  bool _isUploading = false;
  List<dynamic> _history = [];

  // Ensure this IP address is accessible from your device/emulator
  final String serverUrl = "http://192.168.8.122:8000/predict";

  @override
  void initState() {
    super.initState();
    _fetchHistory();
  }

  // Fetch history from backend
  Future<void> _fetchHistory() async {
    final String baseUrl = serverUrl.replaceAll("/predict", "");
    final String historyUrl = "$baseUrl/history/${widget.userId}";

    try {
      final response = await http.get(Uri.parse(historyUrl));

      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _history = jsonDecode(response.body);
          });
        }
      } else {
        print("Server Error fetching history: ${response.statusCode}");
      }
    } catch (e) {
      print("Connection Error fetching history: $e");
    }
  }

  // Show error snackbar
  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  // Function to pick image and upload
  Future<void> _scanLeaf(ImageSource source) async {
    try {
      final XFile? photo = await _picker.pickImage(source: source);
      if (photo == null) return;

      setState(() => _isUploading = true);

      // 1. Create Multipart Request
      var request = http.MultipartRequest('POST', Uri.parse(serverUrl));

      // 2. Add the image file
      request.files.add(await http.MultipartFile.fromPath('file', photo.path));

      // 3. Add User ID (So we can save history)
      request.fields['user_id'] = widget.userId.toString();

      // 4. Send
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        // Refresh history to show the new scan in "Recent Activity"
        _fetchHistory();

        // 5. Navigate to Results Screen
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => DiagnosisScreen(
                diseaseName: data['disease_name'],
                confidence: data['confidence'],
                imagePath: photo.path, // Pass local path to display
                treatment: data['treatment'],
                symptoms: data['symptoms'] ?? [],
              ),
            ),
          );
        }
      } else {
        _showError("Server Error: ${response.statusCode}");
      }
    } catch (e) {
      _showError("Connection Failed: $e");
    } finally {
      if (mounted) {
        setState(() => _isUploading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),

      // Header
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        automaticallyImplyLeading: false,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: const BoxDecoration(
                color: Color(0xFF11D452),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.spa, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 12),
            const Text(
              "TeaCare",
              style: TextStyle(
                color: Color(0xFF1F2937),
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(
              Icons.notifications_outlined,
              color: Color(0xFF6B7280),
            ),
            onPressed: () {},
          ),
          const Padding(
            padding: EdgeInsets.only(right: 16),
            child: CircleAvatar(
              backgroundColor: Color(0xFFFFE0B2),
              child: Icon(Icons.person, color: Colors.orange),
            ),
          ),
        ],
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Column(
                children: [
                  Text(
                    "Welcome back, ${widget.userName}!",
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1F2937),
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    "Keep your tea plants healthy with smart monitoring",
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 14, color: Color(0xFF6B7280)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF11D452)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Container(
                    width: 80,
                    height: 80,
                    decoration: const BoxDecoration(
                      color: Color(0xFFDCFCE7),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.camera_alt_rounded,
                      color: Color(0xFF11D452),
                      size: 40,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    "Scan Tea Leaf",
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1F2937),
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    "Check for diseases and get instant diagnosis",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Color(0xFF6B7280), fontSize: 14),
                  ),
                  const SizedBox(height: 24),

                  // Camera button
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton.icon(
                      onPressed: _isUploading
                          ? null
                          : () => _scanLeaf(ImageSource.camera),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF15803D),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        elevation: 0,
                      ),
                      icon: _isUploading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            )
                          : const Icon(Icons.camera_alt_outlined),
                      label: Text(
                        _isUploading ? "Analyzing..." : "Take Photo",
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  // Select from gallery
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: OutlinedButton.icon(
                      onPressed: _isUploading
                          ? null
                          : () => _scanLeaf(ImageSource.gallery),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Color(0xFF11D452)),
                        foregroundColor: const Color(0xFF15803D),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text(
                        "Pick from Gallery",
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // Quick Actions
            const Text(
              "Quick Actions",
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1F2937),
              ),
            ),
            const SizedBox(height: 16),
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              childAspectRatio: 1.5,
              children: [
                _buildQuickAction(
                  Icons.pest_control,
                  Colors.red,
                  "Disease Reports",
                  "View history",
                  () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            HistoryScreen(userId: widget.userId),
                      ),
                    );
                  },
                ),
                _buildQuickAction(
                  Icons.cloud,
                  Colors.blue,
                  "Weather Alerts",
                  "Today's forecast",
                  () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const WeatherScreen(),
                      ),
                    );
                  },
                ),
                _buildQuickAction(
                  Icons.groups,
                  Colors.green,
                  "Community",
                  "Ask farmers",
                  () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => CommunityScreen(
                          userId: widget.userId,
                          userName: widget.userName,
                        ),
                      ),
                    );
                  },
                ),
                _buildQuickAction(
                  Icons.forum,
                  Colors.purple,
                  "Help Chat",
                  "Get support",
                  () {},
                ),
              ],
            ),
            const SizedBox(height: 32),

            // Recent Activity List
            const Text(
              "Recent Activity",
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1F2937),
              ),
            ),
            const SizedBox(height: 16),
            _history.isEmpty
                ? const Padding(
                    padding: EdgeInsets.symmetric(vertical: 20),
                    child: Center(
                      child: Text(
                        "No scans yet. Take a photo!",
                        style: TextStyle(color: Colors.grey),
                      ),
                    ),
                  )
                : Column(
                    children: _history.map((report) {
                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.05),
                              blurRadius: 5,
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: report['disease_name'] == "Healthy Leaf"
                                    ? const Color(0xFFDCFCE7)
                                    : const Color(0xFFFEE2E2),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(
                                Icons.spa,
                                color: report['disease_name'] == "Healthy Leaf"
                                    ? const Color(0xFF11D452)
                                    : Colors.red,
                                size: 24,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    report['disease_name'],
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: 14,
                                    ),
                                  ),
                                  Text(
                                    report['timestamp'],
                                    style: const TextStyle(
                                      color: Color(0xFF6B7280),
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const Icon(
                              Icons.chevron_right,
                              color: Color(0xFF9CA3AF),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
          ],
        ),
      ),

      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        selectedItemColor: const Color(0xFF11D452),
        unselectedItemColor: const Color(0xFF9CA3AF),
        showUnselectedLabels: true,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: "Home"),
          BottomNavigationBarItem(
            icon: Icon(Icons.document_scanner),
            label: "Scan",
          ),
          BottomNavigationBarItem(icon: Icon(Icons.forum), label: "Forum"),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: "Profile"),
        ],
      ),
    );
  }

  Widget _buildQuickAction(
    IconData icon,
    Color color,
    String title,
    String subtitle,
    VoidCallback onTap,
  ) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 5),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    color: Color(0xFF1F2937),
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 11,
                    color: Color(0xFF6B7280),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

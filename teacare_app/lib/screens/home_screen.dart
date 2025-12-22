import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'diagnosis_screen.dart';
import 'history_screen.dart';
import 'weather_screen.dart';
import 'community_screen.dart';
import 'profile_screen.dart';
import 'heat_map_screen.dart';

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
  
  // Ensure this IP matches your setup
  final String serverUrl = "http://192.168.8.122:8000/predict";

  int _selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    _fetchHistory();
  }

  // --- NAVIGATION LOGIC ---
  void _onItemTapped(int index) {
    if (index == 1) {
      _showScanOptions();
    } else {
      setState(() {
        _selectedIndex = index;
      });
    }
  }

  // --- SCAN MODAL ---
  void _showScanOptions() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (BuildContext bc) {
        return SafeArea(
          child: Wrap(
            children: <Widget>[
              ListTile(
                leading: const Icon(Icons.camera_alt, color: Color(0xFF11D452)),
                title: const Text('Take Photo'),
                onTap: () {
                  Navigator.pop(context);
                  _scanLeaf(ImageSource.camera);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library, color: Color(0xFF15803D)),
                title: const Text('Choose from Gallery'),
                onTap: () {
                  Navigator.pop(context);
                  _scanLeaf(ImageSource.gallery);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  // --- FETCH HISTORY ---
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
      }
    } catch (e) {
      print("Error fetching history: $e");
    }
  }

  // --- SCAN LOGIC ---
  Future<void> _scanLeaf(ImageSource source) async {
    try {
      final XFile? photo = await _picker.pickImage(source: source);
      if (photo == null) return;

      setState(() => _isUploading = true);

      var request = http.MultipartRequest('POST', Uri.parse(serverUrl));
      request.files.add(await http.MultipartFile.fromPath('file', photo.path));
      request.fields['user_id'] = widget.userId.toString();

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _fetchHistory();

        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => DiagnosisScreen(
                diseaseName: data['disease_name'],
                confidence: data['confidence'],
                imagePath: photo.path,
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
      if (mounted) setState(() => _isUploading = false);
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    // --- UPDATED PAGE LIST (Map is now Index 3) ---
    final List<Widget> pages = [
      _buildHomeDashboard(),
      const SizedBox(), 
      CommunityScreen(userId: widget.userId, userName: widget.userName),
      const HeatMapScreen(), // <--- NEW POSITION
    ];

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),

      // --- APP BAR ---
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
            icon: const Icon(Icons.notifications_outlined, color: Color(0xFF6B7280)),
            onPressed: () {},
          ),
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: GestureDetector(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ProfileScreen(userName: widget.userName),
                  ),
                );
              },
              child: const CircleAvatar(
                backgroundColor: Color(0xFFFFE0B2),
                child: Icon(Icons.person, color: Colors.orange),
              ),
            ),
          ),
        ],
      ),

      body: pages[_selectedIndex],

      // --- BOTTOM NAVIGATION (Updated) ---
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        selectedItemColor: const Color(0xFF11D452),
        unselectedItemColor: const Color(0xFF9CA3AF),
        showUnselectedLabels: true,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: "Home",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.document_scanner_outlined),
            activeIcon: Icon(Icons.document_scanner),
            label: "Scan",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.groups_outlined),
            activeIcon: Icon(Icons.groups),
            label: "Community",
          ),
          // --- CHANGED FROM WEATHER TO MAP ---
          BottomNavigationBarItem(
            icon: Icon(Icons.map_outlined),
            activeIcon: Icon(Icons.map),
            label: "Map",
          ),
        ],
      ),
    );
  }

  Widget _buildHomeDashboard() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Welcome Text
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
            "Manage your tea estate efficiently.",
            style: TextStyle(fontSize: 14, color: Color(0xFF6B7280)),
          ),
          const SizedBox(height: 24),

          // Main Scan Card
          GestureDetector(
            onTap: _showScanOptions,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF11D452), Color(0xFF15803D)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF11D452).withOpacity(0.3),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.camera_enhance, color: Colors.white, size: 32),
                  ),
                  const SizedBox(width: 16),
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Identify Disease",
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        "Tap to scan a leaf",
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 32),

          // --- QUICK ACTIONS GRID ---
          const Text(
            "Quick Actions",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1F2937)),
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
              // --- 1. WEATHER (Moved from Bottom Bar) ---
              _buildQuickAction(
                Icons.cloud_outlined, // Cloud Icon
                Colors.blue,          // Weather Color
                "Weather",
                "Rain & Forecast",
                () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const WeatherScreen()),
                  );
                },
              ),
              
              // 2. History
              _buildQuickAction(
                Icons.history_edu,
                Colors.orange, // Changed color to differentiate
                "Reports",
                "Past scans",
                () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => HistoryScreen(userId: widget.userId)),
                  );
                },
              ),
              
              // 3. Expert Support
              _buildQuickAction(
                Icons.support_agent,
                Colors.purple,
                "Expert Help",
                "Chat with pros",
                () {},
              ),
              
              // 4. Market Price
              _buildQuickAction(
                Icons.monetization_on_outlined,
                Colors.green,
                "Market Price",
                "Check rates",
                () {},
              ),
            ],
          ),
          const SizedBox(height: 32),

          // Recent Activity
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "Recent Scans",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1F2937)),
              ),
              TextButton(
                onPressed: () {
                   Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => HistoryScreen(userId: widget.userId)),
                  );
                },
                child: const Text("View All"),
              )
            ],
          ),
          const SizedBox(height: 8),
          
          _history.isEmpty
            ? Container(
                padding: const EdgeInsets.all(20),
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Center(child: Text("No scans yet. Start by scanning a leaf!")),
              )
            : Column(
                children: _history.take(3).map((report) {
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: BorderSide(color: Colors.grey.shade200),
                    ),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: report['disease_name'] == "Healthy Leaf" 
                            ? const Color(0xFFDCFCE7) 
                            : const Color(0xFFFEE2E2),
                        child: Icon(
                          Icons.spa, 
                          color: report['disease_name'] == "Healthy Leaf" 
                              ? const Color(0xFF15803D) 
                              : Colors.red,
                          size: 20,
                        ),
                      ),
                      title: Text(
                        report['disease_name'], 
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)
                      ),
                      subtitle: Text(
                        report['timestamp'],
                        style: const TextStyle(fontSize: 12),
                      ),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: Colors.grey),
                    ),
                  );
                }).toList(),
              ),
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
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(fontSize: 11, color: Colors.grey),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
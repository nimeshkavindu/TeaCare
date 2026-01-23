import 'package:flutter/material.dart';

class AppGuideScreen extends StatefulWidget {
  const AppGuideScreen({super.key});

  @override
  State<AppGuideScreen> createState() => _AppGuideScreenState();
}

class _AppGuideScreenState extends State<AppGuideScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  // --- GUIDE DATA ---
  // Updated to use "imagePath" (String) instead of Image widget
  final List<Map<String, dynamic>> _guideSteps = [
    {
      "title": "Scan Your Plant",
      "desc": "Tap 'Identify Disease' on the home screen. Center the tea leaf in the camera frame and take a clear photo.",
      "imagePath": "assets/images/guide_1.png",
    },
    {
      "title": "Instant AI Analysis",
      "desc": "Our AI scans the leaf texture and spots in seconds to detect diseases like Blister Blight or Red Spider Mite.",
      "imagePath": "assets/images/guide_2.png",
    },
    {
      "title": "Get Treatment Plans",
      "desc": "View the diagnosis confidence and click 'Treatment Recommendation' to see organic and chemical solutions.",
      "imagePath": "assets/images/guide_3.png",
    },
    {
      "title": "Join the Community",
      "desc": "Share your findings, ask questions, and exchange farming tips with other tea planters in the forum.",
      "imagePath": "assets/images/guide_5.png", // Numbering adjusted based on your list
    },
    {
      "title": "Ask the AI Agronomist",
      "desc": "Chat with our smart assistant to get instant answers about fertilizers, soil pH, and general plant care.",
      "imagePath": "assets/images/guide_6.png",
    },
    {
      "title": "Monitor Your Field",
      "desc": "Save the location of diseased plants to populate the Epidemiology Map and track outbreaks.",
      "imagePath": "assets/images/guide_4.png",
    },
  ];

  void _nextPage() {
    if (_currentPage < _guideSteps.length - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      Navigator.pop(context); // Close guide
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Skip", style: TextStyle(color: Colors.grey)),
          ),
        ],
      ),
      body: Column(
        children: [
          // 1. SLIDING CONTENT
          Expanded(
            child: PageView.builder(
              controller: _pageController,
              onPageChanged: (index) => setState(() => _currentPage = index),
              itemCount: _guideSteps.length,
              itemBuilder: (context, index) {
                return _buildPage(
                  _guideSteps[index]['title'],
                  _guideSteps[index]['desc'],
                  _guideSteps[index]['imagePath'], // Pass string path
                );
              },
            ),
          ),

          // 2. BOTTOM CONTROLS
          Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                // Pagination Dots
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(
                    _guideSteps.length,
                    (index) => _buildDot(index),
                  ),
                ),
                const SizedBox(height: 32),

                // Next Button
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: _nextPage,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF4CAF50), // Tea Green
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      elevation: 0,
                    ),
                    child: Text(
                      _currentPage == _guideSteps.length - 1
                          ? "Get Started"
                          : "Next",
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // --- WIDGET BUILDERS ---

  // Updated to accept String imagePath instead of IconData
  Widget _buildPage(String title, String desc, String imagePath) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // IMAGE AREA
          Container(
            height: 280,
            width: double.infinity,
            decoration: BoxDecoration(
              color: const Color(0xFFE8F5E9), // Light Green bg
              borderRadius: BorderRadius.circular(32),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20.0), // Padding inside the green box
              child: Image.asset(
                imagePath,
                fit: BoxFit.contain,
                // Error Builder: Shows an icon if image is missing from assets
                errorBuilder: (context, error, stackTrace) {
                  return Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.image_not_supported, size: 50, color: Colors.grey),
                      const SizedBox(height: 8),
                      Text("Missing: $imagePath", style: const TextStyle(fontSize: 10, color: Colors.grey)),
                    ],
                  );
                },
              ),
            ),
          ),
          const SizedBox(height: 40),

          // TEXT AREA
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1F2937),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            desc,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 16,
              color: Colors.grey,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDot(int index) {
    bool isActive = _currentPage == index;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      margin: const EdgeInsets.symmetric(horizontal: 4),
      height: 8,
      width: isActive ? 24 : 8,
      decoration: BoxDecoration(
        color: isActive ? const Color(0xFF4CAF50) : Colors.grey[300],
        borderRadius: BorderRadius.circular(4),
      ),
    );
  }
}
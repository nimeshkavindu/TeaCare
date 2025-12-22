import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'welcome_screen.dart'; 

class ProfileScreen extends StatelessWidget {
  final String userName;
  // We might need userId later if we want to fetch specific profile details from the server
  // final int userId;

  const ProfileScreen({super.key, required this.userName});

  // --- LOGOUT FUNCTION ---
  Future<void> _handleLogout(BuildContext context) async {
    // 1. Show confirmation dialog
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Logout"),
        content: const Text("Are you sure you want to log out?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false), // Cancel
            child: const Text("Cancel", style: TextStyle(color: Colors.grey)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true), // Confirm
            child: const Text("Logout", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm == true && context.mounted) {
      // 2. Get SharedPreferences and CLEAR all data
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();

      print("User logged out. SharedPreferences cleared.");

      if (!context.mounted) return;
      // 3. Navigate to Welcome Screen and remove all previous screens from history
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (context) => const WelcomeScreen()),
        (Route<dynamic> route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      // Simple AppBar
      appBar: AppBar(
        title: const Text(
          "My Profile",
          style: TextStyle(color: Color(0xFF1F2937), fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        automaticallyImplyLeading: false, // Hide back button
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            // --- HEADER SECTION ---
            const SizedBox(height: 20),
            Center(
              child: Column(
                children: [
                  // Placeholder Avatar using your theme colors
                  CircleAvatar(
                    radius: 50,
                    backgroundColor: const Color(0xFFDCFCE7),
                    child: const Icon(
                      Icons.person,
                      size: 60,
                      color: Color(0xFF11D452),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // User Name
                  Text(
                    userName,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1F2937),
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    "Tea Farmer", // Placeholder role
                    style: TextStyle(
                      fontSize: 16,
                      color: Color(0xFF6B7280),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 40),

            // --- MENU OPTIONS ---
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                      color: Colors.black.withOpacity(0.05), blurRadius: 10),
                ],
              ),
              child: Column(
                children: [
                  _buildProfileOption(
                    icon: Icons.edit_outlined,
                    title: "Edit Profile",
                    onTap: () {
                      // TODO: Navigate to edit profile screen
                      ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text("Coming Soon!")));
                    },
                  ),
                  _buildDivider(),
                  _buildProfileOption(
                    icon: Icons.notifications_outlined,
                    title: "Notifications",
                    onTap: () {
                      // TODO: Notification settings
                    },
                  ),
                  _buildDivider(),
                  _buildProfileOption(
                    icon: Icons.help_outline,
                    title: "Help & Support",
                    onTap: () {
                      // TODO: Navigate to help page or open web link
                    },
                  ),
                  _buildDivider(),
                  _buildProfileOption(
                    icon: Icons.info_outline,
                    title: "About TeaCare",
                    onTap: () {
                       showAboutDialog(
                        context: context,
                        applicationName: "TeaCare",
                        applicationVersion: "1.0.0",
                        applicationLegalese: "© 2024 TeaCare Solutions",
                       );
                    },
                  ),
                ],
              ),
            ),

            const SizedBox(height: 30),

            // --- LOGOUT BUTTON ---
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton.icon(
                onPressed: () => _handleLogout(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFFEE2E2), // Light red
                  foregroundColor: Colors.red, // Red text/icon
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                icon: const Icon(Icons.logout),
                label: const Text(
                  "Log Out",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
             const SizedBox(height: 20),
             Text("Version 1.0.0", style: TextStyle(color: Colors.grey[400])),
          ],
        ),
      ),
    );
  }

  // Helper widget for menu items
  Widget _buildProfileOption({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
            color: const Color(0xFFF3F4F6),
            borderRadius: BorderRadius.circular(8)),
        child: Icon(icon, color: const Color(0xFF1F2937)),
      ),
      title: Text(
        title,
        style: const TextStyle(
            fontSize: 16, fontWeight: FontWeight.w500, color: Color(0xFF1F2937)),
      ),
      trailing:
          const Icon(Icons.chevron_right, color: Color(0xFF9CA3AF), size: 20),
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
    );
  }

  // Helper for dividers
  Widget _buildDivider() {
    return const Divider(height: 1, thickness: 1, color: Color(0xFFF3F4F6));
  }
}
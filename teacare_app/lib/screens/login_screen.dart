import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'home_screen.dart'; 
import 'package:shared_preferences/shared_preferences.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  // Custom Colors
  static const Color kPrimaryGreen = Color(0xFF13EC5B);
  static const Color kBackground = Color(0xFFF6F8F6);
  static const Color kTextDark = Color(0xFF111813);
  static const Color kBorderColor = Color(0xFFDBE6DF);

  final TextEditingController _identifierCtrl = TextEditingController(); 
  final TextEditingController _secretCtrl = TextEditingController(); 

  bool _isLoading = false;

  // UPDATE THIS IP
  final String serverUrl = "http://192.168.8.122:8000/login";

  // --- HELPER: Parse Backend Errors Safely ---
  String _getBackendError(String responseBody) {
    try {
      final data = jsonDecode(responseBody);
      final detail = data['detail'];

      if (detail is String) return detail;
      if (detail is List && detail.isNotEmpty) return detail[0]['msg'];
      
      return "Login failed";
    } catch (e) {
      return "Server Error: $e";
    }
  }

  Future<void> _handleLogin() async {
    String identifier = _identifierCtrl.text.trim();
    String secret = _secretCtrl.text.trim();

    if (identifier.isEmpty || secret.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please enter your credentials")),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final response = await http.post(
        Uri.parse(serverUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "identifier": identifier, 
          "secret": secret          
        }),
      );

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        // Save Session
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('isLoggedIn', true);
        await prefs.setString('userName', data['name']);
        await prefs.setInt('userId', data['user_id']);
        await prefs.setString('userRole', data['role']); 

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Welcome back, ${data['name']}!"),
            backgroundColor: Colors.green[800],
          ),
        );

        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => HomeScreen(
              userName: data['name'],
              userId: data['user_id'], 
            ),
          ),
        );
      } else {
        // Safe Error Handling
        _showError(_getBackendError(response.body));
      }
    } catch (e) {
      _showError("Connection Error: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBackground,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: kTextDark), 
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 20),
              Container(
                height: 96,
                width: 96,
                decoration: BoxDecoration(
                  color: kPrimaryGreen.withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.spa, color: kPrimaryGreen, size: 48),
              ),
              const SizedBox(height: 32),
              const Text(
                "Welcome to TeaCare",
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: kTextDark, height: 1.2),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                "Log in with Phone or Email",
                style: TextStyle(fontSize: 16, color: kTextDark.withOpacity(0.7)),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 40),

              // Inputs
              Align(alignment: Alignment.centerLeft, child: const Text("Phone Number or Email", style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: kTextDark))),
              const SizedBox(height: 8),
              TextField(
                controller: _identifierCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: _inputDecor("Enter phone or email", Icons.person_outline),
              ),
              const SizedBox(height: 24),

              Align(alignment: Alignment.centerLeft, child: const Text("PIN or Password", style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: kTextDark))),
              const SizedBox(height: 8),
              TextField(
                controller: _secretCtrl,
                obscureText: true,
                decoration: _inputDecor("Enter PIN or Password", Icons.lock_outline),
              ),
              const SizedBox(height: 40),

              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: kPrimaryGreen,
                    foregroundColor: kTextDark,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: kTextDark)
                      : const Text("Login", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecor(String hint, IconData icon) {
    return InputDecoration(
      hintText: hint,
      prefixIcon: Icon(icon, color: Colors.grey),
      hintStyle: TextStyle(color: kTextDark.withOpacity(0.4)),
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.all(16),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: kBorderColor)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: kBorderColor)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: kPrimaryGreen, width: 2)),
    );
  }
}
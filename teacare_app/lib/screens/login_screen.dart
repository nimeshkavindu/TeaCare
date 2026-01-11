import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'home_screen.dart';
import 'register_screen.dart';
import 'dart:io';
import 'dart:async';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  // --- STATE & CONTROLLERS ---
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isObscure = true;
  bool _isLoading = false; // RESTORED: Loading state

  // RESTORED: Your Server URL
  final String serverUrl = "http://192.168.8.122:8000/login";

  // --- COLORS (New Design) ---
  final Color kPrimaryColor = const Color(0xFF4CAE4F);
  final Color kBackgroundColor = const Color(0xFFF9FAFB);
  final Color kSurfaceColor = const Color(0xFFFFFFFF);
  final Color kTextColor = const Color(0xFF1F2937);
  final Color kTextMuted = const Color(0xFF6B7280);
  final Color kInputBorder = const Color(0xFFD1D5DB);

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  // --- LOGIC SECTION (Restored from Old Code) ---

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
    // 1. Get Inputs
    String identifier = _emailController.text.trim();
    String secret = _passwordController.text.trim();

    if (identifier.isEmpty || secret.isEmpty) {
      _showError("Please enter your credentials");
      return;
    }

    setState(() => _isLoading = true);

    try {
      // 2. Send Request (With Timeout)
      final response = await http
          .post(
            Uri.parse(serverUrl),
            headers: {"Content-Type": "application/json"},
            body: jsonEncode({"identifier": identifier, "secret": secret}),
          )
          .timeout(const Duration(seconds: 5));

      if (!mounted) return;

      // 3. Handle Responses
      if (response.statusCode == 200) {
        // --- SUCCESS ---
        final data = jsonDecode(response.body);

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

        // Go to Home
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) =>
                HomeScreen(userName: data['name'], userId: data['user_id']),
          ),
        );
      } else if (response.statusCode == 401) {
        _showError("❌ Invalid Phone Number or PIN.");
      } else if (response.statusCode == 403) {
        _showError("⛔ Account Suspended. Contact Admin.");
      } else if (response.statusCode == 500) {
        _showError("⚠️ Server Error. Check Backend Terminal.");
      } else {
        _showError("Login Failed: ${_getBackendError(response.body)}");
      }

      // --- FIX IS HERE: Use Dart Exceptions, not Java ---
    } on SocketException {
      _showError("🔌 Connection Refused. Check IP or Server.");
    } on TimeoutException {
      _showError("⏱️ Connection Timed Out. Check your network.");
    } catch (e) {
      _showError("Error: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  // --- UI SECTION (New Design) ---

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBackgroundColor,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // 1. Header with Back Button
              Align(
                alignment: Alignment.centerLeft,
                child: IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: Icon(Icons.arrow_back, color: kTextColor),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ),

              const SizedBox(height: 40),

              // 2. Logo Section
              Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(
                  color: kPrimaryColor.withOpacity(0.2),
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 20,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Icon(Icons.eco_rounded, color: kPrimaryColor, size: 48),
              ),

              const SizedBox(height: 24),

              // 3. Welcome Text
              Text(
                "Welcome to TeaCare",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.bold,
                  color: kTextColor,
                  fontFamily: 'Poppins',
                ),
              ),
              const SizedBox(height: 8),
              Text(
                "Log in with Phone or Email",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: kTextMuted,
                ),
              ),

              const SizedBox(height: 40),

              // 4. Input Fields Form
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // --- Phone/Email Input ---
                  _buildInputLabel("Phone Number or Email"),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: _emailController,
                    decoration: _buildInputDecoration(
                      hintText: "Enter phone or email",
                      prefixIcon: Icons.person_outline_rounded,
                    ),
                    style: TextStyle(color: kTextColor),
                  ),

                  const SizedBox(height: 24),

                  // --- Password Input ---
                  _buildInputLabel("PIN or Password"),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: _passwordController,
                    obscureText: _isObscure,
                    decoration: _buildInputDecoration(
                      hintText: "Enter PIN or Password",
                      prefixIcon: Icons.lock_outline_rounded,
                      suffixIcon: IconButton(
                        icon: Icon(
                          _isObscure
                              ? Icons.visibility_off_outlined
                              : Icons.visibility_outlined,
                          color: kTextMuted,
                        ),
                        onPressed: () {
                          setState(() {
                            _isObscure = !_isObscure;
                          });
                        },
                      ),
                    ),
                    style: TextStyle(color: kTextColor),
                  ),

                  // --- Forgot Password ---
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: () {
                        // Handle forgot password logic here if needed
                      },
                      child: Text(
                        "Forgot Password?",
                        style: TextStyle(
                          color: kPrimaryColor,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 32),

              // 5. Login Button (NOW FUNCTIONAL)
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  // RESTORED: Logic connection
                  onPressed: _isLoading ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: kPrimaryColor,
                    foregroundColor: Colors.white,
                    elevation: 4,
                    shadowColor: kPrimaryColor.withOpacity(0.4),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(30),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 24,
                          width: 24,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: const [
                            Text(
                              "Login",
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            SizedBox(width: 8),
                            Icon(Icons.arrow_forward_rounded, size: 20),
                          ],
                        ),
                ),
              ),

              const SizedBox(height: 24),

              // 6. Footer (Sign Up)
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    "Don't have an account? ",
                    style: TextStyle(color: kTextMuted, fontSize: 14),
                  ),
                  GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const RegisterScreen(),
                        ),
                      );
                    },
                    child: Text(
                      "Sign Up",
                      style: TextStyle(
                        color: kPrimaryColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  // --- Helper Methods ---

  Widget _buildInputLabel(String label) {
    return Padding(
      padding: const EdgeInsets.only(left: 4.0),
      child: Text(
        label,
        style: TextStyle(
          color: kTextColor,
          fontWeight: FontWeight.w600,
          fontSize: 14,
        ),
      ),
    );
  }

  InputDecoration _buildInputDecoration({
    required String hintText,
    required IconData prefixIcon,
    Widget? suffixIcon,
  }) {
    return InputDecoration(
      filled: true,
      fillColor: kSurfaceColor,
      hintText: hintText,
      hintStyle: TextStyle(color: kTextMuted.withOpacity(0.6), fontSize: 14),
      prefixIcon: Icon(prefixIcon, color: kTextMuted),
      suffixIcon: suffixIcon,
      contentPadding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: kInputBorder),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: kInputBorder),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: kPrimaryColor, width: 2),
      ),
    );
  }
}

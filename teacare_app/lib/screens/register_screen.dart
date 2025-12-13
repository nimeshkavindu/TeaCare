import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _phoneCtrl = TextEditingController();
  final TextEditingController _pinCtrl = TextEditingController();
  bool _isLoading = false;

  final String serverUrl = "http://192.168.8.122:8000/register";

  Future<void> _handleRegister() async {
    // Validate Input
    if (_nameCtrl.text.isEmpty ||
        _phoneCtrl.text.isEmpty ||
        _pinCtrl.text.length < 4) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text("Please fill all fields")));
      }
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final response = await http.post(
        Uri.parse(serverUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "full_name": _nameCtrl.text,
          "phone_number": _phoneCtrl.text,
          "pin": _pinCtrl.text,
        }),
      );

      if (!mounted) return;

      if (response.statusCode == 200) {
        // Success
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Registration Successful! Please Login."),
          ),
        );
        Navigator.pop(context); // Close screen
      } else {
        final error = jsonDecode(response.body)['detail'];
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text("Error: $error")));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text("Connection Error: $e")));
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Create Account",
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: Color(0xFF111813),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              "Join TeaCare to protect your crops",
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
            const SizedBox(height: 32),

            // Name Field
            const Text(
              "Full Name",
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _nameCtrl,
              decoration: _inputDecor("Enter your name"),
            ),
            const SizedBox(height: 16),

            // Phone Field
            const Text(
              "Phone Number",
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _phoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: _inputDecor("077..."),
            ),
            const SizedBox(height: 16),

            // PIN Field
            const Text(
              "Create 4-Digit PIN",
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _pinCtrl,
              keyboardType: TextInputType.number,
              maxLength: 4,
              obscureText: true,
              decoration: _inputDecor("****"),
            ),
            const SizedBox(height: 32),

            // Submit Button
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _handleRegister,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF11D452),
                  foregroundColor: const Color(0xFF102216),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _isLoading
                    ? const CircularProgressIndicator()
                    : const Text(
                        "Register Now",
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  InputDecoration _inputDecor(String hint) {
    return InputDecoration(
      filled: true,
      fillColor: Colors.white,
      hintText: hint,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide.none,
      ),
    );
  }
}

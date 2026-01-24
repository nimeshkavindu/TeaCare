import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class EditProfileScreen extends StatefulWidget {
  final int userId;
  final String currentName;

  const EditProfileScreen({
    super.key,
    required this.userId,
    required this.currentName,
  });

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  late TextEditingController _nameCtrl;
  final TextEditingController _passCtrl = TextEditingController();
  bool _isLoading = false;

  final String serverUrl = "http://192.168.8.122:8000"; // Check your IP

  @override
  void initState() {
    super.initState();
    _nameCtrl = TextEditingController(text: widget.currentName);
  }

  Future<void> _saveChanges() async {
    setState(() => _isLoading = true);

    try {
      final Map<String, dynamic> body = {
        "full_name": _nameCtrl.text.trim(),
      };

      // Only send password if user typed something new
      if (_passCtrl.text.isNotEmpty) {
        if (_passCtrl.text.length < 6) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Password must be at least 6 characters")),
          );
          setState(() => _isLoading = false);
          return;
        }
        body["secret"] = _passCtrl.text.trim();
      }

      final response = await http.put(
        Uri.parse("$serverUrl/users/${widget.userId}"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Profile Updated!"), backgroundColor: Colors.green),
          );
          Navigator.pop(context); // Go back to profile
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("Update Failed: ${response.statusCode}"), backgroundColor: Colors.red),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("Edit Profile", style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Full Name", style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            TextField(
              controller: _nameCtrl,
              decoration: _inputDecor("Enter your name"),
            ),
            const SizedBox(height: 24),
            
            const Text("New Password (Optional)", style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            TextField(
              controller: _passCtrl,
              obscureText: true,
              decoration: _inputDecor("Leave empty to keep current").copyWith(
                prefixIcon: const Icon(Icons.lock_outline, color: Colors.grey),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              "Enter a new password or PIN only if you want to change it.",
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),

            const Spacer(),
            
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _saveChanges,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF11D452),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isLoading 
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text("Save Changes", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  InputDecoration _inputDecor(String hint) {
    return InputDecoration(
      hintText: hint,
      filled: true,
      fillColor: const Color(0xFFF3F4F6),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    );
  }
}
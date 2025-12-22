import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  // Controllers
  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _contactCtrl = TextEditingController();
  final TextEditingController _secretCtrl = TextEditingController();

  // State Variables
  String _registerMethod = "Phone"; // "Phone" or "Email"
  String _selectedRole = "Farmer";
  bool _isLoading = false;

  final List<String> _roles = ["Farmer", "Researcher", "Expert"];
  final String serverUrl = "http://192.168.8.122:8000/register"; 

  // --- LOGIC ---
  Future<void> _handleRegister() async {
    if (_nameCtrl.text.isEmpty || _contactCtrl.text.isEmpty || _secretCtrl.text.isEmpty) {
      _showError("Please fill all fields");
      return;
    }

    // Validation
    if (_registerMethod == "Phone" && _secretCtrl.text.length < 4) {
      _showError("PIN must be at least 4 digits");
      return;
    }
    if (_registerMethod == "Email" && _secretCtrl.text.length < 6) {
      _showError("Password must be at least 6 characters");
      return;
    }

    setState(() => _isLoading = true);

    try {
      final response = await http.post(
        Uri.parse(serverUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "full_name": _nameCtrl.text,
          "contact_type": _registerMethod.toLowerCase(), // "phone" or "email"
          "contact_value": _contactCtrl.text,
          "secret": _secretCtrl.text,
          "role": _selectedRole
        }),
      );

      if (response.statusCode == 200) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text("Registered! Please Login."), backgroundColor: Colors.green));
          Navigator.pop(context);
        }
      } else {
        final data = jsonDecode(response.body);
        _showError(data['detail'] ?? "Registration failed");
      }
    } catch (e) {
      _showError("Connection error: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(title: const Text("Create Account"), backgroundColor: Colors.transparent, elevation: 0, foregroundColor: Colors.black),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("How do you want to login?", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            
            // --- METHOD TOGGLE ---
            Row(
              children: [
                Expanded(child: _buildMethodButton("Phone", Icons.phone_android)),
                const SizedBox(width: 12),
                Expanded(child: _buildMethodButton("Email", Icons.email_outlined)),
              ],
            ),
            const SizedBox(height: 24),

            // --- FORM ---
            TextField(controller: _nameCtrl, decoration: _inputDecor("Full Name", Icons.person)),
            const SizedBox(height: 16),
            
            // Dynamic Contact Field
            TextField(
              controller: _contactCtrl,
              keyboardType: _registerMethod == "Phone" ? TextInputType.phone : TextInputType.emailAddress,
              decoration: _inputDecor(
                _registerMethod == "Phone" ? "Phone Number" : "Email Address",
                _registerMethod == "Phone" ? Icons.phone : Icons.email,
              ),
            ),
            const SizedBox(height: 16),

            // Dynamic Secret Field
            TextField(
              controller: _secretCtrl,
              keyboardType: _registerMethod == "Phone" ? TextInputType.number : TextInputType.text,
              obscureText: true,
              maxLength: _registerMethod == "Phone" ? 4 : null, // Limit PIN length visually
              decoration: _inputDecor(
                _registerMethod == "Phone" ? "Create 4-digit PIN" : "Create Password",
                Icons.lock,
              ),
            ),
            const SizedBox(height: 16),

            // Role Dropdown
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8)),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedRole,
                  isExpanded: true,
                  items: _roles.map((r) => DropdownMenuItem(value: r, child: Text(r))).toList(),
                  onChanged: (val) => setState(() => _selectedRole = val!),
                ),
              ),
            ),
            const SizedBox(height: 32),

            SizedBox(
              width: double.infinity, 
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _handleRegister,
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF11D452), foregroundColor: Colors.white),
                child: _isLoading ? const CircularProgressIndicator(color: Colors.white) : const Text("Register"),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMethodButton(String method, IconData icon) {
    bool isSelected = _registerMethod == method;
    return GestureDetector(
      onTap: () {
        setState(() {
          _registerMethod = method;
          _contactCtrl.clear();
          _secretCtrl.clear();
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF11D452) : Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: isSelected ? Colors.transparent : Colors.grey.shade300),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: isSelected ? Colors.white : Colors.grey),
            const SizedBox(width: 8),
            Text(method, style: TextStyle(color: isSelected ? Colors.white : Colors.black, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  InputDecoration _inputDecor(String hint, IconData icon) {
    return InputDecoration(
      filled: true, fillColor: Colors.white, hintText: hint, prefixIcon: Icon(icon, color: Colors.grey),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
      counterText: "" // Hide character counter
    );
  }
}
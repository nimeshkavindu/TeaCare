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
  String _registerMethod = "Phone";
  String _selectedRole = "Farmer";
  bool _isLoading = false;

  final List<String> _roles = ["Farmer", "Researcher", "Expert"];

  // UPDATE THIS IP TO MATCH YOUR PC
  final String serverUrl = "http://192.168.8.122:8000/register";

  // --- HELPER: Parse Backend Errors Safely ---
  String _getBackendError(String responseBody) {
    try {
      final data = jsonDecode(responseBody);
      final detail = data['detail'];

      // Case 1: Standard Error (String) -> "User already registered"
      if (detail is String) {
        return detail;
      }
      // Case 2: Validation Error (List) -> [{"msg": "Invalid email", ...}]
      if (detail is List && detail.isNotEmpty) {
        return detail[0]['msg'] ?? "Invalid Input";
      }
      return "Registration failed";
    } catch (e) {
      return "Server Error: $e";
    }
  }

  // --- LOGIC ---
  Future<void> _handleRegister() async {
    // 1. Basic Empty Check
    if (_nameCtrl.text.trim().isEmpty ||
        _contactCtrl.text.trim().isEmpty ||
        _secretCtrl.text.trim().isEmpty) {
      _showError("Please fill all fields");
      return;
    }

    String contactVal = _contactCtrl.text.trim();
    String secretVal = _secretCtrl.text.trim();

    // 2. CLIENT-SIDE VALIDATION
    if (_registerMethod == "Phone") {
      // Regex: Only numbers allowed
      if (!RegExp(r'^[0-9]+$').hasMatch(contactVal)) {
        _showError("Phone number must contain only digits.");
        return;
      }
      if (contactVal.length < 9) {
        _showError("Phone number is too short.");
        return;
      }
      if (secretVal.length < 4) {
        _showError("PIN must be at least 4 digits.");
        return;
      }
    } else {
      // Email Validation
      final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
      if (!emailRegex.hasMatch(contactVal)) {
        _showError("Please enter a valid email address.");
        return;
      }
      if (secretVal.length < 6) {
        _showError("Password must be at least 6 characters.");
        return;
      }
    }

    setState(() => _isLoading = true);

    try {
      final response = await http.post(
        Uri.parse(serverUrl), // This calls /register
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "full_name": _nameCtrl.text.trim(),
          "contact_type": _registerMethod.toLowerCase(),
          "contact_value": contactVal,
          "secret": secretVal,
          "role": _selectedRole,
        }),
      );

      if (response.statusCode == 200) {
        // SUCCESS: OTP SENT -> Show Dialog
        if (mounted) {
          _showOtpDialog(contactVal);
        }
      } else {
        _showError(_getBackendError(response.body));
      }
    } catch (e) {
      _showError("Connection error: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // --- SHOW OTP DIALOG ---
  void _showOtpDialog(String contact) {
    final TextEditingController otpController = TextEditingController();
    bool isVerifying = false;

    showDialog(
      context: context,
      barrierDismissible: false, // User must verify or cancel
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text("Enter OTP"),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text("We sent a code to $contact"),
                  const SizedBox(height: 16),
                  TextField(
                    controller: otpController,
                    keyboardType: TextInputType.number,
                    maxLength: 6,
                    textAlign: TextAlign.center,
                    decoration: const InputDecoration(
                      hintText: "6-Digit Code",
                      border: OutlineInputBorder(),
                      counterText: "",
                    ),
                  ),
                  const SizedBox(height: 10),
                  if (isVerifying) const CircularProgressIndicator(),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text("Cancel"),
                ),
                ElevatedButton(
                  onPressed: isVerifying
                      ? null
                      : () => _verifyOtp(contact, otpController.text, setDialogState),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF11D452),
                    foregroundColor: Colors.white, // Ensure text is readable
                  ),
                  child: const Text("Verify"),
                ),
              ],
            );
          },
        );
      },
    );
  }

  // --- CALL VERIFY ENDPOINT ---
  Future<void> _verifyOtp(String contact, String otp, Function setDialogState) async {
    if (otp.length < 6) return;

    setDialogState(() => true); // Show loading in dialog

    // Construct verify URL (Assuming backend is at /verify-otp)
    // Using string replacement to maintain the base IP address logic
    final String verifyUrl = serverUrl.replaceAll("/register", "/verify-otp");

    try {
      final response = await http.post(
        Uri.parse(verifyUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "contact_value": contact,
          "otp": otp,
        }),
      );

      if (response.statusCode == 200) {
        // SUCCESS!
        if (mounted) {
          Navigator.pop(context); // Close Dialog
          Navigator.pop(context); // Close Register Screen (optional, or navigate to login)
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Account Verified! Please Login."), backgroundColor: Colors.green),
          );
        }
      } else {
        // Show error but keep dialog open
        final error = _getBackendError(response.body);
        if (mounted) {
           ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error), backgroundColor: Colors.red));
        }
      }
    } catch (e) {
      print(e);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Connection Error: $e"), backgroundColor: Colors.red));
      }
    } finally {
      // Stop loading regardless of success or failure
      // We check if the widget (dialog) is still in the tree before calling setState
      // Since setDialogState is a callback from StatefulBuilder, it might be tricky to check mounted directly for the dialog
      // But typically safe in this direct flow.
      setDialogState(() => false); 
    }
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: const Text("Create Account"),
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Colors.black,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "How do you want to login?",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),

            // --- METHOD TOGGLE ---
            Row(
              children: [
                Expanded(
                  child: _buildMethodButton("Phone", Icons.phone_android),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMethodButton("Email", Icons.email_outlined),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // --- FORM ---
            TextField(
              controller: _nameCtrl,
              decoration: _inputDecor("Full Name", Icons.person),
            ),
            const SizedBox(height: 16),

            // Dynamic Contact Field
            TextField(
              controller: _contactCtrl,
              keyboardType: _registerMethod == "Phone"
                  ? TextInputType.phone
                  : TextInputType.emailAddress,
              decoration: _inputDecor(
                _registerMethod == "Phone" ? "Phone Number" : "Email Address",
                _registerMethod == "Phone" ? Icons.phone : Icons.email,
              ),
            ),
            const SizedBox(height: 16),

            // Dynamic Secret Field
            TextField(
              controller: _secretCtrl,
              keyboardType: _registerMethod == "Phone"
                  ? TextInputType.number
                  : TextInputType.text,
              obscureText: true,
              maxLength: _registerMethod == "Phone" ? 4 : null,
              decoration: _inputDecor(
                _registerMethod == "Phone"
                    ? "Create 4-digit PIN"
                    : "Create Password",
                Icons.lock,
              ),
            ),
            const SizedBox(height: 16),

            // Role Dropdown
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedRole,
                  isExpanded: true,
                  items: _roles
                      .map((r) => DropdownMenuItem(value: r, child: Text(r)))
                      .toList(),
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
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF11D452),
                  foregroundColor: Colors.white,
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text("Register"),
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
          border: Border.all(
            color: isSelected ? Colors.transparent : Colors.grey.shade300,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: isSelected ? Colors.white : Colors.grey),
            const SizedBox(width: 8),
            Text(
              method,
              style: TextStyle(
                color: isSelected ? Colors.white : Colors.black,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  InputDecoration _inputDecor(String hint, IconData icon) {
    return InputDecoration(
      filled: true,
      fillColor: Colors.white,
      hintText: hint,
      prefixIcon: Icon(icon, color: Colors.grey),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide.none,
      ),
      counterText: "",
    );
  }
}
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class TeaChatScreen extends StatefulWidget {
  const TeaChatScreen({super.key});

  @override
  State<TeaChatScreen> createState() => _TeaChatScreenState();
}

class _TeaChatScreenState extends State<TeaChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<Map<String, String>> _messages = []; 
  bool _isTyping = false;
  String _currentStreamResponse = "";

  // Update with your IP
  final String serverUrl = "http://192.168.8.122:8000"; 

  // --- SEND MESSAGE ---
  void _sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    // 1. Add User Message
    setState(() {
      _messages.add({'role': 'user', 'text': text});
      _isTyping = true;
      _currentStreamResponse = ""; 
      _controller.clear();
      // Add Placeholder for Bot
      _messages.add({'role': 'bot', 'text': ''}); 
    });
    _scrollToBottom();

    try {
      // 2. Setup Request
      final request = http.MultipartRequest('POST', Uri.parse("$serverUrl/chat_stream"));
      request.fields['user_query'] = text;

      // 3. Send & Listen to Stream
      final streamedResponse = await request.send();

      streamedResponse.stream.transform(utf8.decoder).listen(
        (value) {
          if (mounted) {
            setState(() {
              _currentStreamResponse += value;
              // Update the last message (the placeholder) with new text
              _messages.last['text'] = _currentStreamResponse;
            });
            _scrollToBottom();
          }
        },
        onDone: () {
          if (mounted) setState(() => _isTyping = false);
        },
        onError: (e) {
          if (mounted) {
            setState(() {
              _messages.last['text'] = "Error: Tea Expert is offline.";
              _isTyping = false;
            });
          }
        },
      );
    } catch (e) {
      if (mounted) {
        setState(() {
          _messages.last['text'] = "Connection Error.";
          _isTyping = false;
        });
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F8),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: const Row(
          children: [
            Icon(Icons.eco_rounded, color: Colors.white),
            SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("TeaCare Assistant", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                Text("Powered by AI", style: TextStyle(color: Colors.white70, fontSize: 12)),
              ],
            ),
          ],
        ),
        backgroundColor: const Color(0xFF4CAF50),
        elevation: 0,
      ),
      body: Column(
        children: [
          // CHAT AREA
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg['role'] == 'user';
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.all(14),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: isUser ? const Color(0xFF4CAF50) : Colors.white,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(12),
                        topRight: const Radius.circular(12),
                        bottomLeft: isUser ? const Radius.circular(12) : Radius.zero,
                        bottomRight: isUser ? Radius.zero : const Radius.circular(12),
                      ),
                      boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 5)],
                    ),
                    child: Text(
                      msg['text']!,
                      style: TextStyle(color: isUser ? Colors.white : Colors.black87, fontSize: 15),
                    ),
                  ),
                );
              },
            ),
          ),

          // SUGGESTIONS
          if (_messages.isEmpty)
            Container(
              height: 50,
              margin: const EdgeInsets.only(bottom: 10),
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  _suggestionChip("How do I cure Blister Blight?"),
                  _suggestionChip("Best fertilizer for young tea?"),
                  _suggestionChip("Identify red spots on leaves"),
                ],
              ),
            ),

          // INPUT AREA
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(top: BorderSide(color: Colors.black12)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      hintText: "Ask a question...",
                      filled: true,
                      fillColor: Colors.grey[100],
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(30),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                    ),
                    onSubmitted: _sendMessage,
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor: const Color(0xFF4CAF50),
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white, size: 20),
                    onPressed: () => _sendMessage(_controller.text),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _suggestionChip(String label) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ActionChip(
        label: Text(label, style: TextStyle(color: Colors.green[800])),
        backgroundColor: Colors.green[50],
        onPressed: () => _sendMessage(label),
      ),
    );
  }
}
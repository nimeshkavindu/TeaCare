import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class PostDetailScreen extends StatefulWidget {
  final Map<String, dynamic> post;
  final int currentUserId;
  final String currentUserName;

  const PostDetailScreen({
    super.key,
    required this.post,
    required this.currentUserId,
    required this.currentUserName,
  });

  @override
  State<PostDetailScreen> createState() => _PostDetailScreenState();
}

class _PostDetailScreenState extends State<PostDetailScreen> {
  List<dynamic> _comments = [];
  final TextEditingController _commentCtrl = TextEditingController();
  bool _isLoading = true;

  final String serverUrl = "http://192.168.8.122:8000";

  @override
  void initState() {
    super.initState();
    _fetchComments();
  }

  Future<void> _fetchComments() async {
    try {
      final response = await http.get(
        Uri.parse("$serverUrl/posts/${widget.post['post_id']}/comments"),
      );
      if (response.statusCode == 200) {
        setState(() {
          _comments = jsonDecode(response.body);
          _isLoading = false;
        });
      }
    } catch (e) {
      print("Error fetching comments: $e");
    }
  }

  Future<void> _postComment() async {
    if (_commentCtrl.text.isEmpty) return;

    try {
      await http.post(
        Uri.parse("$serverUrl/comments"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "post_id": widget.post['post_id'],
          "user_id": widget.currentUserId,
          "author_name": widget.currentUserName,
          "content": _commentCtrl.text,
        }),
      );
      _commentCtrl.clear();
      _fetchComments(); // refresh comments
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Failed to comment")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Discussion"),
        backgroundColor: Colors.white,
        iconTheme: const IconThemeData(color: Colors.black),
        titleTextStyle: const TextStyle(
          color: Colors.black,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      body: Column(
        children: [
          // post content
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // user info
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: Colors.orange[100],
                          child: Text(
                            widget.post['author_name'][0],
                            style: const TextStyle(color: Colors.orange),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.post['author_name'],
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              widget.post['timestamp'],
                              style: const TextStyle(
                                color: Colors.grey,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  // title and body
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.post['title'],
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          widget.post['content'],
                          style: const TextStyle(fontSize: 16, height: 1.4),
                        ),
                      ],
                    ),
                  ),

                  // Image
                  if (widget.post['image_url'] != null)
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.network(
                          "$serverUrl/${widget.post['image_url']}",
                        ),
                      ),
                    ),

                  const Divider(thickness: 1),
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text(
                      "Comments",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),

                  // Comments List
                  _isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : ListView.builder(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: _comments.length,
                          itemBuilder: (context, index) {
                            final comment = _comments[index];
                            return ListTile(
                              leading: CircleAvatar(
                                radius: 14,
                                backgroundColor: Colors.grey[200],
                                child: Icon(
                                  Icons.person,
                                  size: 16,
                                  color: Colors.grey[600],
                                ),
                              ),
                              title: Text(
                                comment['author_name'],
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                              subtitle: Text(comment['content']),
                            );
                          },
                        ),
                ],
              ),
            ),
          ),

          // input
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black12,
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _commentCtrl,
                    decoration: InputDecoration(
                      hintText: "Write a comment...",
                      filled: true,
                      fillColor: Colors.grey[100],
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor: const Color(0xFF11D452),
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white, size: 18),
                    onPressed: _postComment,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

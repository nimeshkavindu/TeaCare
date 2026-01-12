import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:share_plus/share_plus.dart'; // Import Share
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

  // --- API CALLS ---

  Future<void> _fetchComments() async {
    try {
      final response = await http.get(
        Uri.parse("$serverUrl/posts/${widget.post['post_id']}/comments"),
      );
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _comments = jsonDecode(response.body);
            _isLoading = false;
          });
        }
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
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Failed to comment")),
      );
    }
  }

  Future<void> _deletePost() async {
    try {
      final response = await http.delete(
        Uri.parse("$serverUrl/posts/${widget.post['post_id']}?user_id=${widget.currentUserId}"),
      );
      if (response.statusCode == 200) {
        Navigator.pop(context); // Go back to list
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Post deleted")),
        );
      }
    } catch (e) {
      print(e);
    }
  }

  Future<void> _reportPost() async {
    final reason = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text("Report Reason"),
        children: [
          SimpleDialogOption(onPressed: () => Navigator.pop(context, "Spam"), child: const Text("Spam")),
          SimpleDialogOption(onPressed: () => Navigator.pop(context, "Harassment"), child: const Text("Harassment")),
          SimpleDialogOption(onPressed: () => Navigator.pop(context, "False Info"), child: const Text("False Information")),
        ],
      ),
    );

    if (reason != null) {
      await http.post(
        Uri.parse("$serverUrl/posts/${widget.post['post_id']}/report"),
        body: {"user_id": widget.currentUserId.toString(), "reason": reason},
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Report submitted.")),
      );
    }
  }

  // --- UI WIDGETS ---

  @override
  Widget build(BuildContext context) {
    bool isMyPost = widget.post['user_id'] == widget.currentUserId;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("Discussion"),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        titleTextStyle: const TextStyle(
          color: Colors.black,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
        actions: [
          PopupMenuButton<String>(
            onSelected: (val) {
              if (val == 'delete') _deletePost();
              if (val == 'report') _reportPost();
              if (val == 'share') {
                Share.share("Check out this post on TeaCare: '${widget.post['title']}'");
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'share', child: Text("Share Post")),
              if (isMyPost) 
                const PopupMenuItem(value: 'delete', child: Text("Delete Post", style: TextStyle(color: Colors.red))),
              if (!isMyPost) 
                const PopupMenuItem(value: 'report', child: Text("Report Post")),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // Scrollable Content
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1. Author Info
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: Colors.grey[200],
                          child: Text(
                            widget.post['author_name'][0],
                            style: const TextStyle(color: Colors.black54, fontWeight: FontWeight.bold),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(
                                  widget.post['author_name'],
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                                const SizedBox(width: 6),
                                _buildRoleBadge(widget.post['author_role']),
                              ],
                            ),
                            Text(
                              widget.post['timestamp'],
                              style: const TextStyle(color: Colors.grey, fontSize: 12),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  // 2. Title & Category
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (widget.post['category'] != "General")
                          Container(
                            margin: const EdgeInsets.only(bottom: 8),
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: widget.post['category'] == "Disease Alert" ? Colors.red.shade50 : Colors.blue.shade50,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              widget.post['category'],
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: widget.post['category'] == "Disease Alert" ? Colors.red.shade700 : Colors.blue.shade700,
                              ),
                            ),
                          ),

                        Text(
                          widget.post['title'],
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 20),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          widget.post['content'],
                          style: const TextStyle(fontSize: 16, height: 1.5, color: Colors.black87),
                        ),
                      ],
                    ),
                  ),

                  // 3. Image
                  if (widget.post['image_url'] != null)
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.network(
                          "$serverUrl/${widget.post['image_url']}",
                          fit: BoxFit.cover,
                          errorBuilder: (c, e, s) => const SizedBox(),
                        ),
                      ),
                    ),

                  const Divider(thickness: 1, height: 32),
                  
                  // 4. Comments Header
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Row(
                      children: [
                        const Icon(Icons.comment_outlined, size: 20, color: Colors.grey),
                        const SizedBox(width: 8),
                        Text(
                          "${_comments.length} Comments",
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),

                  // 5. Comments List
                  _isLoading
                      ? const Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator()))
                      : ListView.builder(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: _comments.length,
                          itemBuilder: (context, index) {
                            final comment = _comments[index];
                            return ListTile(
                              leading: CircleAvatar(
                                radius: 16,
                                backgroundColor: Colors.grey[100],
                                child: Text(comment['author_name'][0], style: const TextStyle(fontSize: 12)),
                              ),
                              title: Text(
                                comment['author_name'],
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                              ),
                              subtitle: Text(comment['content']),
                              dense: true,
                            );
                          },
                        ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),

          // 6. Input Field
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -5),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _commentCtrl,
                    decoration: InputDecoration(
                      hintText: "Add a comment...",
                      filled: true,
                      fillColor: Colors.grey[100],
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
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

  // --- HELPER: Role Badge ---
  Widget _buildRoleBadge(String? role) {
    if (role == null || role == "Farmer") return const SizedBox();
    
    Color bg = Colors.blue.shade50;
    Color text = Colors.blue.shade700;
    IconData icon = Icons.verified;

    if (role == "Expert") {
      bg = const Color(0xFFE0E7FF);
      text = const Color(0xFF4338CA);
      icon = Icons.school;
    } else if (role == "Researcher") {
      bg = const Color(0xFFF3E8FF);
      text = const Color(0xFF7E22CE);
      icon = Icons.science;
    } else if (role == "Admin") {
      bg = Colors.red.shade50;
      text = Colors.red.shade700;
      icon = Icons.shield;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          Icon(icon, size: 12, color: text),
          const SizedBox(width: 2),
          Text(role, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: text)),
        ],
      ),
    );
  }
}
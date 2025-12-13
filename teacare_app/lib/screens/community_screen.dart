import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'dart:convert';
import 'dart:io';
import 'post_detail_screen.dart';

class CommunityScreen extends StatefulWidget {
  final int userId;
  final String userName;

  const CommunityScreen({
    super.key,
    required this.userId,
    required this.userName,
  });

  @override
  State<CommunityScreen> createState() => _CommunityScreenState();
}

class _CommunityScreenState extends State<CommunityScreen> {
  List<dynamic> _posts = [];
  bool _isLoading = true;
  final ImagePicker _picker = ImagePicker();

  final String serverUrl = "http://192.168.8.122:8000";

  @override
  void initState() {
    super.initState();
    _fetchPosts();
  }

  Future<void> _fetchPosts() async {
    try {
      final response = await http.get(Uri.parse("$serverUrl/posts"));
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _posts = jsonDecode(response.body);
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _likePost(int postId) async {
    try {
      await http.post(Uri.parse("$serverUrl/posts/$postId/like"));
      _fetchPosts();
    } catch (e) {
      print("Error liking post: $e");
    }
  }

  // create post
  Future<void> _createPostDialog() async {
    final titleCtrl = TextEditingController();
    final contentCtrl = TextEditingController();
    XFile? selectedImage;

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: const Text("Ask the Community"),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: titleCtrl,
                  decoration: const InputDecoration(labelText: "Title"),
                ),
                TextField(
                  controller: contentCtrl,
                  decoration: const InputDecoration(labelText: "Details"),
                  maxLines: 3,
                ),
                const SizedBox(height: 16),

                if (selectedImage != null)
                  Stack(
                    children: [
                      Image.file(
                        File(selectedImage!.path),
                        height: 100,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),
                      Positioned(
                        right: 0,
                        child: IconButton(
                          icon: const Icon(Icons.close, color: Colors.red),
                          onPressed: () =>
                              setDialogState(() => selectedImage = null),
                        ),
                      ),
                    ],
                  ),

                TextButton.icon(
                  onPressed: () async {
                    final img = await _picker.pickImage(
                      source: ImageSource.gallery,
                    );
                    if (img != null) setDialogState(() => selectedImage = img);
                  },
                  icon: const Icon(Icons.image, color: Color(0xFF11D452)),
                  label: const Text("Add Photo"),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text("Cancel"),
              ),
              ElevatedButton(
                onPressed: () async {
                  Navigator.pop(context);
                  await _submitPost(
                    titleCtrl.text,
                    contentCtrl.text,
                    selectedImage,
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF11D452),
                ),
                child: const Text("Post"),
              ),
            ],
          );
        },
      ),
    );
  }

  // submit post
  Future<void> _submitPost(String title, String content, XFile? image) async {
    if (title.isEmpty || content.isEmpty) return;

    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse("$serverUrl/posts"),
      );
      request.fields['user_id'] = widget.userId.toString();
      request.fields['author_name'] = widget.userName;
      request.fields['title'] = title;
      request.fields['content'] = content;

      if (image != null) {
        request.files.add(
          await http.MultipartFile.fromPath('file', image.path),
        );
      }

      var response = await request.send();
      if (response.statusCode == 200) {
        _fetchPosts();
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text("Posted successfully!")));
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Error posting")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: const Text(
          "Community Forum",
          style: TextStyle(color: Colors.black),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _createPostDialog,
        backgroundColor: const Color(0xFF11D452),
        child: const Icon(Icons.add),
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF11D452)),
            )
          : _posts.isEmpty
          ? const Center(
              child: Text(
                "No posts yet.",
                style: TextStyle(color: Colors.grey),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _posts.length,
              itemBuilder: (context, index) {
                final post = _posts[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: InkWell(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => PostDetailScreen(
                            post: post,
                            currentUserId: widget.userId,
                            currentUserName: widget.userName,
                          ),
                        ),
                      );
                    },
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // user info
                          Row(
                            children: [
                              CircleAvatar(
                                backgroundColor: Colors.orange[100],
                                radius: 16,
                                child: Text(
                                  post['author_name'][0],
                                  style: const TextStyle(color: Colors.orange),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                post['author_name'],
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const Spacer(),
                              Text(
                                post['timestamp'],
                                style: const TextStyle(
                                  color: Colors.grey,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),

                          // Content
                          Text(
                            post['title'],
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            post['content'],
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(color: Colors.black87),
                          ),

                          // Image
                          if (post['image_url'] != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 12),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: Image.network(
                                  "$serverUrl/${post['image_url']}",
                                  height: 150,
                                  width: double.infinity,
                                  fit: BoxFit.cover,
                                  errorBuilder: (c, e, s) => const SizedBox(),
                                ),
                              ),
                            ),

                          const Divider(height: 24),

                          // Like & comment
                          Row(
                            children: [
                              InkWell(
                                onTap: () => _likePost(post['post_id']),
                                child: Row(
                                  children: [
                                    const Icon(
                                      Icons.thumb_up_alt_outlined,
                                      size: 18,
                                      color: Colors.grey,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      "${post['likes']} Likes",
                                      style: const TextStyle(
                                        color: Colors.grey,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 24),
                              const Row(
                                children: [
                                  Icon(
                                    Icons.mode_comment_outlined,
                                    size: 18,
                                    color: Colors.grey,
                                  ),
                                  SizedBox(width: 4),
                                  Text(
                                    "Comment",
                                    style: TextStyle(color: Colors.grey),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
    );
  }
}

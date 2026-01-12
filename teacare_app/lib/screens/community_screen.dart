import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:share_plus/share_plus.dart'; 
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
  // Config
  final String serverUrl = "http://192.168.8.122:8000";

  // State
  List<dynamic> _posts = [];
  bool _isLoading = true;
  String _activeFilter = "All"; // All, Popular, Alerts, My Posts
  final TextEditingController _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchPosts();
  }

  // --- API CALLS ---

  Future<void> _fetchPosts({String query = ""}) async {
    setState(() => _isLoading = true);

    // Build Query Params based on Filter
    String sort = "newest";
    String filterBy = "all";

    if (_activeFilter == "Popular") sort = "popular";
    if (_activeFilter == "Unanswered") filterBy = "unanswered";
    if (_activeFilter == "My Posts") filterBy = "my_posts";
    if (_activeFilter == "Alerts") filterBy = "category_alert";

    try {
      final uri = Uri.parse("$serverUrl/posts").replace(queryParameters: {
        "sort": sort,
        "filter_by": filterBy,
        "search": query,
        "user_id": widget.userId.toString(), // Needed for 'My Posts' filter
      });

      final response = await http.get(uri);

      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _posts = jsonDecode(response.body);
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      print("Error fetching posts: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleVote(int postId, int voteType) async {
    // Optimistic UI Update (Update UI instantly before server replies)
    final index = _posts.indexWhere((p) => p['post_id'] == postId);
    if (index != -1) {
      setState(() {
        int currentScore = _posts[index]['score'];
        int userVote = _posts[index]['user_vote']; // 0, 1, -1

        // Remove old vote effect
        currentScore -= userVote;
        
        // Add new vote effect
        currentScore += voteType;

        _posts[index]['score'] = currentScore;
        _posts[index]['user_vote'] = voteType;
      });
    }

    // Send to Server
    try {
      await http.post(
        Uri.parse("$serverUrl/posts/$postId/vote"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"user_id": widget.userId, "vote_type": voteType}),
      );
    } catch (e) {
      _fetchPosts(); // Revert on error
    }
  }

  Future<void> _deletePost(int postId) async {
    try {
      final response = await http.delete(
        Uri.parse("$serverUrl/posts/$postId?user_id=${widget.userId}"),
      );
      if (response.statusCode == 200) {
        _fetchPosts();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Post deleted")),
        );
      }
    } catch (e) {
      print(e);
    }
  }

  Future<void> _reportPost(int postId) async {
    // Simple Report Dialog
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
        Uri.parse("$serverUrl/posts/$postId/report"),
        body: {"user_id": widget.userId.toString(), "reason": reason},
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Report submitted. Thanks for helping!")),
      );
    }
  }

  // --- UI WIDGETS ---

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F4F6),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: TextField(
          controller: _searchCtrl,
          decoration: InputDecoration(
            hintText: "Search discussions...",
            border: InputBorder.none,
            prefixIcon: const Icon(Icons.search, color: Colors.grey),
            suffixIcon: _searchCtrl.text.isNotEmpty 
              ? IconButton(
                  icon: const Icon(Icons.clear, color: Colors.grey), 
                  onPressed: () {
                    _searchCtrl.clear();
                    _fetchPosts();
                  }
                ) 
              : null,
          ),
          onSubmitted: (val) => _fetchPosts(query: val),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => showDialog(
          context: context,
          builder: (_) => CreatePostDialog(
            userId: widget.userId, 
            userName: widget.userName, 
            serverUrl: serverUrl,
            onPostCreated: _fetchPosts,
          ),
        ),
        backgroundColor: const Color(0xFF11D452),
        icon: const Icon(Icons.edit),
        label: const Text("Ask Question"),
      ),
      body: Column(
        children: [
          // 1. FILTERS ROW
          Container(
            height: 60,
            color: Colors.white,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              children: [
                _buildFilterChip("All"),
                const SizedBox(width: 8),
                _buildFilterChip("Popular"),
                const SizedBox(width: 8),
                _buildFilterChip("Alerts"),
                const SizedBox(width: 8),
                _buildFilterChip("Unanswered"),
                const SizedBox(width: 8),
                _buildFilterChip("My Posts"),
              ],
            ),
          ),

          // 2. POST LIST
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: () => _fetchPosts(),
                    child: _posts.isEmpty
                        ? const Center(child: Text("No discussions found."))
                        : ListView.builder(
                            padding: const EdgeInsets.all(12),
                            itemCount: _posts.length,
                            itemBuilder: (context, index) {
                              return _buildPostCard(_posts[index]);
                            },
                          ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label) {
    bool isActive = _activeFilter == label;
    return ChoiceChip(
      label: Text(label),
      selected: isActive,
      onSelected: (bool selected) {
        setState(() => _activeFilter = label);
        _fetchPosts();
      },
      selectedColor: const Color(0xFFE8F5E9),
      labelStyle: TextStyle(
        color: isActive ? const Color(0xFF1B5E20) : Colors.black87,
        fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
      ),
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: isActive ? const Color(0xFF11D452) : Colors.grey.shade300,
        ),
      ),
    );
  }

  // --- PRO CARD WIDGET ---
  Widget _buildPostCard(Map<String, dynamic> post) {
    bool isMyPost = post['user_id'] == widget.userId;
    int vote = post['user_vote'] ?? 0; // 1, -1, or 0

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // A. HEADER (User Info & Menu)
            Row(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: Colors.grey.shade200,
                  child: Text(
                    post['author_name'][0], 
                    style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.black54)
                  ),
                ),
                const SizedBox(width: 10),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(post['author_name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(width: 6),
                        _buildRoleBadge(post['author_role']),
                      ],
                    ),
                    Text(post['timestamp'], style: const TextStyle(fontSize: 11, color: Colors.grey)),
                  ],
                ),
                const Spacer(),
                if (post['category'] != "General")
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: post['category'] == "Disease Alert" ? Colors.red.shade50 : Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(
                         color: post['category'] == "Disease Alert" ? Colors.red.shade200 : Colors.blue.shade200,
                      )
                    ),
                    child: Text(
                      post['category'], 
                      style: TextStyle(
                        fontSize: 10, 
                        fontWeight: FontWeight.bold,
                        color: post['category'] == "Disease Alert" ? Colors.red.shade700 : Colors.blue.shade700
                      )
                    ),
                  ),
                PopupMenuButton<String>(
                  onSelected: (val) {
                    if (val == 'delete') _deletePost(post['post_id']);
                    if (val == 'report') _reportPost(post['post_id']);
                    if (val == 'share') {
                      Share.share("Check out this post on TeaCare: '${post['title']}'");
                    }
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(value: 'share', child: Text("Share Post")),
                    if (isMyPost) const PopupMenuItem(value: 'delete', child: Text("Delete", style: TextStyle(color: Colors.red))),
                    if (!isMyPost) const PopupMenuItem(value: 'report', child: Text("Report")),
                  ],
                ),
              ],
            ),
            
            const SizedBox(height: 12),

            // B. CONTENT
            InkWell(
              onTap: () {
                Navigator.push(context, MaterialPageRoute(
                  builder: (_) => PostDetailScreen(
                    post: post, 
                    currentUserId: widget.userId, 
                    currentUserName: widget.userName
                  )
                ));
              },
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(post['title'], style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(post['content'], maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.black87)),
                  
                  if (post['image_url'] != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          "$serverUrl/${post['image_url']}", 
                          height: 150, width: double.infinity, fit: BoxFit.cover,
                          errorBuilder: (c, e, s) => const SizedBox(),
                        ),
                      ),
                    ),
                ],
              ),
            ),

            const Divider(height: 24),

            // C. FOOTER (Votes & Comments)
            Row(
              children: [
                // Upvote/Downvote Pill
                Container(
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.grey.shade300),
                  ),
                  child: Row(
                    children: [
                      IconButton(
                        icon: Icon(Icons.arrow_upward_rounded, color: vote == 1 ? Colors.orange : Colors.grey, size: 20),
                        onPressed: () => _handleVote(post['post_id'], vote == 1 ? 0 : 1), // Toggle
                        constraints: const BoxConstraints(),
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      ),
                      Text(
                        "${post['score']}", 
                        style: TextStyle(
                          fontWeight: FontWeight.bold, 
                          color: vote == 1 ? Colors.orange : (vote == -1 ? Colors.purple : Colors.black87)
                        )
                      ),
                      IconButton(
                        icon: Icon(Icons.arrow_downward_rounded, color: vote == -1 ? Colors.purple : Colors.grey, size: 20),
                        onPressed: () => _handleVote(post['post_id'], vote == -1 ? 0 : -1), // Toggle
                        constraints: const BoxConstraints(),
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      ),
                    ],
                  ),
                ),

                const SizedBox(width: 16),
                
                // Comment Count
                Row(
                  children: [
                    const Icon(Icons.chat_bubble_outline, size: 18, color: Colors.grey),
                    const SizedBox(width: 4),
                    Text("${post['comment_count']} Comments", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRoleBadge(String? role) {
    if (role == null || role == "Farmer") return const SizedBox();
    
    Color bg = Colors.blue.shade50;
    Color text = Colors.blue.shade700;
    IconData icon = Icons.verified;

    if (role == "Expert") {
      bg = const Color(0xFFE0E7FF); // Indigo Light
      text = const Color(0xFF4338CA); // Indigo Dark
      icon = Icons.school;
    } else if (role == "Researcher") {
      bg = const Color(0xFFF3E8FF); // Purple Light
      text = const Color(0xFF7E22CE); // Purple Dark
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
          Icon(icon, size: 10, color: text),
          const SizedBox(width: 2),
          Text(role, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: text)),
        ],
      ),
    );
  }
}

// --- CREATE POST DIALOG ---
class CreatePostDialog extends StatefulWidget {
  final int userId;
  final String userName;
  final String serverUrl;
  final VoidCallback onPostCreated;

  const CreatePostDialog({super.key, required this.userId, required this.userName, required this.serverUrl, required this.onPostCreated});

  @override
  State<CreatePostDialog> createState() => _CreatePostDialogState();
}

class _CreatePostDialogState extends State<CreatePostDialog> {
  final _titleCtrl = TextEditingController();
  final _contentCtrl = TextEditingController();
  String _category = "General";
  XFile? _image;
  bool _submitting = false;
  final ImagePicker _picker = ImagePicker();

  Future<void> _submit() async {
    if (_titleCtrl.text.isEmpty) return;
    setState(() => _submitting = true);

    var request = http.MultipartRequest('POST', Uri.parse("${widget.serverUrl}/posts"));
    request.fields['user_id'] = widget.userId.toString();
    request.fields['author_name'] = widget.userName;
    request.fields['title'] = _titleCtrl.text;
    request.fields['content'] = _contentCtrl.text;
    request.fields['category'] = _category;

    if (_image != null) {
      request.files.add(await http.MultipartFile.fromPath('file', _image!.path));
    }

    var res = await request.send();
    if (res.statusCode == 200) {
      widget.onPostCreated();
      if (mounted) Navigator.pop(context);
    } else {
      setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text("Create Post"),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<String>(
              value: _category,
              decoration: const InputDecoration(labelText: "Category", border: OutlineInputBorder()),
              items: ["General", "Question", "Disease Alert", "Success Story"]
                  .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                  .toList(),
              onChanged: (val) => setState(() => _category = val!),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _titleCtrl,
              decoration: const InputDecoration(labelText: "Title", border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _contentCtrl,
              maxLines: 3,
              decoration: const InputDecoration(labelText: "Details", border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            if (_image != null)
              Stack(children: [
                Image.file(File(_image!.path), height: 100, width: double.infinity, fit: BoxFit.cover),
                Positioned(right: 0, child: IconButton(icon: const Icon(Icons.close, color: Colors.red), onPressed: () => setState(() => _image = null)))
              ]),
            TextButton.icon(
              onPressed: () async {
                final img = await _picker.pickImage(source: ImageSource.gallery);
                if (img != null) setState(() => _image = img);
              },
              icon: const Icon(Icons.photo), label: const Text("Add Photo")
            )
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text("Cancel")),
        ElevatedButton(
          onPressed: _submitting ? null : _submit,
          style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF11D452)),
          child: _submitting ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white)) : const Text("Post"),
        ),
      ],
    );
  }
}
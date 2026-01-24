import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class NotificationScreen extends StatefulWidget {
  final int userId;
  const NotificationScreen({super.key, required this.userId});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  // UPDATE THIS IP TO MATCH YOUR PC
  final String serverUrl = "http://192.168.8.122:8000"; 
  
  List<dynamic> _notifications = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchNotifications();
  }

  // --- 1. FETCH NOTIFICATIONS ---
  Future<void> _fetchNotifications() async {
    try {
      final response = await http.get(
        Uri.parse("$serverUrl/notifications/${widget.userId}"),
      );

      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _notifications = jsonDecode(response.body);
            _isLoading = false;
          });
        }
      } else {
        // Handle server error quietly
        if (mounted) setState(() => _isLoading = false);
      }
    } catch (e) {
      print("Error fetching notifications: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // --- 2. MARK AS READ ---
  Future<void> _markAsRead(int id) async {
    // UI Optimistic Update: Mark as read instantly before server replies
    setState(() {
      final index = _notifications.indexWhere((n) => n['id'] == id);
      if (index != -1) {
        _notifications[index]['is_read'] = true;
      }
    });

    try {
      // Send update to backend
      await http.patch(Uri.parse("$serverUrl/notifications/$id/read"));
    } catch (e) {
      print("Failed to mark as read on server");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: const Text(
          "Notifications",
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.green))
          : _notifications.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  onRefresh: _fetchNotifications,
                  color: Colors.green,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _notifications.length,
                    itemBuilder: (context, index) {
                      return _buildNotificationCard(_notifications[index]);
                    },
                  ),
                ),
    );
  }

  // --- EMPTY STATE UI ---
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.green.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.notifications_off_outlined,
                size: 64, color: Colors.green[300]),
          ),
          const SizedBox(height: 16),
          Text(
            "No new notifications",
            style: TextStyle(
                color: Colors.grey[600],
                fontSize: 18,
                fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            "We'll let you know when something\nimportant happens.",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[400]),
          ),
        ],
      ),
    );
  }

  // --- NOTIFICATION CARD UI ---
  Widget _buildNotificationCard(dynamic notif) {
    bool isRead = notif['is_read'] ?? false;
    String type = notif['type'] ?? "Info";

    // Dynamic Styling based on Notification Type
    Color iconColor;
    IconData iconData;
    Color bgColor;

    switch (type) {
      case "Alert":
        iconColor = Colors.red;
        iconData = Icons.warning_amber_rounded;
        bgColor = const Color(0xFFFEF2F2); // Light Red
        break;
      case "Success":
        iconColor = Colors.green;
        iconData = Icons.check_circle_outline;
        bgColor = const Color(0xFFF0FDF4); // Light Green
        break;
      case "Announcement":
        iconColor = Colors.orange;
        iconData = Icons.campaign_rounded;
        bgColor = const Color(0xFFFFF7ED); // Light Orange
        break;
      default: // Info
        iconColor = Colors.blue;
        iconData = Icons.info_outline;
        bgColor = const Color(0xFFEFF6FF); // Light Blue
    }

    return GestureDetector(
      onTap: () {
        if (!isRead) _markAsRead(notif['id']);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isRead ? Colors.white : const Color(0xFFF0F9FF), // Highlight unread
          borderRadius: BorderRadius.circular(16),
          border: isRead
              ? Border.all(color: Colors.transparent)
              : Border.all(color: Colors.blue.withOpacity(0.3), width: 1.5),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Icon
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: bgColor,
                shape: BoxShape.circle,
              ),
              child: Icon(iconData, color: iconColor, size: 24),
            ),
            const SizedBox(width: 16),
            
            // Text Content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        notif['title'],
                        style: TextStyle(
                          fontWeight: isRead ? FontWeight.w600 : FontWeight.bold,
                          fontSize: 16,
                          color: const Color(0xFF1F2937),
                        ),
                      ),
                      if (!isRead)
                        Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            color: Colors.blue,
                            shape: BoxShape.circle,
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    notif['message'],
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 14,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    notif['timestamp'],
                    style: TextStyle(
                      color: Colors.grey[400],
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
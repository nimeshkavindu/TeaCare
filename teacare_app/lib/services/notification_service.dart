import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../screens/notification_screen.dart'; 

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();

  static GlobalKey<NavigatorState>? _navigatorKey;
  // 1. Initialize
  static Future<void> init(GlobalKey<NavigatorState> key) async {
    _navigatorKey = key;
    // Android Setup
    const AndroidInitializationSettings androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const InitializationSettings initSettings =
        InitializationSettings(android: androidSettings);

    await _notificationsPlugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onTapNotification, 
    );

    // Request Permission for Android 13+
    if (Platform.isAndroid) {
      await _notificationsPlugin
          .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin
          >()
          ?.requestNotificationsPermission();
    }
  }

  static Future<void> _onTapNotification(NotificationResponse response) async {
    // Navigate to Notification Screen
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getInt('userId') ?? 0;

    if (userId != 0 && _navigatorKey?.currentState != null) {
      _navigatorKey!.currentState!.push(
        MaterialPageRoute(
          builder: (context) => NotificationScreen(userId: userId),
        ),
      );
    }
  }

  // 2. Show Notification
  static Future<void> showNotification({
    required int id,
    required String title,
    required String body,
  }) async {
    const AndroidNotificationDetails androidDetails =
        AndroidNotificationDetails(
          'teacare_channel_id', // Channel ID (Unique)
          'TeaCare Alerts', // Channel Name (Visible to User)
          channelDescription: 'Notifications for disease detection',
          importance: Importance.max,
          priority: Priority.high,
          playSound: true,
        );

    const NotificationDetails details = NotificationDetails(
      android: androidDetails,
    );

    await _notificationsPlugin.show(id, title, body, details);
  }
}

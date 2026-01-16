import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:app_links/app_links.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import 'screens/welcome_screen.dart';
import 'screens/home_screen.dart';
import 'screens/post_detail_screen.dart';

void main() async {
  // 1. Required for async code in main
  WidgetsFlutterBinding.ensureInitialized();

  // 2. Check saved data
  final prefs = await SharedPreferences.getInstance();
  final isLoggedIn = prefs.getBool('isLoggedIn') ?? false;
  final userName = prefs.getString('userName') ?? "Farmer";
  final userId = prefs.getInt('userId') ?? 0;

  // 3. Run App with the correct starting screen
  runApp(
    MyApp(
      startScreen: isLoggedIn
          ? HomeScreen(userName: userName, userId: userId)
          : const WelcomeScreen(),
    ),
  );
}

// Changed to StatefulWidget to listen for Links
class MyApp extends StatefulWidget {
  final Widget startScreen;

  const MyApp({super.key, required this.startScreen});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  // Global Key allows us to navigate even when we are not inside a widget build
  final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();
  late AppLinks _appLinks;

  // Your Server IP
  final String serverUrl = "http://192.168.8.122:8000";

  @override
  void initState() {
    super.initState();
    _initDeepLinks();
  }

  // --- NEW: LINK HANDLING LOGIC ---
  Future<void> _initDeepLinks() async {
    _appLinks = AppLinks();

    // 1. Check Initial Link (if app was closed)
    final Uri? initialUri = await _appLinks.getInitialLink();
    if (initialUri != null) {
      _handleLink(initialUri);
    }

    // 2. Listen for Stream (if app is running)
    _appLinks.uriLinkStream.listen((Uri? uri) {
      if (uri != null) {
        _handleLink(uri);
      }
    });
  }

  Future<void> _handleLink(Uri uri) async {
    // Expected format: teacare://post/5
    if (uri.scheme == 'teacare' && uri.host == 'post') {
      final String postIdStr = uri.pathSegments.first;
      final int? postId = int.tryParse(postIdStr);

      if (postId != null) {
        // We fetch user info again to ensure we have the latest login state
        final prefs = await SharedPreferences.getInstance();
        final int? userId = prefs.getInt('userId');
        final String? userName = prefs.getString('userName');

        if (userId != null && userName != null) {
          _fetchAndNavigate(postId, userId, userName);
        }
      }
    }
  }

  Future<void> _fetchAndNavigate(
    int postId,
    int userId,
    String userName,
  ) async {
    try {
      final response = await http.get(
        Uri.parse("$serverUrl/posts/$postId?user_id=$userId"),
      );

      if (response.statusCode == 200) {
        final post = jsonDecode(response.body);

        // Navigate using the Global Key
        navigatorKey.currentState?.push(
          MaterialPageRoute(
            builder: (context) => PostDetailScreen(
              post: post,
              currentUserId: userId,
              currentUserName: userName,
            ),
          ),
        );
      }
    } catch (e) {
      print("Link Error: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: navigatorKey,
      debugShowCheckedModeBanner: false,
      title: 'TeaCare',
      theme: ThemeData(
        primarySwatch: Colors.green,
        scaffoldBackgroundColor: const Color(0xFFF6F8F6),
      ),
      home: widget.startScreen,
    );
  }
}

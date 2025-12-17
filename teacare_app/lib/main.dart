import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/welcome_screen.dart'; 
import 'screens/home_screen.dart';   

void main() async {
  // 1. Required for async code in main
  WidgetsFlutterBinding.ensureInitialized();

  // 2. Check saved data
  final prefs = await SharedPreferences.getInstance();
  final isLoggedIn = prefs.getBool('isLoggedIn') ?? false;
  final userName = prefs.getString('userName') ?? "Farmer";
  final userId = prefs.getInt('userId') ?? 0;

  // 3. Run App with the correct starting screen
  runApp(MyApp(
    startScreen: isLoggedIn
        ? HomeScreen(userName: userName, userId: userId)
        : const WelcomeScreen(), // If not logged in, show Welcome page
  ));
}

class MyApp extends StatelessWidget {
  final Widget startScreen;

  const MyApp({super.key, required this.startScreen});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'TeaCare',
      theme: ThemeData(
        primarySwatch: Colors.green,
        scaffoldBackgroundColor: const Color(0xFFF6F8F6),
      ),
      home: startScreen,
    );
  }
}
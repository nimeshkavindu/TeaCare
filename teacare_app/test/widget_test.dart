import 'package:flutter_test/flutter_test.dart';
import 'package:teacare_app/main.dart';
import 'package:teacare_app/screens/welcome_screen.dart'; // Import your screen

void main() {
  testWidgets('App loads welcome screen smoke test', (WidgetTester tester) async {
    // 1. Build our app and trigger a frame.
    // We must pass 'startScreen' because MyApp requires it now.
    await tester.pumpWidget(const MyApp(startScreen: WelcomeScreen()));

    // 2. Verify that the Welcome Screen appears.
    // We look for the text "Welcome to TeaCare" which is on your WelcomeScreen.
    expect(find.text('Welcome to TeaCare'), findsOneWidget);
    
    // We verify that we are NOT seeing a counter (just to be safe)
    expect(find.text('0'), findsNothing);
  });
}
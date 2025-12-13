import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class WeatherScreen extends StatefulWidget {
  const WeatherScreen({super.key});

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  Map<String, dynamic>? _weatherData;
  bool _isLoading = true;

  final String serverUrl = "http://192.168.8.122:8000/weather";

  @override
  void initState() {
    super.initState();
    _fetchWeather();
  }

  Future<void> _fetchWeather() async {
    try {
      final response = await http.get(Uri.parse(serverUrl));
      if (response.statusCode == 200) {
        setState(() {
          _weatherData = jsonDecode(response.body);
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: const Text(
          "Weather Risk",
          style: TextStyle(color: Colors.black),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF11D452)),
            )
          : _weatherData == null
          ? const Center(child: Text("Failed to load weather"))
          : Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // location
                  Center(
                    child: Column(
                      children: [
                        Text(
                          _weatherData!['location'],
                          style: const TextStyle(
                            fontSize: 18,
                            color: Colors.grey,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Icon(
                          Icons.cloud,
                          size: 80,
                          color: Colors.blueAccent,
                        ),
                        Text(
                          "${_weatherData!['temperature']}°C",
                          style: const TextStyle(
                            fontSize: 64,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1F2937),
                          ),
                        ),
                        Text(
                          _weatherData!['condition'],
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 40),

                  // risk card
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: _weatherData!['risk_level'] == "High"
                          ? const Color(0xFFFEE2E2)
                          : const Color(0xFFDCFCE7),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: _weatherData!['risk_level'] == "High"
                            ? Colors.red
                            : Colors.green,
                        width: 1.5,
                      ),
                    ),
                    child: Column(
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              _weatherData!['risk_level'] == "High"
                                  ? Icons.warning_rounded
                                  : Icons.check_circle,
                              color: _weatherData!['risk_level'] == "High"
                                  ? Colors.red
                                  : Colors.green,
                              size: 30,
                            ),
                            const SizedBox(width: 10),
                            Text(
                              "${_weatherData!['risk_level']} Disease Risk",
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: _weatherData!['risk_level'] == "High"
                                    ? Colors.red[800]
                                    : Colors.green[800],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Text(
                          "Forecast: ${_weatherData!['disease_forecast']}",
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _weatherData!['advice'],
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.black87),
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

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:geolocator/geolocator.dart'; // Import Geolocator
import 'package:intl/intl.dart';

class WeatherScreen extends StatefulWidget {
  const WeatherScreen({super.key});

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  Map<String, dynamic>? _weatherData;
  bool _isLoading = true;
  String? _errorMessage;

  // Update with your server IP
  final String serverUrl = "http://192.168.8.122:8000/weather";

  @override
  void initState() {
    super.initState();
    _getLocationAndFetchWeather(); // Start the process
  }

  // --- NEW: Get GPS Location first ---
  Future<void> _getLocationAndFetchWeather() async {
    try {
      // 1. Check & Request Permissions
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        throw "Location services are disabled. Please enable GPS.";
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw "Location permissions are denied.";
        }
      }

      if (permission == LocationPermission.deniedForever) {
        throw "Location permissions are permanently denied.";
      }

      // 2. Get Current Position
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high
      );

      // 3. Fetch Weather with REAL Coordinates
      await _fetchWeather(position.latitude, position.longitude);

    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage = e.toString();
      });
      print("Location Error: $e");
      
      // Fallback to Colombo if GPS fails
      _fetchWeather(6.9271, 79.8612);
    }
  }

  Future<void> _fetchWeather(double lat, double lng) async {
    try {
      // Pass lat & lng as query parameters
      final url = Uri.parse("$serverUrl?lat=$lat&lng=$lng");
      
      final response = await http.get(url);
      if (response.statusCode == 200) {
        setState(() {
          _weatherData = jsonDecode(response.body);
          _isLoading = false;
        });
      } else {
        throw "Server error: ${response.statusCode}";
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage = "Failed to load weather data";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F4F6),
      appBar: AppBar(
        title: const Text("Weather Forecast", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF4CAF50)))
          : _errorMessage != null && _weatherData == null
              ? Center(child: Text(_errorMessage!, style: const TextStyle(color: Colors.red)))
              : _weatherData == null
                  ? const Center(child: Text("Failed to load weather data"))
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // 1. CURRENT WEATHER HEADER
                          _buildCurrentWeatherCard(),
                          
                          const SizedBox(height: 20),

                          // 2. SPRAYING ADVISOR & METRICS
                          Row(
                            children: [
                              Expanded(child: _buildInfoTile(
                                "Humidity", 
                                "${_weatherData!['humidity']}%", 
                                Icons.water_drop, 
                                Colors.blue
                              )),
                              const SizedBox(width: 12),
                              Expanded(child: _buildInfoTile(
                                "Wind", 
                                "${_weatherData!['wind_speed']} km/h", 
                                Icons.air, 
                                Colors.grey
                              )),
                            ],
                          ),
                          const SizedBox(height: 12),
                          _buildSprayingCard(),

                          const SizedBox(height: 24),

                          // 3. DISEASE ALERT
                          const Text("Disease Risk Analysis", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 12),
                          _buildRiskCard(),

                          const SizedBox(height: 24),

                          // 4. 7-DAY FORECAST
                          const Text("7-Day Forecast", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 12),
                          _buildForecastList(),
                        ],
                      ),
                    ),
    );
  }
  
  // ... (Keep the rest of your UI widgets: _buildCurrentWeatherCard, etc. unchanged) ...
  // Paste the UI widgets from the previous weather_screen.dart response here
  
  Widget _buildCurrentWeatherCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFF4CAF50), Color(0xFF2E7D32)]),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [BoxShadow(color: Colors.green.withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 5))],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded( // Added Expanded to prevent overflow
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _weatherData!['location'], 
                  style: const TextStyle(color: Colors.white70, fontSize: 16),
                  overflow: TextOverflow.ellipsis, // Handle long location names
                ),
                const SizedBox(height: 4),
                Text(
                  "${_weatherData!['temperature']}°",
                  style: const TextStyle(color: Colors.white, fontSize: 48, fontWeight: FontWeight.bold),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(20)),
                  child: Text(_weatherData!['condition'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                ),
              ],
            ),
          ),
          Icon(_getWeatherIcon(_weatherData!['condition']), color: Colors.white, size: 80),
        ],
      ),
    );
  }

  Widget _buildInfoTile(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        ],
      ),
    );
  }

  Widget _buildSprayingCard() {
    String status = _weatherData!['spraying_condition'];
    bool isSafe = status.contains("Safe");
    Color color = isSafe ? Colors.green : Colors.orange;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
            child: Icon(Icons.science, color: color),
          ),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("Chemical Spraying", style: TextStyle(color: Colors.grey, fontSize: 12)),
              Text(status, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: color)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRiskCard() {
    bool isHigh = _weatherData!['risk_level'] == "High";
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isHigh ? const Color(0xFFFEE2E2) : const Color(0xFFECFDF5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isHigh ? Colors.red.withOpacity(0.3) : Colors.green.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(isHigh ? Icons.warning : Icons.check_circle, color: isHigh ? Colors.red : Colors.green),
              const SizedBox(width: 8),
              Text(
                "${_weatherData!['risk_level']} Disease Risk",
                style: TextStyle(fontWeight: FontWeight.bold, color: isHigh ? Colors.red[800] : Colors.green[800], fontSize: 16),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(_weatherData!['advice'], style: const TextStyle(color: Colors.black87, height: 1.4)),
        ],
      ),
    );
  }

  Widget _buildForecastList() {
    List<dynamic> daily = _weatherData!['daily_forecast'];
    return Container(
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: daily.length,
        separatorBuilder: (c, i) => Divider(height: 1, color: Colors.grey[100]),
        itemBuilder: (context, index) {
          var day = daily[index];
          // Simple date parsing if you don't want intl package:
          String dateStr = day['date'].substring(5); // removes YYYY-
          
          return ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
            leading: Text(dateStr, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
            title: Row(
              children: [
                const SizedBox(width: 10),
                Icon(_getWeatherIcon(day['condition']), size: 24, color: Colors.blueGrey),
                const SizedBox(width: 10),
                Text(day['condition'], style: const TextStyle(fontSize: 14)),
              ],
            ),
            trailing: Text("${day['max_temp']}° / ${day['min_temp']}°", style: const TextStyle(fontWeight: FontWeight.bold)),
          );
        },
      ),
    );
  }

  IconData _getWeatherIcon(String condition) {
    switch (condition) {
      case "Sunny": return Icons.wb_sunny;
      case "Cloudy": return Icons.cloud;
      case "Rainy": return Icons.umbrella;
      case "Storm": return Icons.thunderstorm;
      default: return Icons.wb_cloudy;
    }
  }
}
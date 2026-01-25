import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:geolocator/geolocator.dart'; 
import 'package:shared_preferences/shared_preferences.dart'; // Added for user_id

class WeatherScreen extends StatefulWidget {
  const WeatherScreen({super.key});

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  Map<String, dynamic>? _weatherData;
  bool _isLoading = true;
  String? _errorMessage;

  // Ensure this IP matches your PC
  final String serverUrl = "http://192.168.8.122:8000/weather";

  @override
  void initState() {
    super.initState();
    _getLocationAndFetchWeather();
  }

  // --- 1. GPS LOCATION & FETCH ---
  Future<void> _getLocationAndFetchWeather() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        throw "GPS is disabled. Please enable it.";
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

      // Get accurate location
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      await _fetchWeather(position.latitude, position.longitude);

    } catch (e) {
      print("Location Error: $e");
      // Fallback to a default location (e.g. Badulla/Colombo) if GPS fails
      if (mounted) _fetchWeather(6.9847, 81.0566); 
    }
  }

  Future<void> _fetchWeather(double lat, double lng) async {
    try {
      // Get User ID for the "Demo Notification" trigger
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getInt('userId') ?? 1;

      // Pass lat, lng AND user_id
      final url = Uri.parse("$serverUrl?lat=$lat&lng=$lng&user_id=$userId");
      
      final response = await http.get(url);

      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _weatherData = jsonDecode(response.body);
            _isLoading = false;
          });
        }
      } else {
        throw "Server error: ${response.statusCode}";
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = "Could not connect to weather service.";
        });
      }
    }
  }

  // --- HELPER: Safe Data Extraction (The Fix for the Red Screen) ---
  String _safeVal(String key, {String defaultVal = "N/A"}) {
    if (_weatherData == null || _weatherData![key] == null) return defaultVal;
    return _weatherData![key].toString();
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
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 1. CURRENT WEATHER
                      _buildCurrentWeatherCard(),
                      const SizedBox(height: 20),

                      // 2. METRICS ROW
                      Row(
                        children: [
                          Expanded(child: _buildInfoTile(
                            "Humidity", 
                            "${_safeVal('humidity', defaultVal: '0')}%", 
                            Icons.water_drop, 
                            Colors.blue
                          )),
                          const SizedBox(width: 12),
                          Expanded(child: _buildInfoTile(
                            "Wind", 
                            "${_safeVal('wind_speed', defaultVal: '0')} km/h", 
                            Icons.air, 
                            Colors.grey
                          )),
                        ],
                      ),
                      const SizedBox(height: 12),
                      
                      // 3. SPRAYING ADVICE
                      _buildSprayingCard(),
                      const SizedBox(height: 24),

                      // 4. DISEASE ALERT
                      const Text("Disease Risk Analysis", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      _buildRiskCard(),
                      const SizedBox(height: 24),

                      // 5. 7-DAY FORECAST
                      const Text("7-Day Forecast", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      _buildForecastList(),
                    ],
                  ),
                ),
    );
  }

  // --- UI WIDGETS (Updated with Safe Access) ---

  Widget _buildCurrentWeatherCard() {
    String condition = _safeVal('condition', defaultVal: "Sunny");
    
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
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _safeVal('location', defaultVal: "Tea Estate"), 
                  style: const TextStyle(color: Colors.white70, fontSize: 16),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  "${_safeVal('temperature', defaultVal: '0')}°",
                  style: const TextStyle(color: Colors.white, fontSize: 48, fontWeight: FontWeight.bold),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(20)),
                  child: Text(condition, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                ),
              ],
            ),
          ),
          Icon(_getWeatherIcon(condition), color: Colors.white, size: 80),
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
    String status = _safeVal('spraying_condition', defaultVal: "Safe");
    bool isSafe = !status.contains("Unsafe"); 
    Color color = isSafe ? Colors.green : Colors.red;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
            child: Icon(isSafe ? Icons.check_circle : Icons.cancel, color: color),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("Chemical Spraying", style: TextStyle(color: Colors.grey, fontSize: 12)),
                Text(status, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: color)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRiskCard() {
    String level = _safeVal('risk_level', defaultVal: "Low");
    bool isHigh = level == "High";
    
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
              Icon(isHigh ? Icons.warning : Icons.health_and_safety, color: isHigh ? Colors.red : Colors.green),
              const SizedBox(width: 8),
              Text(
                "$level Risk",
                style: TextStyle(fontWeight: FontWeight.bold, color: isHigh ? Colors.red[800] : Colors.green[800], fontSize: 16),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
             _safeVal('advice', defaultVal: "Monitor field conditions."), 
             style: const TextStyle(color: Colors.black87, height: 1.4)
          ),
        ],
      ),
    );
  }

  Widget _buildForecastList() {
    // Safely check if daily_forecast exists
    List<dynamic> daily = (_weatherData != null && _weatherData!['daily_forecast'] is List) 
        ? _weatherData!['daily_forecast'] 
        : [];

    if (daily.isEmpty) return const Text("Forecast unavailable");

    return Container(
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: daily.length,
        separatorBuilder: (c, i) => Divider(height: 1, color: Colors.grey[100]),
        itemBuilder: (context, index) {
          var day = daily[index];
          String dateStr = day['date'].toString().substring(5);
          String cond = day['condition'] ?? "Cloudy";
          
          return ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
            leading: Text(dateStr, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
            title: Row(
              children: [
                const SizedBox(width: 10),
                Icon(_getWeatherIcon(cond), size: 24, color: Colors.blueGrey),
                const SizedBox(width: 10),
                Text(cond, style: const TextStyle(fontSize: 14)),
              ],
            ),
            trailing: Text("${day['max_temp']}° / ${day['min_temp']}°", style: const TextStyle(fontWeight: FontWeight.bold)),
          );
        },
      ),
    );
  }

  IconData _getWeatherIcon(String condition) {
    if (condition.contains("Rain")) return Icons.umbrella;
    if (condition.contains("Storm")) return Icons.thunderstorm;
    if (condition.contains("Cloud")) return Icons.cloud;
    if (condition.contains("Sunny") || condition.contains("Clear")) return Icons.wb_sunny;
    return Icons.wb_cloudy;
  }
}
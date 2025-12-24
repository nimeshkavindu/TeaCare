import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class LocationPickerScreen extends StatefulWidget {
  const LocationPickerScreen({super.key});

  @override
  State<LocationPickerScreen> createState() => _LocationPickerScreenState();
}

class _LocationPickerScreenState extends State<LocationPickerScreen> {
  final MapController _mapController = MapController();
  final TextEditingController _searchController = TextEditingController();
  
  // Default fallback (Colombo), will be overwritten by GPS
  LatLng _selectedLocation = const LatLng(6.9271, 79.8612);
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // Automatically find user location when screen opens
    _getCurrentLocation();
  }

  // --- 1. GET CURRENT GPS LOCATION ---
  Future<void> _getCurrentLocation() async {
    setState(() => _isLoading = true);
    
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _showError("Location services are disabled.");
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          _showError("Location permissions are denied");
          return;
        }
      }

      // Get accurate position
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high
      );
      
      LatLng newLoc = LatLng(position.latitude, position.longitude);
      
      // Move map and update pin
      _mapController.move(newLoc, 16.0);
      setState(() => _selectedLocation = newLoc);
      
    } catch (e) {
      // Don't show error on init, just fallback to default
      if (mounted) print("Error getting location: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // --- 2. SEARCH LOCATION ---
  Future<void> _searchLocation() async {
    String query = _searchController.text.trim();
    if (query.isEmpty) return;

    setState(() => _isLoading = true);
    FocusScope.of(context).unfocus(); 

    try {
      final url = Uri.parse(
          "https://nominatim.openstreetmap.org/search?q=$query&format=json&limit=1");
      
      final response = await http.get(url, headers: {
        "User-Agent": "TeaCareApp/1.0"
      });

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data.isNotEmpty) {
          double lat = double.parse(data[0]['lat']);
          double lon = double.parse(data[0]['lon']);
          
          LatLng newLoc = LatLng(lat, lon);
          _mapController.move(newLoc, 15.0);
          setState(() => _selectedLocation = newLoc);
        } else {
          _showError("Location not found");
        }
      }
    } catch (e) {
      _showError("Search failed. Check internet.");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Select Estate Location"),
        backgroundColor: const Color(0xFF4E7C46),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      resizeToAvoidBottomInset: false, 
      body: Stack(
        children: [
          // --- THE MAP ---
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _selectedLocation,
              initialZoom: 13.0,
              onTap: (_, point) {
                setState(() => _selectedLocation = point);
              },
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.example.teacare',
              ),
              MarkerLayer(
                markers: [
                  Marker(
                    point: _selectedLocation,
                    width: 80,
                    height: 80,
                    child: const Icon(Icons.location_on, color: Colors.red, size: 50),
                  ),
                ],
              ),
            ],
          ),

          // --- SEARCH BAR ---
          Positioned(
            top: 16,
            left: 16,
            right: 16,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 10),
                ],
              ),
              child: Row(
                children: [
                  const SizedBox(width: 16),
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      decoration: const InputDecoration(
                        hintText: "Search city (e.g. Kandy)",
                        border: InputBorder.none,
                      ),
                      onSubmitted: (_) => _searchLocation(),
                    ),
                  ),
                  IconButton(
                    icon: _isLoading 
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) 
                      : const Icon(Icons.search),
                    onPressed: _searchLocation,
                  ),
                ],
              ),
            ),
          ),

          // --- MY LOCATION BUTTON (Google Maps Style) ---
          Positioned(
            bottom: 100,
            right: 20,
            child: FloatingActionButton(
              heroTag: "gps_btn",
              backgroundColor: Colors.white,
              onPressed: _getCurrentLocation,
              child: const Icon(Icons.my_location, color: Colors.blue),
            ),
          ),

          // --- CONFIRM BUTTON ---
          Positioned(
            bottom: 30,
            left: 20,
            right: 20,
            child: SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context, _selectedLocation);
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4E7C46),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 5,
                ),
                child: const Text("Confirm Location", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class HeatMapScreen extends StatefulWidget {
  const HeatMapScreen({super.key});

  @override
  State<HeatMapScreen> createState() => _HeatMapScreenState();
}

class _HeatMapScreenState extends State<HeatMapScreen> {
  List<Marker> _markers = [];
  bool _isLoading = true;
  
  // Default center (Sri Lanka)
  final LatLng _initialCenter = const LatLng(7.8731, 80.7718); 

  @override
  void initState() {
    super.initState();
    _fetchLocations();
  }

  Future<void> _fetchLocations() async {
    // Update IP if needed
    final String serverUrl = "http://192.168.8.122:8000/reports/locations"; 

    try {
      final response = await http.get(Uri.parse(serverUrl));

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        
        setState(() {
          _markers = data.map((report) {
            double lat = report['latitude'];
            double lng = report['longitude'];
            String disease = report['disease_name'];
            bool isHealthy = disease.toLowerCase().contains('healthy');

            return Marker(
              point: LatLng(lat, lng),
              width: 80,
              height: 80,
              child: GestureDetector(
                onTap: () => _showReportDetails(report),
                child: Icon(
                  Icons.location_on,
                  color: isHealthy ? Colors.green : Colors.red,
                  size: 40,
                ),
              ),
            );
          }).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      print("Error fetching map data: $e");
      setState(() => _isLoading = false);
    }
  }

  void _showReportDetails(dynamic report) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        return Container(
          padding: const EdgeInsets.all(20),
          width: double.infinity,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(report['disease_name'], style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text("Reported on: ${report['timestamp']}", style: TextStyle(color: Colors.grey[600])),
              const SizedBox(height: 16),
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.network(
                  "http://192.168.8.122:8000/${report['image_url']}",
                  height: 150,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (c,e,s) => Container(height: 100, color: Colors.grey[200], child: const Center(child: Icon(Icons.broken_image))),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Disease Outbreak Map", style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator())
        : FlutterMap(
            options: MapOptions(
              initialCenter: _initialCenter,
              initialZoom: 8.0, // Zoomed out to see the whole country
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.example.teacare',
              ),
              MarkerLayer(markers: _markers),
            ],
          ),
    );
  }
}
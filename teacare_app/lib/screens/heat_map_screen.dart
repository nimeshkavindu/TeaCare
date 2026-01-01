import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_map_marker_cluster/flutter_map_marker_cluster.dart';
import 'package:flutter_map_heatmap/flutter_map_heatmap.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class HeatMapScreen extends StatefulWidget {
  const HeatMapScreen({super.key});

  @override
  State<HeatMapScreen> createState() => _HeatMapScreenState();
}

class _HeatMapScreenState extends State<HeatMapScreen> {
  final MapController _mapController = MapController();
  final TextEditingController _searchController = TextEditingController();
  
  List<dynamic> _allReports = [];
  List<Marker> _markers = [];
  List<WeightedLatLng> _heatMapData = [];
  
  bool _isLoading = true;
  bool _isHeatMapMode = false; 

  // --- FILTERS ---
  String _selectedDisease = "All";
  final List<String> _diseaseFilters = ["All", "Healthy Leaf", "Blister Blight", "Red Spider", "Gray Blight", "Helopeltis"];

  String _selectedTime = "All Time";
  final List<String> _timeFilters = ["All Time", "24h", "This Week", "This Month", "This Year"];

  final LatLng _center = const LatLng(7.8731, 80.7718); 

  @override
  void initState() {
    super.initState();
    _getCurrentLocation();
    _fetchLocations();
  }

  // --- GPS & SEARCH (Unchanged) ---
  Future<void> _getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) return;
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) return;
      }
      Position pos = await Geolocator.getCurrentPosition();
      _mapController.move(LatLng(pos.latitude, pos.longitude), 14.0);
    } catch (e) {
      print("GPS Error: $e");
    }
  }

  Future<void> _searchLocation() async {
    String query = _searchController.text.trim();
    if (query.isEmpty) return;
    FocusScope.of(context).unfocus();
    try {
      final url = Uri.parse("https://nominatim.openstreetmap.org/search?q=$query&format=json&limit=1");
      final response = await http.get(url, headers: {"User-Agent": "TeaCareApp/1.0"});
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data.isNotEmpty) {
          double lat = double.parse(data[0]['lat']);
          double lon = double.parse(data[0]['lon']);
          _mapController.move(LatLng(lat, lon), 13.0);
        }
      }
    } catch (e) {
      print("Search Error: $e");
    }
  }

  // --- FETCH DATA ---
  Future<void> _fetchLocations() async {
    // UPDATE YOUR IP
    final String serverUrl = "http://192.168.8.122:8000/reports/locations"; 

    try {
      final response = await http.get(Uri.parse(serverUrl));
      if (response.statusCode == 200) {
        setState(() {
          _allReports = jsonDecode(response.body);
          _applyFilters(); // Apply both filters immediately
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  // --- MAIN FILTER LOGIC ---
  void _applyFilters() {
    List<dynamic> filteredList = _allReports;
    final now = DateTime.now();

    // 1. Filter by DISEASE
    if (_selectedDisease != "All") {
      filteredList = filteredList.where((r) => 
        r['disease_name'].toString().toLowerCase().contains(_selectedDisease.toLowerCase())
      ).toList();
    }

    // 2. Filter by TIME
    if (_selectedTime != "All Time") {
      filteredList = filteredList.where((r) {
        try {
          // Parse "2023-12-25 14:30" -> DateTime
          // Replace space with T to make it ISO-8601 compatible for easier parsing if needed, 
          // or just parse standard SQL format.
          String cleanTime = r['timestamp'].toString().replaceAll(" ", "T"); 
          DateTime reportTime = DateTime.parse(cleanTime);
          
          if (_selectedTime == "24h") {
            return reportTime.isAfter(now.subtract(const Duration(hours: 24)));
          } else if (_selectedTime == "This Week") {
            return reportTime.isAfter(now.subtract(const Duration(days: 7)));
          } else if (_selectedTime == "This Month") {
            return reportTime.isAfter(now.subtract(const Duration(days: 30)));
          } else if (_selectedTime == "This Year") {
            return reportTime.isAfter(now.subtract(const Duration(days: 365)));
          }
          return true;
        } catch (e) {
          return true; // Keep if date parsing fails (safety)
        }
      }).toList();
    }

    // 3. Prepare Markers (Cluster Layer)
    List<Marker> newMarkers = filteredList.map((report) {
      return Marker(
        point: LatLng(report['latitude'], report['longitude']),
        width: 60,
        height: 60,
        child: GestureDetector(
          onTap: () => _showReportDetails(report),
          child: _buildCustomPin(report['disease_name']),
        ),
      );
    }).toList();

    // 4. Prepare Heatmap Data (Density Layer)
    List<WeightedLatLng> newHeatData = [];
    for (var report in filteredList) {
      double intensity = 1.0; 
      try {
        String confStr = report['confidence'].toString().replaceAll('%', '');
        intensity = double.parse(confStr) / 100.0;
      } catch (e) {
        intensity = 1.0;
      }
      
      if (!report['disease_name'].toString().toLowerCase().contains('healthy')) {
         newHeatData.add(WeightedLatLng(
           LatLng(report['latitude'], report['longitude']), 
           intensity
         ));
      }
    }

    setState(() {
      _markers = newMarkers;
      _heatMapData = newHeatData;
    });
  }

  // --- UI HELPERS ---
  Widget _buildCustomPin(String disease) {
    bool isHealthy = disease.toLowerCase().contains("healthy");
    Color color = isHealthy ? Colors.green : Colors.red;
    return Icon(Icons.location_on, color: color, size: 40);
  }

  void _showReportDetails(dynamic report) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        margin: const EdgeInsets.all(16),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(report['disease_name'], style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text("Confidence: ${report['confidence']}"),
            const SizedBox(height: 8),
            Text("Reported: ${report['timestamp']}", style: TextStyle(color: Colors.grey[600])),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // LAYER 1: MAP
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _center,
              initialZoom: 8.0,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.example.teacare',
              ),

              if (_isHeatMapMode)
                HeatMapLayer(
                  heatMapDataSource: InMemoryHeatMapDataSource(data: _heatMapData),
                  heatMapOptions: HeatMapOptions(
                    radius: 35,
                    minOpacity: 0.1,
                    gradient: {0.2: Colors.blue, 0.5: Colors.yellow, 0.8: Colors.orange, 1.0: Colors.red}
                  ),
                ),

              if (!_isHeatMapMode)
                MarkerClusterLayerWidget(
                  options: MarkerClusterLayerOptions(
                    maxClusterRadius: 45,
                    size: const Size(40, 40),
                    alignment: Alignment.center,
                    padding: const EdgeInsets.all(50),
                    markers: _markers,
                    builder: (context, markers) {
                      return Container(
                        decoration: BoxDecoration(
                          color: const Color(0xFF4E7C46),
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 2),
                        ),
                        child: Center(
                          child: Text(
                            markers.length.toString(),
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                        ),
                      );
                    },
                  ),
                ),
            ],
          ),

          // LAYER 2: CONTROLS
          Positioned(
            top: 50, left: 16, right: 16,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. Search Bar
                Container(
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), boxShadow: [const BoxShadow(color: Colors.black12, blurRadius: 10)]),
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: "Search city...",
                      border: InputBorder.none,
                      prefixIcon: const Icon(Icons.search),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    ),
                    onSubmitted: (_) => _searchLocation(),
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // 2. Time Filter Row (NEW)
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: _timeFilters.map((filter) {
                      bool isSelected = _selectedTime == filter;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8.0),
                        child: FilterChip(
                          label: Text(filter),
                          selected: isSelected,
                          onSelected: (val) => setState(() { _selectedTime = filter; _applyFilters(); }),
                          backgroundColor: Colors.white,
                          selectedColor: Colors.blue[100], // Distinct color for time
                          labelStyle: TextStyle(
                            color: isSelected ? Colors.blue[900] : Colors.black87,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal
                          ),
                          checkmarkColor: Colors.blue[900],
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20), 
                            side: BorderSide(color: isSelected ? Colors.blue : Colors.transparent)
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),

                const SizedBox(height: 8),

                // 3. Disease Filter Row
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: _diseaseFilters.map((filter) {
                      bool isSelected = _selectedDisease == filter;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8.0),
                        child: FilterChip(
                          label: Text(filter),
                          selected: isSelected,
                          onSelected: (val) => setState(() { _selectedDisease = filter; _applyFilters(); }),
                          backgroundColor: Colors.white,
                          selectedColor: const Color(0xFF4E7C46).withOpacity(0.2),
                          labelStyle: TextStyle(
                            color: isSelected ? const Color(0xFF4E7C46) : Colors.black87,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal
                          ),
                          checkmarkColor: const Color(0xFF4E7C46),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),
          ),

          // TOGGLE BUTTON
          Positioned(
            bottom: 120, right: 20,
            child: FloatingActionButton.extended(
              heroTag: "mode_toggle",
              onPressed: () => setState(() => _isHeatMapMode = !_isHeatMapMode),
              backgroundColor: Colors.white,
              icon: Icon(_isHeatMapMode ? Icons.pin_drop : Icons.local_fire_department, color: _isHeatMapMode ? Colors.green : Colors.orange),
              label: Text(_isHeatMapMode ? "Show Pins" : "Show Heatmap", style: const TextStyle(color: Colors.black)),
            ),
          ),

          // LOCATE BUTTON
          Positioned(
            bottom: 50, right: 20,
            child: FloatingActionButton(
              heroTag: "gps_btn",
              backgroundColor: Colors.white,
              onPressed: _getCurrentLocation,
              child: const Icon(Icons.my_location, color: Color(0xFF4E7C46)),
            ),
          ),
        ],
      ),
    );
  }
}
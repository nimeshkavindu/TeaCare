import 'package:flutter/material.dart';

class TreatmentScreen extends StatelessWidget {
  final String diseaseName;
  final List<dynamic> treatments;

  const TreatmentScreen({
    super.key,
    required this.diseaseName,
    required this.treatments,
  });

  @override
  Widget build(BuildContext context) {
    // Separate treatments
    final organic = treatments.where((t) => t['type'] == 'Organic').toList();
    final chemical = treatments.where((t) => t['type'] == 'Chemical').toList();

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.grey.shade50,
        appBar: AppBar(
          title: Text(diseaseName, style: const TextStyle(color: Colors.white)),
          backgroundColor: const Color(0xFF658D3D), // Leafy Green
          elevation: 0,
          bottom: const TabBar(
            indicatorColor: Colors.white,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            tabs: [
              Tab(icon: Icon(Icons.eco), text: "Organic Solutions"),
              Tab(icon: Icon(Icons.science), text: "Chemical Treatments"),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildTreatmentList(organic, true),
            _buildTreatmentList(chemical, false),
          ],
        ),
      ),
    );
  }

  Widget _buildTreatmentList(List<dynamic> list, bool isOrganic) {
    if (list.isEmpty) {
      return const Center(child: Text("No recommendations available for this category."));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final t = list[index];
        return _TreatmentCard(
          title: t['title'],
          type: isOrganic ? "Eco-Friendly" : "Chemical",
          tags: isOrganic ? "Organic" : "Synthetic",
          instruction: t['instruction'],
          safetyTip: t['safety_tip'],
          isOrganic: isOrganic,
        );
      },
    );
  }
}

class _TreatmentCard extends StatelessWidget {
  final String title, type, tags, instruction, safetyTip;
  final bool isOrganic;

  const _TreatmentCard({
    required this.title,
    required this.type,
    required this.tags,
    required this.instruction,
    required this.safetyTip,
    required this.isOrganic,
  });

  @override
  Widget build(BuildContext context) {
    Color themeColor = isOrganic ? Colors.green : Colors.teal;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.grey.shade200, blurRadius: 10, offset: const Offset(0, 5))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: themeColor.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                  child: Icon(isOrganic ? Icons.spa : Icons.science, color: themeColor),
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(color: themeColor.withOpacity(0.2), borderRadius: BorderRadius.circular(4)),
                      child: Text(tags, style: TextStyle(fontSize: 12, color: themeColor, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          const Divider(height: 1),
          
          // Instructions
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("Usage Instructions:", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black87)),
                const SizedBox(height: 6),
                Text(instruction, style: const TextStyle(color: Colors.black54, height: 1.5)),
                const SizedBox(height: 16),
                
                // Safety Box
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.amber.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.amber.shade200),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.warning_amber_rounded, color: Colors.amber.shade900, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("Safety Tips:", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.amber.shade900)),
                            const SizedBox(height: 4),
                            Text(safetyTip, style: TextStyle(color: Colors.amber.shade900, fontSize: 13)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

class SmartCameraScreen extends StatefulWidget {
  final Function(String path) onImageCaptured;

  const SmartCameraScreen({super.key, required this.onImageCaptured});

  @override
  State<SmartCameraScreen> createState() => _SmartCameraScreenState();
}

class _SmartCameraScreenState extends State<SmartCameraScreen> {
  CameraController? _controller;
  List<CameraDescription>? cameras;
  bool _isFlashOn = false;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    cameras = await availableCameras();
    if (cameras != null && cameras!.isNotEmpty) {
      _controller = CameraController(cameras![0], ResolutionPreset.high);
      await _controller!.initialize();
      if (mounted) setState(() {});
    }
  }

  Future<void> _takePicture() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    try {
      final image = await _controller!.takePicture();
      widget.onImageCaptured(image.path); // Send path back
      Navigator.pop(context);
    } catch (e) {
      print(e);
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return const Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // 1. Full Screen Camera
          SizedBox(
            height: MediaQuery.of(context).size.height,
            width: double.infinity,
            child: CameraPreview(_controller!),
          ),

          // 2. Leaf Overlay (User Guidance)
          Center(
            child: Opacity(
              opacity: 0.4,
              child: Image.asset(
                'assets/leaf_outline.png', // ADD A WHITE LEAF OUTLINE IMAGE TO ASSETS
                width: 300,
                color: Colors.white,
              ),
            ),
          ),
          
          // 3. Instruction Text
          Positioned(
            top: 100,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              color: Colors.black54,
              child: const Text(
                "Align leaf within the frame",
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ),

          // 4. Controls (Flash, Capture)
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  icon: Icon(_isFlashOn ? Icons.flash_on : Icons.flash_off, color: Colors.white, size: 30),
                  onPressed: () {
                    setState(() => _isFlashOn = !_isFlashOn);
                    _controller!.setFlashMode(_isFlashOn ? FlashMode.torch : FlashMode.off);
                  },
                ),
                GestureDetector(
                  onTap: _takePicture,
                  child: Container(
                    height: 80,
                    width: 80,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 4),
                      color: Colors.transparent,
                    ),
                    child: Container(
                      margin: const EdgeInsets.all(4),
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 40), // Spacer
              ],
            ),
          )
        ],
      ),
    );
  }
}
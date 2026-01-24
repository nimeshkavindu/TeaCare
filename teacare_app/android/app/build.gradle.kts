plugins {
    id("com.android.application")
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.example.teacare_app"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        
        // --- CHANGE 1: Enable Desugaring (Kotlin Syntax) ---
        isCoreLibraryDesugaringEnabled = true  // <--- ADD THIS LINE
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.example.teacare_app"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        
        // Optional: Good to have for larger apps
        multiDexEnabled = true 
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}

// --- CHANGE 2: Add Dependencies Block (Kotlin Syntax) ---
dependencies {
    // This library makes modern Java features work on old Android phones
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.0.4") // <--- ADD THIS
}
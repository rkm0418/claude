plugins {
    id("com.android.application")
    kotlin("android")
}

android {
    namespace = "app.harulock"
    compileSdk = 36

    defaultConfig {
        applicationId = "app.harulock"
        minSdk = 30
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }

    buildFeatures {
        buildConfig = true
    }

    // debug는 시험판(src/debug의 testOnly), release는 정식판. 둘 다 debug 키로 서명한다.
    buildTypes {
        debug {
            buildConfigField("boolean", "FINAL_GUARD", "false")
        }
        release {
            buildConfigField("boolean", "FINAL_GUARD", "true")
            signingConfig = signingConfigs.getByName("debug")
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation(project(":core"))
}

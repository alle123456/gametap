# -*- coding: utf-8 -*-
# ============================================================
#  GameTap 工程一键生成器
#  运行: python3 setup.py  （在仓库根目录，Actions 里自动执行）
#  本地想用: 把下面 ROOT 改成 "GameTap" 再运行，然后压缩上传
#  每个文件前的注释就是【文件名/路径】
# ============================================================
import os

ROOT = "."

FILES = {}

# ---- [1/29] settings.gradle ----
FILES["settings.gradle"] = r"""
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "GameTap"
include ':app'
"""

# ---- [2/29] build.gradle ----
FILES["build.gradle"] = r"""
plugins {
    id 'com.android.application' version '8.5.2' apply false
}
"""

# ---- [3/29] gradle.properties ----
FILES["gradle.properties"] = r"""
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
"""

# ---- [4/29] gradle/wrapper/gradle-wrapper.properties ----
FILES["gradle/wrapper/gradle-wrapper.properties"] = r"""
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.7-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""

# ---- [5/29] app/build.gradle ----
FILES["app/build.gradle"] = r"""
plugins { id 'com.android.application' }

android {
    namespace 'com.gametap.assistant'
    compileSdk 34
    defaultConfig {
        applicationId "com.gametap.assistant"
        minSdk 26
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }
    buildFeatures { aidl true }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_11
        targetCompatibility JavaVersion.VERSION_11
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'dev.rikka.shizuku:api:13.1.5'
    implementation 'dev.rikka.shizuku:provider:13.1.5'
}
"""

# ---- [6/29] app/src/main/AndroidManifest.xml ----
FILES["app/src/main/AndroidManifest.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <queries>
        <package android:name="moe.shizuku.privileged.api" />
        <intent>
            <action android:name="android.intent.action.VIEW" />
            <data android:scheme="shizuku" />
        </intent>
    </queries>

    <application
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/Theme.GameTap"
        android:allowBackup="false">

        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".FloatingService"
            android:exported="false"
            android:foregroundServiceType="specialUse">
            <property
                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="floating game tap controller" />
        </service>

        <service android:name=".InjectorServiceImpl" android:exported="false" />

        <provider
            android:name="rikka.shizuku.ShizukuProvider"
            android:authorities="${applicationId}.shizuku"
            android:multiprocess="false"
            android:enabled="true"
            android:exported="true"
            android:permission="android.permission.INTERACT_ACROSS_USERS_FULL" />
    </application>
</manifest>
"""

# ---- [7/29] app/src/main/aidl/com/gametap/assistant/IInjectorService.aidl ----
FILES["app/src/main/aidl/com/gametap/assistant/IInjectorService.aidl"] = r"""
package com.gametap.assistant;

interface IInjectorService {
    boolean tap(int x, int y, int pressMs);
    oneway void destroy();
}
"""

# ---- [8/29] app/src/main/java/com/gametap/assistant/ShizukuHelper.java ----
FILES["app/src/main/java/com/gametap/assistant/ShizukuHelper.java"] = r"""
package com.gametap.assistant;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.IBinder;
import android.provider.Settings;

import rikka.shizuku.Shizuku;

public class ShizukuHelper {

    public static boolean installed() {
        try { return Shizuku.pingBinder(); } catch (Throwable t) { return false; }
    }

    public static boolean ready() {
        try 

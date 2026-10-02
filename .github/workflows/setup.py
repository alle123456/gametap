# -*- coding: utf-8 -*-
# ============================================================
#  GameTap 工程一键生成器（GitHub Actions 自动运行）
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
        try {
            return Shizuku.pingBinder()
                    && Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED;
        } catch (Throwable t) { return false; }
    }

    @SuppressWarnings("deprecation")
    public static void requestPermission() { Shizuku.requestPermission(0); }

    public static boolean grantOverlay(Context ctx) throws Exception {
        String cmd = "appops set --user 0 " + ctx.getPackageName() + " SYSTEM_ALERT_WINDOW allow";
        Process p = Shizuku.newProcess(new String[]{"sh", "-c", cmd}, null, null);
        p.waitFor();
        return Settings.canDrawOverlays(ctx);
    }

    public static void bindInjector(final Context ctx, final InjectorCallback cb) {
        try {
            Intent it = new Intent(ctx, InjectorServiceImpl.class);
            Shizuku.bindUserService(it, new ServiceConnection() {
                @Override
                public void onServiceConnected(ComponentName name, IBinder service) {
                    cb.onReady(IInjectorService.Stub.asInterface(service));
                }

                @Override
                public void onServiceDisconnected(ComponentName name) {
                    cb.onLost();
                }
            });
        } catch (Throwable t) {
            cb.onLost();
        }
    }

    public interface InjectorCallback {
        void onReady(IInjectorService s);
        void onLost();
    }
}
"""

# ---- [9/29] app/src/main/java/com/gametap/assistant/InjectorServiceImpl.java ----
FILES["app/src/main/java/com/gametap/assistant/InjectorServiceImpl.java"] = r"""
package com.gametap.assistant;

import android.content.Context;
import android.os.SystemClock;
import android.util.Log;
import android.view.InputDevice;
import android.view.InputEvent;
import android.view.MotionEvent;

import java.lang.reflect.Method;

public class InjectorServiceImpl implements IInjectorService {

    private static final String TAG = "GameTapInjector";

    private final Object inputManager;
    private final Method injectMethod;

    public InjectorServiceImpl(Context context) {
        Object im = null;
        Method m = null;
        try {
            Class<?> cls = Class.forName("android.hardware.input.InputManager");
            im = cls.getMethod("getInstance").invoke(null);
            try {
                m = cls.getMethod("injectInputEvent", MotionEvent.class, int.class);
            } catch (NoSuchMethodException e) {
                m = cls.getMethod("injectInputEvent", InputEvent.class, int.class);
            }
        } catch (Throwable t) {
            Log.e(TAG, "init failed", t);
        }
        this.inputManager = im;
        this.injectMethod = m;
    }

    @Override
    public boolean tap(int x, int y, int pressMs) {
        if (inputManager == null || injectMethod == null) return false;
        try {
            long down = SystemClock.uptimeMillis();
            MotionEvent md = MotionEvent.obtain(down, down, MotionEvent.ACTION_DOWN, x, y, 0);
            md.setSource(InputDevice.SOURCE_TOUCHSCREEN);
            injectMethod.invoke(inputManager, md, 0);
            md.recycle();

            if (pressMs > 5) SystemClock.sleep(pressMs);

            long up = SystemClock.uptimeMillis();
            MotionEvent mu = MotionEvent.obtain(down, up, MotionEvent.ACTION_UP, x, y, 0);
            mu.setSource(InputDevice.SOURCE_TOUCHSCREEN);
            injectMethod.invoke(inputManager, mu, 0);
            mu.recycle();
            return true;
        } catch (Throwable t) {
            Log.e(TAG, "tap failed", t);
            return false;
        }
    }

    @Override
    public void destroy() { }
}
"""

# ---- [10/29] app/src/main/java/com/gametap/assistant/PointStore.java ----
FILES["app/src/main/java/com/gametap/assistant/PointStore.java"] = r"""
package com.gametap.assistant;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class PointStore {

    public static class TapPoint {
        public int x, y;
        public int pressMs = 60;
        public int intervalMs = 300;
        public int count = 1;
        public boolean enabled = true;

        public TapPoint() {}
        public TapPoint(int x, int y) { this.x = x; this.y = y; }

        public JSONObject toJson() throws org.json.JSONException {
            return new JSONObject()
                    .put("x", x).put("y", y)
                    .put("press", pressMs).put("interval", intervalMs)
                    .put("count", count).put("on", enabled);
        }

        public static TapPoint fromJson(JSONObject o) {
            TapPoint p = new TapPoint();
            p.x = o.optInt("x");
            p.y = o.optInt("y");
            p.pressMs = o.optInt("press", 60);
            p.intervalMs = o.optInt("interval", 300);
            p.count = o.optInt("count", 1);
            p.enabled = o.optBoolean("on", true);
            return p;
        }
    }

    public static class Profile {
        public String name;
        public int rounds = 0;
        public int roundGapMs = 300;
        public List<TapPoint> points = new ArrayList<>();
    }

    private final SharedPreferences sp;
    public final Map<String, Profile> profiles = new LinkedHashMap<>();
    public String currentName;

    public PointStore(Context c) {
        sp = c.getSharedPreferences("gametap", Context.MODE_PRIVATE);
        load();
    }

    public synchronized void load() {
        profiles.clear();
        try {
            JSONObject root = new JSONObject(sp.getString("data", "{}"));
            JSONArray arr = root.optJSONArray("list");
            if (arr != null) {
                for (int i = 0; i < arr.length(); i++) {
                    JSONObject po = arr.getJSONObject(i);
                    Profile pf = new Profile();
                    pf.name = po.getString("name");
                    pf.rounds = po.optInt("rounds", 0);
                    pf.roundGapMs = po.optInt("gap", 300);
                    JSONArray ps = po.optJSONArray("points");
                    if (ps != null) {
                        for (int j = 0; j < ps.length(); j++) {
                            pf.points.add(TapPoint.fromJson(ps.getJSONObject(j)));
                        }
                    }
                    profiles.put(pf.name, pf);
                }
            }
            currentName = root.optString("current");
        } catch (Exception ignored) { }
        if (profiles.isEmpty()) {
            Profile pf = new Profile();
            pf.name = "方案 1";
            profiles.put(pf.name, pf);
            currentName = pf.name;
            save();
        }
        if (!profiles.containsKey(currentName)) {
            currentName = profiles.keySet().iterator().next();
        }
    }

    public synchronized void save() {
        try {
            JSONArray arr = new JSONArray();
            for (Profile pf : profiles.values()) {
                JSONArray ps = new JSONArray();
                for (TapPoint p : pf.points) ps.put(p.toJson());
                arr.put(new JSONObject()
                        .put("name", pf.name)
                        .put("rounds", pf.rounds)
                        .put("gap", pf.roundGapMs)
                        .put("points", ps));
            }
            sp.edit().putString("data",
                    new JSONObject().put("list", arr).put("current", currentName).toString()).apply();
        } catch (Exception ignored) { }
    }

    public synchronized Profile current() { return profiles.get(currentName); }

    public synchronized void addProfile(String name) {
        Profile pf = new Profile();
        pf.name = name;
        profiles.put(name, pf);
        currentName = name;
        save();
    }

    public synchronized void deleteProfile(String name) {
        profiles.remove(name);
        if (profiles.isEmpty()) { addProfile("方案 1"); return; }
        if (name.equals(currentName)) {
            currentName = profiles.keySet().iterator().next();
        }
        save();
    }
}
"""

# ---- [11/29] app/src/main/java/com/gametap/assistant/TapEngine.java ----
FILES["app/src/main/java/com/gametap/assistant/TapEngine.java"] = r"""
package com.gametap.assistant;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.util.ArrayList;
import java.util.List;

import rikka.shizuku.Shizuku;

public class TapEngine {

    public interface Callback {
        void onProgress(int round, int total);
        void onFinished(String error);
    }

    public static final int MODE_INJECT = 0;
    public static final int MODE_SHELL = 1;

    private static final String OK = "__OK__";

    private volatile Thread worker;
    private volatile boolean running;
    private volatile IInjectorService injector;
    private volatile int mode = MODE_INJECT;

    private Process shellProc;
    private BufferedWriter shellIn;
    private BufferedReader shellOut;

    public void setInjector(IInjectorService s) { injector = s; }
    public void setMode(int m) { mode = m; }
    public boolean isRunning() { return running; }

    public synchronized void start(final PointStore.Profile profile, final Callback cb) {
        if (running) return;
        final List<PointStore.TapPoint> pts = new ArrayList<>(profile.points);
        final int rounds = profile.rounds;
        final int gap = profile.roundGapMs;
        running = true;

        worker = new Thread(() -> {
            String error = null;
            int round = 0;
            try {
                if (mode != MODE_INJECT || injector == null) openShell();
                outer:
                while (running && (rounds <= 0 || round < rounds)) {
                    round++;
                    if (cb != null) cb.onProgress(round, rounds);
                    for (PointStore.TapPoint p : pts) {
                        if (!running) break outer;
                        if (!p.enabled) continue;
                        int c = Math.max(p.count, 1);
                        for (int i = 0; i < c && running; i++) {
                            doTap(p.x, p.y, p.pressMs);
                            if (p.intervalMs > 0) Thread.sleep(p.intervalMs);
                        }
                    }
                    if (gap > 0 && (rounds <= 0 || round < rounds)) Thread.sleep(gap);
                }
            } catch (Throwable t) {
                if (running && !(t instanceof InterruptedException)) {
                    error = t.getMessage() == null ? t.toString() : t.getMessage();
                }
            } finally {
                closeShell();
                running = false;
                worker = null;
                if (cb != null) cb.onFinished(error);
            }
        }, "TapEngine");
        worker.start();
    }

    public synchronized void stop() {
        running = false;
        Thread w = worker;
        if (w != null) w.interrupt();
        closeShell();
    }

    private void doTap(int x, int y, int pressMs) throws Exception {
        if (mode == MODE_INJECT && injector != null) {
            injector.tap(x, y, pressMs);
        } else {
            shellTap(x, y, pressMs);
        }
    }

    private void openShell() throws Exception {
        closeShell();
        shellProc = Shizuku.newProcess(new String[]{"sh"}, null, null);
        shellIn = new BufferedWriter(new OutputStreamWriter(shellProc.getOutputStream()));
        shellOut = new BufferedReader(new InputStreamReader(shellProc.getInputStream()));
    }

    private void shellTap(int x, int y, int pressMs) throws Exception {
        String cmd = pressMs >= 30
                ? String.format("input swipe %d %d %d %d %d", x, y, x, y, pressMs)
                : String.format("input tap %d %d", x, y);
        shellIn.write(cmd + "\necho " + OK + "\n");
        shellIn.flush();
        String line;
        while ((line = shellOut.readLine()) != null) {
            if (line.contains(OK)) return;
        }
        throw new IOException("Shizuku shell 已断开");
    }

    private void closeShell() {
        if (shellProc != null) {
            shellProc.destroy();
            shellProc = null;
        }
        shellIn = null;
        shellOut = null;
    }
}
"""

# ---- [12/29] app/src/main/java/com/gametap/assistant/FloatingService.java ----
FILES["app/src/main/java/com/gametap/assistant/FloatingService.java"] = r"""
package com.gametap.assistant;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;

public class FloatingService extends Service implements ShizukuHelper.InjectorCallback {

    public static boolean alive = false;

    private static final TapEngine ENGINE = new TapEngine();
    public static boolean engineRunning() { return ENGINE.isRunning(); }

    private WindowManager wm;
    private PointStore store;
    private final Handler main = new Handler(Looper.getMainLooper());
    private IInjectorService injector;

    private View handle, panel, capture;
    private WindowManager.LayoutParams handleParams, panelParams;
    private final List<View> markers = new ArrayList<>();
    private boolean panelShown = false;
    private int markerMode = 0;
    private boolean destroyed = false;

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onCreate() {
        super.onCreate();
        alive = true;
        destroyed = false;
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        store = new PointStore(this);
        startForeground(1, buildNotification());
        showHandle();
        bindInjector();
        refreshMarkers();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) { return START_STICKY; }

    @Override
    public void onDestroy() {
        alive = false;
        destroyed = true;
        ENGINE.stop();
        removeAll();
        super.onDestroy();
    }

    private Notification buildNotification() {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        nm.createNotificationChannel(new NotificationChannel(
                "tap", "游戏指令", NotificationManager.IMPORTANCE_LOW));
        return new Notification.Builder(this, "tap")
                .setSmallIcon(R.drawable.ic_launcher)
                .setContentTitle("游戏指令助手运行中")
                .setContentText("点屏幕边缘 ▶ 把手展开控制面板")
                .build();
    }

    private void bindInjector() {
        if (destroyed) return;
        if (!ShizukuHelper.installed()) return;
        ShizukuHelper.bindInjector(this, this);
    }

    @Override
    public void onReady(IInjectorService s) {
        injector = s;
        ENGINE.setInjector(s);
    }

    @Override
    public void onLost() {
        injector = null;
        if (!destroyed) main.postDelayed(this::bindInjector, 3000);
    }

    private WindowManager.LayoutParams overlayParams() {
        WindowManager.LayoutParams p = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);
        p.gravity = Gravity.TOP | Gravity.START;
        return p;
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    private void showHandle() {
        handle = LayoutInflater.from(this).inflate(R.layout.overlay_handle, null);
        handleParams = overlayParams();
        handleParams.x = 0;
        handleParams.y = dp(200);
        wm.addView(handle, handleParams);

        final float[] d = new float[2];
        final boolean[] moved = {false};
        handle.setOnTouchListener((v, e) -> {
            switch (e.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    d[0] = handleParams.x - e.getRawX();
                    d[1] = handleParams.y - e.getRawY();
                    moved[0] = false;
                    return true;
                case MotionEvent.ACTION_MOVE: {
                    int nx = (int) (e.getRawX() + d[0]);
                    int ny = (int) (e.getRawY() + d[1]);
                    if (Math.abs(nx - handleParams.x) + Math.abs(ny - handleParams.y) > 14)
                        moved[0] = true;
                    handleParams.x = nx;
                    handleParams.y = ny;
                    try { wm.updateViewLayout(handle, handleParams); } catch (Exception ignored) {}
                    if (panelShown && panel != null) {
                        panelParams.x = handleParams.x;
                        panelParams.y = handleParams.y + handle.getHeight() + dp(8);
                        try { wm.updateViewLayout(panel, panelParams); } catch (Exception ignored) {}
                    }
                    return true;
                }
                case MotionEvent.ACTION_UP:
                    if (!moved[0]) togglePanel();
                    return true;
            }
            return false;
        });
    }

    private void setHandleRunning(boolean run) {
        if (handle != null) {
            handle.setBackgroundResource(run ? R.drawable.bg_handle_run : R.drawable.bg_handle);
        }
    }

    private void togglePanel() {
        if (panelShown) { hidePanel(); return; }
        store.load();
        refreshMarkers();
        panel = LayoutInflater.from(this).inflate(R.layout.overlay_panel, null);
        panelParams = overlayParams();
        panelParams.x = handleParams.x;
        panelParams.y = handleParams.y + handle.getHeight() + dp(8);

        TextView btnRun = panel.findViewById(R.id.btnRun);
        updateRunLabel(btnRun);
        btnRun.setOnClickListener(v -> {
            if (ENGINE.isRunning()) ENGINE.stop(); else startEngine();
            updateRunLabel(btnRun);
        });
        panel.findViewById(R.id.btnAdd).setOnClickListener(v -> showCapture());
        panel.findViewById(R.id.btnMark).setOnClickListener(v -> {
            markerMode = (markerMode + 1) % 3;
            refreshMarkers();
        });
        panel.findViewById(R.id.btnClose).setOnClickListener(v -> hidePanel());

        wm.addView(panel, panelParams);
        panelShown = true;
    }

    private void hidePanel() {
        if (panel != null) {
            try { wm.removeView(panel); } catch (Exception ignored) {}
            panel = null;
        }
        panelShown = false;
    }

    private void updateRunLabel(TextView b) {
        b.setText(ENGINE.isRunning() ? "■ 停止" : "▶ 开始");
    }

    private void startEngine() {
        if (ENGINE.isRunning()) return;
        store.load();
        PointStore.Profile pf = store.current();
        if (pf.points.isEmpty()) { toast("先添加至少一个点击点"); return; }

        ENGINE.setMode(ShizukuHelper.ready() ? TapEngine.MODE_INJECT : TapEngine.MODE_SHELL);
        ENGINE.setInjector(injector);

        markerMode = 1;
        refreshMarkers();
        setHandleRunning(true);

        ENGINE.start(pf, new TapEngine.Callback() {
            @Override
            public void onProgress(int round, int total) { }

            @Override
            public void onFinished(String error) {
                main.post(() -> {
                    setHandleRunning(false);
                    markerMode = 0;
                    refreshMarkers();
                    if (panelShown && panel != null) {
                        updateRunLabel(panel.findViewById(R.id.btnRun));
                    }
                    toast(error == null ? "执行结束" : "执行出错：" + error);
                });
            }
        });
    }

    private void showCapture() {
        if (ENGINE.isRunning()) { toast("执行中不能添加点位"); return; }
        hidePanel();
        capture = LayoutInflater.from(this).inflate(R.layout.overlay_capture, null);
        capture.setBackgroundColor(0x66000000);

        WindowManager.LayoutParams p = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);
        p.gravity = Gravity.TOP | Gravity.START;

        capture.setOnTouchListener((v, e) -> {
            if (e.getActionMasked() == MotionEvent.ACTION_DOWN) {
                int x = (int) e.getRawX();
                int y = (int) e.getRawY();
                removeCapture();
                store.current().points.add(new PointStore.TapPoint(x, y));
                store.save();
                refreshMarkers();
                toast("已添加点击点 (" + x + "," + y + ")，回 App 里调参数");
            }
            return true;
        });
        wm.addView(capture, p);
    }

    private void removeCapture() {
        if (capture != null) {
            try { wm.removeView(capture); } catch (Exception ignored) {}
            capture = null;
        }
    }

    private void refreshMarkers() {
        for (View v : markers) {
            try { wm.removeView(v); } catch (Exception ignored) {}
        }
        markers.clear();
        if (capture != null || markerMode == 2) return;

        int i = 1;
        for (PointStore.TapPoint p : store.current().points) {
            View m = LayoutInflater.from(this).inflate(R.layout.overlay_marker, null);
            TextView t = m.findViewById(R.id.markerText);
            t.setText(String.valueOf(i++));
            if (!p.enabled) t.setAlpha(0.35f);

            WindowManager.LayoutParams lp = overlayParams();
            lp.width = lp.height = dp(44);
            lp.x = p.x - dp(22);
            lp.y = p.y - dp(22);
            if (markerMode == 1) {
                lp.flags |= WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE;
            }

            if (markerMode == 0) {
                final float[] d = new float[2];
                m.setOnTouchListener((v, e) -> {
                    switch (e.getActionMasked()) {
                        case MotionEvent.ACTION_DOWN:
                            d[0] = lp.x - e.getRawX();
                            d[1] = lp.y - e.getRawY();
                            return true;
                        case MotionEvent.ACTION_MOVE:
                            lp.x = (int) (e.getRawX() + d[0]);
                            lp.y = (int) (e.getRawY() + d[1]);
                            try { wm.updateViewLayout(v, lp); } catch (Exception ignored) {}
                            return true;
                        case MotionEvent.ACTION_UP:
                            p.x = lp.x + dp(22);
                            p.y = lp.y + dp(22);
                            store.save();
                            return true;
                    }
                    return false;
                });
            }
            wm.addView(m, lp);
            markers.add(m);
        }
    }

    private void removeAll() {
        removeCapture();
        for (View v : markers) {
            try { wm.removeView(v); } catch (Exception ignored) {}
        }
        markers.clear();
        hidePanel();
        if (handle != null) {
            try { wm.removeView(handle); } catch (Exception ignored) {}
            handle = null;
        }
    }

    private void toast(String s) {
        Toast.makeText(this, s, Toast.LENGTH_SHORT).show();
    }
}
"""

# ---- [13/29] app/src/main/java/com/gametap/assistant/MainActivity.java ----
FILES["app/src/main/java/com/gametap/assistant/MainActivity.java"] = r"""
package com.gametap.assistant;

import android.Manifest;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private PointStore store;
    private TextView tvShizuku;
    private Spinner spinner;
    private LinearLayout pointsBox;
    private EditText etRounds, etGap;
    private boolean spinnerGuard = false;
    private boolean pendingActivate = false;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.activity_main);
        store = new PointStore(this);

        tvShizuku = findViewById(R.id.tvShizuku);
        spinner = findViewById(R.id.spinnerProfile);
        pointsBox = findViewById(R.id.pointsBox);
        etRounds = findViewById(R.id.etRounds);
        etGap = findViewById(R.id.etGap);

        if (Build.VERSION.SDK_INT >= 33) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
        }

        findViewById(R.id.btnActivate).setOnClickListener(v -> doActivate());
        findViewById(R.id.btnOverlay).setOnClickListener(v -> toggleService());
        findViewById(R.id.btnNewProfile).setOnClickListener(v -> newProfile());
        findViewById(R.id.btnDelProfile).setOnClickListener(v -> delProfile());

        etRounds.addTextChangedListener(simple(s -> {
            store.current().rounds = parseInt(s);
            store.save();
        }));
        etGap.addTextChangedListener(simple(s -> {
            store.current().roundGapMs = parseInt(s);
            store.save();
        }));

        spinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(android.widget.AdapterView<?> parent, View view, int pos, long id) {
                if (spinnerGuard) return;
                String name = (String) parent.getItemAtPosition(pos);
                if (name != null && !name.equals(store.currentName)) {
                    store.currentName = name;
                    store.save();
                    renderAll();
                }
            }

            @Override
            public void onNothingSelected(android.widget.AdapterView<?> parent) { }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        store.load();
        renderAll();
        refreshStatus();
    }

    private void doActivate() {
        if (!ShizukuHelper.installed()) {
            msg("Shizuku 未连接：请先安装 Shizuku 并启动（Root 或 无线调试模式），保持后台运行后重试");
            return;
        }
        if (ShizukuHelper.ready()) { grantOverlay(); return; }
        if (pendingActivate) return;
        pendingActivate = true;
        ShizukuHelper.requestPermission();
        msg("请在弹窗中允许授权…");
        final Handler h = new Handler(Looper.getMainLooper());
        h.postDelayed(new Runnable() {
            int tries = 0;
            @Override
            public void run() {
                if (!pendingActivate) return;
                if (ShizukuHelper.ready()) {
                    pendingActivate = false;
                    grantOverlay();
                    return;
                }
                if (++tries < 60) {
                    h.postDelayed(this, 300);
                } else {
                    pendingActivate = false;
                    refreshStatus();
                    msg("等待授权超时，请重试「一键激活」");
                }
            }
        }, 400);
    }

    private void grantOverlay() {
        pendingActivate = false;
        try {
            boolean ok = ShizukuHelper.grantOverlay(this);
            refreshStatus();
            msg(ok ? "激活成功！悬浮窗权限已自动授予，可以启动悬浮窗了"
                   : "appops 已执行但未生效，请到系统设置手动允许显示悬浮窗");
        } catch (Throwable t) {
            msg("激活失败：" + t.getMessage());
        }
    }

    private void refreshStatus() {
        String s;
        if (!ShizukuHelper.installed()) {
            s = "❌ Shizuku 未运行（需安装并启动）";
        } else if (!ShizukuHelper.ready()) {
            s = "⚠️ Shizuku 已运行，等待授权";
        } else {
            s = "✅ Shizuku 已授权（极速注入可用）";
        }
        s += Settings.canDrawOverlays(this) ? " ｜ 悬浮窗 ✅" : " ｜ 悬浮窗 ❌（点一键激活）";
        tvShizuku.setText(s);
        findViewById(R.id.btnOverlay).setEnabled(Settings.canDrawOverlays(this));
        ((TextView) findViewById(R.id.btnOverlay))
                .setText(FloatingService.alive ? "停止悬浮窗" : "启动悬浮窗");
    }

    private void toggleService() {
        if (FloatingService.alive) {
            stopService(new Intent(this, FloatingService.class));
        } else {
            if (!Settings.canDrawOverlays(this)) {
                msg("悬浮窗权限未授予，先点「一键激活」");
                return;
            }
            startForegroundService(new Intent(this, FloatingService.class));
        }
        tvShizuku.postDelayed(this::refreshStatus, 400);
    }

    private void newProfile() {
        final EditText et = new EditText(this);
        et.setHint("方案名称");
        new AlertDialog.Builder(this).setTitle("新建方案").setView(et)
                .setPositiveButton("确定", (d, w) -> {
                    String n = et.getText().toString().trim();
                    if (!n.isEmpty() && !store.profiles.containsKey(n)) {
                        store.addProfile(n);
                        renderAll();
                    }
                })
                .setNegativeButton("取消", null).show();
    }

    private void delProfile() {
        if (store.profiles.size() <= 1) { msg("至少保留一个方案"); return; }
        new AlertDialog.Builder(this).setTitle("删除方案")
                .setMessage("删除「" + store.currentName + "」及其所有点位？")
                .setPositiveButton("删除", (d, w) -> {
                    store.deleteProfile(store.currentName);
                    store.load();
                    renderAll();
                })
                .setNegativeButton("取消", null).show();
    }

    private void renderAll() {
        List<String> names = new ArrayList<>(store.profiles.keySet());
        spinnerGuard = true;
        spinner.setAdapter(new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_dropdown_item, names));
        int idx = names.indexOf(store.currentName);
        if (idx >= 0) spinner.setSelection(idx);
        spinner.post(() -> spinnerGuard = false);

        PointStore.Profile pf = store.current();
        setTextIf(etRounds, String.valueOf(pf.rounds));
        setTextIf(etGap, String.valueOf(pf.roundGapMs));

        pointsBox.removeAllViews();
        int i = 1;
        for (PointStore.TapPoint p : pf.points) {
            pointsBox.addView(pointView(pf, p, i++));
        }

        ((TextView) findViewById(R.id.tvPointHint)).setText(pf.points.isEmpty()
                ? "还没有点击点：启动悬浮窗 → 点把手 → 「＋ 点位」→ 在屏幕上点一下即取点"
                : "共 " + pf.points.size() + " 个点位；悬浮窗里「◎ 标记」切编辑模式可拖动调整位置");
    }

    private View pointView(final PointStore.Profile pf, final PointStore.TapPoint p, int idx) {
        View v = LayoutInflater.from(this).inflate(R.layout.item_point, pointsBox, false);
        ((TextView) v.findViewById(R.id.tvIndex)).setText(String.valueOf(idx));
        ((TextView) v.findViewById(R.id.tvXY)).setText("(" + p.x + ", " + p.y + ")");

        EditText etPress = v.findViewById(R.id.etPress);
        EditText etInt = v.findViewById(R.id.etInterval);
        EditText etCount = v.findViewById(R.id.etCount);
        etPress.setText(String.valueOf(p.pressMs));
        etInt.setText(String.valueOf(p.intervalMs));
        etCount.setText(String.valueOf(p.count));
        etPress.addTextChangedListener(simple(s -> {
            p.pressMs = parseInt(s);
            store.save();
        }));
        etInt.addTextChangedListener(simple(s -> {
            p.intervalMs = parseInt(s);
            store.save();
        }));
        etCount.addTextChangedListener(simple(s -> {
            p.count = parseInt(s);
            store.save();
        }));

        Switch sw = v.findViewById(R.id.swEnabled);
        sw.setOnCheckedChangeListener(null);
        sw.setChecked(p.enabled);
        sw.setOnCheckedChangeListener((btn, c) -> {
            p.enabled = c;
            store.save();
        });

        v.findViewById(R.id.btnDelete).setOnClickListener(btn -> {
            if (FloatingService.engineRunning()) { msg("执行中，先停止再删除点位"); return; }
            pf.points.remove(p);
            store.save();
            renderAll();
        });
        return v;
    }

    private interface SCallback { void run(String s); }

    private TextWatcher simple(final SCallback cb) {
        return new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence c, int a, int b, int d) { }

            @Override
            public void onTextChanged(CharSequence c, int a, int b, int d) {
                cb.run(c.toString());
            }

            @Override
            public void afterTextChanged(Editable e) { }
        };
    }

    private void setTextIf(EditText et, String s) {
        if (!et.getText().toString().equals(s)) et.setText(s);
    }

    private int parseInt(String s) {
        try { return Integer.parseInt(s.trim()); } catch (Exception e) { return 0; }
    }

    private void msg(String s) {
        Toast.makeText(this, s, Toast.LENGTH_LONG).show();
    }
}
"""

# ---- [14/29] app/src/main/res/drawable/ic_launcher.xml ----
FILES["app/src/main/res/drawable/ic_launcher.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="48dp"
    android:height="48dp"
    android:viewportWidth="48"
    android:viewportHeight="48">
    <path
        android:fillColor="#14141E"
        android:pathData="M24,2 a22,22 0 1,0 0.01,0 z" />
    <path
        android:fillColor="#2979FF"
        android:pathData="M27,7 L14,28 h8 L19,41 L34,20 h-8 Z" />
</vector>
"""

# ---- [15/29] app/src/main/res/drawable/bg_card.xml ----
FILES["app/src/main/res/drawable/bg_card.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="@color/card" />
    <corners android:radius="12dp" />
</shape>
"""

# ---- [16/29] app/src/main/res/drawable/bg_btn.xml ----
FILES["app/src/main/res/drawable/bg_btn.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="#2B2B3A" />
    <corners android:radius="8dp" />
</shape>
"""

# ---- [17/29] app/src/main/res/drawable/bg_panel.xml ----
FILES["app/src/main/res/drawable/bg_panel.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="#E6161620" />
    <corners android:radius="14dp" />
</shape>
"""

# ---- [18/29] app/src/main/res/drawable/bg_marker.xml ----
FILES["app/src/main/res/drawable/bg_marker.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <solid android:color="#332979FF" />
    <stroke android:width="2dp" android:color="@color/accent" />
</shape>
"""

# ---- [19/29] app/src/main/res/drawable/bg_handle.xml ----
FILES["app/src/main/res/drawable/bg_handle.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <solid android:color="#CC2979FF" />
    <stroke android:width="1dp" android:color="#80FFFFFF" />
</shape>
"""

# ---- [20/29] app/src/main/res/drawable/bg_handle_run.xml ----
FILES["app/src/main/res/drawable/bg_handle_run.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <solid android:color="#CCFF5252" />
    <stroke android:width="1dp" android:color="#80FFFFFF" />
</shape>
"""

# ---- [21/29] app/src/main/res/layout/activity_main.xml ----
FILES["app/src/main/res/layout/activity_main.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:fillViewport="true">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp">

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginBottom="12dp"
            android:text="@string/app_name"
            android:textColor="@color/textPrimary"
            android:textSize="24sp"
            android:textStyle="bold" />

        <LinearLayout style="@style/Card">

            <TextView
                android:id="@+id/tvShizuku"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginBottom="10dp"
                android:text="检查 Shizuku 状态中…"
                android:textColor="@color/textPrimary"
                android:textSize="13sp" />

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal">

                <TextView
                    android:id="@+id/btnActivate"
                    style="@style/Btn"
                    android:text="一键激活" />

                <TextView
                    android:id="@+id/btnOverlay"
                    style="@style/Btn"
                    android:text="启动悬浮窗" />
            </LinearLayout>
        </LinearLayout>

        <LinearLayout style="@style/Card">

            <TextView
                style="@style/Label"
                android:text="方案（可建多套指令，游戏里随时切）" />

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:gravity="center_vertical"
                android:orientation="horizontal">

                <Spinner
                    android:id="@+id/spinnerProfile"
                    android:layout_width="0dp"
                    android:layout_height="40dp"
                    android:layout_weight="1"
                    android:background="@drawable/bg_btn" />

                <TextView
                    android:id="@+id/btnNewProfile"
                    style="@style/BtnSmall"
                    android:text="＋" />

                <TextView
                    android:id="@+id/btnDelProfile"
                    style="@style/BtnSmall"
                    android:text="🗑" />
            </LinearLayout>
        </LinearLayout>

        <LinearLayout style="@style/Card">

            <TextView
                style="@style/Label"
                android:text="循环设置" />

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:gravity="center_vertical"
                android:orientation="horizontal">

                <TextView
                    style="@style/Label"
                    android:layout_width="wrap_content"
                    android:layout_marginBottom="0dp"
                    android:text="轮数" />

                <EditText
                    android:id="@+id/etRounds"
                    style="@style/EditNum"
                    android:hint="0=无限" />

                <TextView
                    style="@style/Label"
                    android:layout_width="wrap_content"
                    android:layout_marginBottom="0dp"
                    android:text="轮间隔ms" />

                <EditText
                    android:id="@+id/etGap"
                    style="@style/EditNum"
                    android:hint="300" />
            </LinearLayout>
        </LinearLayout>

        <LinearLayout style="@style/Card">

            <TextView
                style="@style/Label"
                android:text="点击点（从上到下顺序执行）" />

            <TextView
                android:id="@+id/tvPointHint"
                style="@style/Label" />

            <LinearLayout
                android:id="@+id/pointsBox"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="vertical" />
        </LinearLayout>

        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:lineSpacingExtra="4dp"
            android:text="使用流程：① 安装并启动 Shizuku（无线调试或 Root）→ ② 点「一键激活」→ ③ 启动悬浮窗 → ④ 点悬浮把手 →「＋ 点位」在屏幕上取点 → ⑤ 回这里调按住/间隔/次数 → ⑥ 游戏里点「▶ 开始」。\n执行时标记完全穿透不影响游戏；间隔建议 ≥ 60ms（极速模式可低至 20ms）。"
            android:textColor="@color/textDim"
            android:textSize="12sp" />
    </LinearLayout>
</ScrollView>
"""

# ---- [22/29] app/src/main/res/layout/item_point.xml ----
FILES["app/src/main/res/layout/item_point.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:background="@drawable/bg_card"
    android:gravity="center_vertical"
    android:orientation="horizontal"
    android:padding="10dp">

    <TextView
        android:id="@+id/tvIndex"
        android:layout_width="28dp"
        android:layout_height="28dp"
        android:background="@drawable/bg_marker"
        android:gravity="center"
        android:textColor="@color/accent"
        android:textSize="13sp" />

    <LinearLayout
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_marginStart="10dp"
        android:layout_weight="1"
        android:orientation="vertical">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:gravity="center_vertical"
            android:orientation="horizontal">

            <TextView
                android:id="@+id/tvXY"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:textColor="@color/textDim"
                android:textSize="12sp" />

            <Switch
                android:id="@+id/swEnabled"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginStart="8dp" />

            <TextView
                android:id="@+id/btnDelete"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:padding="6dp"
                android:text="✕"
                android:textColor="@color/textDim"
                android:textSize="14sp" />
        </LinearLayout>

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="6dp"
            android:orientation="horizontal">

            <EditText
                android:id="@+id/etPress"
                style="@style/EditNum"
                android:hint="按住ms" />

            <EditText
                android:id="@+id/etInterval"
                style="@style/EditNum"
                android:hint="间隔ms" />

            <EditText
                android:id="@+id/etCount"
                style="@style/EditNum"
                android:hint="次数" />
        </LinearLayout>
    </LinearLayout>
</LinearLayout>
"""

# ---- [23/29] app/src/main/res/layout/overlay_handle.xml ----
FILES["app/src/main/res/layout/overlay_handle.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<TextView xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/handleDot"
    android:layout_width="44dp"
    android:layout_height="44dp"
    android:background="@drawable/bg_handle"
    android:gravity="center"
    android:text="▶"
    android:textColor="#FFFFFF"
    android:textSize="15sp" />
"""

# ---- [24/29] app/src/main/res/layout/overlay_panel.xml ----
FILES["app/src/main/res/layout/overlay_panel.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:background="@drawable/bg_panel"
    android:orientation="vertical"
    android:padding="8dp">

    <TextView
        android:id="@+id/btnRun"
        style="@style/PanelBtn"
        android:text="▶ 开始" />

    <TextView
        android:id="@+id/btnAdd"
        style="@style/PanelBtn"
        android:text="＋ 点位" />

    <TextView
        android:id="@+id/btnMark"
        style="@style/PanelBtn"
        android:text="◎ 标记" />

    <TextView
        android:id="@+id/btnClose"
        style="@style/PanelBtn"
        android:text="✕ 收起" />
</LinearLayout>
"""

# ---- [25/29] app/src/main/res/layout/overlay_marker.xml ----
FILES["app/src/main/res/layout/overlay_marker.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<TextView xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/markerText"
    android:layout_width="44dp"
    android:layout_height="44dp"
    android:background="@drawable/bg_marker"
    android:gravity="center"
    android:text="1"
    android:textColor="@color/accent"
    android:textSize="14sp" />
"""

# ---- [26/29] app/src/main/res/layout/overlay_capture.xml ----
FILES["app/src/main/res/layout/overlay_capture.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_gravity="center"
        android:gravity="center"
        android:text="请在屏幕上点击要连点的位置\n（点击处将添加一个点击点）"
        android:textColor="#FFFFFF"
        android:textSize="18sp" />
</FrameLayout>
"""

# ---- [27/29] app/src/main/res/values/colors.xml ----
FILES["app/src/main/res/values/colors.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="bg">#0E0E14</color>
    <color name="card">#1B1B26</color>
    <color name="accent">#2979FF</color>
    <color name="accentRun">#FF5252</color>
    <color name="textPrimary">#EDEDF2</color>
    <color name="textDim">#9A9AA8</color>
</resources>
"""

# ---- [28/29] app/src/main/res/values/strings.xml ----
FILES["app/src/main/res/values/strings.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">游戏指令助手</string>
</resources>
"""

# ---- [29/29] app/src/main/res/values/themes.xml ----
FILES["app/src/main/res/values/themes.xml"] = r"""
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.GameTap" parent="Theme.AppCompat.NoActionBar">
        <item name="android:windowBackground">@color/bg</item>
        <item name="colorPrimary">@color/accent</item>
        <item name="colorAccent">@color/accent</item>
        <item name="android:statusBarColor">@color/bg</item>
        <item name="android:textColorPrimary">@color/textPrimary</item>
        <item name="android:textColorHint">@color/textDim</item>
    </style>

    <style name="Card">
        <item name="android:layout_width">match_parent</item>
        <item name="android:layout_height">wrap_content</item>
        <item name="android:orientation">vertical</item>
        <item name="android:background">@drawable/bg_card</item>
        <item name="android:padding">14dp</item>
        <item name="android:layout_marginBottom">12dp</item>
    </style>

    <style name="Btn">
        <item name="android:layout_width">0dp</item>
        <item name="android:layout_weight">1</item>
        <item name="android:layout_height">44dp</item>
        <item name="android:gravity">center</item>
        <item name="android:background">@drawable/bg_btn</item>
        <item name="android:textColor">@color/textPrimary</item>
        <item name="android:textSize">14sp</item>
        <item name="android:clickable">true</item>
        <item name="android:layout_marginEnd">8dp</item>
    </style>

    <style name="BtnSmall">
        <item name="android:layout_width">40dp</item>
        <item name="android:layout_height">40dp</item>
        <item name="android:layout_marginStart">6dp</item>
        <item name="android:gravity">center</item>
        <item name="android:background">@drawable/bg_btn</item>
        <item name="android:textColor">@color/textPrimary</item>
        <item name="android:clickable">true</item>
    </style>

    <style name="PanelBtn">
        <item name="android:layout_width">match_parent</item>
        <item name="android:layout_height">42dp</item>
        <item name="android:gravity">center</item>
        <item name="android:textColor">@color/textPrimary</item>
        <item name="android:textSize">14sp</item>
        <item name="android:clickable">true</item>
    </style>

    <style name="EditNum">
        <item name="android:layout_width">0dp</item>
        <item name="android:layout_weight">1</item>
        <item name="android:layout_height">40dp</item>
        <item name="android:layout_marginEnd">6dp</item>
        <item name="android:background">@drawable/bg_btn</item>
        <item name="android:inputType">number</item>
        <item name="android:gravity">center</item>
        <item name="android:textSize">13sp</item>
        <item name="android:textColor">@color/textPrimary</item>
        <item name="android:paddingStart">6dp</item>
        <item name="android:paddingEnd">6dp</item>
    </style>

    <style name="Label">
        <item name="android:layout_width">match_parent</item>
        <item name="android:layout_height">wrap_content</item>
        <item name="android:textColor">@color/textDim</item>
        <item name="android:textSize">12sp</item>
        <item name="android:layout_marginBottom">8dp</item>
    </style>
</resources>
"""

# ================= 生成 =================
count = 0
for rel, content in FILES.items():
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.strip("\n") + "\n")
    print("OK", rel)
    count += 1

print("\n完成！共生成 %d 个文件" % count)

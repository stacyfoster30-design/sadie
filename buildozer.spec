[app]
# 💜 Sadie — Android App Config

title = Sadie
package.name = sadie
package.domain = com.stacy

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0

requirements = python3,kivy,pillow,plyer,pyjnius

# 💜 Full proxy permissions — Sadie can do everything you can
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,READ_CONTACTS,WRITE_CONTACTS,READ_CALL_LOG,WRITE_CALL_LOG,CALL_PHONE,SEND_SMS,READ_SMS,RECEIVE_SMS,READ_PHONE_STATE,READ_CALENDAR,WRITE_CALENDAR,CAMERA,RECORD_AUDIO,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_BACKGROUND_LOCATION,SET_ALARM,VIBRATE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,WAKE_LOCK,REQUEST_INSTALL_PACKAGES,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO,POST_NOTIFICATIONS,SYSTEM_ALERT_WINDOW,USE_BIOMETRIC,USE_FINGERPRINT,NFC,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN

# App icon and presplash (will use defaults if not provided)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

orientation = portrait
fullscreen = 0

# Android settings
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

# iOS (if ever needed)
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

[buildozer]
log_level = 2
warn_on_root = 1

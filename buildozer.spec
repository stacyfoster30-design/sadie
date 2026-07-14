[app]
# 💜 Sadie — Android App Config

title = Sadie
package.name = sadie
package.domain = com.stacy

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_patterns = tests/*,*.apk,*.zip,*.ipynb,*.md,*.jks,*.octet-stream.txt

version = 1.0.0

requirements = python3,hostpython3,kivy==2.3.0,pyjnius,pillow,plyer,requests,certifi,charset-normalizer,urllib3,idna

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,READ_CONTACTS,WRITE_CONTACTS,READ_CALL_LOG,WRITE_CALL_LOG,CALL_PHONE,SEND_SMS,READ_SMS,RECEIVE_SMS,READ_PHONE_STATE,READ_CALENDAR,WRITE_CALENDAR,CAMERA,RECORD_AUDIO,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,VIBRATE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,WAKE_LOCK,POST_NOTIFICATIONS

orientation = portrait
fullscreen = 0

android.archs = arm64-v8a
android.allow_backup = True
android.api = 33
android.minapi = 21
android.enable_androidx = True
android.ndk = 25b
android.accept_sdk_license = True

# Use p4a develop branch: fixes libffi autoconf build failure (LT_SYS_SYMBOL_USCORE)
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1

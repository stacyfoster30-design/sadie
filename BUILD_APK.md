# 💜 How to Build Sadie's APK (Free Android App)

## Option 1: Build on Your Computer (Recommended)

### Step 1: Install Buildozer
```bash
pip install buildozer
```

### Step 2: Install System Dependencies

**Linux/WSL (Windows Subsystem for Linux):**
```bash
sudo apt update
sudo apt install -y python3-pip build-essential git python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev \
    libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev \
    libavcodec-dev zlib1g-dev libgstreamer1.0-dev \
    gstreamer1.0-plugins-base libunwind-dev \
    autoconf automake libtool pkg-config \
    openjdk-17-jdk unzip zip
```

**Mac:**
```bash
brew install automake autoconf libtool pkg-config sdl2 sdl2_image sdl2_mixer sdl2_ttf
```

### Step 3: Build the APK
Navigate to the `ai-proxy-agent` folder and run:
```bash
cd ai-proxy-agent
buildozer android debug
```

☕ First build takes 15-30 minutes (downloads Android SDK/NDK).
After that, the APK will be at: `bin/sadie-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`

### Step 4: Install on Your Phone
1. Transfer the APK to your phone (email it, USB, Google Drive)
2. On your phone: Settings → Security → Allow Unknown Sources
3. Tap the APK file to install
4. Open Sadie! 💜

---

## Option 2: Build for Free on Google Colab

If your computer is slow, use Google Colab (free cloud computer):

### Step 1: Open Google Colab
Go to: https://colab.research.google.com → New Notebook

### Step 2: Paste & Run This
```python
# Cell 1: Setup
!pip install buildozer cython
!sudo apt-get install -y python3-pip build-essential git python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev \
    libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev \
    libavcodec-dev zlib1g-dev openjdk-17-jdk unzip zip

# Cell 2: Create the app files
# (Upload sadie_core.py, main.py, and buildozer.spec to Colab)
# Or clone from a GitHub repo if you upload there

# Cell 3: Build
%cd /content/ai-proxy-agent
!buildozer android debug

# Cell 4: Download the APK
from google.colab import files
import glob
apk = glob.glob('bin/*.apk')[0]
files.download(apk)
```

---

## Option 3: Build on Your Phone (Termux)

If you ONLY have a phone:

### Step 1: Install Termux
Download from F-Droid (NOT Google Play): https://f-droid.org/packages/com.termux/

### Step 2: Set Up Termux
```bash
pkg update && pkg upgrade -y
pkg install python git build-essential -y
pip install kivy buildozer
```

### Step 3: Copy the Files
```bash
mkdir -p ~/sadie
# Copy sadie_core.py, main.py, and buildozer.spec into ~/sadie
```

### Step 4: Build
```bash
cd ~/sadie
buildozer android debug
```

---

## ⚡ Quick Start (Without APK)

Don't want to build an APK? Run Sadie directly in terminal:
```bash
pip install kivy
python sadie_core.py    # Terminal mode (text only)
python main.py          # GUI mode (with Kivy window)
```

---

## 🔧 Connecting to Ollama (The AI Brain)

The app needs Ollama running to give Sadie her AI brain.

**On your computer:**
1. Download Ollama: https://ollama.com
2. Run: `ollama run llama3.1`
3. Sadie connects automatically on localhost

**On your phone:**
1. Ollama doesn't run natively on Android yet
2. Options:
   - Run Ollama on your computer and connect your phone via WiFi
   - Use the `SADIE_OLLAMA_URL` environment variable to point to your computer's IP
   - Set: `export SADIE_OLLAMA_URL=http://192.168.1.XXX:11434`

---

## 💜 File Listing
```
ai-proxy-agent/
├── sadie_core.py      ← Sadie's brain, memory, personality, all abilities
├── main.py            ← Android/desktop GUI (Kivy)
├── buildozer.spec     ← APK build configuration
├── BUILD_APK.md       ← This file
├── SETUP.md           ← General setup guide
└── ai_proxy.py        ← Original basic version (from Google instructions)
```

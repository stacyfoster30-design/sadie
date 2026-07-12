# 🤖 Stacy's AI Proxy — Self-Learning Edition

## What It Does
A 100% free AI agent that runs on YOUR computer. No subscriptions, no API keys, no cloud.

### Built-in Powers
- 💻 **Code & fix repos** — writes, edits, and runs code
- 📧 **Check & send email** — full Gmail access
- 💬 **Text anyone** — free SMS via email gateways
- 📁 **Read, edit, create files** — anywhere on your system
- 🖥️ **Run terminal commands** — full shell access

### Learning Powers (NEW!)
- 🧠 **Remembers facts** — "remember that mom's birthday is March 5"
- 📇 **Saves contacts** — "save contact mom 5551234567 verizon"
- 🎓 **Learns new skills** — teach it custom workflows and it saves them forever
- ⚙️ **Stores preferences** — "prefer dark mode" or "set preference language = python"
- 📈 **Gets smarter over time** — everything persists between sessions

---

## Setup (15 minutes, one time)

### Step 1: Install Ollama (Free AI Engine)
Go to **https://ollama.com** and download for your OS.

Then open terminal and run:
```bash
ollama run llama3.1
```
Wait for it to download (~4GB). This is your free AI brain.

### Step 2: Install Python
Make sure you have Python 3.10+:
```bash
python --version
```
If not installed: **https://python.org/downloads**

### Step 3: Install Dependencies
```bash
pip install autogen-agentchat[azure,openai] autogen-ext
```

### Step 4: Configure Your Email
Open `ai_proxy_full.py` and fill in:
```python
EMAIL_ADDRESS = "your_actual_email@gmail.com"
EMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
```

**To get an App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. You need 2-Factor Authentication turned ON first
3. Generate a password for "Mail"
4. Copy paste the 16-character code

### Step 5: Run It!
```bash
python ai_proxy_full.py
```

---

## How the Learning System Works

### Teaching Skills
```
🫵 What do you need? > teach skill clean_downloads
🎓 Teaching me 'clean_downloads'!
📝 > Removes files older than 30 days from Downloads
💻 > import os, time
💻 > from pathlib import Path
💻 > def run():
💻 >     downloads = Path.home() / "Downloads"
💻 >     cutoff = time.time() - (30 * 86400)
💻 >     for f in downloads.iterdir():
💻 >         if f.stat().st_mtime < cutoff:
💻 >             f.unlink()
💻 > END
```
Now you can use it anytime: `use skill clean_downloads`

### Memory
```
🫵 What do you need? > remember that my wifi password is Sunshine2024
🧠 Got it! I'll remember that my wifi password = Sunshine2024

🫵 What do you need? > what do you know
🧠 Everything I know:
  • my wifi password: Sunshine2024
```

### Contacts
```
🫵 What do you need? > save contact mom 5551234567 verizon
📇 Saved contact: mom

🫵 What do you need? > text mom that I'm on my way home
✅ Text sent!
```

---

## Running on Your Phone (Android via Termux)
1. Install **Termux** from F-Droid
2. Run: `pkg install python ollama`
3. Copy the files over and run: `python ai_proxy_full.py`

---

## File Structure After Running
```
ai-proxy-agent/
├── ai_proxy.py           ← Basic version (from Google's instructions)
├── ai_proxy_full.py      ← Full version with learning (this one!)
├── SETUP.md              ← This file
├── skills/               ← Learned skills saved here
│   ├── registry.json     ← Skill index
│   └── skill_*.py        ← Individual skill files
├── memory/               ← Persistent memory
│   ├── knowledge.json    ← Facts & knowledge
│   ├── contacts.json     ← Saved contacts
│   └── preferences.json  ← Your preferences
└── logs/                 ← Conversation history
    └── log_YYYYMMDD.txt  ← Daily logs
```

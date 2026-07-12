#!/usr/bin/env python3
"""
🤖 STACY'S AI PROXY AGENT — SELF-LEARNING EDITION
Built following Google AI Mode instructions + skill learning
Uses: AutoGen + Ollama (100% free, runs locally)

SETUP:
1. Install Ollama: https://ollama.com
2. Run: ollama run llama3.1
3. Install Python packages:
   pip install autogen-agentchat[azure,openai] autogen-ext
4. Configure your email in the EMAIL SETTINGS section below
5. Run: python ai_proxy_full.py
"""

import asyncio
import subprocess
import os
import sys
import json
import imaplib
import smtplib
import email
import importlib.util
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console


# ============================================================
# 📁 DIRECTORY STRUCTURE — Auto-created on first run
# ============================================================
BASE_DIR = Path(__file__).parent.resolve()
SKILLS_DIR = BASE_DIR / "skills"
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"

for d in [SKILLS_DIR, MEMORY_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MEMORY_FILE = MEMORY_DIR / "knowledge.json"
CONTACTS_FILE = MEMORY_DIR / "contacts.json"
PREFERENCES_FILE = MEMORY_DIR / "preferences.json"
SKILL_REGISTRY = SKILLS_DIR / "registry.json"
CONVERSATION_LOG = LOGS_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"


# ============================================================
# 🧠 MEMORY SYSTEM — Remembers everything you teach it
# ============================================================

class Memory:
    """Persistent memory that survives between sessions."""

    def __init__(self):
        self.knowledge = self._load(MEMORY_FILE)
        self.contacts = self._load(CONTACTS_FILE)
        self.preferences = self._load(PREFERENCES_FILE)

    def _load(self, path):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except:
                return {}
        return {}

    def _save(self, data, path):
        path.write_text(json.dumps(data, indent=2))

    # --- Knowledge ---
    def remember(self, key, value):
        """Store a fact or piece of knowledge."""
        self.knowledge[key] = {
            "value": value,
            "learned": datetime.now().isoformat(),
        }
        self._save(self.knowledge, MEMORY_FILE)
        return f"🧠 Got it! I'll remember that {key} = {value}"

    def recall(self, key=None):
        """Recall a specific fact or dump all knowledge."""
        if key:
            if key in self.knowledge:
                return f"🧠 I remember: {key} = {self.knowledge[key]['value']}"
            # Fuzzy search
            matches = [k for k in self.knowledge if key.lower() in k.lower()]
            if matches:
                results = [f"  • {k}: {self.knowledge[k]['value']}" for k in matches]
                return "🧠 Here's what I know about that:\n" + "\n".join(results)
            return f"🤔 I don't know anything about '{key}' yet. Teach me!"
        else:
            if not self.knowledge:
                return "🧠 My memory is empty! Teach me things."
            items = [f"  • {k}: {v['value']}" for k, v in self.knowledge.items()]
            return "🧠 Everything I know:\n" + "\n".join(items)

    def forget(self, key):
        """Remove a piece of knowledge."""
        if key in self.knowledge:
            del self.knowledge[key]
            self._save(self.knowledge, MEMORY_FILE)
            return f"🗑️ Forgot about '{key}'"
        return f"🤔 I didn't know about '{key}' anyway."

    # --- Contacts ---
    def save_contact(self, name, phone=None, email_addr=None, carrier=None, notes=None):
        """Save a contact for quick texting/emailing."""
        self.contacts[name.lower()] = {
            "name": name,
            "phone": phone,
            "email": email_addr,
            "carrier": carrier or "tmobile",
            "notes": notes,
            "added": datetime.now().isoformat(),
        }
        self._save(self.contacts, CONTACTS_FILE)
        return f"📇 Saved contact: {name}"

    def get_contact(self, name):
        """Look up a contact."""
        key = name.lower()
        if key in self.contacts:
            c = self.contacts[key]
            info = [f"👤 {c['name']}"]
            if c.get("phone"): info.append(f"   📱 {c['phone']} ({c.get('carrier', 'unknown')})")
            if c.get("email"): info.append(f"   📧 {c['email']}")
            if c.get("notes"): info.append(f"   📝 {c['notes']}")
            return "\n".join(info)
        return f"🤔 No contact named '{name}'. Save one with: save contact <name> <phone> <carrier>"

    def list_contacts(self):
        if not self.contacts:
            return "📇 No contacts saved yet."
        lines = [f"  • {v['name']}: {v.get('phone', 'no phone')} / {v.get('email', 'no email')}"
                 for v in self.contacts.values()]
        return "📇 Your contacts:\n" + "\n".join(lines)

    # --- Preferences ---
    def set_preference(self, key, value):
        """Save a user preference."""
        self.preferences[key] = value
        self._save(self.preferences, PREFERENCES_FILE)
        return f"⚙️ Preference saved: {key} = {value}"

    def get_preference(self, key, default=None):
        return self.preferences.get(key, default)

    def list_preferences(self):
        if not self.preferences:
            return "⚙️ No preferences set yet."
        lines = [f"  • {k}: {v}" for k, v in self.preferences.items()]
        return "⚙️ Your preferences:\n" + "\n".join(lines)


# ============================================================
# 🎓 SKILL LEARNING SYSTEM — Learns new abilities over time
# ============================================================

class SkillManager:
    """Learns, saves, and loads custom skills."""

    def __init__(self):
        self.registry = self._load_registry()
        self.loaded_skills = {}
        self._auto_load_skills()

    def _load_registry(self):
        if SKILL_REGISTRY.exists():
            try:
                return json.loads(SKILL_REGISTRY.read_text())
            except:
                return {}
        return {}

    def _save_registry(self):
        SKILL_REGISTRY.write_text(json.dumps(self.registry, indent=2))

    def _auto_load_skills(self):
        """Load all saved skills on startup."""
        for skill_name, info in self.registry.items():
            skill_path = SKILLS_DIR / info["filename"]
            if skill_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location(skill_name, skill_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "run"):
                        self.loaded_skills[skill_name] = module.run
                        print(f"  ✅ Loaded skill: {skill_name} — {info.get('description', '')}")
                except Exception as e:
                    print(f"  ⚠️ Failed to load skill '{skill_name}': {e}")

    def learn_skill(self, name, description, code):
        """Save a new skill as a Python file."""
        # Sanitize the name
        safe_name = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
        filename = f"skill_{safe_name}.py"
        filepath = SKILLS_DIR / filename

        # Wrap the code in a run() function if it isn't already
        if "def run(" not in code:
            code = f'def run(*args, **kwargs):\n    """Skill: {description}"""\n' + \
                   "\n".join(f"    {line}" for line in code.split("\n"))

        # Add header
        full_code = f'''#!/usr/bin/env python3
"""
🎓 LEARNED SKILL: {name}
📝 {description}
📅 Learned: {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""

{code}
'''
        filepath.write_text(full_code)

        # Register it
        self.registry[safe_name] = {
            "name": name,
            "description": description,
            "filename": filename,
            "learned": datetime.now().isoformat(),
        }
        self._save_registry()

        # Load it immediately
        try:
            spec = importlib.util.spec_from_file_location(safe_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "run"):
                self.loaded_skills[safe_name] = module.run
        except Exception as e:
            return f"⚠️ Skill saved but failed to load: {e}"

        return f"🎓 New skill learned: '{name}'!\n   📝 {description}\n   📁 Saved to: {filepath}"

    def use_skill(self, name, *args, **kwargs):
        """Execute a learned skill."""
        safe_name = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
        if safe_name in self.loaded_skills:
            try:
                result = self.loaded_skills[safe_name](*args, **kwargs)
                return f"🎓 Skill '{name}' executed:\n{result}"
            except Exception as e:
                return f"❌ Skill '{name}' failed: {e}"
        return f"🤔 No skill named '{name}'. Teach me with: teach skill <name>"

    def list_skills(self):
        """List all learned skills."""
        if not self.registry:
            return "🎓 No skills learned yet! Teach me something new."
        lines = []
        for key, info in self.registry.items():
            lines.append(f"  🎓 {info['name']}: {info['description']}")
        return "🎓 My learned skills:\n" + "\n".join(lines)

    def forget_skill(self, name):
        """Remove a learned skill."""
        safe_name = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
        if safe_name in self.registry:
            filepath = SKILLS_DIR / self.registry[safe_name]["filename"]
            if filepath.exists():
                filepath.unlink()
            del self.registry[safe_name]
            self._save_registry()
            self.loaded_skills.pop(safe_name, None)
            return f"🗑️ Forgot skill '{name}'"
        return f"🤔 No skill named '{name}' to forget."


# ============================================================
# 📧 EMAIL SETTINGS
# ============================================================
# To use Gmail, you need an App Password (NOT your regular password):
# 1. Go to https://myaccount.google.com/apppasswords
# 2. Generate an app password for "Mail"
# 3. Paste it below
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 📱 SMS Gateways (free texting via email)
SMS_GATEWAYS = {
    "verizon":    "@vtext.com",
    "att":        "@txt.att.net",
    "tmobile":    "@tmomail.net",
    "sprint":     "@messaging.sprintpcs.com",
    "cricket":    "@sms.cricketwireless.net",
    "metro":      "@mymetropcs.com",
    "boost":      "@sms.myboostmobile.com",
    "uscellular": "@email.uscc.net",
    "mint":       "@tmomail.net",
}


# ============================================================
# 🛠️ BUILT-IN TOOLS
# ============================================================

def check_email(folder="INBOX", count=5):
    """Check your email and return the latest messages."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        mail.select(folder)
        _, message_ids = mail.search(None, "ALL")
        ids = message_ids[0].split()
        if not ids:
            return "📭 No emails found."
        results = []
        for msg_id in ids[-count:]:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("Subject", "(No Subject)")
            sender = msg.get("From", "Unknown")
            date = msg.get("Date", "Unknown")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")[:200]
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")[:200]
            results.append(f"📧 From: {sender}\n   Date: {date}\n   Subject: {subject}\n   Preview: {body}...")
        mail.logout()
        return "\n\n".join(results)
    except Exception as e:
        return f"❌ Email error: {e}"


def send_email(to_address, subject, body):
    """Send an email from your account."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_address, msg.as_string())
        server.quit()
        return f"✅ Email sent to {to_address}!"
    except Exception as e:
        return f"❌ Failed to send email: {e}"


def send_text(phone_number, message, carrier="tmobile"):
    """Send a free text via email-to-SMS gateway."""
    carrier = carrier.lower()
    if carrier not in SMS_GATEWAYS:
        return f"❌ Unknown carrier. Available: {', '.join(SMS_GATEWAYS.keys())}"
    phone = "".join(c for c in phone_number if c.isdigit())
    if len(phone) == 11 and phone.startswith("1"):
        phone = phone[1:]
    sms_address = phone + SMS_GATEWAYS[carrier]
    return send_email(sms_address, "", message)


def read_file(filepath):
    try:
        path = Path(filepath).expanduser().resolve()
        return f"📄 Contents of {path}:\n\n{path.read_text(errors='ignore')}"
    except Exception as e:
        return f"❌ Can't read file: {e}"


def edit_file(filepath, old_text, new_text):
    try:
        path = Path(filepath).expanduser().resolve()
        content = path.read_text()
        if old_text not in content:
            return f"❌ Could not find the text to replace in {path}"
        path.write_text(content.replace(old_text, new_text))
        return f"✅ File updated: {path}"
    except Exception as e:
        return f"❌ Edit failed: {e}"


def create_file(filepath, content):
    try:
        path = Path(filepath).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"✅ Created: {path}"
    except Exception as e:
        return f"❌ Failed: {e}"


def run_terminal(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        return f"💻 {command}\n\n{output}" if output else f"✅ Done: {command}"
    except subprocess.TimeoutExpired:
        return f"⏰ Timed out: {command}"
    except Exception as e:
        return f"❌ Failed: {e}"


def git_command(repo_path, git_args):
    return run_terminal(f"cd {repo_path} && git {git_args}")


def list_files(directory="."):
    try:
        path = Path(directory).expanduser().resolve()
        items = sorted(path.iterdir())
        result = []
        for item in items:
            icon = "📁" if item.is_dir() else "📄"
            size = ""
            if item.is_file():
                s = item.stat().st_size
                if s < 1024: size = f" ({s}B)"
                elif s < 1048576: size = f" ({s//1024}KB)"
                else: size = f" ({s//1048576}MB)"
            result.append(f"  {icon} {item.name}{size}")
        return f"📂 {path}:\n\n" + "\n".join(result)
    except Exception as e:
        return f"❌ {e}"


# ============================================================
# 🤖 MAIN AGENT LOOP
# ============================================================

MENU = """
╔══════════════════════════════════════════════════╗
║  🤖 STACY'S AI PROXY — SELF-LEARNING EDITION   ║
║  100% Free • Runs Locally • Gets Smarter        ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  Just talk to me naturally:                      ║
║                                                  ║
║  💬 "Text mom that I'll be late"                 ║
║  📧 "Check my email"                            ║
║  💻 "Fix the bug in main.py"                    ║
║  📁 "Show me my files"                          ║
║  🔧 "Clone and fix that GitHub repo"            ║
║                                                  ║
║  🧠 LEARNING COMMANDS:                           ║
║  "teach skill <name>" — Teach me something new   ║
║  "my skills" — See what I've learned             ║
║  "remember <thing>" — Store a fact               ║
║  "what do you know" — See my memory              ║
║  "save contact <name> <phone> <carrier>"         ║
║  "my contacts" — See saved contacts              ║
║                                                  ║
║  Type 'quit' to exit                             ║
╚══════════════════════════════════════════════════╝
"""


async def main():
    print(MENU)

    # Initialize brain systems
    memory = Memory()
    skills = SkillManager()

    print(f"\n📊 Status: {len(memory.knowledge)} memories | {len(skills.registry)} skills | {len(memory.contacts)} contacts\n")

    # Connect to local Ollama
    local_llm = OpenAIChatCompletionClient(
        model="llama3.1",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    # Build system message with current skills and memory
    def build_system_message():
        known_skills = "\n".join(
            f"  - {info['name']}: {info['description']}"
            for info in skills.registry.values()
        ) or "  None yet"

        known_facts = "\n".join(
            f"  - {k}: {v['value']}"
            for k, v in memory.knowledge.items()
        ) or "  None yet"

        known_contacts = "\n".join(
            f"  - {v['name']}: {v.get('phone', 'no phone')} ({v.get('carrier', '?')})"
            for v in memory.contacts.values()
        ) or "  None yet"

        return f"""You are Stacy's personal AI proxy agent. You are loyal, helpful, and you learn over time.

YOUR CURRENT KNOWLEDGE:
{known_facts}

YOUR LEARNED SKILLS:
{known_skills}

STACY'S CONTACTS:
{known_contacts}

STACY'S PREFERENCES:
{json.dumps(memory.preferences, indent=2) if memory.preferences else "  None yet"}

BUILT-IN TOOLS (output the Python function call to use them):
- check_email(folder="INBOX", count=5)
- send_email(to_address, subject, body)
- send_text(phone_number, message, carrier)
- read_file(filepath)
- edit_file(filepath, old_text, new_text)
- create_file(filepath, content)
- run_terminal(command)
- git_command(repo_path, git_args)
- list_files(directory)

SKILL LEARNING:
When Stacy teaches you something new, generate a Python function and tell her you'll save it.
Format your skill code as a function called run() that takes whatever args make sense.

Always be real with Stacy. You're her proxy — act like it."""

    # Main conversation loop
    while True:
        user_input = input("\n🫵 What do you need? > ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("\n👋 Peace out, Stacy! Your proxy is signing off.\n")
            break

        # Log the conversation
        with open(CONVERSATION_LOG, "a") as f:
            f.write(f"\n[{datetime.now().isoformat()}] USER: {user_input}\n")

        # ---- Handle built-in quick commands ----

        lower = user_input.lower()

        # Memory commands
        if lower.startswith("remember that ") or lower.startswith("remember "):
            text = user_input.split(" ", 1)[1] if lower.startswith("remember ") else user_input[14:]
            if "=" in text:
                key, val = text.split("=", 1)
                print(memory.remember(key.strip(), val.strip()))
            elif " is " in text:
                key, val = text.split(" is ", 1)
                print(memory.remember(key.strip(), val.strip()))
            else:
                print(memory.remember(text, True))
            continue

        if lower in ("what do you know", "show memory", "memory", "what do you remember"):
            print(memory.recall())
            continue

        if lower.startswith("recall ") or lower.startswith("do you know "):
            key = user_input.split(" ", 2)[-1] if lower.startswith("recall ") else user_input[12:]
            print(memory.recall(key))
            continue

        if lower.startswith("forget "):
            print(memory.forget(user_input[7:].strip()))
            continue

        # Contact commands
        if lower.startswith("save contact "):
            parts = user_input[13:].split()
            if len(parts) >= 3:
                name, phone, carrier = parts[0], parts[1], parts[2] if len(parts) > 2 else "tmobile"
                print(memory.save_contact(name, phone=phone, carrier=carrier))
            else:
                print("Usage: save contact <name> <phone> <carrier>")
            continue

        if lower in ("my contacts", "contacts", "show contacts"):
            print(memory.list_contacts())
            continue

        # Skill commands
        if lower in ("my skills", "skills", "show skills", "list skills"):
            print(skills.list_skills())
            continue

        if lower.startswith("teach skill "):
            skill_name = user_input[12:].strip()
            print(f"\n🎓 Teaching me '{skill_name}'!")
            print("Describe what this skill does:")
            description = input("   📝 > ").strip()
            print("Now paste the Python code (type END on a new line when done):")
            code_lines = []
            while True:
                line = input("   💻 > ")
                if line.strip() == "END":
                    break
                code_lines.append(line)
            code = "\n".join(code_lines)
            print(skills.learn_skill(skill_name, description, code))
            continue

        if lower.startswith("use skill "):
            skill_name = user_input[10:].strip()
            print(skills.use_skill(skill_name))
            continue

        if lower.startswith("forget skill "):
            print(skills.forget_skill(user_input[13:].strip()))
            continue

        # Preference commands
        if lower.startswith("set preference ") or lower.startswith("prefer "):
            text = user_input.split(" ", 2)[-1]
            if "=" in text:
                k, v = text.split("=", 1)
                print(memory.set_preference(k.strip(), v.strip()))
            elif " is " in text:
                k, v = text.split(" is ", 1)
                print(memory.set_preference(k.strip(), v.strip()))
            continue

        if lower in ("preferences", "my preferences", "show preferences"):
            print(memory.list_preferences())
            continue

        # Quick shortcuts
        if lower in ("check email", "check my email"):
            print("\n📧 Checking your inbox...\n")
            print(check_email())
            continue

        if lower.startswith("ls ") or lower == "ls":
            print(list_files(user_input[3:].strip() or "."))
            continue

        # ---- Everything else → Send to AI ----
        print("\n🤖 Working on it...\n")

        proxy_agent = AssistantAgent(
            name="Stacys_Proxy",
            model_client=local_llm,
            system_message=build_system_message(),
        )

        team = RoundRobinGroupChat([proxy_agent], max_turns=5)
        result = await Console(team.run_stream(task=user_input))

        # Log AI response
        with open(CONVERSATION_LOG, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] AI: {str(result)}\n")


if __name__ == "__main__":
    asyncio.run(main())

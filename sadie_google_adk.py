#!/usr/bin/env python3
"""
💜 SADIE — Google ADK Autonomous Agent
Builds Sadie's autonomous capabilities on top of the Google Agent Development Kit (ADK)
using Gemini as the LLM backbone.

Architecture:
  • All of Sadie's tools (files, terminal, web, memory, code, GitHub, comms, calendar)
    are exposed as plain Python functions — the ADK discovers and calls them in a loop.
  • Sadie's soul / personality prompt is injected as the Agent instruction so she stays
    herself while working autonomously.
  • An evaluation suite lives in tests/eval/ so quality can be measured and iterated.

Setup:
    pip install google-adk google-generativeai

Run interactively (ADK dev UI):
    adk web

Run a single goal from the CLI:
    python sadie_google_adk.py "Research the latest Python 3.13 features and summarise them"

Evaluate:
    adk eval tests/eval/evalsets/sadie.evalset.json --config tests/eval/eval_config.json
"""

from __future__ import annotations

import inspect
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# ── Google ADK ────────────────────────────────────────────────────────────────
try:
    from google.adk.agents import Agent
    from google.adk.models.lite_llm import LiteLlm
    _ADK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ADK_AVAILABLE = False

# ── Sadie core (memory + actions live here) ───────────────────────────────────
try:
    from sadie_core import SadieMemory, SadieActions, SADIE_SOUL, SADIE_CAPABILITIES
    _SADIE_CORE = True
except ImportError:  # running standalone without Sadie installed
    _SADIE_CORE = False
    SADIE_SOUL = "You are Sadie, a warm, witty, highly capable AI agent. 💜"
    SADIE_CAPABILITIES = ""

# ═════════════════════════════════════════════════════════════════════════════
# 🏗️  SHARED STATE — memory + actions singletons used by all tool functions
# ═════════════════════════════════════════════════════════════════════════════

_memory: Optional["SadieMemory"] = None
_actions: Optional["SadieActions"] = None


def _get_state():
    """Lazily initialise Sadie's memory and actions once."""
    global _memory, _actions
    if _memory is None and _SADIE_CORE:
        _memory = SadieMemory()
        _actions = SadieActions(_memory)
    return _memory, _actions


# ═════════════════════════════════════════════════════════════════════════════
# 🧰  TOOL FUNCTIONS — every function exposed to the ADK agent
# The docstring of each function is used by the ADK as the tool description.
# ═════════════════════════════════════════════════════════════════════════════

# ── Files & terminal ──────────────────────────────────────────────────────────

def read_file(path: str) -> str:
    """Read a text file from disk and return its full contents."""
    _, actions = _get_state()
    if actions:
        return actions.read_file(path)
    try:
        return Path(path).expanduser().read_text(errors="replace")
    except Exception as exc:
        return f"ERROR reading file: {exc}"


def write_file(path: str, content: str) -> str:
    """Create or overwrite a file with the given text content."""
    _, actions = _get_state()
    if actions:
        return actions.write_file(path, content)
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"✅ Written: {path}"
    except Exception as exc:
        return f"ERROR writing file: {exc}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace the first occurrence of old_text with new_text in a file."""
    _, actions = _get_state()
    if actions:
        return actions.edit_file(path, old_text, new_text)
    try:
        p = Path(path).expanduser()
        original = p.read_text()
        if old_text not in original:
            return f"ERROR: '{old_text[:60]}…' not found in {path}"
        p.write_text(original.replace(old_text, new_text, 1))
        return f"✅ Edited: {path}"
    except Exception as exc:
        return f"ERROR editing file: {exc}"


def list_files(path: str = ".") -> str:
    """List files and directories at the given path (defaults to current directory)."""
    _, actions = _get_state()
    if actions:
        return actions.list_files(path)
    try:
        entries = sorted(Path(path).expanduser().iterdir(), key=lambda e: (e.is_file(), e.name))
        lines = [f"{'📁' if e.is_dir() else '📄'} {e.name}" for e in entries]
        return "\n".join(lines) or "(empty directory)"
    except Exception as exc:
        return f"ERROR listing files: {exc}"


def run_command(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr output."""
    _, actions = _get_state()
    if actions:
        return actions.run_command(command)
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        out = result.stdout + result.stderr
        return out[:4000] if out else f"(exit code {result.returncode})"
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out after 60 s"
    except Exception as exc:
        return f"ERROR running command: {exc}"


def run_python(code: str) -> str:
    """Execute a Python code snippet and return its stdout/stderr output."""
    _, actions = _get_state()
    if actions:
        return actions.run_python(code)
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as fh:
            fh.write(code)
            tmp = fh.name
        result = subprocess.run(
            [sys.executable, tmp], capture_output=True, text=True, timeout=60
        )
        Path(tmp).unlink(missing_ok=True)
        return (result.stdout + result.stderr)[:4000] or f"(exit {result.returncode})"
    except Exception as exc:
        return f"ERROR: {exc}"


def pip_install(packages: str) -> str:
    """Install one or more Python packages (space- or comma-separated) via pip."""
    _, actions = _get_state()
    if actions:
        return actions.pip_install(packages)
    pkg_list = packages.replace(",", " ").split()
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", *pkg_list],
        capture_output=True, text=True, timeout=120,
    )
    return (result.stdout + result.stderr)[:2000]


# ── Web ───────────────────────────────────────────────────────────────────────

def web_search(query: str) -> str:
    """Search the web with DuckDuckGo and return the top result titles and links."""
    _, actions = _get_state()
    if actions:
        return actions.web_search(query)
    return f"(web_search unavailable — sadie_core not loaded) query: {query}"


def web_scrape(url: str, selector: str = "") -> str:
    """Fetch a URL and return its readable text content. Optional CSS selector to focus on a section."""
    _, actions = _get_state()
    if actions:
        return actions.web_scrape(url, selector or None)
    return f"(web_scrape unavailable — sadie_core not loaded) url: {url}"


def web_download(url: str, save_to: str = "") -> str:
    """Download a file from a URL to disk. save_to is optional; defaults to ~/.sadie/downloads/."""
    _, actions = _get_state()
    if actions:
        return actions.web_download(url, save_to or None)
    return f"(web_download unavailable) url: {url}"


def web_get_json(url: str, headers: str = "") -> str:
    """Call a JSON REST API and return the parsed response as a JSON string. headers is an optional JSON string."""
    _, actions = _get_state()
    parsed_headers = {}
    if headers:
        try:
            parsed_headers = json.loads(headers)
        except json.JSONDecodeError:
            pass
    if actions:
        return actions.web_get_json(url, parsed_headers or None)
    return f"(web_get_json unavailable) url: {url}"


# ── Memory ────────────────────────────────────────────────────────────────────

def remember(key: str, value: str) -> str:
    """Store a fact in Sadie's long-term memory so it persists across sessions."""
    memory, _ = _get_state()
    if memory:
        memory.remember(key, value)
        return f"💜 Remembered: {key} = {value}"
    return "(memory unavailable)"


def recall(key: str = "") -> str:
    """Retrieve a stored fact by key, or return all stored facts if key is omitted."""
    memory, _ = _get_state()
    if memory:
        result = memory.recall(key or None)
        return json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)
    return "(memory unavailable)"


def record_learning(topic: str, lesson: str) -> str:
    """Record a lesson learned so Sadie adapts and improves over time."""
    memory, _ = _get_state()
    if memory:
        memory.record_learning(topic, lesson)
        return f"🌱 Lesson recorded under '{topic}'"
    return "(memory unavailable)"


def update_identity(field: str, value: str) -> str:
    """Evolve Sadie's soul: set 'name' or 'essence', or add a new 'value'."""
    memory, _ = _get_state()
    if memory:
        return memory.update_identity(field, value)
    return "(memory unavailable)"


def list_skills() -> str:
    """List the custom skills Sadie has learned."""
    memory, _ = _get_state()
    if memory:
        skills = memory.list_skills()
        return json.dumps(skills, ensure_ascii=False) if skills else "No skills learned yet."
    return "(memory unavailable)"


def use_skill(name: str) -> str:
    """Run a previously learned custom skill by name."""
    memory, _ = _get_state()
    if memory:
        return memory.run_skill(name)
    return "(memory unavailable)"


# ── GitHub ────────────────────────────────────────────────────────────────────

def github_list_repos() -> str:
    """List the authenticated user's GitHub repositories."""
    _, actions = _get_state()
    if actions:
        return actions.github_list_repos()
    return "(GitHub unavailable)"


def github_create_repo(name: str, description: str = "", private: bool = False) -> str:
    """Create a new GitHub repository. private defaults to False (public)."""
    _, actions = _get_state()
    if actions:
        return actions.github_create_repo(name, description, private)
    return "(GitHub unavailable)"


def github_create_issue(owner: str, repo: str, title: str, body: str = "") -> str:
    """Open a new issue on a GitHub repository."""
    _, actions = _get_state()
    if actions:
        return actions.github_create_issue(owner, repo, title, body)
    return "(GitHub unavailable)"


def git_status(repo_path: str = ".") -> str:
    """Show the git status for a repository at the given path."""
    _, actions = _get_state()
    if actions:
        return actions.git_status(repo_path)
    return run_command(f"git -C {repo_path} status")


# ── Communication ─────────────────────────────────────────────────────────────

def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to the given address."""
    _, actions = _get_state()
    if actions:
        return actions.send_email(to, subject, body)
    return "(email unavailable)"


def send_text(name_or_number: str, message: str, carrier: str = "") -> str:
    """Send a text/SMS to a saved contact name or phone number. carrier required for new numbers."""
    _, actions = _get_state()
    if actions:
        return actions.send_text(name_or_number, message, carrier or None)
    return "(SMS unavailable)"


def discord_send(webhook_url: str, message: str) -> str:
    """Post a message to a Discord channel via webhook URL."""
    _, actions = _get_state()
    if actions:
        return actions.discord_send(webhook_url, message)
    return "(Discord unavailable)"


# ── Calendar & device ─────────────────────────────────────────────────────────

def get_calendar_events() -> str:
    """Retrieve upcoming calendar events from the device."""
    _, actions = _get_state()
    if actions:
        return actions.get_calendar_events()
    return "(calendar unavailable)"


def add_calendar_event(title: str, start_time: str, end_time: str = "") -> str:
    """Add an event to the device calendar. Times should be ISO 8601 or natural language."""
    _, actions = _get_state()
    if actions:
        return actions.add_calendar_event(title, start_time, end_time or None)
    return "(calendar unavailable)"


def system_info() -> str:
    """Return system/device information: OS, CPU, memory, disk."""
    _, actions = _get_state()
    if actions:
        return actions.system_info()
    return f"OS: {platform.system()} {platform.release()}, Python: {platform.python_version()}"


# ── Code & projects ───────────────────────────────────────────────────────────

def create_project(name: str, project_type: str = "python") -> str:
    """Scaffold a new project of the given type (python, web, node, etc.)."""
    _, actions = _get_state()
    if actions:
        return actions.create_project(name, project_type)
    return "(project scaffolding unavailable)"


# ═════════════════════════════════════════════════════════════════════════════
# 🤖  ADK AGENT DEFINITION
# ═════════════════════════════════════════════════════════════════════════════

_TOOLS = [
    # Files & terminal
    read_file, write_file, edit_file, list_files,
    run_command, run_python, pip_install,
    # Web
    web_search, web_scrape, web_download, web_get_json,
    # Memory & identity
    remember, recall, record_learning, update_identity,
    list_skills, use_skill,
    # GitHub
    github_list_repos, github_create_repo, github_create_issue, git_status,
    # Communication
    send_email, send_text, discord_send,
    # Calendar & device
    get_calendar_events, add_calendar_event, system_info,
    # Projects
    create_project,
]

_INSTRUCTION = f"""{SADIE_SOUL}

{SADIE_CAPABILITIES}

🤖 AUTONOMOUS MODE:
You are now operating as a fully autonomous agent. Use your tools step-by-step to
accomplish the user's goal. Think out loud briefly before each tool call. When the
goal is complete, summarise what you did and the outcome clearly.

Rules:
- Make real progress each step — do not repeat identical tool calls.
- Do not run destructive commands (rm -rf, disk format, DROP TABLE, etc.).
- Ask for permission the first time you do a brand-new kind of external action
  (sending email, posting to social media, etc.).
- Keep observations under 4 000 characters; truncate longer output.
"""

# The `root_agent` name is the ADK convention; `adk web` / `adk run` discover it.
if _ADK_AVAILABLE:
    root_agent = Agent(
        name="sadie_agent",
        model=LiteLlm(model="gemini/gemini-2.0-flash"),
        instruction=_INSTRUCTION,
        tools=_TOOLS,
    )
else:
    root_agent = None  # type: ignore[assignment]


# ═════════════════════════════════════════════════════════════════════════════
# 🚀  FALLBACK RUNNER — used when the ADK is not installed or for quick tests
# ═════════════════════════════════════════════════════════════════════════════

def run_with_gemini(goal: str, api_key: str | None = None) -> str:
    """
    Run the autonomous agent using the Gemini API directly (no ADK required).
    Implements a plan→act→observe loop compatible with the ADK tool schema.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return "❌ Install google-generativeai: pip install google-generativeai"

    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        return "❌ Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."

    genai.configure(api_key=key)

    # Build function declarations for every tool
    tool_map = {fn.__name__: fn for fn in _TOOLS}
    genai_tools = []
    for fn in _TOOLS:
        sig = inspect.signature(fn)
        props: dict = {}
        required: list = []
        for pname, param in sig.parameters.items():
            ann = param.annotation
            ptype = "string"
            if ann in (bool,):
                ptype = "boolean"
            elif ann in (int,):
                ptype = "integer"
            elif ann in (float,):
                ptype = "number"
            props[pname] = {"type": ptype, "description": f"Parameter: {pname}"}
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        genai_tools.append(
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name=fn.__name__,
                        description=(fn.__doc__ or "").strip(),
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={k: genai.protos.Schema(type=v["type"].upper()) for k, v in props.items()},
                            required=required,
                        ) if props else None,
                    )
                ]
            )
        )

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=_INSTRUCTION,
        tools=genai_tools,
        generation_config=genai.GenerationConfig(temperature=0.2),
    )
    chat = model.start_chat()

    print(f"\n💜 Sadie (ADK) — Goal: {goal}\n{'─' * 60}")
    max_steps = 20
    transcript: list[dict] = []

    response = chat.send_message(goal)

    for step in range(1, max_steps + 1):
        # Collect all function call parts in this response
        fn_calls = [
            p.function_call
            for candidate in response.candidates
            for p in candidate.content.parts
            if p.function_call.name
        ]

        if not fn_calls:
            # No tool calls — the model is done
            final = "".join(
                p.text
                for candidate in response.candidates
                for p in candidate.content.parts
                if hasattr(p, "text") and p.text
            )
            print(f"\n✅ Done in {step - 1} step(s).\n📋 Result:\n{final}")
            return final

        tool_responses = []
        for fn_call in fn_calls:
            name = fn_call.name
            args = dict(fn_call.args)
            print(f"\n🔧 [{step}] {name}({json.dumps(args, ensure_ascii=False)[:120]})")

            fn = tool_map.get(name)
            if fn is None:
                observation = f"ERROR: unknown tool '{name}'"
            else:
                try:
                    observation = fn(**args)
                    if not isinstance(observation, str):
                        observation = json.dumps(observation, ensure_ascii=False, default=str)
                except Exception as exc:
                    observation = f"ERROR: {exc}"

            if len(observation) > 4000:
                observation = observation[:4000] + "\n…(truncated)"

            print(f"   👀 {observation[:200]}{'…' if len(observation) > 200 else ''}")
            transcript.append({"step": step, "tool": name, "args": args, "observation": observation})

            tool_responses.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=name,
                        response={"result": observation},
                    )
                )
            )

        response = chat.send_message(tool_responses)

    return f"⚠️ Reached {max_steps}-step limit.\n" + "\n".join(
        f"{t['step']}. {t['tool']}: {str(t['observation'])[:80]}" for t in transcript
    )


# ═════════════════════════════════════════════════════════════════════════════
# 🏃  CLI ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python sadie_google_adk.py \"<goal>\"\n"
            "       adk web        — launch the ADK interactive UI\n"
            "       adk run sadie_google_adk -- \"<goal>\"  — ADK CLI runner\n"
        )
        sys.exit(1)

    goal = " ".join(sys.argv[1:])

    if _ADK_AVAILABLE and root_agent is not None:
        # Use the ADK runner when available
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        import asyncio

        async def _adk_run():
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="sadie", user_id="user", session_id="cli"
            )
            runner = Runner(agent=root_agent, app_name="sadie", session_service=session_service)
            from google.adk.types import Content, Part
            async for event in runner.run_async(
                user_id="user",
                session_id="cli",
                new_message=Content(role="user", parts=[Part(text=goal)]),
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    print(event.content.parts[0].text)

        asyncio.run(_adk_run())
    else:
        # Fall back to direct Gemini API runner
        run_with_gemini(goal)

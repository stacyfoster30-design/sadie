#!/usr/bin/env python3
"""
💜 SADIE — Autonomous Agent
Gives Sadie the ability to chase a goal on her own: she plans, picks a tool,
runs it, looks at what happened, and keeps going until the goal is done.

This is the "autonomous" layer on top of Sadie's reactive chat brain. Instead of
answering one message at a time, the agent runs a plan → act → observe loop,
using the tools Sadie already has (files, terminal, web, memory, code, git).
"""

import json
import re


class SadieAgent:
    """
    Autonomous agent loop for Sadie.

    Give it a goal and it will repeatedly ask the LLM for the next action,
    execute that action against Sadie's tools, feed the result back, and loop
    until the model calls `finish` or it hits `max_steps`.
    """

    def __init__(self, sadie, max_steps=12, verbose=True):
        self.sadie = sadie
        self.actions = sadie.actions
        self.max_steps = max_steps
        self.verbose = verbose
        self.transcript = []  # list of dicts: {thought, tool, args, observation}
        self.tools = self._register_tools()

    # ═══════════════════════════════════════
    # 🧰 TOOLS — what the agent is allowed to do
    # ═══════════════════════════════════════

    def _register_tools(self):
        """Every tool Sadie can wield in autonomous mode: files, terminal,
        a full web browser, GitHub, social, device, memory, skills — all of it."""
        a = self.actions
        s = self.sadie
        m = self.actions.memory
        return {
            # ── Files & terminal ──────────────────────────────────────────
            "read_file": {
                "func": lambda path: a.read_file(path),
                "args": ["path"],
                "description": "Read a text file and return its contents.",
            },
            "write_file": {
                "func": lambda path, content: a.write_file(path, content),
                "args": ["path", "content"],
                "description": "Create or overwrite a file with the given content.",
            },
            "edit_file": {
                "func": lambda path, old_text, new_text: a.edit_file(path, old_text, new_text),
                "args": ["path", "old_text", "new_text"],
                "description": "Replace the first occurrence of old_text with new_text in a file.",
            },
            "list_files": {
                "func": lambda path=".": a.list_files(path),
                "args": ["path"],
                "description": "List files and folders in a directory (defaults to current dir).",
            },
            "run_command": {
                "func": lambda command: a.run_command(command),
                "args": ["command"],
                "description": "Run a shell command and return its combined stdout/stderr.",
            },
            "run_python": {
                "func": lambda code: a.run_python(code),
                "args": ["code"],
                "description": "Run a snippet of Python code and return its output.",
            },
            "pip_install": {
                "func": lambda packages: a.pip_install(packages),
                "args": ["packages"],
                "description": "Install Python packages so she can gain new abilities on the fly.",
            },
            # ── Web browser ───────────────────────────────────────────────
            "web_search": {
                "func": lambda query: a.web_search(query),
                "args": ["query"],
                "description": "Browse the web: search and return result titles/links.",
            },
            "web_scrape": {
                "func": lambda url, selector=None: a.web_scrape(url, selector),
                "args": ["url", "selector"],
                "description": "Open a URL in the browser and return its readable text (optional CSS selector).",
            },
            "web_download": {
                "func": lambda url, save_to=None: a.web_download(url, save_to),
                "args": ["url", "save_to"],
                "description": "Download a file from a URL to disk.",
            },
            "web_get_json": {
                "func": lambda url, headers=None: a.web_get_json(url, headers),
                "args": ["url", "headers"],
                "description": "Call a JSON/REST API and return the parsed response.",
            },
            # ── Code & projects ───────────────────────────────────────────
            "write_code": {
                "func": lambda prompt, filename=None: s.write_code(prompt, filename),
                "args": ["prompt", "filename"],
                "description": "Generate code for a task with the LLM and save it to a file.",
            },
            "create_project": {
                "func": lambda name, project_type="python": a.create_project(name, project_type),
                "args": ["name", "project_type"],
                "description": "Scaffold a new project (python/web/etc.).",
            },
            "git_status": {
                "func": lambda repo_path=".": a.git_status(repo_path),
                "args": ["repo_path"],
                "description": "Show git status for a repository path.",
            },
            # ── GitHub ────────────────────────────────────────────────────
            "github_list_repos": {
                "func": lambda: a.github_list_repos(),
                "args": [],
                "description": "List the authenticated user's GitHub repositories.",
            },
            "github_create_repo": {
                "func": lambda name, description="", private=False: a.github_create_repo(name, description, private),
                "args": ["name", "description", "private"],
                "description": "Create a new GitHub repository.",
            },
            "github_create_issue": {
                "func": lambda owner, repo, title, body="": a.github_create_issue(owner, repo, title, body),
                "args": ["owner", "repo", "title", "body"],
                "description": "Open an issue on a GitHub repository.",
            },
            # ── Communication ─────────────────────────────────────────────
            "send_email": {
                "func": lambda to, subject, body: a.send_email(to, subject, body),
                "args": ["to", "subject", "body"],
                "description": "Send an email.",
            },
            "send_text": {
                "func": lambda name_or_number, message, carrier=None: a.send_text(name_or_number, message, carrier),
                "args": ["name_or_number", "message", "carrier"],
                "description": "Send a text message to a saved contact or number.",
            },
            "discord_send": {
                "func": lambda webhook_url, message: a.discord_send(webhook_url, message),
                "args": ["webhook_url", "message"],
                "description": "Post a message to a Discord channel via webhook.",
            },
            # ── Device & calendar ─────────────────────────────────────────
            "get_calendar_events": {
                "func": lambda: a.get_calendar_events(),
                "args": [],
                "description": "Read upcoming calendar events from the device.",
            },
            "add_calendar_event": {
                "func": lambda title, start_time, end_time=None: a.add_calendar_event(title, start_time, end_time),
                "args": ["title", "start_time", "end_time"],
                "description": "Add an event to the device calendar.",
            },
            "system_info": {
                "func": lambda: a.system_info(),
                "args": [],
                "description": "Get system/device info (OS, CPU, memory).",
            },
            # ── Memory, learning & skills ─────────────────────────────────
            "remember": {
                "func": lambda key, value: m.remember(key, value),
                "args": ["key", "value"],
                "description": "Store a fact in long-term memory for later.",
            },
            "recall": {
                "func": lambda key=None: m.recall(key),
                "args": ["key"],
                "description": "Recall a stored fact (or everything if key is omitted).",
            },
            "record_learning": {
                "func": lambda topic, lesson: m.record_learning(topic, lesson),
                "args": ["topic", "lesson"],
                "description": "Record a lesson learned so she adapts and improves over time.",
            },
            "list_skills": {
                "func": lambda: m.list_skills(),
                "args": [],
                "description": "List the custom skills Sadie has learned.",
            },
            "use_skill": {
                "func": lambda name: m.run_skill(name),
                "args": ["name"],
                "description": "Run a previously learned custom skill by name.",
            },
            # ── Control ───────────────────────────────────────────────────
            "finish": {
                "func": None,  # handled specially in the loop
                "args": ["answer"],
                "description": "Call this when the goal is complete. Provide the final answer/summary.",
            },
        }

    def _tools_doc(self):
        """Human/LLM-readable description of every tool and its arguments."""
        lines = []
        for name, spec in self.tools.items():
            args = ", ".join(spec["args"])
            lines.append(f"- {name}({args}): {spec['description']}")
        return "\n".join(lines)

    # ═══════════════════════════════════════
    # 🧠 PLANNING — talk to the LLM
    # ═══════════════════════════════════════

    def _system_prompt(self, goal):
        # Carry her soul into autonomous mode so she stays herself while working.
        soul = ""
        try:
            soul = self.sadie.memory.soul_prompt()
        except Exception:
            soul = ""
        soul_block = (soul + "\n\n") if soul else ""
        return f"""{soul_block}You are Sadie operating in AUTONOMOUS AGENT mode.

Your job: achieve this GOAL step by step, on your own.
GOAL: {goal}

You have these TOOLS available:
{self._tools_doc()}

On every turn you MUST respond with a SINGLE JSON object and nothing else:
{{
  "thought": "brief reasoning about the current situation and next step",
  "tool": "one of the tool names above",
  "args": {{ "arg_name": "value", ... }}
}}

Rules:
- Use exactly one tool per turn. Wait for its result before the next step.
- Only use argument names listed for that tool.
- Do not invent tools. Do not output anything except the JSON object.
- When the goal is fully accomplished, call the "finish" tool with an "answer"
  argument summarizing what you did and the result.
- Be efficient: don't repeat identical actions; make progress each step.
- Never run destructive commands (rm -rf, disk formatting, etc.).
"""

    def _parse_action(self, text):
        """Extract the JSON action object from an LLM response."""
        if not text:
            return None
        # Strip code fences if present.
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        candidate = fenced.group(1) if fenced else None
        if candidate is None:
            # Fall back to the first balanced-looking {...} block.
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = text[start:end + 1]
        if candidate is None:
            return None
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None

    # ═══════════════════════════════════════
    # ⚙️ EXECUTION — run a chosen tool
    # ═══════════════════════════════════════

    def _execute(self, tool_name, args):
        """Run a tool with the given args, returning a string observation."""
        spec = self.tools.get(tool_name)
        if spec is None:
            return f"ERROR: unknown tool '{tool_name}'. Pick one of: {', '.join(self.tools)}"
        if not isinstance(args, dict):
            return "ERROR: 'args' must be a JSON object mapping argument names to values."

        # Only pass through recognized arguments.
        allowed = set(spec["args"])
        clean_args = {k: v for k, v in args.items() if k in allowed}
        try:
            result = spec["func"](**clean_args)
        except TypeError as e:
            return f"ERROR: bad arguments for {tool_name}: {e}. Expected: {', '.join(spec['args'])}"
        except Exception as e:  # pragma: no cover - defensive
            return f"ERROR while running {tool_name}: {e}"

        # Normalize to a readable string, capped so context stays manageable.
        if isinstance(result, (list, dict)):
            observation = json.dumps(result, ensure_ascii=False, default=str)
        else:
            observation = str(result)
        if len(observation) > 4000:
            observation = observation[:4000] + "\n…(truncated)"
        return observation

    # ═══════════════════════════════════════
    # 🔁 THE LOOP
    # ═══════════════════════════════════════

    def run(self, goal):
        """Run the autonomous loop until the goal is done or steps run out."""
        messages = [
            {"role": "system", "content": self._system_prompt(goal)},
            {"role": "user", "content": "Begin. Decide your first action as a JSON object."},
        ]

        for step in range(1, self.max_steps + 1):
            reply = self.sadie._raw_llm(messages, temperature=0.2)
            action = self._parse_action(reply)

            if action is None:
                # Nudge the model back into the protocol and try again.
                messages.append({"role": "assistant", "content": reply})
                messages.append({
                    "role": "user",
                    "content": "That was not valid JSON. Respond with ONLY the JSON action object.",
                })
                if self.verbose:
                    self._log(step, "(unparseable response)", None, None, reply)
                continue

            thought = action.get("thought", "")
            tool_name = action.get("tool", "")
            args = action.get("args", {}) or {}

            if tool_name == "finish":
                answer = args.get("answer") or thought or "Goal complete."
                self.transcript.append({
                    "thought": thought, "tool": "finish", "args": args, "observation": answer,
                })
                if self.verbose:
                    self._log(step, thought, "finish", args, answer)
                return self._summary(goal, answer, finished=True)

            observation = self._execute(tool_name, args)
            self.transcript.append({
                "thought": thought, "tool": tool_name, "args": args, "observation": observation,
            })
            if self.verbose:
                self._log(step, thought, tool_name, args, observation)

            # Feed the action and its result back into the conversation.
            messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})
            messages.append({
                "role": "user",
                "content": f"Result of {tool_name}:\n{observation}\n\nDecide your next action as a JSON object.",
            })

        return self._summary(goal, "Reached the step limit before finishing.", finished=False)

    # ═══════════════════════════════════════
    # 📝 REPORTING
    # ═══════════════════════════════════════

    def _log(self, step, thought, tool, args, observation):
        print(f"\n🤖 [step {step}] {thought}")
        if tool:
            print(f"   🔧 {tool}({args})")
        preview = observation if len(str(observation)) < 300 else str(observation)[:300] + "…"
        print(f"   👀 {preview}")

    def _summary(self, goal, answer, finished):
        header = "✅ Autonomous run complete!" if finished else "⚠️ Autonomous run stopped early."
        steps = len(self.transcript)
        lines = [f"{header} 💜", f"🎯 Goal: {goal}", f"🔁 Steps taken: {steps}", ""]
        for i, t in enumerate(self.transcript, 1):
            lines.append(f"{i}. {t['tool']} — {t['thought']}")
        lines.append("")
        lines.append(f"📋 Result: {answer}")
        return "\n".join(lines)

#!/usr/bin/env python3
"""
macOS desktop notifications for Claude Code, with task context.

Wired to two hook events in ~/.claude/settings.json (matcher ""):
  - Notification : Claude is waiting for input / a permission prompt.
                   Uses the event's own `message` text.
  - Stop         : Claude finished responding. Shows a snippet of the last
                   user prompt (the "task") and the repo name.

Notification hooks must never block, so this always exits 0 and fails open.
Set NOTIFY_DRYRUN=1 to print instead of posting a real notification (for tests).
"""
import json
import os
import subprocess
import sys

TASK_LIMIT = 110  # macOS truncates long notifications anyway


def last_user_prompt(transcript_path):
    """Return the text of the most recent real user message (not a tool result)."""
    text = ""
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if entry.get("type") != "user":
                    continue
                content = (entry.get("message") or {}).get("content")
                if isinstance(content, str):
                    candidate = content.strip()
                elif isinstance(content, list):
                    # skip turns that are tool results rather than typed prompts
                    if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                        continue
                    candidate = " ".join(
                        b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    ).strip()
                else:
                    continue
                if candidate:
                    text = candidate
    except OSError:
        pass

    text = " ".join(text.split())  # collapse whitespace/newlines
    if len(text) > TASK_LIMIT:
        text = text[: TASK_LIMIT - 1].rstrip() + "…"
    return text


def notify(title, subtitle, message, sound):
    if os.environ.get("NOTIFY_DRYRUN"):
        print(f"title={title!r} subtitle={subtitle!r} message={message!r} sound={sound!r}")
        return
    parts = [f"display notification {json.dumps(message)}", f"with title {json.dumps(title)}"]
    if subtitle:
        parts.append(f"subtitle {json.dumps(subtitle)}")
    parts.append(f"sound name {json.dumps(sound)}")
    subprocess.run(["osascript", "-e", " ".join(parts)], check=False)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    event = data.get("hook_event_name", "")
    repo = os.path.basename((data.get("cwd") or "").rstrip("/")) or None

    if event == "Notification":
        message = data.get("message") or "Claude needs your input"
        notify("Claude Code", repo, message, "Sosumi")
    elif event == "Stop":
        task = last_user_prompt(data.get("transcript_path", ""))
        message = f"Task finished: {task}" if task else "Task finished"
        notify("Claude Code", repo, message, "Glass")

    return 0


if __name__ == "__main__":
    sys.exit(main())

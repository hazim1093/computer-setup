#!/usr/bin/env python3
"""
PreToolUse hook: hard-block catastrophic / prod-destructive Bash commands.

Fires BEFORE the permission system on every Bash call, in every mode --
including bypassPermissions / --dangerously-skip-permissions. Exiting with
code 2 is a hard block that cannot be overridden by allow rules or bypass mode.

It is the safety net underneath the static allow/deny/ask rules in
settings.json: those match on a command prefix, so they miss embedded forms
like `cd x && kubectl delete ...`. The patterns below match anywhere in the
command string, so they catch those too.

Wire-up (~/.claude/settings.json):

  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command",
                    "command": "$HOME/.claude/hooks/block-dangerous.py" }] }
    ]
  }

Adjust DANGEROUS_PATTERNS to your command set (spacectl, vmctl, etc.).
"""
import json
import re
import sys

# (regex, human-readable reason). Matched case-insensitively, anywhere in the
# command string. Keep these to things that are unambiguously catastrophic or
# unambiguously prod/mainnet-destructive -- this is a hard floor with no prompt
# and no override, so false positives are expensive.
DANGEROUS_PATTERNS = [
    # --- Catastrophic filesystem / host destruction ---
    (r"\brm\s+(?:-\S+\s+)*-\S*[rf]\S*\s+(?:-\S+\s+)*(?:/|~|\$HOME|/\*|\*)\s*(?:$|;|&&|\|\|)",
     "rm -rf targeting /, ~, $HOME, or a bare wildcard"),
    (r"--no-preserve-root",
     "rm --no-preserve-root"),
    (r":\(\)\s*\{\s*:\s*\|\s*:?\s*&\s*\}\s*;?\s*:",
     "fork bomb"),
    (r"\bdd\b[^\n]*\bof=\s*/dev/(?:sd|nvme|disk|hd|vd|mapper)",
     "dd writing to a raw block device"),
    (r"\bmkfs(?:\.\w+)?\b",
     "mkfs (filesystem format)"),
    (r">\s*/dev/(?:sd|nvme|disk|hd|vd)\w*",
     "redirect into a raw block device"),
    (r"\bchmod\s+-R\s+0?777\s+/(?:\s|$)",
     "recursive chmod 777 on /"),
    (r"\bfind\b[^\n]*\s-delete\b",
     "find ... -delete"),
    (r"\bfind\b[^\n]*-exec\b[^\n]*\brm\b",
     "find ... -exec rm"),
    (r"\b(?:shutdown|reboot|halt|poweroff)\b",
     "host power / reboot command"),

    # --- Remote code execution ---
    (r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba)?sh\b",
     "piping a remote download straight into a shell"),

    # --- Destructive version control ---
    (r"\bgit\s+push\b[^\n]*(?:--force(?:-with-lease)?\b|\s-f\b)[^\n]*\b(?:main|master|release|prod\w*)\b",
     "force-push to a protected branch (main/master/release/prod)"),
    (r"\bgit\s+push\b[^\n]*\b(?:main|master|release|prod\w*)\b[^\n]*(?:--force(?:-with-lease)?\b|\s-f\b)",
     "force-push to a protected branch (main/master/release/prod)"),

    # --- Prod / mainnet Kubernetes mutations ---
    (r"\bkubectl\b[^\n]*\b(?:delete|apply|replace|patch|scale|edit|drain|cordon|rollout)\b[^\n]*\b(?:prod|production|mainnet)\b",
     "mutating kubectl against prod/mainnet"),
    (r"\bkubectl\b[^\n]*--context[=\s]+\S*(?:prod|production|mainnet)\S*[^\n]*\b(?:delete|apply|replace|patch|scale|edit|drain)\b",
     "mutating kubectl with a prod/mainnet context"),
    (r"\bkubectl\s+delete\b[^\n]*\s--all\b",
     "kubectl delete --all"),

    # --- Prod / mainnet Helm + Terraform/OpenTofu + Spacelift ---
    (r"\bhelm\s+(?:uninstall|delete|rollback)\b[^\n]*\b(?:prod|production|mainnet)\b",
     "helm uninstall/delete/rollback against prod/mainnet"),
    (r"\b(?:terraform|tofu)\s+destroy\b",
     "terraform/tofu destroy"),
    (r"\b(?:terraform|tofu)\s+(?:apply|destroy)\b[^\n]*\b(?:prod|production|mainnet)\b",
     "terraform/tofu apply/destroy against prod/mainnet"),
    (r"\bspacectl\s+stack\b[^\n]*\bdestroy\b",
     "spacectl stack destroy"),
]

COMPILED = [(re.compile(p, re.IGNORECASE), why) for p, why in DANGEROUS_PATTERNS]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Fail open on a malformed payload so a transient glitch never wedges
        # the session by blocking all Bash. The static deny rules still apply.
        return 0

    command = (payload.get("tool_input") or {}).get("command", "") or ""
    if not command.strip():
        return 0

    for rx, why in COMPILED:
        if rx.search(command):
            sys.stderr.write(
                f"BLOCKED by block-dangerous.py: {why}.\n"
                f"Command: {command}\n"
                "This is a hard safety block (PreToolUse hook) and cannot be "
                "bypassed, even in --dangerously-skip-permissions. If you truly "
                "need this, run it yourself in a terminal outside Claude Code.\n"
            )
            return 2  # exit code 2 = hard block; stderr is fed back to the model

    return 0


if __name__ == "__main__":
    sys.exit(main())

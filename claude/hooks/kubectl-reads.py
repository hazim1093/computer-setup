#!/usr/bin/env python3
"""
PreToolUse (Bash) hook: auto-approve READ-ONLY kubectl commands.

Prefix allow-rules (`Bash(kubectl get:*)`) only match when the subcommand comes
first, so `kubectl --context X -n Y get ...` (flags before the verb) prompts.
They also can't match an unexpanded `$ctx`. This hook fixes both by inspecting
the raw command and approving on the *verb*, in any flag position.

SAFETY: it emits permissionDecision "allow" ONLY when EVERY segment of the
command is provably read-only:
  - a kubectl invocation whose subcommand is a read verb (get/logs/describe/...),
  - a read-only pipe tool (grep/rg/tail/head/cat/jq/yq/wc/sort/...),
  - echo / cd / true, or a plain VAR=value assignment.
Any write/unknown verb, command substitution ($(...) / backticks), a file
redirect, or an unrecognized command -> it stays SILENT (exit 0), so the normal
permission flow prompts as usual. It never approves a write, and it never
overrides block-dangerous.py (a deny always wins over an allow).
"""
import json
import re
import shlex
import sys

KUBECTL_READ_VERBS = {
    "get", "logs", "describe", "top", "explain", "api-resources",
    "api-versions", "cluster-info", "version", "events", "diff", "wait",
}
# Full verb set is used only to locate the subcommand reliably (so a read-looking
# token appearing after a write verb, e.g. `exec ... -- get`, isn't mistaken for
# the subcommand). Anything not resolving to a read verb -> not approved.
KUBECTL_WRITE_VERBS = {
    "create", "apply", "delete", "patch", "replace", "edit", "scale",
    "autoscale", "expose", "run", "set", "label", "annotate", "taint",
    "drain", "cordon", "uncordon", "exec", "attach", "cp", "port-forward",
    "proxy", "debug", "kustomize", "certificate", "plugin", "apiresources",
}
KUBECTL_SPECIAL = {"config", "auth", "rollout"}
KUBECTL_ALL = KUBECTL_READ_VERBS | KUBECTL_WRITE_VERBS | KUBECTL_SPECIAL

SAFE_TOOLS = {
    "grep", "egrep", "fgrep", "rg", "tail", "head", "cat", "jq", "yq", "wc",
    "sort", "uniq", "cut", "column", "less", "echo", "cd", "tr", "nl", "true",
    "dirname", "basename", "date", "printf",
}

SAFE_REDIRECTS = ["2>&1", "2>/dev/null", ">/dev/null", "&>/dev/null",
                  "1>/dev/null", ">&2", "1>&2", "2>&-"]


def kubectl_subcommand(tokens):
    """Return the resolved read verb for a kubectl token list, or None."""
    i = 1  # skip 'kubectl'
    verb = None
    while i < len(tokens):
        t = tokens[i]
        if t == "--":
            break
        if t.startswith("-"):
            i += 1
            continue
        if t in KUBECTL_ALL:
            verb = t
            break
        i += 1  # flag value or resource that isn't a verb
    if verb is None:
        return None
    rest = tokens[i + 1:]
    nxt = next((x for x in rest if not x.startswith("-")), None)
    if verb in KUBECTL_READ_VERBS:
        return verb
    if verb == "config" and nxt in {"view", "get-contexts", "current-context", "current-namespace"}:
        return "config " + nxt
    if verb == "auth" and nxt == "can-i":
        return "auth can-i"
    if verb == "rollout" and nxt == "status":
        return "rollout status"
    return None  # write verb


def segment_is_safe(tokens):
    """(is_safe, is_kubectl_read) for one command segment's token list."""
    if not tokens:
        return True, False
    first = tokens[0]
    base = first.split("/")[-1]
    if base == "kubectl" or base.startswith("kubectl"):
        return (kubectl_subcommand(tokens) is not None), True
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", first):  # VAR=value assignment
        return True, False
    if base in SAFE_TOOLS:
        return True, False
    return False, False


def all_read_only(command):
    if "$(" in command or "`" in command:
        return False  # command substitution -> unsafe
    stripped = command
    for r in SAFE_REDIRECTS:
        stripped = stripped.replace(r, "")
    if ">" in stripped or "<" in stripped:
        return False  # real file redirect -> let normal flow handle it

    has_kubectl_read = False
    OPS = {"|", "||", "&&", ";", "&", "|&"}
    for line in command.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            lex = shlex.shlex(line, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            toks = list(lex)
        except ValueError:
            return False  # unparseable -> don't approve
        seg = []
        for t in toks:
            if t in OPS:
                ok, kr = segment_is_safe(seg)
                if not ok:
                    return False
                has_kubectl_read = has_kubectl_read or kr
                seg = []
            elif set(t) <= {">", "<", "&"}:  # stray redirect punctuation token
                continue
            else:
                seg.append(t)
        ok, kr = segment_is_safe(seg)
        if not ok:
            return False
        has_kubectl_read = has_kubectl_read or kr
    return has_kubectl_read


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    command = (data.get("tool_input") or {}).get("command", "") or ""
    if "kubectl" not in command:
        return 0  # nothing for us to approve; leave to normal flow
    try:
        if all_read_only(command):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": "read-only kubectl (verb + all pipe stages are read-only)",
                }
            }))
    except Exception:
        return 0  # never let a bug turn into a wrong decision
    return 0


if __name__ == "__main__":
    sys.exit(main())

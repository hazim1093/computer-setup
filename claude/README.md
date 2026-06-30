# Claude Code config

Curated, **non-secret** Claude Code config — the rest of `~/.claude`
(transcripts, credentials, caches, session state) is deliberately *not* stored
here and must never be.

| File | What it is |
|------|------------|
| `settings.json` | Global `~/.claude/settings.json`: permission allow/deny/ask rules + dangerous-command hook wiring + enabled plugins/prefs |
| `hooks/block-dangerous.py` | `PreToolUse` hook that hard-blocks catastrophic / prod-destructive Bash commands (runs in every mode, even bypass) |

## Install

```sh
./link.sh
```

Symlinks these files into `~/.claude`. Safe to re-run: it backs up any real
file it replaces, and if Claude ever replaced a symlink with a real file
(atomic write), it copies that newer content back into this repo *before*
re-linking — so re-running never serves a stale config.

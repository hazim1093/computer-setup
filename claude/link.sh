#!/usr/bin/env bash
#
# Deploy this repo's Claude Code config into ~/.claude via symlinks.
#
# Why this script is "absorb-then-link" instead of a plain `ln -sf`:
#   Claude rewrites settings.json (theme, accepted-dialog flags, fast mode...).
#     - An in-place write goes straight through the symlink, so the repo copy
#       updates automatically and never goes stale.
#     - An ATOMIC write (write-temp + rename) REPLACES the symlink with a fresh
#       real file in ~/.claude. If we then naively re-linked, we'd point back at
#       the stale repo copy and lose what Claude just wrote.
#   So before linking, if we find a real file where a symlink should be, we copy
#   its content BACK into the repo first. Re-running is therefore always safe:
#   the repo ends up current and you just review + commit the diff.
#
# Safe to re-run any time. Real files are always backed up before replacement.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE="$HOME/.claude"

deploy() {
  local rel="$1"
  local src="$REPO/$rel"
  local dst="$CLAUDE/$rel"
  mkdir -p "$(dirname "$dst")"

  if [ -L "$dst" ]; then
    ln -sf "$src" "$dst"            # already a symlink: re-point at the repo
    echo "ok      $dst"
    return
  fi

  if [ -e "$dst" ]; then            # real file: clobbered link, or first run
    if ! cmp -s "$dst" "$src"; then
      cp "$dst" "$src"             # absorb newer live content into the repo
      echo "absorb  $dst -> repo  (review & commit the diff)"
    fi
    local bak="$dst.bak.$(date +%Y%m%d%H%M%S)"
    mv "$dst" "$bak"
    echo "backup  $bak"
  fi

  ln -sf "$src" "$dst"
  echo "link    $dst -> $src"
}

deploy "settings.json"
deploy "hooks/block-dangerous.py"
deploy "hooks/notify.py"
deploy "hooks/kubectl-reads.py"
chmod +x "$REPO/hooks/block-dangerous.py" "$REPO/hooks/notify.py" "$REPO/hooks/kubectl-reads.py"
echo "done."

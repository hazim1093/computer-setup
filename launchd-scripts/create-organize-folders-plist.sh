#!/bin/bash

PLIST_PATH="$HOME/Library/LaunchAgents/com.hazim1093.OrganizeFolders.plist"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PARENT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
ORGANIZE_CMD="organize run --config-file ${PARENT_DIR}/organize.yaml"

WATCH_PATHS=(
    "<string>$HOME/Downloads</string>"
)

# Create or modify the plist file
cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hazim1093.OrganizeFolders</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/.pyenv/shims/organize</string>
        <string>run</string>
        <string>${PARENT_DIR}/organize.yaml</string>
    </array>
    <key>WatchPaths</key>
    <array>
        ${WATCH_PATHS[@]}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

# To enable logging in the plist add:
# <key>StandardOutPath</key>
# <string>/tmp/organize-folders.log</string>
# <key>StandardErrorPath</key>
# <string>/tmp/organize-folders.err</string>

# Lint plist
plutil -lint $PLIST_PATH

# Unload if already loaded
launchctl unload "$PLIST_PATH" 2>/dev/null
# Load the plist
launchctl load "$PLIST_PATH"

echo "Plist created and loaded: $PLIST_PATH"

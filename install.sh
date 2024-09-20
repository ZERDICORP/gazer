#!/bin/bash

cat <<"EOF"
   _____                      _____           _        _ _
  / ____|                    |_   _|         | |      | | |
 | |  __  __ _ _______ _ __    | |  _ __  ___| |_ __ _| | |
 | | |_ |/ _` |_  / _ \ '__|   | | | '_ \/ __| __/ _` | | |
 | |__| | (_| |/ /  __/ |     _| |_| | | \__ \ || (_| | | |
  \_____|\__,_/___\___|_|    |_____|_| |_|___/\__\__,_|_|_|

EOF

if [[ $EUID -ne 0 ]]; then
  echo "Error :("
  echo "This script must be run as root"
  exit 1
fi

GITHUB_URL="https://github.com/ZERDICORP/gazer/releases/latest/download/gazer"
DEST_PATH="/usr/local/bin/gazer"

wget "$GITHUB_URL" -O "$DEST_PATH" -q
chmod +x "$DEST_PATH"

echo "Success!"
echo "Executable can be found in '$DEST_PATH'"

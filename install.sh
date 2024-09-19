#!/bin/bash

GITHUB_URL="https://github.com/username/repository/raw/master/gaze"
FILE_NAME="gaze"
DEST_DIR="/usr/local/bin"
DEST_PATH="$DEST_DIR/$FILE_NAME"

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root"
  exit 1
fi

echo "Downloading gazer..."
curl -L "$GITHUB_URL" -o "$FILE_NAME"

if [[ $? -ne 0 ]]; then
  echo "Error downloading file."
  exit 1
fi

echo "Moving file to $DEST_DIR..."
mv "$FILE_NAME" "$DEST_PATH"

if [[ $? -ne 0 ]]; then
  echo "Error moving file."
  exit 1
fi

echo "Making the file executable..."
chmod +x "$DEST_PATH"

if [[ $? -eq 0 ]]; then
  echo "File successfully downloaded, moved to $DEST_DIR, and made executable!"
else
  echo "Error setting executable permission."
  exit 1
fi

#!/bin/sh
set -e

# Copy default extensions if they don't exist in the mounted volume
if [ -d /app/default_extensions ]; then
    echo "============================================="
    echo "Syncing default extensions to extensions volume..."
    echo "============================================="
    mkdir -p /app/extensions
    for f in /app/default_extensions/*; do
        filename=$(basename "$f")
        if [ ! -f "/app/extensions/$filename" ]; then
            echo "Provisioning default extension: $filename"
            cp "$f" "/app/extensions/"
        fi
    done
fi

# Check if a custom requirements.txt file exists inside the mounted extensions directory
if [ -f /app/extensions/requirements.txt ]; then
    echo "============================================="
    echo "Custom requirements found in extensions/ directory."
    echo "Installing custom extension dependencies..."
    echo "============================================="
    pip install --no-cache-dir -r /app/extensions/requirements.txt
fi

# Start the uvicorn server
exec uvicorn src.main:app --host 0.0.0.0 --port 8000

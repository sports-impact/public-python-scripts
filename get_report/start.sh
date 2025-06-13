#!/bin/bash

set -e

SCRIPT_PATH="./get_report.py"
EXECUTABLE_NAME="get_report"

echo "🚧 Cleaning previous build..."
rm -rf build dist "$EXECUTABLE_NAME".spec

echo "📦 Building macOS executable with PyInstaller..."
pyinstaller -F "$SCRIPT_PATH"

echo "✅ Build complete."

echo "🚀 Running the executable..."
./dist/"$EXECUTABLE_NAME"
`

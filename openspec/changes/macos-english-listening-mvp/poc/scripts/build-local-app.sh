#!/usr/bin/env bash

set -euo pipefail

POC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK_PATH="${SDKROOT:-/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk}"
APP_ROOT="$POC_ROOT/.build/local-app/磨耳朵 POC.app"
CONTENTS="$APP_ROOT/Contents"
EXECUTABLE="$POC_ROOT/.build/release/morerduo-app-poc"

cd "$POC_ROOT"
SDKROOT="$SDK_PATH" swift build -c release --product morerduo-app-poc

mkdir -p "$CONTENTS/MacOS"
cp "$POC_ROOT/AppResources/Info.plist" "$CONTENTS/Info.plist"
cp "$EXECUTABLE" "$CONTENTS/MacOS/morerduo-app-poc"
chmod 755 "$CONTENTS/MacOS/morerduo-app-poc"

plutil -lint "$CONTENTS/Info.plist"
codesign --force --sign - --timestamp=none "$APP_ROOT"
codesign --verify --deep --strict --verbose=2 "$APP_ROOT"

echo "$APP_ROOT"

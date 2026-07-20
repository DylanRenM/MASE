#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXECUTABLE="$ROOT_DIR/.build/release/MorerduoApp"
OUTPUT="$ROOT_DIR/dist/磨耳朵.app"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --executable)
            EXECUTABLE="${2:-}"
            shift 2
            ;;
        --output)
            OUTPUT="${2:-}"
            shift 2
            ;;
        *)
            echo "unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if [[ ! -x "$EXECUTABLE" ]]; then
    echo "executable not found or not executable: $EXECUTABLE" >&2
    exit 2
fi

INFO_PLIST="$ROOT_DIR/resources/Info.plist"
if [[ ! -f "$INFO_PLIST" ]]; then
    echo "Info.plist not found: $INFO_PLIST" >&2
    exit 2
fi

STAGING_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/morerduo-app.XXXXXX")"
trap 'rm -rf "$STAGING_ROOT"' EXIT
STAGING_APP="$STAGING_ROOT/磨耳朵.app"

mkdir -p "$STAGING_APP/Contents/MacOS" "$STAGING_APP/Contents/Resources"
install -m 755 "$EXECUTABLE" "$STAGING_APP/Contents/MacOS/MorerduoApp"
install -m 644 "$INFO_PLIST" "$STAGING_APP/Contents/Info.plist"

/usr/bin/plutil -lint "$STAGING_APP/Contents/Info.plist" >/dev/null
/usr/bin/codesign --force --deep --sign - "$STAGING_APP" >/dev/null
/usr/bin/codesign --verify --deep --strict "$STAGING_APP"

mkdir -p "$(dirname "$OUTPUT")"
rm -rf "$OUTPUT"
mv "$STAGING_APP" "$OUTPUT"

echo "built: $OUTPUT"

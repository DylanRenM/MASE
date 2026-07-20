#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-root)
            ROOT_DIR="${2:-}"
            shift 2
            ;;
        *)
            echo "unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if [[ ! -f "$ROOT_DIR/Package.swift" ]]; then
    echo "Package.swift not found: $ROOT_DIR" >&2
    exit 2
fi

cd "$ROOT_DIR"

export DEVELOPER_DIR="${DEVELOPER_DIR:-$(xcode-select -p)}"
export SDKROOT="${SDKROOT:-$(xcrun --sdk macosx --show-sdk-path)}"
export CLANG_MODULE_CACHE_PATH="$ROOT_DIR/.build/clang-module-cache"
export SWIFTPM_MODULECACHE_OVERRIDE="$ROOT_DIR/.build/swiftpm-module-cache"

CACHE_ARGS=()
POC_CACHE="$ROOT_DIR/openspec/changes/macos-english-listening-mvp/poc/.build"
if [[ -d "$POC_CACHE/repositories" ]]; then
    CACHE_ARGS=(--cache-path "$POC_CACHE")
fi

echo "[1/6] build test runners"
swift build --disable-sandbox "${CACHE_ARGS[@]}"

echo "[2/6] unit tests"
"$ROOT_DIR/.build/debug/MorerduoUnitTests"

echo "[3/6] integration and contract tests"
"$ROOT_DIR/.build/debug/MorerduoIntegrationTests"
"$ROOT_DIR/.build/debug/MorerduoContractTests"

echo "[4/6] release build"
swift build --disable-sandbox "${CACHE_ARGS[@]}" -c release --product MorerduoApp

echo "[5/6] app bundle and ad-hoc signature"
"$ROOT_DIR/scripts/build-morerduo-app.sh"
/usr/bin/plutil -lint "$ROOT_DIR/dist/磨耳朵.app/Contents/Info.plist" >/dev/null
/usr/bin/codesign --verify --deep --strict "$ROOT_DIR/dist/磨耳朵.app"

echo "[6/6] E2E runner"
"$ROOT_DIR/.build/debug/MorerduoE2ERunner"

echo "Morerduo verification passed"

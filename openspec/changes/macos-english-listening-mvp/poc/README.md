# Design L1 POC

Run from this directory:

```bash
SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk swift run morerduo-poc
```

The explicit SDK is a temporary workaround for this machine: the active Command Line Tools compiler patch does not match the installed default macOS 26.5 SDK. After installing a matching full Xcode toolchain, the expected command is simply `swift run morerduo-poc`.

The executable verifies:

1. SwiftUI compilation and native layout on macOS 13+;
2. English audio-buffer synthesis, progress ranges, and distinguishable rates through `AVSpeechSynthesizer`;
3. text extraction from a generated text PDF with PDFKit;
4. DOCX ZIP extraction with ZIPFoundation and text extraction with `XMLParser`;
5. strict English filtering against a 20MB-class fixture;
6. local source-file append and atomic-replacement detection within five seconds.

The POC creates all fixtures under the process temporary directory and removes them on exit.

Run the manual speaker-output check separately:

```bash
SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk swift run morerduo-poc --audible
```

This mode uses `AVSpeechSynthesizer.speak(...)` rather than the silent buffer API and must be confirmed by a person listening to the Mac speakers.

## Local app bundle

Build and ad-hoc sign a standard local `.app` without full Xcode:

```bash
./scripts/build-local-app.sh
```

The output is `.build/local-app/磨耳朵 POC.app`. The script validates the plist and runs strict codesign verification.

Run the Accessibility UI flow:

```bash
open -n '.build/local-app/磨耳朵 POC.app'
osascript scripts/verify-accessibility.applescript
```

The terminal or automation host must be enabled under macOS Privacy & Security → Accessibility. The script locates controls by stable `AXIdentifier` values rather than screen coordinates.

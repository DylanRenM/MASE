# macOS Accessibility E2E adapter

- Use stable `AXIdentifier` values owned by the application.
- Prefer role/identifier over window coordinates or localized visible text.
- Probe Accessibility permission before running and report an actionable skip/failure.
- Launch a clean app instance, isolate fixture files and terminate the app after each spec group.
- Treat audible TTS as an explicit smoke test; silent automation proves callbacks/state but not speaker output.
- Test pause/resume/stop, disabled controls and dialogs through the native accessibility tree.

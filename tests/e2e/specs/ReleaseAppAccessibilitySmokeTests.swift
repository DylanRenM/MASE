import Foundation
import MorerduoKit
import Testing

@Suite("Release app Accessibility smoke", .serialized)
struct ReleaseAppAccessibilitySmokeTests {
  @Test("[P0] signed app first launch exposes idle controls")
  func firstLaunchIdleControls() async throws {
    let executable = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .appending(path: "dist/磨耳朵.app/Contents/MacOS/MorerduoApp")
    #expect(FileManager.default.isExecutableFile(atPath: executable.path))
    let process = Process()
    process.executableURL = executable
    process.environment = ["LANG": "zh_CN.UTF-8"]
    try process.run()
    defer {
      if process.isRunning { process.terminate() }
      process.waitUntilExit()
    }

    let page = try MorerduoPage(applicationPID: process.processIdentifier)
    try await page.waitForElement(
      identifier: AppAccessibilityIdentifiers.appTitle
    )

    #expect(
      try page.value(identifier: AppAccessibilityIdentifiers.sessionStatus)
        == "等待选择文件"
    )
    #expect(try page.isEnabled(identifier: AppAccessibilityIdentifiers.filePickerButton))
    #expect(try !page.isEnabled(identifier: AppAccessibilityIdentifiers.playPauseButton))
    #expect(try !page.isEnabled(identifier: AppAccessibilityIdentifiers.stopButton))
    #expect(try page.isEnabled(identifier: AppAccessibilityIdentifiers.speedPicker))
    #expect(try page.isEnabled(identifier: AppAccessibilityIdentifiers.timerMinutesField))
  }
}

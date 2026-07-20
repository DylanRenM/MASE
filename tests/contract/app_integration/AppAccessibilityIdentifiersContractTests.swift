import MorerduoKit
import Testing

@Suite("App Accessibility identifier contract")
struct AppAccessibilityIdentifiersContractTests {
  @Test("all interactive and status identifiers are stable and unique")
  func identifiersAreStableAndUnique() {
    #expect(AppAccessibilityIdentifiers.appTitle == "appTitle")
    #expect(AppAccessibilityIdentifiers.filePickerButton == "filePickerButton")
    #expect(AppAccessibilityIdentifiers.playPauseButton == "playPauseButton")
    #expect(AppAccessibilityIdentifiers.stopButton == "stopButton")
    #expect(AppAccessibilityIdentifiers.speedPicker == "speedPicker")
    #expect(AppAccessibilityIdentifiers.timerMinutesField == "timerMinutesField")
    #expect(AppAccessibilityIdentifiers.reloadSourceDialog == "reloadSourceDialog")
    #expect(
      Set(AppAccessibilityIdentifiers.all).count
        == AppAccessibilityIdentifiers.all.count
    )
    #expect(AppAccessibilityIdentifiers.all.allSatisfy { !$0.isEmpty })
  }
}

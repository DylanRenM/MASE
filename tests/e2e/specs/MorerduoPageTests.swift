import Testing

@Suite("Morerduo Accessibility page")
struct MorerduoPageTests {
  @Test("finds a nested element by AXIdentifier")
  func findsNestedElementByIdentifier() throws {
    let playButton = FixtureAccessibilityElement(identifier: "playPauseButton")
    let root = FixtureAccessibilityElement(
      children: [
        FixtureAccessibilityElement(
          children: [playButton]
        )
      ]
    )
    let page = try MorerduoPage(root: root, isProcessTrusted: { true })

    let element = try page.element(identifier: "playPauseButton")

    #expect(try element.identifier() == "playPauseButton")
  }

  @Test("reports a missing AXIdentifier")
  func reportsMissingIdentifier() throws {
    let page = try MorerduoPage(
      root: FixtureAccessibilityElement(),
      isProcessTrusted: { true }
    )

    #expect(throws: MorerduoPageError.elementNotFound("stopButton")) {
      try page.element(identifier: "stopButton")
    }
  }

  @Test("fails fast when Accessibility permission is missing")
  func failsWithoutAccessibilityPermission() {
    #expect(throws: MorerduoPageError.permissionDenied) {
      try MorerduoPage(
        root: FixtureAccessibilityElement(),
        isProcessTrusted: { false }
      )
    }
  }

  @Test("reads enabled value and invokes press through the page object")
  func readsAndPressesElement() throws {
    let button = FixtureAccessibilityElement(
      identifier: "playPauseButton",
      enabled: false,
      value: "播放"
    )
    let page = try MorerduoPage(root: button, isProcessTrusted: { true })

    #expect(try !page.isEnabled(identifier: "playPauseButton"))
    #expect(try page.value(identifier: "playPauseButton") == "播放")
    try page.press(identifier: "playPauseButton")
    #expect(button.pressCount == 1)
  }
}

private final class FixtureAccessibilityElement: AccessibilityElementReading {
  let storedIdentifier: String?
  let storedChildren: [any AccessibilityElementReading]
  let storedEnabled: Bool
  let storedValue: String?
  private(set) var pressCount = 0

  init(
    identifier: String? = nil,
    children: [any AccessibilityElementReading] = [],
    enabled: Bool = true,
    value: String? = nil
  ) {
    storedIdentifier = identifier
    storedChildren = children
    storedEnabled = enabled
    storedValue = value
  }

  func identifier() throws -> String? {
    storedIdentifier
  }

  func children() throws -> [any AccessibilityElementReading] {
    storedChildren
  }

  func isEnabled() throws -> Bool {
    storedEnabled
  }

  func stringValue() throws -> String? {
    storedValue
  }

  func press() throws {
    pressCount += 1
  }
}

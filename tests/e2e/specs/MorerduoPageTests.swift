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
}

private struct FixtureAccessibilityElement: AccessibilityElementReading {
  let storedIdentifier: String?
  let storedChildren: [any AccessibilityElementReading]

  init(
    identifier: String? = nil,
    children: [any AccessibilityElementReading] = []
  ) {
    storedIdentifier = identifier
    storedChildren = children
  }

  func identifier() throws -> String? {
    storedIdentifier
  }

  func children() throws -> [any AccessibilityElementReading] {
    storedChildren
  }
}

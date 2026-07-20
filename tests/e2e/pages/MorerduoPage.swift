import ApplicationServices
import Foundation

enum MorerduoPageError: Error, Equatable {
  case permissionDenied
  case elementNotFound(String)
  case attributeReadFailed(String)
  case invalidChildren
  case queryLimitExceeded
  case actionFailed(String)
  case timeout(String)
}

protocol AccessibilityElementReading {
  func identifier() throws -> String?
  func children() throws -> [any AccessibilityElementReading]
  func isEnabled() throws -> Bool
  func stringValue() throws -> String?
  func press() throws
}

struct MorerduoPage {
  private static let maximumVisitedElements = 10_000
  private let root: any AccessibilityElementReading

  init(
    applicationPID: pid_t,
    isProcessTrusted: () -> Bool = { AXIsProcessTrusted() }
  ) throws {
    try self.init(
      root: AXAccessibilityElement(
        element: AXUIElementCreateApplication(applicationPID)
      ),
      isProcessTrusted: isProcessTrusted
    )
  }

  init(
    root: any AccessibilityElementReading,
    isProcessTrusted: () -> Bool
  ) throws {
    guard isProcessTrusted() else {
      throw MorerduoPageError.permissionDenied
    }
    self.root = root
  }

  func element(identifier: String) throws -> any AccessibilityElementReading {
    var pending: [any AccessibilityElementReading] = [root]
    var visitedCount = 0

    while let candidate = pending.popLast() {
      visitedCount += 1
      guard visitedCount <= Self.maximumVisitedElements else {
        throw MorerduoPageError.queryLimitExceeded
      }
      if try candidate.identifier() == identifier {
        return candidate
      }
      pending.append(contentsOf: try candidate.children().reversed())
    }

    throw MorerduoPageError.elementNotFound(identifier)
  }

  func isEnabled(identifier: String) throws -> Bool {
    try element(identifier: identifier).isEnabled()
  }

  func value(identifier: String) throws -> String? {
    try element(identifier: identifier).stringValue()
  }

  func press(identifier: String) throws {
    try element(identifier: identifier).press()
  }

  func waitForElement(
    identifier: String,
    timeout: Duration = .seconds(5)
  ) async throws {
    let clock = ContinuousClock()
    let deadline = clock.now.advanced(by: timeout)
    while clock.now < deadline {
      if (try? element(identifier: identifier)) != nil { return }
      try await Task.sleep(for: .milliseconds(25))
    }
    throw MorerduoPageError.timeout(identifier)
  }
}

private struct AXAccessibilityElement: AccessibilityElementReading {
  let element: AXUIElement

  func identifier() throws -> String? {
    var value: CFTypeRef?
    let result = AXUIElementCopyAttributeValue(
      element,
      kAXIdentifierAttribute as CFString,
      &value
    )
    if result == .noValue || result == .attributeUnsupported {
      return nil
    }
    guard result == .success else {
      throw MorerduoPageError.attributeReadFailed(kAXIdentifierAttribute)
    }
    return value as? String
  }

  func children() throws -> [any AccessibilityElementReading] {
    var value: CFTypeRef?
    let result = AXUIElementCopyAttributeValue(
      element,
      kAXChildrenAttribute as CFString,
      &value
    )
    if result == .noValue || result == .attributeUnsupported {
      return []
    }
    guard result == .success else {
      throw MorerduoPageError.attributeReadFailed(kAXChildrenAttribute)
    }
    guard let children = value as? [AXUIElement] else {
      throw MorerduoPageError.invalidChildren
    }
    return children.map { AXAccessibilityElement(element: $0) }
  }

  func isEnabled() throws -> Bool {
    try attribute(kAXEnabledAttribute) as? Bool ?? false
  }

  func stringValue() throws -> String? {
    try attribute(kAXValueAttribute) as? String
  }

  func press() throws {
    let result = AXUIElementPerformAction(element, kAXPressAction as CFString)
    guard result == .success else {
      throw MorerduoPageError.actionFailed(kAXPressAction)
    }
  }

  private func attribute(_ name: String) throws -> CFTypeRef? {
    var value: CFTypeRef?
    let result = AXUIElementCopyAttributeValue(element, name as CFString, &value)
    if result == .noValue || result == .attributeUnsupported { return nil }
    guard result == .success else {
      throw MorerduoPageError.attributeReadFailed(name)
    }
    return value
  }
}

import ApplicationServices
import Foundation

enum MorerduoPageError: Error, Equatable {
  case permissionDenied
  case elementNotFound(String)
  case attributeReadFailed(String)
  case invalidChildren
  case queryLimitExceeded
}

protocol AccessibilityElementReading {
  func identifier() throws -> String?
  func children() throws -> [any AccessibilityElementReading]
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
}

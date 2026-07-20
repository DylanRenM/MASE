import Foundation

public struct ReloadPromptToken: Equatable, Hashable, Sendable {
  public let rawValue: UUID

  public init(rawValue: UUID) {
    self.rawValue = rawValue
  }
}

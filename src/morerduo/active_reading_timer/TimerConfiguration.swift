import Foundation

public struct TimerConfiguration: Equatable, Sendable {
  public static let validMinutes = 1...240
  public static let unlimited = TimerConfiguration(limit: nil)

  public let limit: Duration?

  private init(limit: Duration?) {
    self.limit = limit
  }

  public init(minutes: Int?) throws {
    guard let minutes else {
      limit = nil
      return
    }
    guard Self.validMinutes.contains(minutes) else {
      throw TimerConfigurationError.invalidMinutes
    }
    limit = .seconds(minutes * 60)
  }

  public static func parse(_ input: String) throws -> TimerConfiguration {
    let trimmed = input.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !trimmed.isEmpty else {
      return try TimerConfiguration(minutes: nil)
    }
    guard let minutes = Int(trimmed) else {
      throw TimerConfigurationError.invalidMinutes
    }
    return try TimerConfiguration(minutes: minutes)
  }
}

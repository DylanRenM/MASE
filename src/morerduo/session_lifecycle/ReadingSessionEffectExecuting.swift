public protocol ReadingSessionEffectExecuting: Sendable {
  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent?
}

public struct Transition: Equatable, Sendable {
  public let state: ReadingSessionState
  public let effects: [ReadingSessionEffect]

  public init(state: ReadingSessionState, effects: [ReadingSessionEffect]) {
    self.state = state
    self.effects = effects
  }
}

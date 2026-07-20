public protocol ReadingSessionReducing: Sendable {
  func reduce(
    state: ReadingSessionState,
    event: ReadingSessionEvent
  ) -> Transition
}

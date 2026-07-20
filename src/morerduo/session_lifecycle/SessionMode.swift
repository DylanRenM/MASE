public enum SessionMode: CaseIterable, Equatable, Sendable {
  case idle
  case loading
  case ready
  case playing
  case paused
  case awaitingReloadDecision
}

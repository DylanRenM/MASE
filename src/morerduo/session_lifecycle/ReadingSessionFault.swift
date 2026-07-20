public enum ReadingSessionFault: Equatable, Sendable {
  case invalidState
  case illegalTransition
  case invalidCursor
}

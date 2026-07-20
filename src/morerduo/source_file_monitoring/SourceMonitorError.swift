public enum SourceMonitorError: Error, Equatable, Sendable {
  case invalidSource
  case alreadyActive
  case unavailable
}

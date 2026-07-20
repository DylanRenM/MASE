public enum SpeechEngineError: Error, Equatable, Sendable {
  case unavailable
  case alreadyActive
  case noActiveRequest
  case synthesisFailed
}

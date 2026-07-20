public enum UserFacingError: Equatable, Sendable {
  case document(DocumentLoadError)
  case sourceUnavailable
  case speechUnavailable
  case speechFailure
  case timerFailure
  case monitorFailure
  case internalFailure
}

public enum SpeechEvent: Equatable, Sendable {
  case progressed(SpeechProgress)
  case finished(sessionToken: ReadingSessionToken, requestToken: SpeechRequestToken)
  case cancelled(sessionToken: ReadingSessionToken, requestToken: SpeechRequestToken)
  case failed(
    SpeechEngineError,
    sessionToken: ReadingSessionToken,
    requestToken: SpeechRequestToken
  )
}

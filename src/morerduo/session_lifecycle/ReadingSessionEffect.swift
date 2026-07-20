import Foundation

public enum ReadingSessionEffect: Equatable, Sendable {
  case loadDocument(URL, token: ReadingSessionToken, autoplay: Bool)
  case verifySource(LoadedDocument, token: ReadingSessionToken)
  case startSpeech(
    document: LoadedDocument,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    token: ReadingSessionToken
  )
  case pauseSpeech(token: ReadingSessionToken)
  case resumeSpeech(token: ReadingSessionToken, rebuild: Bool)
  case stopSpeech(token: ReadingSessionToken)
  case startClock(token: ReadingSessionToken)
  case freezeClock(token: ReadingSessionToken)
  case stopClock(token: ReadingSessionToken)
  case startMonitor(source: ValidatedSource, token: ReadingSessionToken)
  case stopMonitor(token: ReadingSessionToken)
  case emergencyCleanup
  case recordFault(ReadingSessionFault)
}

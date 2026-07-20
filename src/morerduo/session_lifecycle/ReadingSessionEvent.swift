import Foundation

public enum ReadingSessionEvent: Equatable, Sendable {
  case selectFile(URL, token: ReadingSessionToken)
  case documentLoaded(LoadedDocument, token: ReadingSessionToken, autoplay: Bool)
  case documentLoadFailed(DocumentLoadError, token: ReadingSessionToken)
  case effectFailed(UserFacingError, token: ReadingSessionToken)
  case play(token: ReadingSessionToken)
  case pause
  case resume
  case stop
  case changeSpeed(ReadingSpeed)
  case cursorAdvanced(ReadingCursor, token: ReadingSessionToken)
  case paragraphFinished(token: ReadingSessionToken)
  case timerExpired(TimerExpiry)
  case sourceChanged(promptToken: ReloadPromptToken, sessionToken: ReadingSessionToken)
  case reloadSource(token: ReadingSessionToken)
  case continueOldContent
  case dismissError
  case appTerminate
}

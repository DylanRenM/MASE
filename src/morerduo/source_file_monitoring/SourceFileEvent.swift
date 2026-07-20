public struct SourceFileEvent: Equatable, Sendable {
  public let changes: SourceFileChange
  public let sessionToken: ReadingSessionToken

  public init(
    changes: SourceFileChange,
    sessionToken: ReadingSessionToken
  ) {
    precondition(!changes.isEmpty, "Source file event must contain a change")
    self.changes = changes
    self.sessionToken = sessionToken
  }
}

public struct ReadingSessionState: Equatable, Sendable {
  public let mode: SessionMode
  public let document: LoadedDocument?
  public let cursor: ReadingCursor
  public let speed: ReadingSpeed
  public let timer: TimerConfiguration
  public let sessionToken: ReadingSessionToken?
  public let reloadPromptToken: ReloadPromptToken?
  public let error: UserFacingError?
  public let requiresUtteranceRebuild: Bool

  private init(
    mode: SessionMode,
    document: LoadedDocument?,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    timer: TimerConfiguration,
    sessionToken: ReadingSessionToken?,
    reloadPromptToken: ReloadPromptToken?,
    error: UserFacingError? = nil,
    requiresUtteranceRebuild: Bool = false,
    validatesInvariants: Bool = true
  ) {
    if validatesInvariants {
      precondition(
        Self.satisfiesInvariants(
          mode: mode,
          document: document,
          cursor: cursor,
          sessionToken: sessionToken,
          reloadPromptToken: reloadPromptToken
        ),
        "ReadingSessionState violates its module invariants"
      )
    }
    self.mode = mode
    self.document = document
    self.cursor = cursor
    self.speed = speed
    self.timer = timer
    self.sessionToken = sessionToken
    self.reloadPromptToken = reloadPromptToken
    self.error = error
    self.requiresUtteranceRebuild = requiresUtteranceRebuild
  }

  public static func initial(
    timer: TimerConfiguration,
    speed: ReadingSpeed = .normal,
    error: UserFacingError? = nil
  ) -> Self {
    Self(
      mode: .idle,
      document: nil,
      cursor: .zero,
      speed: speed,
      timer: timer,
      sessionToken: nil,
      reloadPromptToken: nil,
      error: error
    )
  }

  public static func loading(
    speed: ReadingSpeed,
    timer: TimerConfiguration,
    sessionToken: ReadingSessionToken
  ) -> Self {
    Self(
      mode: .loading,
      document: nil,
      cursor: .zero,
      speed: speed,
      timer: timer,
      sessionToken: sessionToken,
      reloadPromptToken: nil
    )
  }

  public static func ready(
    document: LoadedDocument,
    speed: ReadingSpeed,
    timer: TimerConfiguration,
    error: UserFacingError? = nil
  ) -> Self {
    Self(
      mode: .ready,
      document: document,
      cursor: .zero,
      speed: speed,
      timer: timer,
      sessionToken: nil,
      reloadPromptToken: nil,
      error: error
    )
  }

  public static func playing(
    document: LoadedDocument,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    timer: TimerConfiguration,
    sessionToken: ReadingSessionToken
  ) -> Self {
    loadedState(
      mode: .playing,
      document: document,
      cursor: cursor,
      speed: speed,
      timer: timer,
      sessionToken: sessionToken
    )
  }

  public static func paused(
    document: LoadedDocument,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    timer: TimerConfiguration,
    sessionToken: ReadingSessionToken,
    requiresUtteranceRebuild: Bool = false
  ) -> Self {
    loadedState(
      mode: .paused,
      document: document,
      cursor: cursor,
      speed: speed,
      timer: timer,
      sessionToken: sessionToken,
      requiresUtteranceRebuild: requiresUtteranceRebuild
    )
  }

  public static func awaitingReloadDecision(
    document: LoadedDocument,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    timer: TimerConfiguration,
    sessionToken: ReadingSessionToken,
    promptToken: ReloadPromptToken
  ) -> Self {
    Self(
      mode: .awaitingReloadDecision,
      document: document,
      cursor: cursor,
      speed: speed,
      timer: timer,
      sessionToken: sessionToken,
      reloadPromptToken: promptToken
    )
  }

  public var isClockActive: Bool {
    mode == .playing
  }

  public var satisfiesInvariants: Bool {
    Self.satisfiesInvariants(
      mode: mode,
      document: document,
      cursor: cursor,
      sessionToken: sessionToken,
      reloadPromptToken: reloadPromptToken
    )
  }

  public static func satisfiesInvariants(
    mode: SessionMode,
    document: LoadedDocument?,
    cursor: ReadingCursor,
    sessionToken: ReadingSessionToken?,
    reloadPromptToken: ReloadPromptToken?
  ) -> Bool {
    guard cursorIsValid(cursor, for: document) else {
      return false
    }
    switch mode {
    case .idle:
      return document == nil && cursor == .zero && sessionToken == nil
        && reloadPromptToken == nil
    case .loading:
      return document == nil && cursor == .zero && sessionToken != nil
        && reloadPromptToken == nil
    case .ready:
      return document != nil && sessionToken == nil && reloadPromptToken == nil
    case .playing, .paused:
      return document != nil && sessionToken != nil && reloadPromptToken == nil
    case .awaitingReloadDecision:
      return document != nil && sessionToken != nil && reloadPromptToken != nil
    }
  }

  static func unchecked(
    mode: SessionMode,
    document: LoadedDocument?,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    timer: TimerConfiguration,
    sessionToken: ReadingSessionToken?,
    reloadPromptToken: ReloadPromptToken?,
    error: UserFacingError? = nil,
    requiresUtteranceRebuild: Bool = false
  ) -> Self {
    Self(
      mode: mode,
      document: document,
      cursor: cursor,
      speed: speed,
      timer: timer,
      sessionToken: sessionToken,
      reloadPromptToken: reloadPromptToken,
      error: error,
      requiresUtteranceRebuild: requiresUtteranceRebuild,
      validatesInvariants: false
    )
  }

  private static func loadedState(
    mode: SessionMode,
    document: LoadedDocument,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    timer: TimerConfiguration,
    sessionToken: ReadingSessionToken,
    requiresUtteranceRebuild: Bool = false
  ) -> Self {
    Self(
      mode: mode,
      document: document,
      cursor: cursor,
      speed: speed,
      timer: timer,
      sessionToken: sessionToken,
      reloadPromptToken: nil,
      requiresUtteranceRebuild: requiresUtteranceRebuild
    )
  }

  private static func cursorIsValid(
    _ cursor: ReadingCursor,
    for document: LoadedDocument?
  ) -> Bool {
    guard let document else {
      return cursor == .zero
    }
    guard document.paragraphs.indices.contains(cursor.paragraphIndex) else {
      return false
    }
    return (0...document.paragraphs[cursor.paragraphIndex].utf16Length)
      .contains(cursor.utf16Offset)
  }
}

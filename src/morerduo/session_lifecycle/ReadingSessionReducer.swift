import Foundation

public struct ReadingSessionReducer: ReadingSessionReducing, Sendable {
  private let contractMode: ContractMode

  public init(contractMode: ContractMode) {
    self.contractMode = contractMode
  }

  public func reduce(
    state: ReadingSessionState,
    event: ReadingSessionEvent
  ) -> Transition {
    let inputCheck = Contract.invariantCheck(
      state.satisfiesInvariants,
      "reducer input state must satisfy session invariants",
      mode: contractMode
    )
    if case .violation = inputCheck {
      return failSafe(state: state, fault: .invalidState)
    }
    let result = transition(state: state, event: event) ?? invalid(state: state)
    let outputCheck = Contract.invariantCheck(
      result.state.satisfiesInvariants,
      "reducer output state must satisfy session invariants",
      mode: contractMode
    )
    if case .violation = outputCheck {
      return failSafe(state: state, fault: .invalidState)
    }
    return result
  }

  private func transition(
    state: ReadingSessionState,
    event: ReadingSessionEvent
  ) -> Transition? {
    switch event {
    case .selectFile(let url, let token):
      return selectFile(state: state, url: url, token: token)
    case .documentLoaded(let document, let token, let autoplay):
      return documentLoaded(state: state, document: document, token: token, autoplay: autoplay)
    case .documentLoadFailed(let error, let token):
      return documentLoadFailed(state: state, error: error, token: token)
    case .effectFailed(let error, let token):
      return effectFailed(state: state, error: error, token: token)
    case .play(let token):
      return play(state: state, token: token)
    case .pause:
      return pause(state: state)
    case .resume:
      return resume(state: state)
    case .stop:
      return stop(state: state)
    case .timerExpired(let expiry):
      return timerExpired(state: state, expiry: expiry)
    case .cursorAdvanced(let cursor, let token):
      return cursorAdvanced(state: state, cursor: cursor, token: token)
    case .paragraphFinished(let token):
      return paragraphFinished(state: state, token: token)
    case .appTerminate:
      return terminate(state: state)
    case .dismissError:
      return dismissError(state: state)
    case .changeSpeed(let speed):
      return changeSpeed(state: state, speed: speed)
    case .changeTimer(let timer):
      return changeTimer(state: state, timer: timer)
    case .sourceChanged(let promptToken, let sessionToken):
      return sourceChanged(
        state: state,
        promptToken: promptToken,
        sessionToken: sessionToken
      )
    case .reloadSource(let promptToken, let token):
      return reloadSource(state: state, promptToken: promptToken, token: token)
    case .continueOldContent(let promptToken):
      return continueOldContent(state: state, promptToken: promptToken)
    }
  }

  private func sourceChanged(
    state: ReadingSessionState,
    promptToken: ReloadPromptToken,
    sessionToken: ReadingSessionToken
  ) -> Transition? {
    guard state.sessionToken == sessionToken else {
      return ignoredLateCallback(state: state)
    }
    if state.mode == .awaitingReloadDecision {
      return Transition(state: state, effects: [])
    }
    if state.mode == .paused {
      return ignoredLateCallback(state: state)
    }
    guard
      state.mode == .playing,
      let document = state.document
    else {
      return nil
    }
    return Transition(
      state: .awaitingReloadDecision(
        document: document,
        cursor: state.cursor,
        speed: state.speed,
        timer: state.timer,
        sessionToken: sessionToken,
        promptToken: promptToken
      ),
      effects: [
        .freezeClock(token: sessionToken),
        .pauseSpeech(token: sessionToken),
      ]
    )
  }

  private func reloadSource(
    state: ReadingSessionState,
    promptToken: ReloadPromptToken,
    token: ReadingSessionToken
  ) -> Transition? {
    guard state.reloadPromptToken == promptToken else {
      return ignoredLateCallback(state: state)
    }
    guard
      state.mode == .awaitingReloadDecision,
      let document = state.document,
      let oldToken = state.sessionToken
    else {
      return nil
    }
    return Transition(
      state: .loading(
        speed: state.speed,
        timer: state.timer,
        sessionToken: token
      ),
      effects: stopEffects(token: oldToken)
        + [
          .loadDocument(
            document.source.url,
            token: token,
            autoplay: true
          )
        ]
    )
  }

  private func continueOldContent(
    state: ReadingSessionState,
    promptToken: ReloadPromptToken
  ) -> Transition? {
    guard state.reloadPromptToken == promptToken else {
      return ignoredLateCallback(state: state)
    }
    guard
      state.mode == .awaitingReloadDecision,
      let document = state.document,
      let token = state.sessionToken
    else {
      return nil
    }
    return Transition(
      state: .playing(
        document: document,
        cursor: state.cursor,
        speed: state.speed,
        timer: state.timer,
        sessionToken: token
      ),
      effects: [
        .resumeSpeech(
          document: document,
          cursor: state.cursor,
          speed: state.speed,
          token: token,
          rebuild: false
        ),
        .startClock(token: token),
      ]
    )
  }

  private func documentLoadFailed(
    state: ReadingSessionState,
    error: DocumentLoadError,
    token: ReadingSessionToken
  ) -> Transition? {
    guard state.mode == .loading, state.sessionToken == token else {
      return ignoredLateCallback(state: state)
    }
    return Transition(
      state: .initial(timer: state.timer, error: .document(error)),
      effects: []
    )
  }

  private func dismissError(state: ReadingSessionState) -> Transition? {
    guard state.error != nil else {
      return Transition(state: state, effects: [])
    }
    if state.mode == .idle {
      return Transition(state: .initial(timer: state.timer), effects: [])
    }
    guard state.mode == .ready, let document = state.document else {
      return nil
    }
    return Transition(
      state: .ready(document: document, speed: state.speed, timer: state.timer),
      effects: []
    )
  }

  private func effectFailed(
    state: ReadingSessionState,
    error: UserFacingError,
    token: ReadingSessionToken
  ) -> Transition? {
    guard state.sessionToken == token else {
      return ignoredLateCallback(state: state)
    }
    if error == .sourceUnavailable {
      return Transition(
        state: .initial(timer: state.timer, error: error),
        effects: stopEffects(token: token)
      )
    }
    if case .document = error {
      return Transition(
        state: .initial(timer: state.timer, error: error),
        effects: activeStopEffects(state: state)
      )
    }
    guard let document = state.document else {
      return Transition(
        state: .initial(timer: state.timer, error: error),
        effects: []
      )
    }
    return Transition(
      state: .ready(
        document: document,
        speed: state.speed,
        timer: state.timer,
        error: error
      ),
      effects: stopEffects(token: token)
    )
  }

  private func selectFile(
    state: ReadingSessionState,
    url: URL,
    token: ReadingSessionToken
  ) -> Transition {
    let loading = ReadingSessionState.loading(
      speed: state.speed,
      timer: state.timer,
      sessionToken: token
    )
    var effects = activeStopEffects(state: state)
    effects.append(.loadDocument(url, token: token, autoplay: false))
    return Transition(state: loading, effects: effects)
  }

  private func documentLoaded(
    state: ReadingSessionState,
    document: LoadedDocument,
    token: ReadingSessionToken,
    autoplay: Bool
  ) -> Transition? {
    guard state.mode == .loading, state.sessionToken == token else {
      return ignoredLateCallback(state: state)
    }
    guard autoplay else {
      return Transition(
        state: .ready(document: document, speed: state.speed, timer: state.timer),
        effects: []
      )
    }
    let playing = ReadingSessionState.playing(
      document: document,
      cursor: .zero,
      speed: state.speed,
      timer: state.timer,
      sessionToken: token
    )
    return Transition(state: playing, effects: startEffects(state: playing))
  }

  private func play(
    state: ReadingSessionState,
    token: ReadingSessionToken
  ) -> Transition? {
    if state.mode == .playing {
      return Transition(state: state, effects: [])
    }
    guard state.mode == .ready, let document = state.document else {
      return nil
    }
    let playing = ReadingSessionState.playing(
      document: document,
      cursor: state.cursor,
      speed: state.speed,
      timer: state.timer,
      sessionToken: token
    )
    return Transition(state: playing, effects: startEffects(state: playing))
  }

  private func pause(state: ReadingSessionState) -> Transition? {
    if state.mode == .paused {
      return Transition(state: state, effects: [])
    }
    if state.mode == .ready {
      return Transition(state: state, effects: [])
    }
    guard
      state.mode == .playing,
      let document = state.document,
      let token = state.sessionToken
    else {
      return nil
    }
    let paused = ReadingSessionState.paused(
      document: document,
      cursor: state.cursor,
      speed: state.speed,
      timer: state.timer,
      sessionToken: token
    )
    return Transition(
      state: paused,
      effects: [
        .freezeClock(token: token),
        .pauseSpeech(token: token),
        .stopMonitor(token: token),
      ]
    )
  }

  private func resume(state: ReadingSessionState) -> Transition? {
    if state.mode == .playing {
      return Transition(state: state, effects: [])
    }
    if state.mode == .ready {
      return Transition(state: state, effects: [])
    }
    guard
      state.mode == .paused,
      let document = state.document,
      let token = state.sessionToken
    else {
      return nil
    }
    let playing = ReadingSessionState.playing(
      document: document,
      cursor: state.cursor,
      speed: state.speed,
      timer: state.timer,
      sessionToken: token
    )
    return Transition(
      state: playing,
      effects: [
        .verifySource(document, token: token),
        .resumeSpeech(
          document: document,
          cursor: state.cursor,
          speed: state.speed,
          token: token,
          rebuild: state.requiresUtteranceRebuild
        ),
        .startClock(token: token),
        .startMonitor(source: document.source, token: token),
      ]
    )
  }

  private func changeSpeed(
    state: ReadingSessionState,
    speed: ReadingSpeed
  ) -> Transition? {
    if state.speed == speed {
      return Transition(state: state, effects: [])
    }
    switch state.mode {
    case .idle:
      return Transition(
        state: .initial(timer: state.timer, speed: speed, error: state.error),
        effects: []
      )
    case .ready:
      guard let document = state.document else { return nil }
      return Transition(
        state: .ready(
          document: document,
          speed: speed,
          timer: state.timer,
          error: state.error
        ),
        effects: []
      )
    case .paused:
      guard let document = state.document, let token = state.sessionToken else {
        return nil
      }
      return Transition(
        state: .paused(
          document: document,
          cursor: state.cursor,
          speed: speed,
          timer: state.timer,
          sessionToken: token,
          requiresUtteranceRebuild: true
        ),
        effects: []
      )
    case .loading, .playing, .awaitingReloadDecision:
      return nil
    }
  }

  private func changeTimer(
    state: ReadingSessionState,
    timer: TimerConfiguration
  ) -> Transition? {
    if state.timer == timer {
      return Transition(state: state, effects: [])
    }
    switch state.mode {
    case .idle:
      return Transition(
        state: .initial(timer: timer, speed: state.speed, error: state.error),
        effects: []
      )
    case .ready:
      guard let document = state.document else { return nil }
      return Transition(
        state: .ready(
          document: document,
          speed: state.speed,
          timer: timer,
          error: state.error
        ),
        effects: []
      )
    case .loading, .playing, .paused, .awaitingReloadDecision:
      return nil
    }
  }

  private func stop(state: ReadingSessionState) -> Transition? {
    if state.mode == .ready {
      return Transition(state: state, effects: [])
    }
    guard
      state.mode == .playing || state.mode == .paused
        || state.mode == .awaitingReloadDecision,
      let document = state.document,
      let token = state.sessionToken
    else {
      return nil
    }
    return Transition(
      state: .ready(document: document, speed: state.speed, timer: state.timer),
      effects: stopEffects(token: token)
    )
  }

  private func timerExpired(
    state: ReadingSessionState,
    expiry: TimerExpiry
  ) -> Transition? {
    guard state.sessionToken == expiry.token else {
      return ignoredLateCallback(state: state)
    }
    return stop(state: state)
  }

  private func cursorAdvanced(
    state: ReadingSessionState,
    cursor: ReadingCursor,
    token: ReadingSessionToken
  ) -> Transition? {
    guard state.sessionToken == token else {
      return ignoredLateCallback(state: state)
    }
    guard state.mode == .playing, let document = state.document else {
      if state.mode == .paused || state.mode == .awaitingReloadDecision {
        return ignoredLateCallback(state: state)
      }
      return nil
    }
    let isValid = ReadingSessionState.satisfiesInvariants(
      mode: .playing,
      document: document,
      cursor: cursor,
      sessionToken: token,
      reloadPromptToken: nil
    )
    guard isValid else {
      let cursorCheck = Contract.invariantCheck(
        false,
        "current session cursor must remain in document bounds",
        mode: contractMode
      )
      if case .violation = cursorCheck {
        return failSafe(state: state, fault: .invalidCursor)
      }
      return ignoredLateCallback(state: state)
    }
    guard !isBefore(cursor, state.cursor) else {
      return ignoredLateCallback(state: state)
    }
    return Transition(
      state: .playing(
        document: document,
        cursor: cursor,
        speed: state.speed,
        timer: state.timer,
        sessionToken: token
      ),
      effects: []
    )
  }

  private func isBefore(_ candidate: ReadingCursor, _ current: ReadingCursor) -> Bool {
    if candidate.paragraphIndex != current.paragraphIndex {
      return candidate.paragraphIndex < current.paragraphIndex
    }
    return candidate.utf16Offset < current.utf16Offset
  }

  private func paragraphFinished(
    state: ReadingSessionState,
    token: ReadingSessionToken
  ) -> Transition? {
    guard
      state.mode == .playing,
      state.sessionToken == token,
      let document = state.document
    else {
      return ignoredLateCallback(state: state)
    }
    let nextIndex = state.cursor.paragraphIndex + 1
    let cursor =
      document.paragraphs.indices.contains(nextIndex)
      ? ReadingCursor(paragraphIndex: nextIndex, utf16Offset: 0)
      : .zero
    let playing = ReadingSessionState.playing(
      document: document,
      cursor: cursor,
      speed: state.speed,
      timer: state.timer,
      sessionToken: token
    )
    return Transition(
      state: playing,
      effects: [
        .startSpeech(
          document: document,
          cursor: cursor,
          speed: state.speed,
          token: token
        )
      ]
    )
  }

  private func terminate(state: ReadingSessionState) -> Transition {
    Transition(
      state: .initial(timer: state.timer),
      effects: activeStopEffects(state: state)
    )
  }

  private func startEffects(state: ReadingSessionState) -> [ReadingSessionEffect] {
    guard let document = state.document, let token = state.sessionToken else {
      preconditionFailure("playing state must carry document and token")
    }
    return [
      .verifySource(document, token: token),
      .startSpeech(
        document: document,
        cursor: state.cursor,
        speed: state.speed,
        token: token
      ),
      .startClock(token: token),
      .startMonitor(source: document.source, token: token),
    ]
  }

  private func activeStopEffects(state: ReadingSessionState) -> [ReadingSessionEffect] {
    guard
      state.mode == .playing || state.mode == .paused
        || state.mode == .awaitingReloadDecision,
      let token = state.sessionToken
    else {
      return []
    }
    return stopEffects(token: token)
  }

  private func stopEffects(token: ReadingSessionToken) -> [ReadingSessionEffect] {
    [
      .stopSpeech(token: token),
      .stopMonitor(token: token),
      .stopClock(token: token),
    ]
  }

  private func ignoredLateCallback(state: ReadingSessionState) -> Transition {
    Transition(state: state, effects: [])
  }

  private func invalid(state: ReadingSessionState) -> Transition {
    let transitionCheck = Contract.invariantCheck(
      false,
      "illegal session transition",
      mode: contractMode
    )
    if case .violation = transitionCheck {
      return failSafe(state: state, fault: .illegalTransition)
    }
    return Transition(state: state, effects: [])
  }

  private func failSafe(
    state: ReadingSessionState,
    fault: ReadingSessionFault
  ) -> Transition {
    let recoveredState: ReadingSessionState
    if let document = state.document {
      recoveredState = .ready(
        document: document,
        speed: state.speed,
        timer: state.timer,
        error: .internalFailure
      )
    } else {
      recoveredState = .initial(timer: state.timer, error: .internalFailure)
    }
    return Transition(
      state: recoveredState,
      effects: failSafeEffects(state: state, fault: fault)
    )
  }

  private func failSafeEffects(
    state: ReadingSessionState,
    fault: ReadingSessionFault
  ) -> [ReadingSessionEffect] {
    let cleanupEffects =
      fault == .invalidState
      ? [ReadingSessionEffect.emergencyCleanup]
      : activeStopEffects(state: state)
    return cleanupEffects + [.recordFault(fault)]
  }
}

import Foundation
import Testing

@testable import MorerduoKit

@Suite("ReadingSessionReducer")
struct ReadingSessionReducerTests {
  @Test("select load play pause resume and stop follow the main flow")
  func mainFlow() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let timer = try TimerConfiguration(minutes: 30)
    let document = makeDocument()
    let loadToken = token(1)
    let playToken = token(2)
    let url = document.source.url

    let loading = reducer.reduce(
      state: .initial(timer: timer),
      event: .selectFile(url, token: loadToken)
    )
    #expect(loading.state == .loading(speed: .normal, timer: timer, sessionToken: loadToken))
    #expect(loading.effects == [.loadDocument(url, token: loadToken, autoplay: false)])

    let ready = reducer.reduce(
      state: loading.state,
      event: .documentLoaded(document, token: loadToken, autoplay: false)
    )
    #expect(ready.state == .ready(document: document, speed: .normal, timer: timer))
    #expect(ready.effects.isEmpty)

    let playing = reducer.reduce(state: ready.state, event: .play(token: playToken))
    #expect(
      playing.state
        == .playing(
          document: document,
          cursor: .zero,
          speed: .normal,
          timer: timer,
          sessionToken: playToken
        )
    )
    #expect(
      playing.effects == [
        .verifySource(document, token: playToken),
        .startSpeech(
          document: document,
          cursor: .zero,
          speed: .normal,
          token: playToken
        ),
        .startClock(token: playToken),
        .startMonitor(source: document.source, token: playToken),
      ]
    )

    let paused = reducer.reduce(state: playing.state, event: .pause)
    #expect(paused.state.mode == .paused)
    #expect(
      paused.effects == [
        .freezeClock(token: playToken),
        .pauseSpeech(token: playToken),
        .stopMonitor(token: playToken),
      ]
    )

    let resumed = reducer.reduce(state: paused.state, event: .resume)
    #expect(resumed.state.mode == .playing)
    #expect(
      resumed.effects == [
        .verifySource(document, token: playToken),
        .resumeSpeech(
          document: document,
          cursor: .zero,
          speed: .normal,
          token: playToken,
          rebuild: false
        ),
        .startClock(token: playToken),
        .startMonitor(source: document.source, token: playToken),
      ]
    )

    let stopped = reducer.reduce(state: resumed.state, event: .stop)
    #expect(stopped.state == .ready(document: document, speed: .normal, timer: timer))
    #expect(stopped.effects == stopEffects(token: playToken))
  }

  @Test("timer expiry is identical to independent stop")
  func timerExpiryMatchesStop() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 5))
    let sessionToken = try #require(playing.sessionToken)

    let stopped = reducer.reduce(state: playing, event: .stop)
    let expired = reducer.reduce(
      state: playing,
      event: .timerExpired(TimerExpiry(token: sessionToken))
    )

    #expect(expired == stopped)
    #expect(expired.state.cursor == .zero)
    #expect(expired.state.document == playing.document)
    #expect(expired.state.timer == playing.timer)
  }

  @Test("paused speed change preserves cursor and requests a suffix rebuild")
  func pausedSpeedChangeRequiresRebuild() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(
      cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 6)
    )
    let document = try #require(playing.document)
    let sessionToken = try #require(playing.sessionToken)
    let paused = reducer.reduce(state: playing, event: .pause).state

    let changed = reducer.reduce(state: paused, event: .changeSpeed(.fast))
    #expect(changed.state.mode == .paused)
    #expect(changed.state.cursor == paused.cursor)
    #expect(changed.state.speed == .fast)
    #expect(changed.state.requiresUtteranceRebuild)

    let resumed = reducer.reduce(state: changed.state, event: .resume)
    #expect(
      resumed.effects == [
        .verifySource(document, token: sessionToken),
        .resumeSpeech(
          document: document,
          cursor: paused.cursor,
          speed: .fast,
          token: sessionToken,
          rebuild: true
        ),
        .startClock(token: sessionToken),
        .startMonitor(source: document.source, token: sessionToken),
      ]
    )
  }

  @Test("speed may change while idle or ready without starting speech")
  func nonPlayingSpeedChangeIsConfigurationOnly() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let timer = try TimerConfiguration(minutes: nil)
    let idle = reducer.reduce(
      state: .initial(timer: timer),
      event: .changeSpeed(.slow)
    )
    #expect(idle.state.speed == .slow)
    #expect(idle.effects.isEmpty)

    let document = makeDocument()
    let ready = reducer.reduce(
      state: .ready(document: document, speed: .normal, timer: timer),
      event: .changeSpeed(.fast)
    )
    #expect(ready.state.speed == .fast)
    #expect(ready.effects.isEmpty)
  }

  @Test("timer configuration may change while idle or ready")
  func timerChangesBeforePlayback() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let unlimited = try TimerConfiguration(minutes: nil)
    let thirtyMinutes = try TimerConfiguration(minutes: 30)
    let document = makeDocument()

    let idle = reducer.reduce(
      state: .initial(timer: unlimited),
      event: .changeTimer(thirtyMinutes)
    )
    let ready = reducer.reduce(
      state: .ready(document: document, speed: .fast, timer: unlimited),
      event: .changeTimer(thirtyMinutes)
    )

    #expect(idle.state == .initial(timer: thirtyMinutes))
    #expect(
      ready.state
        == .ready(document: document, speed: .fast, timer: thirtyMinutes)
    )
    #expect(idle.effects.isEmpty)
    #expect(ready.effects.isEmpty)
  }

  @Test("selecting a new file while paused clears old resources before loading")
  func selectingFileWhilePaused() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 3))
    let oldToken = try #require(playing.sessionToken)
    let paused = ReadingSessionState.paused(
      document: try #require(playing.document),
      cursor: playing.cursor,
      speed: playing.speed,
      timer: playing.timer,
      sessionToken: oldToken
    )
    let newToken = token(4)
    let newURL = URL(fileURLWithPath: "/tmp/new.txt")

    let transition = reducer.reduce(
      state: paused,
      event: .selectFile(newURL, token: newToken)
    )

    #expect(
      transition.state
        == .loading(
          speed: .normal,
          timer: paused.timer,
          sessionToken: newToken
        )
    )
    #expect(
      transition.effects == stopEffects(token: oldToken)
        + [.loadDocument(newURL, token: newToken, autoplay: false)]
    )
  }

  @Test("application termination discards the loaded session")
  func terminationReturnsToIdle() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 2))
    let sessionToken = try #require(playing.sessionToken)

    let transition = reducer.reduce(state: playing, event: .appTerminate)

    #expect(transition.state == .initial(timer: playing.timer))
    #expect(transition.effects == stopEffects(token: sessionToken))
  }

  @Test("a source change freezes playback and duplicate prompts are ignored")
  func sourceChangePromptIsDeduplicated() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(
      cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 6)
    )
    let sessionToken = try #require(playing.sessionToken)
    let firstPrompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000021")!
    )
    let duplicatePrompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000022")!
    )

    let first = reducer.reduce(
      state: playing,
      event: .sourceChanged(
        promptToken: firstPrompt,
        sessionToken: sessionToken
      )
    )
    let duplicate = reducer.reduce(
      state: first.state,
      event: .sourceChanged(
        promptToken: duplicatePrompt,
        sessionToken: sessionToken
      )
    )

    #expect(first.state.mode == .awaitingReloadDecision)
    #expect(first.state.cursor == playing.cursor)
    #expect(first.state.reloadPromptToken == firstPrompt)
    #expect(
      first.effects == [
        .freezeClock(token: sessionToken),
        .pauseSpeech(token: sessionToken),
      ]
    )
    #expect(duplicate == Transition(state: first.state, effects: []))
  }

  @Test("a late source token cannot prompt the current session")
  func lateSourceTokenIsIgnored() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: .zero)
    let prompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000023")!
    )

    let transition = reducer.reduce(
      state: playing,
      event: .sourceChanged(promptToken: prompt, sessionToken: token(24))
    )

    #expect(transition == Transition(state: playing, effects: []))
  }

  @Test("a source callback queued before pause is ignored after monitor stop")
  func pausedIgnoresQueuedSourceCallback() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: .zero)
    let sessionToken = try #require(playing.sessionToken)
    let paused = reducer.reduce(state: playing, event: .pause).state
    let prompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000030")!
    )

    let transition = reducer.reduce(
      state: paused,
      event: .sourceChanged(promptToken: prompt, sessionToken: sessionToken)
    )

    #expect(transition == Transition(state: paused, effects: []))
  }

  @Test("timer expiry closes an active reload prompt with stop semantics")
  func timerExpiryWinsReloadPromptRace() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 5))
    let sessionToken = try #require(playing.sessionToken)
    let document = try #require(playing.document)
    let prompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000031")!
    )
    let awaiting = reducer.reduce(
      state: playing,
      event: .sourceChanged(promptToken: prompt, sessionToken: sessionToken)
    ).state

    let transition = reducer.reduce(
      state: awaiting,
      event: .timerExpired(TimerExpiry(token: sessionToken))
    )

    #expect(
      transition.state
        == .ready(document: document, speed: playing.speed, timer: playing.timer)
    )
    #expect(transition.effects == stopEffects(token: sessionToken))
  }

  @Test("stale and duplicate prompt decisions cannot affect a new state")
  func promptDecisionIdentityIsEnforced() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: .zero)
    let sessionToken = try #require(playing.sessionToken)
    let currentPrompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000032")!
    )
    let stalePrompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000033")!
    )
    let awaiting = reducer.reduce(
      state: playing,
      event: .sourceChanged(
        promptToken: currentPrompt,
        sessionToken: sessionToken
      )
    ).state

    let stale = reducer.reduce(
      state: awaiting,
      event: .continueOldContent(promptToken: stalePrompt)
    )
    let continued = reducer.reduce(
      state: awaiting,
      event: .continueOldContent(promptToken: currentPrompt)
    )
    let duplicate = reducer.reduce(
      state: continued.state,
      event: .continueOldContent(promptToken: currentPrompt)
    )

    #expect(stale == Transition(state: awaiting, effects: []))
    #expect(continued.state.mode == .playing)
    #expect(duplicate == Transition(state: continued.state, effects: []))
  }

  @Test("reload stops the old session and loads the same path for autoplay")
  func reloadStartsAtomicAutoplayLoad() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(
      cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 6)
    )
    let oldToken = try #require(playing.sessionToken)
    let document = try #require(playing.document)
    let prompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000025")!
    )
    let awaiting = ReadingSessionState.awaitingReloadDecision(
      document: document,
      cursor: playing.cursor,
      speed: playing.speed,
      timer: playing.timer,
      sessionToken: oldToken,
      promptToken: prompt
    )
    let newToken = token(26)

    let transition = reducer.reduce(
      state: awaiting,
      event: .reloadSource(promptToken: prompt, token: newToken)
    )

    #expect(
      transition.state
        == .loading(
          speed: awaiting.speed,
          timer: awaiting.timer,
          sessionToken: newToken
        )
    )
    #expect(
      transition.effects == stopEffects(token: oldToken)
        + [
          .loadDocument(
            document.source.url,
            token: newToken,
            autoplay: true
          )
        ]
    )
  }

  @Test("continue old content resumes the frozen cursor and clock")
  func continueOldContentResumesFrozenSession() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(
      cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 6)
    )
    let sessionToken = try #require(playing.sessionToken)
    let document = try #require(playing.document)
    let prompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000027")!
    )
    let awaiting = ReadingSessionState.awaitingReloadDecision(
      document: document,
      cursor: playing.cursor,
      speed: playing.speed,
      timer: playing.timer,
      sessionToken: sessionToken,
      promptToken: prompt
    )

    let transition = reducer.reduce(
      state: awaiting,
      event: .continueOldContent(promptToken: prompt)
    )

    #expect(
      transition.state
        == .playing(
          document: document,
          cursor: awaiting.cursor,
          speed: awaiting.speed,
          timer: awaiting.timer,
          sessionToken: sessionToken
        )
    )
    #expect(
      transition.effects == [
        .resumeSpeech(
          document: document,
          cursor: awaiting.cursor,
          speed: awaiting.speed,
          token: sessionToken,
          rebuild: false
        ),
        .startClock(token: sessionToken),
      ]
    )
  }

  @Test("speech callbacks queued before the reload prompt are ignored")
  func promptIgnoresQueuedSpeechCallbacks() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: .zero)
    let sessionToken = try #require(playing.sessionToken)
    let document = try #require(playing.document)
    let awaiting = ReadingSessionState.awaitingReloadDecision(
      document: document,
      cursor: .zero,
      speed: playing.speed,
      timer: playing.timer,
      sessionToken: sessionToken,
      promptToken: ReloadPromptToken(
        rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000028")!
      )
    )

    let progress = reducer.reduce(
      state: awaiting,
      event: .cursorAdvanced(
        ReadingCursor(paragraphIndex: 0, utf16Offset: 5),
        token: sessionToken
      )
    )
    let finish = reducer.reduce(
      state: awaiting,
      event: .paragraphFinished(token: sessionToken)
    )

    #expect(progress == Transition(state: awaiting, effects: []))
    #expect(finish == Transition(state: awaiting, effects: []))
  }

  @Test("illegal events recover safely and record a fault in relaxed mode")
  func illegalEventRecoversWhenRelaxed() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let initial = ReadingSessionState.initial(timer: try TimerConfiguration(minutes: nil))

    let transition = reducer.reduce(state: initial, event: .pause)

    #expect(
      transition
        == Transition(
          state: .initial(timer: initial.timer, error: .internalFailure),
          effects: [.recordFault(.illegalTransition)]
        )
    )
  }

  @Test("a stale reload decision is ignored outside its prompt")
  func staleReloadDecisionIsIgnored() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let playing = try makePlaying(cursor: .zero)
    let stalePrompt = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000029")!
    )

    let transition = reducer.reduce(
      state: playing,
      event: .continueOldContent(promptToken: stalePrompt)
    )

    #expect(transition == Transition(state: playing, effects: []))
  }

  @Test("repeated play pause and stop commands are idempotent")
  func repeatedCommandsAreIdempotent() throws {
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let playing = try makePlaying(cursor: .zero)
    let token = try #require(playing.sessionToken)
    let paused = reducer.reduce(state: playing, event: .pause).state
    let ready = reducer.reduce(state: playing, event: .stop).state

    #expect(reducer.reduce(state: playing, event: .play(token: token)).effects.isEmpty)
    #expect(reducer.reduce(state: paused, event: .pause).effects.isEmpty)
    #expect(reducer.reduce(state: ready, event: .stop).effects.isEmpty)
  }

  @Test("a late paragraph completion after expiry cannot restart speech")
  func lateParagraphAfterExpiryIsIgnored() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let playing = try makePlaying(cursor: .zero)
    let token = try #require(playing.sessionToken)
    let ready = reducer.reduce(
      state: playing,
      event: .timerExpired(TimerExpiry(token: token))
    ).state

    let late = reducer.reduce(state: ready, event: .paragraphFinished(token: token))

    #expect(late == Transition(state: ready, effects: []))
  }

  @Test("document failures recover idle and dismiss clears the typed error")
  func documentFailureCanBeDismissed() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let timer = try TimerConfiguration(minutes: nil)
    let loadToken = token(7)
    let loading = ReadingSessionState.loading(
      speed: .normal,
      timer: timer,
      sessionToken: loadToken
    )

    let failed = reducer.reduce(
      state: loading,
      event: .documentLoadFailed(.corrupted, token: loadToken)
    )
    #expect(failed.state.mode == .idle)
    #expect(failed.state.error == .document(.corrupted))
    #expect(failed.effects.isEmpty)

    let dismissed = reducer.reduce(state: failed.state, event: .dismissError)
    #expect(dismissed == Transition(state: .initial(timer: timer), effects: []))
  }

  @Test("a document effect failure in an active session stops all resources")
  func activeDocumentEffectFailureStopsResources() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let playing = try makePlaying(cursor: .zero)
    let sessionToken = try #require(playing.sessionToken)

    let failed = reducer.reduce(
      state: playing,
      event: .effectFailed(.document(.corrupted), token: sessionToken)
    )

    #expect(
      failed.state
        == .initial(timer: playing.timer, error: .document(.corrupted))
    )
    #expect(failed.effects == stopEffects(token: sessionToken))
  }

  @Test("a current-session cursor callback cannot move progress backward")
  func cursorCannotMoveBackward() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let playing = try makePlaying(
      cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 5)
    )
    let sessionToken = try #require(playing.sessionToken)

    let transition = reducer.reduce(
      state: playing,
      event: .cursorAdvanced(
        ReadingCursor(paragraphIndex: 0, utf16Offset: 3),
        token: sessionToken
      )
    )

    #expect(transition == Transition(state: playing, effects: []))
  }

  @Test("an invalid current cursor recovers safely in relaxed mode")
  func invalidCursorRecoversWhenRelaxed() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let playing = try makePlaying(cursor: .zero)
    let document = try #require(playing.document)
    let sessionToken = try #require(playing.sessionToken)

    let transition = reducer.reduce(
      state: playing,
      event: .cursorAdvanced(
        ReadingCursor(paragraphIndex: 1, utf16Offset: 0),
        token: sessionToken
      )
    )

    #expect(
      transition.state
        == .ready(
          document: document,
          speed: playing.speed,
          timer: playing.timer,
          error: .internalFailure
        )
    )
    #expect(
      transition.effects == stopEffects(token: sessionToken)
        + [.recordFault(.invalidCursor)]
    )
  }

  @Test("every mode and event pair is deterministic and preserves invariants")
  func modeEventMatrixPreservesContracts() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let document = makeDocument()
    let timer = try TimerConfiguration(minutes: nil)
    let sessionToken = token(11)
    let promptUUID = try #require(
      UUID(uuidString: "00000000-0000-0000-0000-000000000012")
    )
    let promptToken = ReloadPromptToken(rawValue: promptUUID)
    let states: [ReadingSessionState] = [
      .initial(timer: timer),
      .loading(speed: .normal, timer: timer, sessionToken: sessionToken),
      .ready(document: document, speed: .normal, timer: timer),
      .playing(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: timer,
        sessionToken: sessionToken
      ),
      .paused(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: timer,
        sessionToken: sessionToken
      ),
      .awaitingReloadDecision(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: timer,
        sessionToken: sessionToken,
        promptToken: promptToken
      ),
    ]
    let events: [ReadingSessionEvent] = [
      .selectFile(document.source.url, token: token(13)),
      .documentLoaded(document, token: sessionToken, autoplay: false),
      .documentLoadFailed(.corrupted, token: sessionToken),
      .effectFailed(.speechFailure, token: sessionToken),
      .play(token: token(14)),
      .pause,
      .resume,
      .stop,
      .changeSpeed(.fast),
      .changeTimer(try TimerConfiguration(minutes: 10)),
      .cursorAdvanced(.zero, token: sessionToken),
      .paragraphFinished(token: sessionToken),
      .timerExpired(TimerExpiry(token: sessionToken)),
      .sourceChanged(promptToken: promptToken, sessionToken: sessionToken),
      .reloadSource(promptToken: promptToken, token: token(15)),
      .continueOldContent(promptToken: promptToken),
      .dismissError,
      .appTerminate,
    ]

    for state in states {
      for event in events {
        let first = reducer.reduce(state: state, event: event)
        let second = reducer.reduce(state: state, event: event)
        #expect(first == second)
        #expect(first.state.satisfiesInvariants)
        #expect(first.effects.filter(\.startsSpeech).count <= 1)
      }
    }
  }

  private func makePlaying(cursor: ReadingCursor) throws -> ReadingSessionState {
    ReadingSessionState.playing(
      document: makeDocument(),
      cursor: cursor,
      speed: .normal,
      timer: try TimerConfiguration(minutes: 30),
      sessionToken: token(3)
    )
  }

  private func makeDocument() -> LoadedDocument {
    LoadedDocument(
      source: ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/session.txt"),
        kind: .txt,
        fingerprint: SourceFingerprint(
          size: 11,
          modifiedAt: Date(timeIntervalSince1970: 0),
          resourceID: nil
        )
      ),
      paragraphs: [EnglishParagraph(text: "Hello world", ordinal: 0)]
    )
  }

  private func token(_ value: UInt8) -> ReadingSessionToken {
    let suffix = String(format: "%012x", value)
    return ReadingSessionToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
    )
  }

  private func stopEffects(token: ReadingSessionToken) -> [ReadingSessionEffect] {
    [
      .stopSpeech(token: token),
      .stopMonitor(token: token),
      .stopClock(token: token),
    ]
  }
}

extension ReadingSessionEffect {
  fileprivate var startsSpeech: Bool {
    if case .startSpeech = self { return true }
    return false
  }
}

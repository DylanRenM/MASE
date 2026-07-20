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
    #expect(paused.effects == [.freezeClock(token: playToken), .pauseSpeech(token: playToken)])

    let resumed = reducer.reduce(state: paused.state, event: .resume)
    #expect(resumed.state.mode == .playing)
    #expect(
      resumed.effects == [
        .resumeSpeech(token: playToken, rebuild: false),
        .startClock(token: playToken),
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

  @Test("an illegal active transition stops resources in relaxed mode")
  func illegalActiveTransitionStopsResources() throws {
    let reducer = ReadingSessionReducer(contractMode: .relaxed)
    let playing = try makePlaying(cursor: .zero)
    let document = try #require(playing.document)
    let sessionToken = try #require(playing.sessionToken)

    let transition = reducer.reduce(state: playing, event: .continueOldContent)

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
        + [.recordFault(.illegalTransition)]
    )
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
      .cursorAdvanced(.zero, token: sessionToken),
      .paragraphFinished(token: sessionToken),
      .timerExpired(TimerExpiry(token: sessionToken)),
      .sourceChanged(promptToken: promptToken, sessionToken: sessionToken),
      .reloadSource(token: token(15)),
      .continueOldContent,
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

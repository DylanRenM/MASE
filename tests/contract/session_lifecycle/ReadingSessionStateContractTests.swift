import Foundation
import Testing

@testable import MorerduoKit

@Suite("ReadingSessionState contract")
struct ReadingSessionStateContractTests {
  @Test("session mode has exactly the six specified values")
  func hasSixExclusiveModes() {
    #expect(
      SessionMode.allCases == [
        .idle,
        .loading,
        .ready,
        .playing,
        .paused,
        .awaitingReloadDecision,
      ]
    )
  }

  @Test("a new application session is idle with no resources")
  func initialStateIsIdle() throws {
    let state = ReadingSessionState.initial(
      timer: try TimerConfiguration(minutes: nil)
    )

    #expect(state.mode == .idle)
    #expect(state.document == nil)
    #expect(state.cursor == .zero)
    #expect(state.speed == .normal)
    #expect(state.sessionToken == nil)
    #expect(state.reloadPromptToken == nil)
    #expect(!state.isClockActive)
    #expect(state.satisfiesInvariants)
  }

  @Test("constructors produce valid loading and loaded states")
  func constructorsPreserveInvariants() throws {
    let timer = try TimerConfiguration(minutes: 30)
    let document = makeDocument()
    let sessionToken = ReadingSessionToken(rawValue: uuid(1))
    let promptToken = ReloadPromptToken(rawValue: uuid(2))
    let states = [
      ReadingSessionState.loading(
        speed: .normal,
        timer: timer,
        sessionToken: sessionToken
      ),
      ReadingSessionState.ready(document: document, speed: .slow, timer: timer),
      ReadingSessionState.playing(
        document: document,
        cursor: .zero,
        speed: .fast,
        timer: timer,
        sessionToken: sessionToken
      ),
      ReadingSessionState.paused(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: timer,
        sessionToken: sessionToken
      ),
      ReadingSessionState.awaitingReloadDecision(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: timer,
        sessionToken: sessionToken,
        promptToken: promptToken
      ),
    ]

    #expect(states.map(\.mode) == [.loading, .ready, .playing, .paused, .awaitingReloadDecision])
    #expect(states.allSatisfy { $0.satisfiesInvariants })
    #expect(states[2].isClockActive)
    #expect(!states[3].isClockActive)
    #expect(!states[4].isClockActive)
  }

  @Test("commands carry coordinator-generated tokens for pure reduction")
  func commandsCarryTokens() throws {
    let token = ReadingSessionToken(rawValue: uuid(6))
    let url = URL(fileURLWithPath: "/tmp/new-session.txt")
    let loading = ReadingSessionState.loading(
      speed: .normal,
      timer: try TimerConfiguration(minutes: nil),
      sessionToken: token
    )

    #expect(loading.sessionToken == token)
    #expect(ReadingSessionEvent.selectFile(url, token: token) == .selectFile(url, token: token))
    #expect(ReadingSessionEvent.play(token: token) == .play(token: token))
    #expect(ReadingSessionEvent.reloadSource(token: token) == .reloadSource(token: token))
  }

  @Test("module invariants reject inconsistent mode payloads")
  func rejectsInconsistentPayloads() throws {
    let document = makeDocument()
    let sessionToken = ReadingSessionToken(rawValue: uuid(3))
    let promptToken = ReloadPromptToken(rawValue: uuid(4))

    #expect(
      !ReadingSessionState.satisfiesInvariants(
        mode: .idle,
        document: document,
        cursor: .zero,
        sessionToken: nil,
        reloadPromptToken: nil
      )
    )
    #expect(
      !ReadingSessionState.satisfiesInvariants(
        mode: .playing,
        document: document,
        cursor: .zero,
        sessionToken: nil,
        reloadPromptToken: nil
      )
    )
    #expect(
      !ReadingSessionState.satisfiesInvariants(
        mode: .awaitingReloadDecision,
        document: document,
        cursor: .zero,
        sessionToken: sessionToken,
        reloadPromptToken: nil
      )
    )
    #expect(
      !ReadingSessionState.satisfiesInvariants(
        mode: .ready,
        document: document,
        cursor: ReadingCursor(paragraphIndex: 1, utf16Offset: 0),
        sessionToken: nil,
        reloadPromptToken: promptToken
      )
    )
  }

  @Test("events effects and transitions have deterministic value semantics")
  func publicTransitionTypesAreValues() throws {
    let token = ReadingSessionToken(rawValue: uuid(5))
    let state = ReadingSessionState.initial(
      timer: try TimerConfiguration(minutes: nil)
    )
    let event = ReadingSessionEvent.pause
    let effect = ReadingSessionEffect.freezeClock(token: token)
    let transition = Transition(state: state, effects: [effect])

    #expect(event == .pause)
    #expect(effect == .freezeClock(token: token))
    #expect(transition == Transition(state: state, effects: [effect]))
  }

  private func makeDocument() -> LoadedDocument {
    LoadedDocument(
      source: ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/session-fixture.txt"),
        kind: .txt,
        fingerprint: SourceFingerprint(
          size: 5,
          modifiedAt: Date(timeIntervalSince1970: 0),
          resourceID: nil
        )
      ),
      paragraphs: [EnglishParagraph(text: "Hello", ordinal: 0)]
    )
  }

  private func uuid(_ value: UInt8) -> UUID {
    let suffix = String(format: "%012x", value)
    return UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
  }
}

import Foundation
import MorerduoKit
import MorerduoTestSupport
import Testing

@Suite("Morerduo application effect executor")
struct MorerduoEffectExecutorTests {
  @MainActor
  @Test("loads and filters a document as one emitted domain result")
  func loadsAndFiltersDocument() async throws {
    let parsed = ParsedDocument(
      source: makeSource(),
      paragraphs: ["Hello, 世界 123", "Listen again!"]
    )
    let executor = MorerduoEffectExecutor(
      documentLoader: StubDocumentLoader(result: .success(parsed)),
      speech: FakeSpeechEngine(),
      monitor: FakeSourceMonitor()
    )
    let sessionToken = token(1)

    let event = try await executor.execute(
      .loadDocument(parsed.source.url, token: sessionToken, autoplay: false)
    )

    guard case .documentLoaded(let document, let emittedToken, let autoplay) = event else {
      Issue.record("expected a documentLoaded event")
      return
    }
    #expect(document.paragraphs.map(\.text) == ["Hello", "Listen again"])
    #expect(emittedToken == sessionToken)
    #expect(!autoplay)
  }

  @MainActor
  @Test("forwards speech completion as a paragraph event")
  func forwardsSpeechCompletion() async throws {
    let speech = FakeSpeechEngine()
    let executor = MorerduoEffectExecutor(
      documentLoader: StubDocumentLoader(result: .failure(.notReadable)),
      speech: speech,
      monitor: FakeSourceMonitor()
    )
    await executor.startEventForwarding()
    var events = executor.events.makeAsyncIterator()
    let sessionToken = token(2)

    _ = try await executor.execute(
      .startSpeech(
        document: makeDocument(),
        cursor: .zero,
        speed: .normal,
        token: sessionToken
      )
    )
    speech.finishActiveRequest()

    #expect(await events.next() == .paragraphFinished(token: sessionToken))
    await executor.shutdown()
  }

  @MainActor
  @Test("forwards source changes with a decision token")
  func forwardsSourceChanges() async throws {
    let monitor = FakeSourceMonitor()
    let executor = MorerduoEffectExecutor(
      documentLoader: StubDocumentLoader(result: .failure(.notReadable)),
      speech: FakeSpeechEngine(),
      monitor: monitor
    )
    await executor.startEventForwarding()
    var events = executor.events.makeAsyncIterator()
    let sessionToken = token(3)
    let source = makeSource()

    _ = try await executor.execute(
      .startMonitor(source: source, token: sessionToken)
    )
    monitor.emit(.write)

    guard
      case .sourceChanged(let promptToken, let emittedToken) = await events.next()
    else {
      Issue.record("expected a sourceChanged event")
      return
    }
    #expect(emittedToken == sessionToken)
    #expect(promptToken.rawValue != UUID())
    await executor.shutdown()
  }

  @MainActor
  @Test("forwards one timer expiry from accumulated playing time")
  func forwardsTimerExpiry() async throws {
    let clock = LockedReadingClock()
    let executor = MorerduoEffectExecutor(
      documentLoader: StubDocumentLoader(result: .failure(.notReadable)),
      speech: FakeSpeechEngine(),
      monitor: FakeSourceMonitor(),
      clock: clock,
      timerConfiguration: try TimerConfiguration(minutes: 1),
      timerPollingInterval: .milliseconds(10)
    )
    await executor.startEventForwarding()
    var events = executor.events.makeAsyncIterator()
    let sessionToken = token(4)

    _ = try await executor.execute(.startClock(token: sessionToken))
    clock.advance(by: .seconds(60))

    #expect(
      await events.next()
        == .timerExpired(TimerExpiry(token: sessionToken))
    )
    _ = try await executor.execute(.stopClock(token: sessionToken))
    await executor.shutdown()
  }

  private func makeDocument() -> LoadedDocument {
    LoadedDocument(
      source: makeSource(),
      paragraphs: [EnglishParagraph(text: "Hello world", ordinal: 0)]
    )
  }

  private func makeSource() -> ValidatedSource {
    ValidatedSource(
      url: URL(fileURLWithPath: "/tmp/executor.txt"),
      kind: .txt,
      fingerprint: SourceFingerprint(
        size: 32,
        modifiedAt: Date(timeIntervalSince1970: 0),
        resourceID: nil
      )
    )
  }

  private func token(_ value: UInt8) -> ReadingSessionToken {
    let suffix = String(format: "%012x", value)
    return ReadingSessionToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
    )
  }
}

private struct StubDocumentLoader: DocumentLoading {
  let result: Result<ParsedDocument, DocumentLoadError>

  func load(url: URL) async throws -> ParsedDocument {
    try result.get()
  }
}

private final class LockedReadingClock: ReadingClock, @unchecked Sendable {
  private let lock = NSLock()
  private var storedNow: Duration = .zero

  var now: Duration {
    lock.withLock { storedNow }
  }

  func advance(by duration: Duration) {
    lock.withLock { storedNow += duration }
  }
}

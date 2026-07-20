import Foundation
import Testing

@testable import MorerduoKit

@Suite("SessionCoordinator integration")
@MainActor
struct SessionCoordinatorTests {
  @Test("effects execute in reducer order")
  func effectsExecuteInOrder() async throws {
    let document = makeDocument()
    let timer = try TimerConfiguration(minutes: 30)
    let sessionToken = token(1)
    let executor = RecordingEffectExecutor()
    let coordinator = SessionCoordinator(
      initialState: .ready(document: document, speed: .normal, timer: timer),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    await coordinator.send(.play(token: sessionToken))
    let effects = await executor.effects

    #expect(
      effects == [
        .verifySource(document, token: sessionToken),
        .startSpeech(
          document: document,
          cursor: .zero,
          speed: .normal,
          token: sessionToken
        ),
        .startClock(token: sessionToken),
        .startMonitor(source: document.source, token: sessionToken),
      ]
    )
    #expect(coordinator.state.mode == .playing)
  }

  @Test("an adapter failure stops resources and recovers ready with a typed error")
  func adapterFailureRecoversReady() async throws {
    let document = makeDocument()
    let timer = try TimerConfiguration(minutes: 30)
    let sessionToken = token(2)
    let failingEffect = ReadingSessionEffect.startSpeech(
      document: document,
      cursor: .zero,
      speed: .normal,
      token: sessionToken
    )
    let executor = RecordingEffectExecutor(
      failure: .init(effect: failingEffect, error: .speechFailure)
    )
    let coordinator = SessionCoordinator(
      initialState: .ready(document: document, speed: .normal, timer: timer),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    await coordinator.send(.play(token: sessionToken))
    let effects = await executor.effects

    #expect(coordinator.state.mode == .ready)
    #expect(coordinator.state.document == document)
    #expect(coordinator.state.error == .speechFailure)
    #expect(
      effects == [
        .verifySource(document, token: sessionToken),
        failingEffect,
        .stopSpeech(token: sessionToken),
        .stopMonitor(token: sessionToken),
        .stopClock(token: sessionToken),
      ]
    )
  }

  @Test("a late document result cannot replace the current loading generation")
  func lateDocumentTokenIsIgnored() async throws {
    let currentToken = token(3)
    let executor = RecordingEffectExecutor()
    let coordinator = SessionCoordinator(
      initialState: .loading(
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil),
        sessionToken: currentToken
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    await coordinator.send(
      .documentLoaded(makeDocument(), token: token(4), autoplay: false)
    )
    let effects = await executor.effects

    #expect(coordinator.state.mode == .loading)
    #expect(coordinator.state.sessionToken == currentToken)
    #expect(effects.isEmpty)
  }

  @Test("rapid legal controls converge to the last event")
  func rapidControlsConverge() async throws {
    let document = makeDocument()
    let sessionToken = token(5)
    let executor = RecordingEffectExecutor()
    let coordinator = SessionCoordinator(
      initialState: .ready(
        document: document,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil)
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    await coordinator.send(.play(token: sessionToken))
    await coordinator.send(.pause)
    await coordinator.send(.resume)
    await coordinator.send(.pause)

    #expect(coordinator.state.mode == .paused)
    #expect(coordinator.state.sessionToken == sessionToken)
  }

  @Test("a queued stale resume after stop is harmless")
  func queuedStaleResumeAfterStopIsHarmless() async throws {
    let document = makeDocument()
    let sessionToken = token(17)
    let executor = CancellationObservingNonCooperativeExecutor()
    let coordinator = SessionCoordinator(
      initialState: .playing(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil),
        sessionToken: sessionToken
      ),
      reducer: ReadingSessionReducer(contractMode: .relaxed),
      effectExecutor: executor
    )

    let pause = Task { await coordinator.send(.pause) }
    await executor.waitUntilFirstEffectStarts()
    let stop = Task { await coordinator.send(.stop) }
    await executor.waitUntilCancellationIsObserved()
    let resume = Task { await coordinator.send(.resume) }
    await executor.releaseFirstEffect()
    await pause.value
    await stop.value
    await resume.value

    #expect(coordinator.state.mode == .ready)
    #expect(coordinator.state.error == nil)
  }

  @Test("a superseding stop cancels startup effects from the prior generation")
  func newEventCancelsPriorEffects() async throws {
    let document = makeDocument()
    let sessionToken = token(6)
    let executor = SuspendingEffectExecutor()
    let coordinator = SessionCoordinator(
      initialState: .ready(
        document: document,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil)
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    let firstSend = Task {
      await coordinator.send(.play(token: sessionToken))
    }
    await executor.waitUntilFirstEffectStarts()
    await coordinator.send(.stop)
    await firstSend.value
    let effects = await executor.effects

    #expect(coordinator.state.mode == .ready)
    #expect(effects.first == .verifySource(document, token: sessionToken))
    #expect(
      !effects.contains { effect in
        if case .startSpeech = effect { return true }
        return false
      })
    #expect(!effects.contains(.startMonitor(source: document.source, token: sessionToken)))
  }

  @Test("a non-cooperative cancelled effect finishes before the next batch starts")
  func nonCooperativeCancellationStaysSerial() async throws {
    let document = makeDocument()
    let sessionToken = token(7)
    let executor = NonCooperativeEffectExecutor()
    let coordinator = SessionCoordinator(
      initialState: .ready(
        document: document,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil)
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    let play = Task { await coordinator.send(.play(token: sessionToken)) }
    await executor.waitUntilFirstEffectStarts()
    let stop = Task { await coordinator.send(.stop) }
    for _ in 0..<20 { await Task.yield() }
    let beforeRelease = await executor.effects

    #expect(beforeRelease == [.verifySource(document, token: sessionToken)])

    await executor.releaseFirstEffect()
    await play.value
    await stop.value
    #expect(coordinator.state.mode == .ready)
  }

  @Test("a cancelled non-cooperative effect cannot publish a returned event")
  func cancelledNonCooperativeEffectCannotPublishEvent() async throws {
    let firstDocument = makeDocument()
    let firstToken = token(15)
    let secondToken = token(16)
    let secondURL = URL(fileURLWithPath: "/tmp/replacement.txt")
    let executor = NonCooperativeReturningExecutor(
      event: .documentLoaded(firstDocument, token: firstToken, autoplay: true)
    )
    let coordinator = SessionCoordinator(
      initialState: .initial(timer: try TimerConfiguration(minutes: nil)),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    let firstLoad = Task {
      await coordinator.send(.selectFile(firstDocument.source.url, token: firstToken))
    }
    await executor.waitUntilFirstEffectStarts()
    let replacementLoad = Task {
      await coordinator.send(.selectFile(secondURL, token: secondToken))
    }
    await executor.waitUntilCancellationIsObserved()
    await executor.releaseFirstEffect()
    await firstLoad.value
    await replacementLoad.value

    #expect(coordinator.state.mode == .loading)
    #expect(coordinator.state.sessionToken == secondToken)
    #expect(
      await executor.effects == [
        .loadDocument(firstDocument.source.url, token: firstToken, autoplay: false),
        .loadDocument(secondURL, token: secondToken, autoplay: false),
      ]
    )
  }

  @Test("cleanup failure does not skip remaining cleanup or the next load")
  func cleanupFailureContinuesBatch() async throws {
    let document = makeDocument()
    let oldToken = token(8)
    let newToken = token(9)
    let failedStop = ReadingSessionEffect.stopSpeech(token: oldToken)
    let executor = RecordingEffectExecutor(
      failure: .init(effect: failedStop, error: .speechFailure)
    )
    let coordinator = SessionCoordinator(
      initialState: .paused(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil),
        sessionToken: oldToken
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )
    let newURL = URL(fileURLWithPath: "/tmp/next.txt")

    await coordinator.send(.selectFile(newURL, token: newToken))
    let effects = await executor.effects

    #expect(
      effects == [
        failedStop,
        .stopMonitor(token: oldToken),
        .stopClock(token: oldToken),
        .loadDocument(newURL, token: newToken, autoplay: false),
      ]
    )
    #expect(coordinator.state.mode == .loading)
  }

  @Test("a superseding selection during cleanup skips the old load")
  func supersedingSelectionDuringCleanupSkipsOldLoad() async throws {
    let document = makeDocument()
    let oldToken = token(19)
    let firstLoadToken = token(20)
    let finalLoadToken = token(21)
    let firstURL = URL(fileURLWithPath: "/tmp/first-replacement.txt")
    let finalURL = URL(fileURLWithPath: "/tmp/final-replacement.txt")
    let executor = CleanupBlockingExecutor()
    let coordinator = SessionCoordinator(
      initialState: .paused(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil),
        sessionToken: oldToken
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    let firstSelection = Task {
      await coordinator.send(.selectFile(firstURL, token: firstLoadToken))
    }
    await executor.waitUntilFirstCleanupStarts()
    let releaseCleanup = Task { await executor.releaseFirstCleanup() }
    await coordinator.send(.selectFile(finalURL, token: finalLoadToken))
    await releaseCleanup.value
    await firstSelection.value

    #expect(coordinator.state.mode == .loading)
    #expect(coordinator.state.sessionToken == finalLoadToken)
    #expect(
      await executor.effects == [
        .stopSpeech(token: oldToken),
        .stopMonitor(token: oldToken),
        .stopClock(token: oldToken),
        .loadDocument(finalURL, token: finalLoadToken, autoplay: false),
      ]
    )
  }

  @Test("an untyped source verification failure maps to source unavailable")
  func untypedVerifyFailureUsesEffectContext() async throws {
    let document = makeDocument()
    let sessionToken = token(10)
    let coordinator = SessionCoordinator(
      initialState: .ready(
        document: document,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil)
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: UntypedFailingEffectExecutor()
    )

    await coordinator.send(.play(token: sessionToken))

    #expect(coordinator.state.mode == .idle)
    #expect(coordinator.state.document == nil)
    #expect(coordinator.state.error == .sourceUnavailable)
  }

  @Test("deleting a ready source makes real play verification return idle")
  func deletedReadySourceCannotPlay() async throws {
    let directory = FileManager.default.temporaryDirectory
      .appendingPathComponent("morerduo-ready-delete-\(UUID().uuidString)", isDirectory: true)
    try FileManager.default.createDirectory(
      at: directory,
      withIntermediateDirectories: true
    )
    defer { try? FileManager.default.removeItem(at: directory) }
    let url = directory.appendingPathComponent("ready.txt")
    try Data("Hello world".utf8).write(to: url)
    let source = try FilePolicy.validate(url: url)
    let document = LoadedDocument(
      source: source,
      paragraphs: [EnglishParagraph(text: "Hello world", ordinal: 0)]
    )
    try FileManager.default.removeItem(at: url)
    let coordinator = SessionCoordinator(
      initialState: .ready(
        document: document,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil)
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: RealSourceVerifyingExecutor()
    )

    await coordinator.send(.play(token: token(25)))

    #expect(coordinator.state.mode == .idle)
    #expect(coordinator.state.document == nil)
    #expect(coordinator.state.error == .sourceUnavailable)
  }

  @Test("an executor result is reduced without a side-channel callback")
  func executorCanReturnDomainEvent() async throws {
    let document = makeDocument()
    let loadToken = token(11)
    let coordinator = SessionCoordinator(
      initialState: .initial(timer: try TimerConfiguration(minutes: nil)),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: DocumentCompletingEffectExecutor(document: document)
    )

    await coordinator.send(.selectFile(document.source.url, token: loadToken))

    #expect(coordinator.state.mode == .ready)
    #expect(coordinator.state.document == document)
  }

  @Test("reload completion atomically starts new content from the beginning")
  func reloadCompletionStartsNewContent() async throws {
    let oldDocument = makeDocument()
    let oldToken = token(21)
    let newToken = token(22)
    let executor = RecordingEffectExecutor()
    let awaiting = ReadingSessionState.awaitingReloadDecision(
      document: oldDocument,
      cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 5),
      speed: .fast,
      timer: try TimerConfiguration(minutes: 30),
      sessionToken: oldToken,
      promptToken: ReloadPromptToken(
        rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000021")!
      )
    )
    let coordinator = SessionCoordinator(
      initialState: awaiting,
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    await coordinator.send(
      .reloadSource(
        promptToken: try #require(awaiting.reloadPromptToken),
        token: newToken
      )
    )
    let newDocument = makeDocument()
    await coordinator.send(
      .documentLoaded(newDocument, token: newToken, autoplay: true)
    )

    #expect(coordinator.state.mode == .playing)
    #expect(coordinator.state.document == newDocument)
    #expect(coordinator.state.cursor == .zero)
    #expect(coordinator.state.sessionToken == newToken)
    #expect(
      await executor.effects == [
        .stopSpeech(token: oldToken),
        .stopMonitor(token: oldToken),
        .stopClock(token: oldToken),
        .loadDocument(oldDocument.source.url, token: newToken, autoplay: true),
        .verifySource(newDocument, token: newToken),
        .startSpeech(
          document: newDocument,
          cursor: .zero,
          speed: .fast,
          token: newToken
        ),
        .startClock(token: newToken),
        .startMonitor(source: newDocument.source, token: newToken),
      ]
    )
  }

  @Test("reload failure discards the old in-memory session")
  func reloadFailureReturnsIdle() async throws {
    let document = makeDocument()
    let oldToken = token(23)
    let newToken = token(24)
    let promptToken = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000023")!
    )
    let coordinator = SessionCoordinator(
      initialState: .awaitingReloadDecision(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil),
        sessionToken: oldToken,
        promptToken: promptToken
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: RecordingEffectExecutor()
    )

    await coordinator.send(
      .reloadSource(promptToken: promptToken, token: newToken)
    )
    await coordinator.send(.documentLoadFailed(.corrupted, token: newToken))

    #expect(coordinator.state.mode == .idle)
    #expect(coordinator.state.document == nil)
    #expect(coordinator.state.error == .document(.corrupted))
  }

  @Test("a returned event supersedes the current effect batch")
  func returnedEventSupersedesCurrentBatch() async throws {
    let document = makeDocument()
    let sessionToken = token(18)
    let returnedEvent = ReadingSessionEvent.stop
    let executor = EventReturningExecutor(
      matching: .verifySource(document, token: sessionToken),
      event: returnedEvent
    )
    let coordinator = SessionCoordinator(
      initialState: .ready(
        document: document,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil)
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    await coordinator.send(.play(token: sessionToken))

    #expect(coordinator.state.mode == .ready)
    #expect(
      await executor.effects == [
        .verifySource(document, token: sessionToken),
        .stopSpeech(token: sessionToken),
        .stopMonitor(token: sessionToken),
        .stopClock(token: sessionToken),
      ]
    )
  }

  @Test("a late expiry cannot cancel the current session startup")
  func lateExpiryDoesNotCancelCurrentStartup() async throws {
    let document = makeDocument()
    let currentToken = token(12)
    let executor = NonCooperativeEffectExecutor()
    let coordinator = SessionCoordinator(
      initialState: .ready(
        document: document,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil)
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    let play = Task { await coordinator.send(.play(token: currentToken)) }
    await executor.waitUntilFirstEffectStarts()
    let lateExpiry = Task {
      await coordinator.send(.timerExpired(TimerExpiry(token: token(13))))
    }
    for _ in 0..<20 { await Task.yield() }
    #expect(await executor.effects.count == 1)

    await executor.releaseFirstEffect()
    await play.value
    await lateExpiry.value
    #expect(coordinator.state.mode == .playing)
    #expect(coordinator.state.sessionToken == currentToken)
    #expect(
      await executor.effects == [
        .verifySource(document, token: currentToken),
        .startSpeech(
          document: document,
          cursor: .zero,
          speed: .normal,
          token: currentToken
        ),
        .startClock(token: currentToken),
        .startMonitor(source: document.source, token: currentToken),
      ]
    )
  }

  @Test("a cancelled startup error cannot overwrite a superseding stop")
  func cancelledErrorCannotRecoverOldGeneration() async throws {
    let document = makeDocument()
    let sessionToken = token(14)
    let executor = CancelledThenFailingExecutor()
    let coordinator = SessionCoordinator(
      initialState: .ready(
        document: document,
        speed: .normal,
        timer: try TimerConfiguration(minutes: nil)
      ),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    let play = Task { await coordinator.send(.play(token: sessionToken)) }
    await executor.waitUntilFirstEffectStarts()
    let stop = Task { await coordinator.send(.stop) }
    await executor.waitUntilCancellationIsObserved()
    await executor.releaseWithFailure()
    await play.value
    await stop.value

    #expect(coordinator.state.mode == .ready)
    #expect(coordinator.state.error == nil)
  }

  private func makeDocument() -> LoadedDocument {
    LoadedDocument(
      source: ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/coordinator.txt"),
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
}

private actor RecordingEffectExecutor: ReadingSessionEffectExecuting {
  struct Failure: Sendable {
    let effect: ReadingSessionEffect
    let error: UserFacingError
  }

  private(set) var effects: [ReadingSessionEffect] = []
  private let failure: Failure?

  init(failure: Failure? = nil) {
    self.failure = failure
  }

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    effects.append(effect)
    if let failure, failure.effect == effect {
      throw ReadingSessionEffectExecutionError.userFacing(failure.error)
    }
    return nil
  }
}

private actor SuspendingEffectExecutor: ReadingSessionEffectExecuting {
  private(set) var effects: [ReadingSessionEffect] = []
  private var hasStarted = false

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    effects.append(effect)
    guard !hasStarted else {
      return nil
    }
    hasStarted = true
    while !Task.isCancelled {
      await Task.yield()
    }
    throw CancellationError()
  }

  func waitUntilFirstEffectStarts() async {
    while !hasStarted {
      await Task.yield()
    }
  }
}

private actor NonCooperativeReturningExecutor: ReadingSessionEffectExecuting {
  private(set) var effects: [ReadingSessionEffect] = []
  private var hasStarted = false
  private var hasObservedCancellation = false
  private var continuation: CheckedContinuation<Void, Never>?
  private let event: ReadingSessionEvent

  init(event: ReadingSessionEvent) {
    self.event = event
  }

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    effects.append(effect)
    guard !hasStarted else { return nil }
    hasStarted = true
    while !Task.isCancelled { await Task.yield() }
    hasObservedCancellation = true
    await withCheckedContinuation { continuation in
      self.continuation = continuation
    }
    return event
  }

  func waitUntilFirstEffectStarts() async {
    while !hasStarted { await Task.yield() }
  }

  func waitUntilCancellationIsObserved() async {
    while !hasObservedCancellation { await Task.yield() }
  }

  func releaseFirstEffect() {
    continuation?.resume()
    continuation = nil
  }
}

private actor CancellationObservingNonCooperativeExecutor:
  ReadingSessionEffectExecuting
{
  private var hasStarted = false
  private var hasObservedCancellation = false
  private var continuation: CheckedContinuation<Void, Never>?

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    guard !hasStarted else { return nil }
    hasStarted = true
    while !Task.isCancelled { await Task.yield() }
    hasObservedCancellation = true
    await withCheckedContinuation { continuation in
      self.continuation = continuation
    }
    return nil
  }

  func waitUntilFirstEffectStarts() async {
    while !hasStarted { await Task.yield() }
  }

  func waitUntilCancellationIsObserved() async {
    while !hasObservedCancellation { await Task.yield() }
  }

  func releaseFirstEffect() {
    continuation?.resume()
    continuation = nil
  }
}

private actor CleanupBlockingExecutor: ReadingSessionEffectExecuting {
  private(set) var effects: [ReadingSessionEffect] = []
  private var hasStarted = false
  private var continuation: CheckedContinuation<Void, Never>?

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    effects.append(effect)
    guard !hasStarted else { return nil }
    hasStarted = true
    await withCheckedContinuation { continuation in
      self.continuation = continuation
    }
    return nil
  }

  func waitUntilFirstCleanupStarts() async {
    while !hasStarted { await Task.yield() }
  }

  func releaseFirstCleanup() {
    continuation?.resume()
    continuation = nil
  }
}

private actor NonCooperativeEffectExecutor: ReadingSessionEffectExecuting {
  private(set) var effects: [ReadingSessionEffect] = []
  private var hasStarted = false
  private var continuation: CheckedContinuation<Void, Never>?

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    effects.append(effect)
    guard !hasStarted else { return nil }
    hasStarted = true
    await withCheckedContinuation { continuation in
      self.continuation = continuation
    }
    return nil
  }

  func waitUntilFirstEffectStarts() async {
    while !hasStarted { await Task.yield() }
  }

  func releaseFirstEffect() {
    continuation?.resume()
    continuation = nil
  }
}

private struct UntypedFailingEffectExecutor: ReadingSessionEffectExecuting {
  private struct ProbeError: Error {}

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    throw ProbeError()
  }
}

private struct RealSourceVerifyingExecutor: ReadingSessionEffectExecuting {
  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    guard case .verifySource(let document, _) = effect else { return nil }
    try SourceAvailabilityVerifier.verify(document.source)
    return nil
  }
}

private struct DocumentCompletingEffectExecutor: ReadingSessionEffectExecuting {
  let document: LoadedDocument

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    guard case .loadDocument(_, let token, let autoplay) = effect else {
      return nil
    }
    return .documentLoaded(document, token: token, autoplay: autoplay)
  }
}

private actor EventReturningExecutor: ReadingSessionEffectExecuting {
  private(set) var effects: [ReadingSessionEffect] = []
  private let matchingEffect: ReadingSessionEffect
  private let event: ReadingSessionEvent

  init(matching: ReadingSessionEffect, event: ReadingSessionEvent) {
    matchingEffect = matching
    self.event = event
  }

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    effects.append(effect)
    return effect == matchingEffect ? event : nil
  }
}

private actor CancelledThenFailingExecutor: ReadingSessionEffectExecuting {
  private var hasStarted = false
  private var hasObservedCancellation = false
  private var continuation: CheckedContinuation<Void, Never>?

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    guard !hasStarted else { return nil }
    hasStarted = true
    while !Task.isCancelled { await Task.yield() }
    hasObservedCancellation = true
    await withCheckedContinuation { continuation in
      self.continuation = continuation
    }
    throw ReadingSessionEffectExecutionError.userFacing(.speechFailure)
  }

  func waitUntilFirstEffectStarts() async {
    while !hasStarted { await Task.yield() }
  }

  func waitUntilCancellationIsObserved() async {
    while !hasObservedCancellation { await Task.yield() }
  }

  func releaseWithFailure() {
    continuation?.resume()
    continuation = nil
  }
}

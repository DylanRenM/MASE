import Foundation
import Testing

@testable import MorerduoKit

@Suite("ReadingSessionEffectExecuting contract")
@MainActor
struct ReadingSessionEffectExecutingContractTests {
  @Test("a returned event supersedes the original effect batch")
  func returnedEventSupersedesBatch() async throws {
    let document = makeDocument()
    let sessionToken = token(1)
    let verifyEffect = ReadingSessionEffect.verifySource(
      document,
      token: sessionToken
    )
    let executor = ContractRecordingExecutor(
      returnedEvent: .init(effect: verifyEffect, event: .stop)
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
        verifyEffect,
        .stopSpeech(token: sessionToken),
        .stopMonitor(token: sessionToken),
        .stopClock(token: sessionToken),
      ]
    )
  }

  @Test("a cancelled effect result cannot modify the superseding generation")
  func cancelledResultIsDiscarded() async throws {
    let document = makeDocument()
    let firstToken = token(2)
    let finalToken = token(3)
    let finalURL = URL(fileURLWithPath: "/tmp/contract-final.txt")
    let executor = ContractCancelledReturningExecutor(
      event: .documentLoaded(document, token: firstToken, autoplay: true)
    )
    let coordinator = SessionCoordinator(
      initialState: .initial(timer: try TimerConfiguration(minutes: nil)),
      reducer: ReadingSessionReducer(contractMode: .strict),
      effectExecutor: executor
    )

    let firstLoad = Task {
      await coordinator.send(.selectFile(document.source.url, token: firstToken))
    }
    await executor.waitUntilFirstEffectStarts()
    let release = Task {
      await executor.waitUntilCancellationIsObserved()
      await executor.releaseFirstEffect()
    }
    await coordinator.send(.selectFile(finalURL, token: finalToken))
    await release.value
    await firstLoad.value

    #expect(coordinator.state.mode == .loading)
    #expect(coordinator.state.sessionToken == finalToken)
    #expect(
      await executor.effects == [
        .loadDocument(document.source.url, token: firstToken, autoplay: false),
        .loadDocument(finalURL, token: finalToken, autoplay: false),
      ]
    )
  }

  @Test("cleanup remains best effort when one adapter call fails")
  func cleanupFailureDoesNotSkipRemainingEffects() async throws {
    let document = makeDocument()
    let oldToken = token(4)
    let newToken = token(5)
    let newURL = URL(fileURLWithPath: "/tmp/contract-next.txt")
    let failedEffect = ReadingSessionEffect.stopSpeech(token: oldToken)
    let executor = ContractRecordingExecutor(failingEffect: failedEffect)
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

    await coordinator.send(.selectFile(newURL, token: newToken))

    #expect(
      await executor.effects == [
        failedEffect,
        .stopMonitor(token: oldToken),
        .stopClock(token: oldToken),
        .loadDocument(newURL, token: newToken, autoplay: false),
      ]
    )
  }

  private func makeDocument() -> LoadedDocument {
    LoadedDocument(
      source: ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/contract-executor.txt"),
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

  private func token(_ value: UInt8) -> ReadingSessionToken {
    let suffix = String(format: "%012x", value)
    return ReadingSessionToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
    )
  }
}

private actor ContractRecordingExecutor: ReadingSessionEffectExecuting {
  struct ReturnedEvent: Sendable {
    let effect: ReadingSessionEffect
    let event: ReadingSessionEvent
  }

  private(set) var effects: [ReadingSessionEffect] = []
  private let failingEffect: ReadingSessionEffect?
  private let returnedEvent: ReturnedEvent?

  init(
    failingEffect: ReadingSessionEffect? = nil,
    returnedEvent: ReturnedEvent? = nil
  ) {
    self.failingEffect = failingEffect
    self.returnedEvent = returnedEvent
  }

  func execute(_ effect: ReadingSessionEffect) async throws -> ReadingSessionEvent? {
    effects.append(effect)
    if effect == failingEffect {
      throw ReadingSessionEffectExecutionError.userFacing(.speechFailure)
    }
    if let returnedEvent, effect == returnedEvent.effect {
      return returnedEvent.event
    }
    return nil
  }
}

private actor ContractCancelledReturningExecutor: ReadingSessionEffectExecuting {
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

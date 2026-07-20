import AVFoundation
import Foundation
import Testing

@testable import MorerduoKit

@Suite("AVSpeechEngine integration")
@MainActor
struct AVSpeechEngineTests {
  @Test("start configures the requested text English voice and centralized rate")
  func startConfiguresUtterance() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let voice = try #require(AVSpeechSynthesisVoice(language: "en-US"))
    let engine = AVSpeechEngine(synthesizer: system, voiceProvider: { voice })
    let request = try makeRequest(text: "Hello world", offset: 6, requestID: 1)

    try await engine.start(request)
    let utterance = try #require(system.spokenUtterances.first)

    #expect(utterance.speechString == "world")
    #expect(utterance.voice?.identifier == voice.identifier)
    #expect(utterance.rate == SpeechRateConfiguration.rate(for: .fast))
    #expect(engine.activeRequest == request)
  }

  @Test("a delegate range maps to the original paragraph UTF-16 range")
  func rangeMapsToOriginalParagraph() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let request = try makeRequest(text: "Hello world", offset: 6, requestID: 2)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(request)
    let utterance = try #require(system.spokenUtterances.first)
    system.emitProgress(NSRange(location: 0, length: 5), for: utterance)

    let event = try #require(await events.next())
    guard case .progressed(let progress) = event else {
      Issue.record("expected a progress event")
      return
    }
    #expect(progress.requestUTF16Range == 0..<5)
    #expect(progress.originalParagraphUTF16Range == 6..<11)
    #expect(progress.safeResumeUTF16Offset == 6)
    #expect(progress.paragraphOrdinal == 0)
    #expect(progress.requestToken == request.requestToken)
  }

  @Test("out-of-order ranges cannot move the safe boundary backward")
  func outOfOrderRangeIsIgnored() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let request = try makeRequest(text: "Hello world", offset: 0, requestID: 16)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(request)
    let utterance = try #require(system.spokenUtterances.first)
    system.emitProgress(NSRange(location: 6, length: 5), for: utterance)
    guard case .progressed(let first) = await events.next() else {
      Issue.record("expected the first forward range")
      return
    }
    system.emitProgress(NSRange(location: 0, length: 5), for: utterance)
    system.emitProgress(NSRange(location: 7, length: 4), for: utterance)
    guard case .progressed(let second) = await events.next() else {
      Issue.record("expected the next forward range")
      return
    }

    #expect(first.safeResumeUTF16Offset == 6)
    #expect(second.safeResumeUTF16Offset == 7)
  }

  @Test("an out-of-bounds system range is ignored")
  func invalidSystemRangeIsIgnored() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let request = try makeRequest(text: "Hello", offset: 0, requestID: 12)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(request)
    let utterance = try #require(system.spokenUtterances.first)
    system.emitProgress(NSRange(location: 4, length: 2), for: utterance)
    system.emitProgress(NSRange(location: 0, length: 5), for: utterance)

    guard case .progressed(let progress) = await events.next() else {
      Issue.record("expected the valid range after ignoring the invalid callback")
      return
    }
    #expect(progress.requestUTF16Range == 0..<5)
  }

  @Test("finishing the active utterance emits one identity-bound event")
  func finishEmitsIdentityBoundEvent() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let request = try makeRequest(text: "Hello", offset: 0, requestID: 3)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(request)
    let utterance = try #require(system.spokenUtterances.first)
    system.emitFinish(for: utterance)

    #expect(
      await events.next()
        == .finished(
          sessionToken: request.sessionToken,
          requestToken: request.requestToken
        )
    )
    #expect(engine.activeRequest == nil)
  }

  @Test("an old utterance callback cannot finish the new request")
  func oldUtteranceCannotFinishNewRequest() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let first = try makeRequest(text: "Hello", offset: 0, requestID: 4)
    let second = try makeRequest(text: "World", offset: 0, requestID: 5)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(first)
    let oldUtterance = try #require(system.spokenUtterances.last)
    system.emitFinish(for: oldUtterance)
    _ = await events.next()

    try await engine.start(second)
    let currentUtterance = try #require(system.spokenUtterances.last)
    system.emitFinish(for: oldUtterance)
    system.emitProgress(NSRange(location: 0, length: 5), for: currentUtterance)

    guard case .progressed(let progress) = await events.next() else {
      Issue.record("expected progress for the current utterance")
      return
    }
    #expect(progress.requestToken == second.requestToken)
    #expect(engine.activeRequest == second)
  }

  @Test("stop retires identity before a late delegate callback")
  func stopRetiresIdentityBeforeLateCallback() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let first = try makeRequest(text: "Hello", offset: 0, requestID: 6)
    let second = try makeRequest(text: "World", offset: 0, requestID: 7)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(first)
    let oldUtterance = try #require(system.spokenUtterances.last)
    await engine.stop()
    _ = await events.next()
    system.emitProgress(NSRange(location: 0, length: 5), for: oldUtterance)

    try await engine.start(second)
    let currentUtterance = try #require(system.spokenUtterances.last)
    system.emitProgress(NSRange(location: 0, length: 5), for: currentUtterance)

    guard case .progressed(let progress) = await events.next() else {
      Issue.record("expected progress for the replacement request")
      return
    }
    #expect(progress.requestToken == second.requestToken)
    #expect(system.stopCalls == 1)
  }

  @Test("start fails with a typed error when no English voice exists")
  func missingVoiceIsTypedFailure() async throws {
    let engine = AVSpeechEngine(
      synthesizer: FakeSystemSpeechSynthesizer(),
      voiceProvider: { nil }
    )

    await #expect(throws: SpeechEngineError.unavailable) {
      try await engine.start(
        makeRequest(text: "Hello", offset: 0, requestID: 8)
      )
    }
    #expect(engine.activeRequest == nil)
  }

  @Test("pause and unchanged-speed resume retain the system utterance")
  func pauseAndResumeRetainUtterance() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let request = try makeRequest(text: "Hello world", offset: 0, requestID: 9)

    try await engine.start(request)
    try await engine.pause()
    #expect(system.lastPauseBoundary == .immediate)
    try await engine.resume(rebuildingWith: nil)

    #expect(system.pauseCalls == 1)
    #expect(system.continueCalls == 1)
    #expect(system.spokenUtterances.count == 1)
    #expect(engine.activeRequest == request)
  }

  @Test("a range callback cannot advance progress while paused")
  func pausedRangeIsIgnored() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let request = try makeRequest(text: "Hello", offset: 0, requestID: 13)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(request)
    let utterance = try #require(system.spokenUtterances.first)
    try await engine.pause()
    system.emitProgress(NSRange(location: 0, length: 2), for: utterance)
    try await engine.resume(rebuildingWith: nil)
    system.emitProgress(NSRange(location: 0, length: 5), for: utterance)

    guard case .progressed(let progress) = await events.next() else {
      Issue.record("expected progress only after resume")
      return
    }
    #expect(progress.requestUTF16Range == 0..<5)
  }

  @Test("paused speed change replaces speech with the unread suffix")
  func speedChangeRebuildsUnreadSuffix() async throws {
    let system = FakeSystemSpeechSynthesizer()
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let original = try makeRequest(text: "Hello world", offset: 0, requestID: 10)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(original)
    let originalUtterance = try #require(system.spokenUtterances.last)
    system.emitProgress(NSRange(location: 6, length: 5), for: originalUtterance)
    guard case .progressed(let progress) = await events.next() else {
      Issue.record("expected a safe word boundary")
      return
    }
    let replacement = try makeRequest(
      text: "Hello world",
      offset: progress.safeResumeUTF16Offset,
      requestID: 11
    )
    try await engine.pause()
    try await engine.resume(rebuildingWith: replacement)
    let currentUtterance = try #require(system.spokenUtterances.last)
    system.emitProgress(NSRange(location: 0, length: 5), for: currentUtterance)

    #expect(system.stopCalls == 1)
    #expect(system.continueCalls == 0)
    #expect(system.spokenUtterances.map(\.speechString) == ["Hello world", "world"])
    #expect(engine.activeRequest == replacement)
    #expect(
      await events.next()
        == .cancelled(
          sessionToken: original.sessionToken,
          requestToken: original.requestToken
        )
    )
  }

  @Test("failed rebuild stop remains recoverable by cleanup")
  func failedRebuildStopCanBeRetried() async throws {
    let system = FakeSystemSpeechSynthesizer()
    system.stopResult = false
    let engine = AVSpeechEngine(
      synthesizer: system,
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
    let original = try makeRequest(text: "Hello world", offset: 0, requestID: 14)
    let replacement = try makeRequest(text: "Hello world", offset: 6, requestID: 15)

    try await engine.start(original)
    try await engine.pause()
    await #expect(throws: SpeechEngineError.synthesisFailed) {
      try await engine.resume(rebuildingWith: replacement)
    }
    system.stopResult = true
    await engine.stop()

    #expect(system.stopCalls == 2)
    #expect(engine.activeRequest == nil)
    #expect(system.spokenUtterances.count == 1)
  }

  private func makeRequest(
    text: String,
    offset: Int,
    requestID: UInt8
  ) throws -> SpeechRequest {
    try SpeechRequest(
      paragraph: EnglishParagraph(text: text, ordinal: 0),
      utf16Offset: offset,
      speed: .fast,
      sessionToken: ReadingSessionToken(rawValue: uuid(1)),
      requestToken: SpeechRequestToken(rawValue: uuid(requestID))
    )
  }

  private func uuid(_ value: UInt8) -> UUID {
    let suffix = String(format: "%012x", value)
    return UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
  }
}

@MainActor
private final class FakeSystemSpeechSynthesizer: SystemSpeechSynthesizing {
  weak var delegate: AVSpeechSynthesizerDelegate?
  private(set) var spokenUtterances: [AVSpeechUtterance] = []
  private(set) var stopCalls = 0
  private(set) var pauseCalls = 0
  private(set) var continueCalls = 0
  private(set) var lastPauseBoundary: AVSpeechBoundary?
  var stopResult = true

  func speak(_ utterance: AVSpeechUtterance) {
    spokenUtterances.append(utterance)
  }

  func pauseSpeaking(at boundary: AVSpeechBoundary) -> Bool {
    pauseCalls += 1
    lastPauseBoundary = boundary
    return true
  }

  func continueSpeaking() -> Bool {
    continueCalls += 1
    return true
  }

  func stopSpeaking(at boundary: AVSpeechBoundary) -> Bool {
    stopCalls += 1
    return stopResult
  }

  func emitProgress(_ range: NSRange, for utterance: AVSpeechUtterance) {
    delegate?.speechSynthesizer?(
      AVSpeechSynthesizer(),
      willSpeakRangeOfSpeechString: range,
      utterance: utterance
    )
  }

  func emitFinish(for utterance: AVSpeechUtterance) {
    delegate?.speechSynthesizer?(
      AVSpeechSynthesizer(),
      didFinish: utterance
    )
  }
}

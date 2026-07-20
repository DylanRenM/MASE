@preconcurrency import AVFoundation
import Foundation

@MainActor
public final class AVSpeechEngine: NSObject, SpeechSynthesizing,
  AVSpeechSynthesizerDelegate
{
  public nonisolated let events: AsyncStream<SpeechEvent>
  public private(set) var activeRequest: SpeechRequest?

  private let synthesizer: any SystemSpeechSynthesizing
  private let voiceProvider: @MainActor () -> AVSpeechSynthesisVoice?
  private let continuation: AsyncStream<SpeechEvent>.Continuation
  private let progressGate = SpeechProgressCallbackGate()
  private var activeUtteranceID: ObjectIdentifier?
  private var activeProgressGeneration: UInt64?
  private var isPaused = false
  private var lastSafeRequestUTF16Offset = 0

  public override convenience init() {
    self.init(
      synthesizer: AVSpeechSynthesizer(),
      voiceProvider: { AVSpeechSynthesisVoice(language: "en-US") }
    )
  }

  init(
    synthesizer: any SystemSpeechSynthesizing,
    voiceProvider: @escaping @MainActor () -> AVSpeechSynthesisVoice?
  ) {
    let pair = AsyncStream.makeStream(of: SpeechEvent.self)
    events = pair.stream
    continuation = pair.continuation
    self.synthesizer = synthesizer
    self.voiceProvider = voiceProvider
    super.init()
    synthesizer.delegate = self
  }

  deinit {
    continuation.finish()
  }

  public func start(_ request: SpeechRequest) async throws {
    guard activeRequest == nil else {
      throw SpeechEngineError.alreadyActive
    }
    guard let voice = voiceProvider() else {
      throw SpeechEngineError.unavailable
    }
    let utterance = AVSpeechUtterance(string: request.text)
    utterance.voice = voice
    utterance.rate = SpeechRateConfiguration.rate(for: request.speed)
    activeRequest = request
    activeUtteranceID = ObjectIdentifier(utterance)
    activeProgressGeneration = progressGate.open()
    isPaused = false
    lastSafeRequestUTF16Offset = 0
    synthesizer.speak(utterance)
  }

  public func pause() async throws {
    guard activeRequest != nil else {
      throw SpeechEngineError.noActiveRequest
    }
    if isPaused { return }
    activeProgressGeneration = progressGate.close()
    guard synthesizer.pauseSpeaking(at: .immediate) else {
      activeProgressGeneration = progressGate.open()
      throw SpeechEngineError.synthesisFailed
    }
    isPaused = true
  }

  public func resume(rebuildingWith request: SpeechRequest?) async throws {
    guard activeRequest != nil else {
      throw SpeechEngineError.noActiveRequest
    }
    if let request {
      let retiredRequest = retireActiveRequest()
      let didStop = synthesizer.stopSpeaking(at: .immediate)
      if let retiredRequest {
        continuation.yield(
          .cancelled(
            sessionToken: retiredRequest.sessionToken,
            requestToken: retiredRequest.requestToken
          )
        )
      }
      guard didStop else {
        throw SpeechEngineError.synthesisFailed
      }
      try await start(request)
      return
    }
    if !isPaused { return }
    activeProgressGeneration = progressGate.open()
    guard synthesizer.continueSpeaking() else {
      activeProgressGeneration = progressGate.close()
      throw SpeechEngineError.synthesisFailed
    }
    isPaused = false
  }

  public func stop() async {
    let request = retireActiveRequest()
    _ = synthesizer.stopSpeaking(at: .immediate)
    guard let request else { return }
    continuation.yield(
      .cancelled(
        sessionToken: request.sessionToken,
        requestToken: request.requestToken
      )
    )
  }

  nonisolated public func speechSynthesizer(
    _ synthesizer: AVSpeechSynthesizer,
    willSpeakRangeOfSpeechString characterRange: NSRange,
    utterance: AVSpeechUtterance
  ) {
    let utteranceID = ObjectIdentifier(utterance)
    guard let progressGeneration = progressGate.stampIfOpen() else { return }
    Task { @MainActor [weak self] in
      self?.handleProgress(
        characterRange,
        utteranceID: utteranceID,
        progressGeneration: progressGeneration
      )
    }
  }

  nonisolated public func speechSynthesizer(
    _ synthesizer: AVSpeechSynthesizer,
    didFinish utterance: AVSpeechUtterance
  ) {
    let utteranceID = ObjectIdentifier(utterance)
    Task { @MainActor [weak self] in
      self?.handleFinished(utteranceID)
    }
  }

  nonisolated public func speechSynthesizer(
    _ synthesizer: AVSpeechSynthesizer,
    didCancel utterance: AVSpeechUtterance
  ) {
    let utteranceID = ObjectIdentifier(utterance)
    Task { @MainActor [weak self] in
      self?.handleCancelled(utteranceID)
    }
  }

  private func handleProgress(
    _ range: NSRange,
    utteranceID: ObjectIdentifier,
    progressGeneration: UInt64
  ) {
    guard
      utteranceID == activeUtteranceID,
      progressGeneration == activeProgressGeneration,
      let request = activeRequest,
      !isPaused,
      range.location >= 0,
      range.length >= 0,
      range.location <= request.text.utf16.count,
      range.length <= request.text.utf16.count - range.location,
      range.location >= lastSafeRequestUTF16Offset
    else {
      return
    }
    lastSafeRequestUTF16Offset = range.location
    continuation.yield(
      .progressed(
        SpeechProgress(
          request: request,
          requestUTF16Range: range.location..<(range.location + range.length)
        )
      )
    )
  }

  private func handleFinished(_ utteranceID: ObjectIdentifier) {
    guard utteranceID == activeUtteranceID, let request = retireActiveRequest() else {
      return
    }
    continuation.yield(
      .finished(
        sessionToken: request.sessionToken,
        requestToken: request.requestToken
      )
    )
  }

  private func handleCancelled(_ utteranceID: ObjectIdentifier) {
    guard utteranceID == activeUtteranceID, let request = retireActiveRequest() else {
      return
    }
    continuation.yield(
      .cancelled(
        sessionToken: request.sessionToken,
        requestToken: request.requestToken
      )
    )
  }

  private func retireActiveRequest() -> SpeechRequest? {
    let request = activeRequest
    activeRequest = nil
    activeUtteranceID = nil
    activeProgressGeneration = progressGate.close()
    isPaused = false
    lastSafeRequestUTF16Offset = 0
    return request
  }
}

private final class SpeechProgressCallbackGate: @unchecked Sendable {
  private let lock = NSLock()
  private var generation: UInt64 = 0
  private var isOpen = false

  func open() -> UInt64 {
    lock.withLock {
      generation &+= 1
      isOpen = true
      return generation
    }
  }

  func close() -> UInt64 {
    lock.withLock {
      generation &+= 1
      isOpen = false
      return generation
    }
  }

  func stampIfOpen() -> UInt64? {
    lock.withLock {
      isOpen ? generation : nil
    }
  }
}

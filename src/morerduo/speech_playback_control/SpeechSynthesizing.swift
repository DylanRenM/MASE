@MainActor
public protocol SpeechSynthesizing: Sendable {
  var events: AsyncStream<SpeechEvent> { get }

  func start(_ request: SpeechRequest) async throws
  func pause() async throws
  func resume(rebuildingWith request: SpeechRequest?) async throws
  func stop() async
}

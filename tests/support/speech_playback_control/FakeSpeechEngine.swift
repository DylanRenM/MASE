import MorerduoKit

@MainActor
public final class FakeSpeechEngine: SpeechSynthesizing {
  public nonisolated let events: AsyncStream<SpeechEvent>
  public private(set) var activeRequest: SpeechRequest?
  public private(set) var isPaused = false

  private let continuation: AsyncStream<SpeechEvent>.Continuation

  public init() {
    let pair = AsyncStream.makeStream(of: SpeechEvent.self)
    events = pair.stream
    continuation = pair.continuation
  }

  deinit {
    continuation.finish()
  }

  public func start(_ request: SpeechRequest) async throws {
    guard activeRequest == nil else {
      throw SpeechEngineError.alreadyActive
    }
    activeRequest = request
    isPaused = false
  }

  public func pause() async throws {
    guard activeRequest != nil else {
      throw SpeechEngineError.noActiveRequest
    }
    isPaused = true
  }

  public func resume(rebuildingWith request: SpeechRequest?) async throws {
    guard let retiredRequest = activeRequest else {
      throw SpeechEngineError.noActiveRequest
    }
    if let request {
      activeRequest = request
      isPaused = false
      continuation.yield(
        .cancelled(
          sessionToken: retiredRequest.sessionToken,
          requestToken: retiredRequest.requestToken
        )
      )
      return
    }
    isPaused = false
  }

  public func stop() async {
    guard let request = activeRequest else { return }
    activeRequest = nil
    isPaused = false
    continuation.yield(
      .cancelled(
        sessionToken: request.sessionToken,
        requestToken: request.requestToken
      )
    )
  }

  public func finishActiveRequest() {
    guard let request = activeRequest else { return }
    activeRequest = nil
    isPaused = false
    continuation.yield(
      .finished(
        sessionToken: request.sessionToken,
        requestToken: request.requestToken
      )
    )
  }

  public func emitProgress(requestUTF16Range: Range<Int>) {
    guard let request = activeRequest else { return }
    continuation.yield(
      .progressed(
        SpeechProgress(
          request: request,
          requestUTF16Range: requestUTF16Range
        )
      )
    )
  }
}

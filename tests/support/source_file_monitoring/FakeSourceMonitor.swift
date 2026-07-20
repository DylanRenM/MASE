import Foundation
import MorerduoKit

@MainActor
public final class FakeSourceMonitor: SourceMonitoring {
  public let events: AsyncStream<SourceFileEvent>
  public private(set) var activeURL: URL?
  public private(set) var activeFingerprint: SourceFingerprint?
  public private(set) var activeSessionToken: ReadingSessionToken?

  private let continuation: AsyncStream<SourceFileEvent>.Continuation

  public init() {
    let pair = AsyncStream.makeStream(of: SourceFileEvent.self)
    events = pair.stream
    continuation = pair.continuation
  }

  deinit {
    continuation.finish()
  }

  public func start(
    url: URL,
    fingerprint: SourceFingerprint,
    sessionToken: ReadingSessionToken
  ) async throws {
    guard url.isFileURL, fingerprint.size >= 0 else {
      throw SourceMonitorError.invalidSource
    }
    guard activeURL == nil else {
      throw SourceMonitorError.alreadyActive
    }
    activeURL = url
    activeFingerprint = fingerprint
    activeSessionToken = sessionToken
  }

  public func stop() async {
    activeURL = nil
    activeFingerprint = nil
    activeSessionToken = nil
  }

  public func emit(_ changes: SourceFileChange) {
    guard !changes.isEmpty, let activeSessionToken else { return }
    continuation.yield(
      SourceFileEvent(
        changes: changes,
        sessionToken: activeSessionToken
      )
    )
  }
}

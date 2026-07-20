import Foundation

@MainActor
public protocol SourceMonitoring: Sendable {
  var events: AsyncStream<SourceFileEvent> { get }

  func start(
    url: URL,
    fingerprint: SourceFingerprint,
    sessionToken: ReadingSessionToken
  ) async throws

  func stop() async
}

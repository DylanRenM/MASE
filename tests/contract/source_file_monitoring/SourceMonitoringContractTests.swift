import Foundation
import MorerduoTestSupport
import Testing

@testable import MorerduoKit

@Suite("SourceMonitoring contract")
@MainActor
struct SourceMonitoringContractTests {
  @Test("the public event set and five-second deadline match the specification")
  func eventSetAndDeadline() {
    let allChanges: SourceFileChange = [
      .write, .extend, .attribute, .rename, .delete,
    ]

    #expect(allChanges.rawValue.nonzeroBitCount == 5)
    #expect(SourceMonitorPolicy.maximumDetectionLatency == .seconds(5))
  }

  @Test("start enforces one active source and stop permits replacement")
  func singleActiveSource() async throws {
    let monitor = FakeSourceMonitor()
    let firstToken = sessionToken(1)

    try await monitor.start(
      url: fileURL("first.txt"),
      fingerprint: fingerprint(size: 5),
      sessionToken: firstToken
    )
    await #expect(throws: SourceMonitorError.alreadyActive) {
      try await monitor.start(
        url: fileURL("second.txt"),
        fingerprint: fingerprint(size: 6),
        sessionToken: sessionToken(2)
      )
    }

    await monitor.stop()
    try await monitor.start(
      url: fileURL("second.txt"),
      fingerprint: fingerprint(size: 6),
      sessionToken: sessionToken(2)
    )
    #expect(monitor.activeURL == fileURL("second.txt"))
  }

  @Test("events retain change kinds and the active session token")
  func eventIdentity() async throws {
    let monitor = FakeSourceMonitor()
    let oldToken = sessionToken(3)
    let currentToken = sessionToken(4)
    var events = monitor.events.makeAsyncIterator()

    try await monitor.start(
      url: fileURL("old.txt"),
      fingerprint: fingerprint(size: 3),
      sessionToken: oldToken
    )
    await monitor.stop()
    monitor.emit([.write])
    try await monitor.start(
      url: fileURL("current.txt"),
      fingerprint: fingerprint(size: 7),
      sessionToken: currentToken
    )
    monitor.emit([.rename, .delete])

    #expect(
      await events.next()
        == SourceFileEvent(
          changes: [.rename, .delete],
          sessionToken: currentToken
        )
    )
  }

  @Test("non-file URLs and invalid fingerprints are typed failures")
  func invalidInput() async {
    let monitor = FakeSourceMonitor()

    await #expect(throws: SourceMonitorError.invalidSource) {
      try await monitor.start(
        url: URL(string: "https://example.invalid/file.txt")!,
        fingerprint: fingerprint(size: 1),
        sessionToken: sessionToken(5)
      )
    }
    await #expect(throws: SourceMonitorError.invalidSource) {
      try await monitor.start(
        url: fileURL("invalid.txt"),
        fingerprint: fingerprint(size: -1),
        sessionToken: sessionToken(5)
      )
    }
  }

  private func fileURL(_ name: String) -> URL {
    URL(fileURLWithPath: "/tmp/\(name)")
  }

  private func fingerprint(size: Int64) -> SourceFingerprint {
    SourceFingerprint(
      size: size,
      modifiedAt: Date(timeIntervalSince1970: 0),
      resourceID: nil
    )
  }

  private func sessionToken(_ value: UInt8) -> ReadingSessionToken {
    let suffix = String(format: "%012x", value)
    return ReadingSessionToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
    )
  }
}

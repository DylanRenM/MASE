import Darwin
import Foundation
import Testing

@testable import MorerduoKit

@Suite("DispatchSourceFileMonitor integration")
@MainActor
struct DispatchSourceFileMonitorTests {
  @Test("an in-place write emits a token-bound write or extend event")
  func inPlaceWrite() async throws {
    let fixture = try TemporarySourceFixture(name: "write.txt", contents: "before")
    defer { fixture.remove() }
    let monitor = DispatchSourceFileMonitor()
    let token = sessionToken(1)

    try await monitor.start(
      url: fixture.url,
      fingerprint: try fixture.fingerprint(),
      sessionToken: token
    )
    let eventTask = Task { try await nextEvent(from: monitor.events) }
    let startedAt = ContinuousClock.now
    try fixture.append(" after")
    let event = try await eventTask.value
    let detectionLatency = startedAt.duration(to: .now)
    await monitor.stop()

    #expect(event.sessionToken == token)
    #expect(!event.changes.intersection([.write, .extend]).isEmpty)
    #expect(detectionLatency < SourceMonitorPolicy.maximumDetectionLatency)
  }

  @Test("stop retires old callbacks before a replacement source starts")
  func stopIsolatesLateCallbacks() async throws {
    let oldFixture = try TemporarySourceFixture(name: "old.txt", contents: "old")
    let currentFixture = try TemporarySourceFixture(name: "current.txt", contents: "current")
    defer {
      oldFixture.remove()
      currentFixture.remove()
    }
    let monitor = DispatchSourceFileMonitor()

    try await monitor.start(
      url: oldFixture.url,
      fingerprint: try oldFixture.fingerprint(),
      sessionToken: sessionToken(2)
    )
    await monitor.stop()
    try oldFixture.append(" ignored")
    let currentToken = sessionToken(3)
    try await monitor.start(
      url: currentFixture.url,
      fingerprint: try currentFixture.fingerprint(),
      sessionToken: currentToken
    )
    let eventTask = Task { try await nextEvent(from: monitor.events) }
    try currentFixture.append(" accepted")
    let event = try await eventTask.value
    await monitor.stop()

    #expect(event.sessionToken == currentToken)
  }

  @Test("a missing source fails without occupying the active slot")
  func missingSourceIsTypedFailure() async throws {
    let monitor = DispatchSourceFileMonitor()
    let missingURL = FileManager.default.temporaryDirectory
      .appendingPathComponent("morerduo-missing-\(UUID().uuidString).txt")

    await #expect(throws: SourceMonitorError.unavailable) {
      try await monitor.start(
        url: missingURL,
        fingerprint: fingerprint(size: 1),
        sessionToken: sessionToken(4)
      )
    }
    #expect(!monitor.isMonitoring)
  }

  @Test("all five vnode event kinds map specifically within five seconds")
  func allEventKindsMapWithinDeadline() async throws {
    try await assertMutation(name: "write", expected: .write) {
      try $0.overwrite(with: "BEFORE")
    }
    try await assertMutation(name: "extend", expected: .extend) {
      try $0.append(" extended")
    }
    try await assertMutation(name: "attribute", expected: .attribute) {
      try $0.changePermissions()
    }
    try await assertMutation(name: "rename", expected: .rename) {
      try $0.renameFile()
    }
    try await assertMutation(name: "delete", expected: .delete) {
      try $0.deleteFile()
    }
  }

  @Test("an atomic replacement rearms monitoring on the replacement inode")
  func atomicReplacementRearms() async throws {
    let fixture = try TemporarySourceFixture(name: "replace.txt", contents: "before")
    defer { fixture.remove() }
    let monitor = DispatchSourceFileMonitor()
    let token = sessionToken(5)

    try await monitor.start(
      url: fixture.url,
      fingerprint: try fixture.fingerprint(),
      sessionToken: token
    )
    let replacementEvent = Task { try await nextEvent(from: monitor.events) }
    try fixture.replace(with: "replacement")
    let first = try await replacementEvent.value
    try await Task.sleep(for: .milliseconds(100))
    let rearmedEvent = Task { try await nextEvent(from: monitor.events) }
    try fixture.append(" changed again")
    let second = try await rearmedEvent.value
    await monitor.stop()

    #expect(!first.changes.intersection([.rename, .delete]).isEmpty)
    #expect(second.sessionToken == token)
    #expect(!second.changes.intersection([.write, .extend]).isEmpty)
  }

  @Test("delete followed by recreation rearms the original path")
  func deletionRearmsAfterRecreation() async throws {
    let fixture = try TemporarySourceFixture(name: "delete.txt", contents: "before")
    defer { fixture.remove() }
    let monitor = DispatchSourceFileMonitor()
    let token = sessionToken(6)

    try await monitor.start(
      url: fixture.url,
      fingerprint: try fixture.fingerprint(),
      sessionToken: token
    )
    let deletionEvent = Task { try await nextEvent(from: monitor.events) }
    try fixture.deleteFile()
    let first = try await deletionEvent.value
    try await Task.sleep(for: .milliseconds(100))
    try fixture.recreate(with: "recreated")
    try await Task.sleep(for: .milliseconds(100))
    let rearmedEvent = Task { try await nextEvent(from: monitor.events) }
    try fixture.append(" changed again")
    let second = try await rearmedEvent.value
    await monitor.stop()

    #expect(first.changes.contains(.delete))
    #expect(second.sessionToken == token)
  }

  @Test("an abandoned rearm task cannot retain the monitor")
  func abandonedRearmDoesNotRetainMonitor() async throws {
    let fixture = try TemporarySourceFixture(name: "abandoned.txt", contents: "before")
    defer { fixture.remove() }
    var monitor: DispatchSourceFileMonitor? = DispatchSourceFileMonitor()
    let weakMonitor = WeakMonitorBox(monitor)
    do {
      let currentMonitor = try #require(monitor)
      try await currentMonitor.start(
        url: fixture.url,
        fingerprint: try fixture.fingerprint(),
        sessionToken: sessionToken(7)
      )
      let deletionEvent = Task { try await nextEvent(from: currentMonitor.events) }
      try fixture.deleteFile()
      _ = try await deletionEvent.value
    }
    monitor = nil

    for _ in 0..<20 where weakMonitor.value != nil {
      try await Task.sleep(for: .milliseconds(10))
    }

    #expect(weakMonitor.value == nil)
  }

  private func nextEvent(
    from stream: AsyncStream<SourceFileEvent>
  ) async throws -> SourceFileEvent {
    try await withThrowingTaskGroup(of: SourceFileEvent.self) { group in
      group.addTask {
        var iterator = stream.makeAsyncIterator()
        guard let event = await iterator.next() else {
          throw SourceMonitorTestError.streamEnded
        }
        return event
      }
      group.addTask {
        try await Task.sleep(for: .seconds(2))
        throw SourceMonitorTestError.timedOut
      }
      guard let event = try await group.next() else {
        throw SourceMonitorTestError.streamEnded
      }
      group.cancelAll()
      return event
    }
  }

  private func assertMutation(
    name: String,
    expected: SourceFileChange,
    mutation: (TemporarySourceFixture) throws -> Void
  ) async throws {
    let fixture = try TemporarySourceFixture(name: "\(name).txt", contents: "before")
    defer { fixture.remove() }
    let monitor = DispatchSourceFileMonitor()
    try await monitor.start(
      url: fixture.url,
      fingerprint: try fixture.fingerprint(),
      sessionToken: sessionToken(10)
    )
    let eventTask = Task { try await nextEvent(from: monitor.events) }
    let startedAt = ContinuousClock.now
    try mutation(fixture)
    let event = try await eventTask.value
    let latency = startedAt.duration(to: .now)
    await monitor.stop()

    #expect(event.changes.contains(expected))
    #expect(latency < SourceMonitorPolicy.maximumDetectionLatency)
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

private enum SourceMonitorTestError: Error {
  case streamEnded
  case timedOut
  case mutationFailed
}

private final class WeakMonitorBox {
  weak var value: DispatchSourceFileMonitor?

  init(_ value: DispatchSourceFileMonitor?) {
    self.value = value
  }
}

private final class TemporarySourceFixture {
  let url: URL

  init(name: String, contents: String) throws {
    let directory = FileManager.default.temporaryDirectory
      .appendingPathComponent("morerduo-monitor-\(UUID().uuidString)", isDirectory: true)
    try FileManager.default.createDirectory(
      at: directory,
      withIntermediateDirectories: true
    )
    url = directory.appendingPathComponent(name)
    try Data(contents.utf8).write(to: url)
  }

  func fingerprint() throws -> SourceFingerprint {
    try FilePolicy.validate(url: url).fingerprint
  }

  func append(_ text: String) throws {
    let handle = try FileHandle(forWritingTo: url)
    defer { try? handle.close() }
    _ = try handle.seekToEnd()
    try handle.write(contentsOf: Data(text.utf8))
    try handle.synchronize()
  }

  func overwrite(with text: String) throws {
    let handle = try FileHandle(forWritingTo: url)
    defer { try? handle.close() }
    try handle.seek(toOffset: 0)
    try handle.write(contentsOf: Data(text.utf8))
    try handle.synchronize()
  }

  func changePermissions() throws {
    guard chmod(url.path, S_IRUSR | S_IWUSR) == 0 else {
      throw SourceMonitorTestError.mutationFailed
    }
  }

  func renameFile() throws {
    try FileManager.default.moveItem(
      at: url,
      to: url.deletingLastPathComponent().appendingPathComponent("renamed.txt")
    )
  }

  func replace(with text: String) throws {
    try Data(text.utf8).write(to: url, options: .atomic)
  }

  func deleteFile() throws {
    try FileManager.default.removeItem(at: url)
  }

  func recreate(with text: String) throws {
    try Data(text.utf8).write(to: url)
  }

  func remove() {
    try? FileManager.default.removeItem(at: url.deletingLastPathComponent())
  }
}

import Darwin
import Dispatch
import Foundation

@MainActor
public final class DispatchSourceFileMonitor: SourceMonitoring {
  public nonisolated let events: AsyncStream<SourceFileEvent>
  public private(set) var isMonitoring = false

  private let continuation: AsyncStream<SourceFileEvent>.Continuation
  private let eventQueue = DispatchQueue(label: "cn.mase.morerduo.source-monitor")
  private var monitoringRequest: MonitoringRequest?
  private var activeSource: ActiveSource?
  private var rearmTask: Task<Void, Never>?
  private var generation: UInt64 = 0

  public init() {
    let pair = AsyncStream.makeStream(of: SourceFileEvent.self)
    events = pair.stream
    continuation = pair.continuation
    continuation.onTermination = { [weak self] _ in
      Task { @MainActor in
        await self?.stop()
      }
    }
  }

  deinit {
    rearmTask?.cancel()
    activeSource?.source.cancel()
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
    guard monitoringRequest == nil else {
      throw SourceMonitorError.alreadyActive
    }
    let request = MonitoringRequest(
      url: url,
      fingerprint: fingerprint,
      sessionToken: sessionToken
    )
    monitoringRequest = request
    do {
      try arm(request)
    } catch {
      monitoringRequest = nil
      throw error
    }
    isMonitoring = true
  }

  public func stop() async {
    guard monitoringRequest != nil else { return }
    monitoringRequest = nil
    rearmTask?.cancel()
    rearmTask = nil
    generation &+= 1
    let retiredSource = activeSource
    activeSource = nil
    isMonitoring = false
    retiredSource?.source.cancel()
  }

  private func arm(_ request: MonitoringRequest) throws {
    let descriptor = open(request.url.path, O_EVTONLY | O_CLOEXEC)
    guard descriptor >= 0 else {
      throw SourceMonitorError.unavailable
    }
    generation &+= 1
    let currentGeneration = generation
    let source = makeSource(
      descriptor: descriptor,
      sessionToken: request.sessionToken,
      generation: currentGeneration
    )
    activeSource = ActiveSource(
      source: source,
      sessionToken: request.sessionToken,
      generation: currentGeneration
    )
    source.resume()
  }

  private func makeSource(
    descriptor: Int32,
    sessionToken: ReadingSessionToken,
    generation: UInt64
  ) -> any DispatchSourceFileSystemObject {
    let source = DispatchSource.makeFileSystemObjectSource(
      fileDescriptor: descriptor,
      eventMask: [.write, .extend, .attrib, .rename, .delete],
      queue: eventQueue
    )
    let reference = SourceReference(source: source)
    let eventHandler: @Sendable () -> Void = { [weak self, reference] in
      guard let source = reference.source else { return }
      let flags = source.data
      Task { @MainActor in
        self?.handle(
          flags,
          sessionToken: sessionToken,
          generation: generation
        )
      }
    }
    let cancelHandler: @Sendable () -> Void = { [reference] in
      close(descriptor)
      reference.source = nil
    }
    source.setEventHandler(handler: eventHandler)
    source.setCancelHandler(handler: cancelHandler)
    return source
  }

  private func handle(
    _ flags: DispatchSource.FileSystemEvent,
    sessionToken: ReadingSessionToken,
    generation: UInt64
  ) {
    guard
      let activeSource,
      activeSource.generation == generation,
      activeSource.sessionToken == sessionToken
    else {
      return
    }
    let changes = Self.map(flags)
    guard !changes.isEmpty else { return }
    continuation.yield(
      SourceFileEvent(changes: changes, sessionToken: sessionToken)
    )
    if !changes.intersection([.rename, .delete]).isEmpty {
      beginRearming(retiredSource: activeSource)
    }
  }

  private func beginRearming(retiredSource: ActiveSource) {
    guard let request = monitoringRequest else { return }
    activeSource = nil
    retiredSource.source.cancel()
    rearmTask?.cancel()
    rearmTask = Task { @MainActor [weak self] in
      while !Task.isCancelled {
        guard let shouldRetry = self?.attemptRearm(request) else { return }
        if !shouldRetry { return }
        do {
          try await Task.sleep(for: SourceRearmPolicy.retryInterval)
        } catch {
          return
        }
      }
    }
  }

  private func attemptRearm(_ request: MonitoringRequest) -> Bool? {
    guard monitoringRequest == request, activeSource == nil else { return nil }
    do {
      try arm(request)
      rearmTask = nil
      return false
    } catch SourceMonitorError.unavailable {
      return true
    } catch {
      monitoringRequest = nil
      isMonitoring = false
      rearmTask = nil
      return false
    }
  }

  private static func map(
    _ flags: DispatchSource.FileSystemEvent
  ) -> SourceFileChange {
    var changes: SourceFileChange = []
    if flags.contains(.write) { changes.insert(.write) }
    if flags.contains(.extend) { changes.insert(.extend) }
    if flags.contains(.attrib) { changes.insert(.attribute) }
    if flags.contains(.rename) { changes.insert(.rename) }
    if flags.contains(.delete) { changes.insert(.delete) }
    return changes
  }
}

private struct ActiveSource {
  let source: any DispatchSourceFileSystemObject
  let sessionToken: ReadingSessionToken
  let generation: UInt64
}

private struct MonitoringRequest: Equatable {
  let url: URL
  let fingerprint: SourceFingerprint
  let sessionToken: ReadingSessionToken
}

private enum SourceRearmPolicy {
  static let retryInterval: Duration = .milliseconds(50)
}

private final class SourceReference: @unchecked Sendable {
  var source: (any DispatchSourceFileSystemObject)?

  init(source: any DispatchSourceFileSystemObject) {
    self.source = source
  }
}

import Foundation

public actor MorerduoEffectExecutor: ReadingSessionEffectExecuting {
  public nonisolated let events: AsyncStream<ReadingSessionEvent>

  private let documentLoader: any DocumentLoading
  private let filterPipeline: EnglishFilterPipeline
  private let speech: any SpeechSynthesizing
  private let monitor: any SourceMonitoring
  private let clock: any ReadingClock
  private let timerPollingInterval: Duration
  private let eventContinuation: AsyncStream<ReadingSessionEvent>.Continuation

  private var timerConfiguration: TimerConfiguration
  private var activeTime: ActiveTimeAccumulator
  private var activeRequests: [SpeechRequestToken: ActiveSpeechRequest] = [:]
  private var speechForwardingTask: Task<Void, Never>?
  private var monitorForwardingTask: Task<Void, Never>?
  private var timerTask: Task<Void, Never>?
  private var isForwardingEvents = false
  private var isShutdown = false
  public private(set) var lastFault: ReadingSessionFault?

  public init(
    documentLoader: any DocumentLoading = DocumentLoader(),
    filtering: any EnglishFiltering = EnglishTextFilter(),
    speech: any SpeechSynthesizing,
    monitor: any SourceMonitoring,
    clock: any ReadingClock = ContinuousReadingClock(),
    timerConfiguration: TimerConfiguration = .unlimited,
    timerPollingInterval: Duration = .milliseconds(100)
  ) {
    let pair = AsyncStream.makeStream(of: ReadingSessionEvent.self)
    events = pair.stream
    eventContinuation = pair.continuation
    self.documentLoader = documentLoader
    filterPipeline = EnglishFilterPipeline(filtering: filtering)
    self.speech = speech
    self.monitor = monitor
    self.clock = clock
    self.timerConfiguration = timerConfiguration
    activeTime = ActiveTimeAccumulator(configuration: timerConfiguration)
    self.timerPollingInterval = timerPollingInterval
  }

  public func startEventForwarding() async {
    guard !isForwardingEvents, !isShutdown else { return }
    isForwardingEvents = true
    let speechEvents = await speech.events
    let monitorEvents = await monitor.events
    speechForwardingTask = Task { [weak self] in
      for await event in speechEvents {
        guard !Task.isCancelled else { return }
        await self?.forward(speechEvent: event)
      }
    }
    monitorForwardingTask = Task { [weak self] in
      for await event in monitorEvents {
        guard !Task.isCancelled else { return }
        await self?.forward(sourceEvent: event)
      }
    }
  }

  @discardableResult
  public func updateTimerConfiguration(_ configuration: TimerConfiguration) -> Bool {
    guard !activeTime.isActive, !isShutdown else { return false }
    timerTask?.cancel()
    timerTask = nil
    timerConfiguration = configuration
    activeTime = ActiveTimeAccumulator(configuration: configuration)
    return true
  }

  public func execute(_ effect: ReadingSessionEffect) async throws
    -> ReadingSessionEvent?
  {
    guard !isShutdown else {
      throw ReadingSessionEffectExecutionError.userFacing(.internalFailure)
    }
    switch effect {
    case .loadDocument(let url, let token, let autoplay):
      return await loadDocument(url: url, token: token, autoplay: autoplay)
    case .verifySource(let document, _):
      try verifySource(document)
    case .startSpeech(let document, let cursor, let speed, let token):
      try await startSpeech(
        document: document,
        cursor: cursor,
        speed: speed,
        token: token
      )
    case .pauseSpeech:
      try await performSpeechOperation { try await speech.pause() }
    case .resumeSpeech(let document, let cursor, let speed, let token, let rebuild):
      try await resumeSpeech(
        document: document,
        cursor: cursor,
        speed: speed,
        token: token,
        rebuild: rebuild
      )
    case .stopSpeech(let token):
      removeRequests(for: token)
      await speech.stop()
    case .startClock(let token):
      activeTime.beginPlaying(now: clock.now, token: token)
      scheduleTimerPolling()
    case .freezeClock:
      activeTime.freeze(now: clock.now)
      cancelTimerPolling()
    case .stopClock:
      activeTime.stop(now: clock.now)
      cancelTimerPolling()
    case .startMonitor(let source, let token):
      try await startMonitor(source: source, token: token)
    case .stopMonitor:
      await monitor.stop()
    case .emergencyCleanup:
      await cleanupResources()
    case .recordFault(let fault):
      lastFault = fault
    }
    return nil
  }

  public func shutdown() async {
    guard !isShutdown else { return }
    isShutdown = true
    speechForwardingTask?.cancel()
    monitorForwardingTask?.cancel()
    cancelTimerPolling()
    await cleanupResources()
    eventContinuation.finish()
  }

  private func loadDocument(
    url: URL,
    token: ReadingSessionToken,
    autoplay: Bool
  ) async -> ReadingSessionEvent {
    do {
      let parsed = try await documentLoader.load(url: url)
      let paragraphs = try await filterPipeline.filter(document: parsed)
      let document = LoadedDocument(source: parsed.source, paragraphs: paragraphs)
      return .documentLoaded(document, token: token, autoplay: autoplay)
    } catch let error as DocumentLoadError {
      return .documentLoadFailed(error, token: token)
    } catch {
      return .documentLoadFailed(.notReadable, token: token)
    }
  }

  private func verifySource(_ document: LoadedDocument) throws {
    do {
      try SourceAvailabilityVerifier.verify(document.source)
    } catch {
      throw ReadingSessionEffectExecutionError.userFacing(.sourceUnavailable)
    }
  }

  private func startSpeech(
    document: LoadedDocument,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    token: ReadingSessionToken
  ) async throws {
    let request = try makeSpeechRequest(
      document: document,
      cursor: cursor,
      speed: speed,
      token: token
    )
    activeRequests[request.requestToken] = ActiveSpeechRequest(
      paragraphIndex: cursor.paragraphIndex,
      sessionToken: token
    )
    do {
      try await speech.start(request)
    } catch {
      activeRequests[request.requestToken] = nil
      throw speechExecutionError(error)
    }
  }

  private func resumeSpeech(
    document: LoadedDocument,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    token: ReadingSessionToken,
    rebuild: Bool
  ) async throws {
    guard rebuild else {
      try await performSpeechOperation {
        try await speech.resume(rebuildingWith: nil)
      }
      return
    }
    let request = try makeSpeechRequest(
      document: document,
      cursor: cursor,
      speed: speed,
      token: token
    )
    activeRequests[request.requestToken] = ActiveSpeechRequest(
      paragraphIndex: cursor.paragraphIndex,
      sessionToken: token
    )
    do {
      try await speech.resume(rebuildingWith: request)
    } catch {
      activeRequests[request.requestToken] = nil
      throw speechExecutionError(error)
    }
  }

  private func makeSpeechRequest(
    document: LoadedDocument,
    cursor: ReadingCursor,
    speed: ReadingSpeed,
    token: ReadingSessionToken
  ) throws -> SpeechRequest {
    guard document.paragraphs.indices.contains(cursor.paragraphIndex) else {
      throw ReadingSessionEffectExecutionError.userFacing(.internalFailure)
    }
    do {
      return try SpeechRequest(
        paragraph: document.paragraphs[cursor.paragraphIndex],
        utf16Offset: cursor.utf16Offset,
        speed: speed,
        sessionToken: token,
        requestToken: SpeechRequestToken(rawValue: UUID())
      )
    } catch {
      throw ReadingSessionEffectExecutionError.userFacing(.speechFailure)
    }
  }

  private func performSpeechOperation(
    _ operation: () async throws -> Void
  ) async throws {
    do {
      try await operation()
    } catch {
      throw speechExecutionError(error)
    }
  }

  private func speechExecutionError(_ error: Error)
    -> ReadingSessionEffectExecutionError
  {
    if let speechError = error as? SpeechEngineError, speechError == .unavailable {
      return .userFacing(.speechUnavailable)
    }
    return .userFacing(.speechFailure)
  }

  private func startMonitor(
    source: ValidatedSource,
    token: ReadingSessionToken
  ) async throws {
    do {
      try await monitor.start(
        url: source.url,
        fingerprint: source.fingerprint,
        sessionToken: token
      )
    } catch {
      throw ReadingSessionEffectExecutionError.userFacing(.monitorFailure)
    }
  }

  private func cleanupResources() async {
    activeRequests.removeAll()
    await speech.stop()
    await monitor.stop()
    activeTime.stop(now: clock.now)
  }

  private func removeRequests(for token: ReadingSessionToken) {
    activeRequests = activeRequests.filter { $0.value.sessionToken != token }
  }

  private func scheduleTimerPolling() {
    cancelTimerPolling()
    guard timerConfiguration.limit != nil else { return }
    let interval = timerPollingInterval
    timerTask = Task { [weak self] in
      while !Task.isCancelled {
        do {
          try await Task.sleep(for: interval)
        } catch {
          return
        }
        guard let self else { return }
        if await self.pollTimer() { return }
      }
    }
  }

  private func cancelTimerPolling() {
    timerTask?.cancel()
    timerTask = nil
  }

  private func pollTimer() -> Bool {
    guard let expiry = activeTime.takeExpiry(now: clock.now) else {
      return false
    }
    eventContinuation.yield(.timerExpired(expiry))
    timerTask = nil
    return true
  }

  private func forward(speechEvent: SpeechEvent) {
    switch speechEvent {
    case .progressed(let progress):
      guard let request = activeRequests[progress.requestToken] else { return }
      eventContinuation.yield(
        .cursorAdvanced(
          ReadingCursor(
            paragraphIndex: request.paragraphIndex,
            utf16Offset: progress.safeResumeUTF16Offset
          ),
          token: progress.sessionToken
        )
      )
    case .finished(let sessionToken, let requestToken):
      guard activeRequests.removeValue(forKey: requestToken) != nil else { return }
      eventContinuation.yield(.paragraphFinished(token: sessionToken))
    case .cancelled(_, let requestToken):
      activeRequests[requestToken] = nil
    case .failed(let error, let sessionToken, let requestToken):
      activeRequests[requestToken] = nil
      let userError: UserFacingError =
        error == .unavailable ? .speechUnavailable : .speechFailure
      eventContinuation.yield(.effectFailed(userError, token: sessionToken))
    }
  }

  private func forward(sourceEvent: SourceFileEvent) {
    eventContinuation.yield(
      .sourceChanged(
        promptToken: ReloadPromptToken(rawValue: UUID()),
        sessionToken: sourceEvent.sessionToken
      )
    )
  }
}

private struct ActiveSpeechRequest: Sendable {
  let paragraphIndex: Int
  let sessionToken: ReadingSessionToken
}

@MainActor
public final class SessionCoordinator {
  public private(set) var state: ReadingSessionState

  private let reducer: any ReadingSessionReducing
  private let effectExecutor: any ReadingSessionEffectExecuting
  private var eventTail: Task<Void, Never>?
  private var effectTask: Task<Void, Never>?
  private var eventGeneration: UInt64 = 0
  private var latestSupersedingGeneration: UInt64?
  private var isCleanupProtected = false

  public init(
    initialState: ReadingSessionState,
    reducer: any ReadingSessionReducing,
    effectExecutor: any ReadingSessionEffectExecuting
  ) {
    precondition(initialState.satisfiesInvariants)
    state = initialState
    self.reducer = reducer
    self.effectExecutor = effectExecutor
  }

  public func send(_ event: ReadingSessionEvent) async {
    eventGeneration &+= 1
    let generation = eventGeneration
    if shouldCancelInFlight(for: event) {
      latestSupersedingGeneration = generation
      if !isCleanupProtected {
        effectTask?.cancel()
      }
    }
    let predecessor = eventTail
    let task = Task { @MainActor [weak self] in
      await predecessor?.value
      guard let self else { return }
      await self.process(event, generation: generation)
    }
    eventTail = task
    await task.value
    if eventGeneration == generation {
      eventTail = nil
    }
  }

  deinit {
    effectTask?.cancel()
    eventTail?.cancel()
  }

  private func process(
    _ event: ReadingSessionEvent,
    generation: UInt64
  ) async {
    let transition = reducer.reduce(state: state, event: event)
    state = transition.state
    let task = Task { [weak self] in
      guard let self else { return }
      await self.execute(transition.effects, generation: generation)
    }
    effectTask = task
    await task.value
    effectTask = nil
    isCleanupProtected = false
  }

  private func execute(
    _ effects: [ReadingSessionEffect],
    generation: UInt64
  ) async {
    for effect in effects {
      isCleanupProtected = effect.isCleanup
      defer { isCleanupProtected = false }
      if Task.isCancelled || isSuperseded(generation), !effect.isCleanup {
        return
      }
      do {
        let emittedEvent = try await effectExecutor.execute(effect)
        if Task.isCancelled {
          if effect.isCleanup { continue }
          return
        }
        if isSuperseded(generation) {
          if effect.isCleanup { continue }
          return
        }
        if let emittedEvent {
          await applyEmitted(emittedEvent, generation: generation)
          return
        }
      } catch is CancellationError {
        if !effect.isCleanup { return }
      } catch let executionError as ReadingSessionEffectExecutionError {
        if effect.isCleanup { continue }
        if Task.isCancelled { return }
        await recover(from: executionError, failedEffect: effect)
        return
      } catch {
        if effect.isCleanup { continue }
        if Task.isCancelled { return }
        await recover(
          from: .userFacing(defaultError(for: effect)),
          failedEffect: effect
        )
        return
      }
    }
  }

  private func recover(
    from executionError: ReadingSessionEffectExecutionError,
    failedEffect: ReadingSessionEffect
  ) async {
    guard !Task.isCancelled, let token = failedEffect.sessionToken else { return }
    let error: UserFacingError
    switch executionError {
    case .userFacing(let userFacingError):
      error = userFacingError
    }
    let transition = reducer.reduce(
      state: state,
      event: .effectFailed(error, token: token)
    )
    state = transition.state
    isCleanupProtected = true
    for effect in transition.effects {
      do {
        _ = try await effectExecutor.execute(effect)
      } catch {
        continue
      }
    }
  }

  private func applyEmitted(
    _ event: ReadingSessionEvent,
    generation: UInt64
  ) async {
    let transition = reducer.reduce(state: state, event: event)
    state = transition.state
    await execute(transition.effects, generation: generation)
  }

  private func isSuperseded(_ generation: UInt64) -> Bool {
    guard let latestSupersedingGeneration else { return false }
    return latestSupersedingGeneration > generation
  }

  private func shouldCancelInFlight(for event: ReadingSessionEvent) -> Bool {
    switch event {
    case .selectFile, .stop, .appTerminate:
      return true
    case .timerExpired(let expiry):
      return state.sessionToken == expiry.token
    case .documentLoaded, .documentLoadFailed, .effectFailed, .play, .pause,
      .resume, .changeSpeed, .changeTimer, .cursorAdvanced,
      .paragraphFinished, .sourceChanged, .reloadSource, .continueOldContent,
      .dismissError:
      return false
    }
  }

  private func defaultError(for effect: ReadingSessionEffect) -> UserFacingError {
    switch effect {
    case .loadDocument:
      return .document(.notReadable)
    case .verifySource:
      return .sourceUnavailable
    case .startMonitor, .stopMonitor:
      return .monitorFailure
    case .startClock, .freezeClock, .stopClock:
      return .timerFailure
    case .startSpeech, .pauseSpeech, .resumeSpeech, .stopSpeech:
      return .speechFailure
    case .emergencyCleanup, .recordFault:
      return .internalFailure
    }
  }
}

extension ReadingSessionEffect {
  fileprivate var sessionToken: ReadingSessionToken? {
    switch self {
    case .loadDocument(_, let token, _), .verifySource(_, let token),
      .pauseSpeech(let token), .stopSpeech(let token), .startClock(let token),
      .freezeClock(let token), .stopClock(let token), .stopMonitor(let token):
      return token
    case .startSpeech(_, _, _, let token),
      .resumeSpeech(_, _, _, let token, _), .startMonitor(_, let token):
      return token
    case .emergencyCleanup, .recordFault:
      return nil
    }
  }

  fileprivate var isCleanup: Bool {
    switch self {
    case .stopSpeech, .stopMonitor, .stopClock, .emergencyCleanup, .recordFault:
      return true
    default:
      return false
    }
  }
}

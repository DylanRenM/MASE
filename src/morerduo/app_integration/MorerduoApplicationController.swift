import Foundation

@MainActor
public final class MorerduoApplicationController {
  public private(set) var viewState: AppViewState
  public var onViewStateChange: ((AppViewState) -> Void)? {
    didSet { onViewStateChange?(viewState) }
  }

  private let coordinator: SessionCoordinator
  private let effectExecutor: MorerduoEffectExecutor
  private let viewClock = ContinuousClock()
  private let progressPublicationInterval: Duration = .milliseconds(100)
  private var eventTask: Task<Void, Never>?
  private var pendingProgressPublication: Task<Void, Never>?
  private var lastProgressPublication: ContinuousClock.Instant?
  private var isTerminated = false

  public convenience init() {
    let effectExecutor = MorerduoEffectExecutor(
      speech: AVSpeechEngine(),
      monitor: DispatchSourceFileMonitor()
    )
    self.init(
      initialState: .initial(timer: .unlimited),
      contractMode: .relaxed,
      effectExecutor: effectExecutor
    )
  }

  public init(
    initialState: ReadingSessionState,
    contractMode: ContractMode,
    effectExecutor: MorerduoEffectExecutor
  ) {
    precondition(initialState.satisfiesInvariants)
    viewState = Self.project(initialState)
    coordinator = SessionCoordinator(
      initialState: initialState,
      reducer: ReadingSessionReducer(contractMode: contractMode),
      effectExecutor: effectExecutor
    )
    self.effectExecutor = effectExecutor
  }

  deinit {
    eventTask?.cancel()
    pendingProgressPublication?.cancel()
  }

  public func start() async {
    guard eventTask == nil, !isTerminated else { return }
    await effectExecutor.startEventForwarding()
    let events = effectExecutor.events
    eventTask = Task { @MainActor [weak self] in
      for await event in events {
        guard !Task.isCancelled, let self else { return }
        await self.send(event)
      }
    }
    publish()
  }

  public func selectFile(_ url: URL) async {
    guard viewState.canChooseFile, url.isFileURL, !isTerminated else { return }
    await send(.selectFile(url, token: makeSessionToken()))
  }

  public func playPause() async {
    guard viewState.canPlayPause, !isTerminated else { return }
    switch coordinator.state.mode {
    case .ready:
      guard await effectExecutor.updateTimerConfiguration(coordinator.state.timer) else {
        return
      }
      await send(.play(token: makeSessionToken()))
    case .playing:
      await send(.pause)
    case .paused:
      await send(.resume)
    case .idle, .loading, .awaitingReloadDecision:
      return
    }
  }

  public func stop() async {
    guard viewState.canStop, !isTerminated else { return }
    await send(.stop)
  }

  public func changeSpeed(_ speed: ReadingSpeed) async {
    guard viewState.canEditSpeed, !isTerminated else { return }
    await send(.changeSpeed(speed))
  }

  public func updateTimerInput(_ input: String) async -> String? {
    guard viewState.canEditTimer, !isTerminated else { return nil }
    do {
      let configuration = try TimerConfiguration.parse(input)
      guard await effectExecutor.updateTimerConfiguration(configuration) else {
        return "当前状态无法更改定时；请停止朗读后重试。"
      }
      await send(.changeTimer(configuration))
      return nil
    } catch {
      return "请输入 1 至 240 的整数分钟，或留空表示不限时。"
    }
  }

  public func reloadSource() async {
    guard
      !isTerminated,
      let promptToken = coordinator.state.reloadPromptToken
    else {
      return
    }
    await send(
      .reloadSource(promptToken: promptToken, token: makeSessionToken())
    )
  }

  public func continueOldContent() async {
    guard
      !isTerminated,
      let promptToken = coordinator.state.reloadPromptToken
    else {
      return
    }
    await send(.continueOldContent(promptToken: promptToken))
  }

  public func dismissError() async {
    guard coordinator.state.error != nil, !isTerminated else { return }
    await send(.dismissError)
  }

  public func terminate() async {
    guard !isTerminated else { return }
    isTerminated = true
    await send(.appTerminate)
    eventTask?.cancel()
    eventTask = nil
    pendingProgressPublication?.cancel()
    pendingProgressPublication = nil
    await effectExecutor.shutdown()
  }

  private func send(_ event: ReadingSessionEvent) async {
    await coordinator.send(event)
    if case .cursorAdvanced = event {
      publishProgressWhenDue()
    } else {
      pendingProgressPublication?.cancel()
      pendingProgressPublication = nil
      publish()
    }
  }

  private func publishProgressWhenDue() {
    let now = viewClock.now
    if let lastProgressPublication {
      let elapsed = lastProgressPublication.duration(to: now)
      if elapsed < progressPublicationInterval {
        scheduleProgressPublication(after: progressPublicationInterval - elapsed)
        return
      }
    }
    lastProgressPublication = now
    publish()
  }

  private func scheduleProgressPublication(after delay: Duration) {
    guard pendingProgressPublication == nil else { return }
    pendingProgressPublication = Task { @MainActor [weak self] in
      do {
        try await Task.sleep(for: delay)
      } catch {
        return
      }
      guard let self else { return }
      self.pendingProgressPublication = nil
      self.lastProgressPublication = self.viewClock.now
      self.publish()
    }
  }

  private func publish() {
    viewState = Self.project(coordinator.state)
    onViewStateChange?(viewState)
  }

  private func makeSessionToken() -> ReadingSessionToken {
    ReadingSessionToken(rawValue: UUID())
  }

  private static func project(_ state: ReadingSessionState) -> AppViewState {
    do {
      return try AppViewState(session: state)
    } catch {
      preconditionFailure("valid session state must produce valid app view state")
    }
  }
}

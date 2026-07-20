import Foundation
import MorerduoKit
import MorerduoTestSupport

@MainActor
final class NativeSessionE2EHarness {
  let speech: FakeSpeechEngine
  let clock: E2EReadingClock
  let controller: MorerduoApplicationController

  init(usesRealMonitor: Bool = false, usesRealClock: Bool = false) {
    speech = FakeSpeechEngine()
    clock = E2EReadingClock()
    let monitor: any SourceMonitoring =
      usesRealMonitor ? DispatchSourceFileMonitor() : FakeSourceMonitor()
    let executor = MorerduoEffectExecutor(
      speech: speech,
      monitor: monitor,
      clock: usesRealClock ? ContinuousReadingClock() : clock,
      timerPollingInterval: .milliseconds(10)
    )
    controller = MorerduoApplicationController(
      initialState: .initial(timer: .unlimited),
      contractMode: .strict,
      effectExecutor: executor
    )
  }

  var viewState: AppViewState {
    controller.viewState
  }

  func start() async {
    await controller.start()
  }

  func load(_ url: URL) async {
    await controller.selectFile(url)
  }

  func playPause() async {
    await controller.playPause()
  }

  func stop() async {
    await controller.stop()
  }

  func changeSpeed(_ speed: ReadingSpeed) async {
    await controller.changeSpeed(speed)
  }

  func configureTimer(_ input: String) async -> String? {
    await controller.updateTimerInput(input)
  }

  func finishParagraph() {
    speech.finishActiveRequest()
  }

  func emitProgress(_ range: Range<Int>) {
    speech.emitProgress(requestUTF16Range: range)
  }

  func advanceClock(by duration: Duration) {
    clock.advance(by: duration)
  }

  func awaitMode(
    _ mode: SessionMode,
    timeout: Duration = .seconds(5)
  ) async throws {
    try await eventually(timeout: timeout) { self.viewState.mode == mode }
  }

  func awaitProgress(
    containing fragment: String,
    timeout: Duration = .seconds(2)
  ) async throws {
    try await eventually(timeout: timeout) {
      self.viewState.progressText.contains(fragment)
    }
  }

  func awaitCondition(
    timeout: Duration = .seconds(5),
    _ condition: @escaping @MainActor () -> Bool
  ) async throws {
    try await eventually(timeout: timeout, condition: condition)
  }

  func continueOldContent() async {
    await controller.continueOldContent()
  }

  func reloadSource() async {
    await controller.reloadSource()
  }

  func dismissError() async {
    await controller.dismissError()
  }

  func terminate() async {
    await controller.terminate()
  }

  private func eventually(
    timeout: Duration,
    condition: @escaping @MainActor () -> Bool
  ) async throws {
    let clock = ContinuousClock()
    let deadline = clock.now.advanced(by: timeout)
    while clock.now < deadline {
      if condition() { return }
      try await Task.sleep(for: .milliseconds(10))
    }
    throw NativeE2EError.timeout
  }
}

enum NativeE2EError: Error {
  case timeout
}

final class E2EReadingClock: ReadingClock, @unchecked Sendable {
  private let lock = NSLock()
  private var storedNow: Duration = .zero

  var now: Duration {
    lock.withLock { storedNow }
  }

  func advance(by duration: Duration) {
    lock.withLock { storedNow += duration }
  }
}

import AppKit

@MainActor
final class AppLifecycleDelegate: NSObject, NSApplicationDelegate {
  private weak var viewModel: AppViewModel?
  private var isTerminating = false

  func bind(_ viewModel: AppViewModel) {
    self.viewModel = viewModel
  }

  func applicationShouldTerminate(_ sender: NSApplication)
    -> NSApplication.TerminateReply
  {
    guard let viewModel, !isTerminating else { return .terminateNow }
    isTerminating = true
    Task { @MainActor in
      await viewModel.terminate()
      sender.reply(toApplicationShouldTerminate: true)
    }
    return .terminateLater
  }
}

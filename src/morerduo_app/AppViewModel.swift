import AppKit
import Foundation
import MorerduoKit

@MainActor
final class AppViewModel: ObservableObject {
  @Published private(set) var state: AppViewState
  @Published var isFileImporterPresented = false
  @Published var timerInput = ""
  @Published private(set) var timerValidationMessage: String?
  @Published private(set) var importerErrorMessage: String?

  private let controller: MorerduoApplicationController
  private var hasStarted = false

  init(controller: MorerduoApplicationController = MorerduoApplicationController()) {
    self.controller = controller
    state = controller.viewState
    controller.onViewStateChange = { [weak self] viewState in
      let previousStatus = self?.state.statusText
      self?.state = viewState
      if previousStatus != viewState.statusText {
        self?.announce(viewState.statusText)
      }
    }
  }

  var presentedErrorMessage: String? {
    importerErrorMessage ?? state.errorMessage
  }

  func start() {
    guard !hasStarted else { return }
    hasStarted = true
    Task { await controller.start() }
  }

  func chooseFile() {
    guard state.canChooseFile else { return }
    isFileImporterPresented = true
  }

  func acceptImportedFile(_ url: URL) {
    importerErrorMessage = nil
    Task { await controller.selectFile(url) }
  }

  func rejectImportedFile() {
    importerErrorMessage = "无法打开所选文件；请重新选择 TXT、DOCX 或文本型 PDF。"
  }

  func playPause() {
    Task {
      if state.mode == .ready {
        timerValidationMessage = await controller.updateTimerInput(timerInput)
        guard timerValidationMessage == nil else { return }
      }
      await controller.playPause()
    }
  }

  func stop() {
    Task { await controller.stop() }
  }

  func changeSpeed(_ speed: ReadingSpeed) {
    Task { await controller.changeSpeed(speed) }
  }

  func validateTimerInput() {
    Task {
      timerValidationMessage = await controller.updateTimerInput(timerInput)
    }
  }

  func reloadSource() {
    Task { await controller.reloadSource() }
  }

  func continueOldContent() {
    Task { await controller.continueOldContent() }
  }

  func dismissError() {
    if importerErrorMessage != nil {
      importerErrorMessage = nil
      return
    }
    Task { await controller.dismissError() }
  }

  func terminate() async {
    await controller.terminate()
  }

  private func announce(_ message: String) {
    let application = NSApplication.shared
    let element: Any = application.mainWindow ?? application
    NSAccessibility.post(
      element: element,
      notification: .announcementRequested,
      userInfo: [
        .announcement: message,
        .priority: NSAccessibilityPriorityLevel.medium.rawValue,
      ]
    )
  }
}

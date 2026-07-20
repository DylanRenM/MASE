import SwiftUI

@main
struct MorerduoApp: App {
  @NSApplicationDelegateAdaptor(AppLifecycleDelegate.self)
  private var appLifecycleDelegate
  @StateObject private var viewModel = AppViewModel()

  var body: some Scene {
    WindowGroup("磨耳朵") {
      MorerduoMainView(viewModel: viewModel)
        .onAppear {
          appLifecycleDelegate.bind(viewModel)
          viewModel.start()
        }
    }
    .defaultSize(width: 760, height: 640)
  }
}

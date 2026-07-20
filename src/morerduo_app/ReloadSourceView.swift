import MorerduoKit
import SwiftUI

struct ReloadSourceView: View {
  @ObservedObject var viewModel: AppViewModel
  @FocusState private var isReloadFocused: Bool

  var body: some View {
    VStack(alignment: .leading, spacing: 20) {
      Text("源文件已被修改")
        .font(.title2.bold())
      Text("重新加载会使用新内容并从头播放；继续则收听已载入内存的旧内容。")
        .fixedSize(horizontal: false, vertical: true)

      HStack {
        Spacer()
        Button("继续旧内容") { viewModel.continueOldContent() }
          .accessibilityIdentifier(
            AppAccessibilityIdentifiers.continueOldContentButton
          )
        Button("重新加载") { viewModel.reloadSource() }
          .buttonStyle(.borderedProminent)
          .focused($isReloadFocused)
          .accessibilityIdentifier(AppAccessibilityIdentifiers.reloadSourceButton)
      }
    }
    .padding(28)
    .frame(width: 430)
    .accessibilityElement(children: .contain)
    .accessibilityIdentifier(AppAccessibilityIdentifiers.reloadSourceDialog)
    .interactiveDismissDisabled()
    .onAppear { isReloadFocused = true }
  }
}

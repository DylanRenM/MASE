import MorerduoKit
import SwiftUI

struct ReadingWorkspaceView: View {
  @ObservedObject var viewModel: AppViewModel

  var body: some View {
    VStack(spacing: 20) {
      HStack(alignment: .firstTextBaseline) {
        Text(viewModel.state.statusText)
          .font(.title3.weight(.semibold))
          .accessibilityIdentifier(AppAccessibilityIdentifiers.sessionStatus)
        Spacer()
        Text(viewModel.state.progressText)
          .monospacedDigit()
          .foregroundStyle(.secondary)
          .accessibilityIdentifier(AppAccessibilityIdentifiers.readingProgressLabel)
      }

      ProgressView(value: viewModel.state.progressFraction)
        .tint(.indigo)
        .accessibilityLabel("朗读进度")
        .accessibilityValue(viewModel.state.progressText)
        .accessibilityIdentifier(AppAccessibilityIdentifiers.readingProgress)

      Text("文件内容只作为本地数据处理；选择文件后不会自动播放。")
        .font(.callout)
        .foregroundStyle(.secondary)
        .frame(maxWidth: .infinity, alignment: .leading)

      HStack(spacing: 12) {
        Button(viewModel.state.playPauseTitle) { viewModel.playPause() }
          .buttonStyle(.borderedProminent)
          .tint(.indigo)
          .keyboardShortcut(.space, modifiers: [])
          .accessibilityLabel(viewModel.state.playPauseTitle)
          .accessibilityIdentifier(AppAccessibilityIdentifiers.playPauseButton)
          .disabled(!viewModel.state.canPlayPause)

        Button("停止并重置") { viewModel.stop() }
          .buttonStyle(.bordered)
          .keyboardShortcut(".", modifiers: .command)
          .accessibilityLabel("停止朗读并将进度重置到文件开头")
          .accessibilityIdentifier(AppAccessibilityIdentifiers.stopButton)
          .disabled(!viewModel.state.canStop)
      }
      .controlSize(.large)
    }
    .padding(.vertical, 8)
  }
}

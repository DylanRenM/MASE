import MorerduoKit
import SwiftUI

struct FileSelectionView: View {
  @ObservedObject var viewModel: AppViewModel

  var body: some View {
    HStack(spacing: 16) {
      Image(systemName: "doc.text")
        .font(.title2)
        .foregroundStyle(Color.accentColor)
        .accessibilityHidden(true)

      VStack(alignment: .leading, spacing: 4) {
        Text(viewModel.state.fileName)
          .font(.headline)
          .lineLimit(1)
          .truncationMode(.middle)
          .accessibilityIdentifier(AppAccessibilityIdentifiers.fileNameLabel)
        Text("支持 TXT、DOCX、文本型 PDF · 最大 20MB")
          .font(.caption)
          .foregroundStyle(.secondary)
      }

      Spacer(minLength: 12)

      if viewModel.state.isLoading {
        ProgressView()
          .controlSize(.small)
          .accessibilityLabel("正在载入文件")
      }

      Button("选择文件…") { viewModel.chooseFile() }
        .keyboardShortcut("o", modifiers: .command)
        .accessibilityLabel("选择英文文档")
        .accessibilityIdentifier(AppAccessibilityIdentifiers.filePickerButton)
        .disabled(!viewModel.state.canChooseFile)
    }
    .padding(18)
    .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 12))
  }
}

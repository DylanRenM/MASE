import MorerduoKit
import SwiftUI
import UniformTypeIdentifiers

struct MorerduoMainView: View {
  @ObservedObject var viewModel: AppViewModel

  private static let allowedContentTypes: [UTType] = {
    var types: [UTType] = [.plainText, .pdf]
    if let docx = UTType(filenameExtension: "docx") {
      types.append(docx)
    }
    return types
  }()

  var body: some View {
    VStack(alignment: .leading, spacing: 28) {
      header
      FileSelectionView(viewModel: viewModel)
      ReadingWorkspaceView(viewModel: viewModel)
      ListeningSettingsView(viewModel: viewModel)
      footer
    }
    .padding(36)
    .frame(minWidth: 640, idealWidth: 760, maxWidth: 900, minHeight: 560)
    .fileImporter(
      isPresented: $viewModel.isFileImporterPresented,
      allowedContentTypes: Self.allowedContentTypes,
      allowsMultipleSelection: false
    ) { result in
      switch result {
      case .success(let urls):
        guard let url = urls.first else {
          viewModel.rejectImportedFile()
          return
        }
        viewModel.acceptImportedFile(url)
      case .failure:
        viewModel.rejectImportedFile()
      }
    }
    .sheet(isPresented: reloadPromptBinding) {
      ReloadSourceView(viewModel: viewModel)
    }
    .alert("无法继续", isPresented: errorBinding) {
      Button("好") { viewModel.dismissError() }
    } message: {
      Text(viewModel.presentedErrorMessage ?? "发生未知错误。")
        .accessibilityIdentifier(AppAccessibilityIdentifiers.errorMessage)
    }
  }

  private var header: some View {
    VStack(alignment: .leading, spacing: 6) {
      Text("磨耳朵")
        .font(.system(size: 30, weight: .bold))
        .accessibilityIdentifier(AppAccessibilityIdentifiers.appTitle)
      Text("选择本地英文文档，使用系统语音持续循环朗读。")
        .foregroundStyle(.secondary)
    }
  }

  private var footer: some View {
    Text("系统默认英文语音 · 内容仅在本机处理 · 不支持 DOC、扫描 PDF 或 OCR")
      .font(.footnote)
      .foregroundStyle(.secondary)
      .fixedSize(horizontal: false, vertical: true)
  }

  private var reloadPromptBinding: Binding<Bool> {
    Binding(
      get: { viewModel.state.isReloadPromptPresented },
      set: { _ in }
    )
  }

  private var errorBinding: Binding<Bool> {
    Binding(
      get: { viewModel.presentedErrorMessage != nil },
      set: { isPresented in
        if !isPresented { viewModel.dismissError() }
      }
    )
  }
}

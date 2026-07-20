public enum AppErrorMessageMapper {
  public static func message(for error: UserFacingError) -> String {
    switch error {
    case .document(let documentError):
      return documentMessage(for: documentError)
    case .sourceUnavailable:
      return "源文件已移动、删除或不可读。请重新选择文件。"
    case .speechUnavailable:
      return "系统没有可用的英文语音。请先在 macOS 设置中安装英文语音。"
    case .speechFailure:
      return "系统语音朗读失败。请停止后重试。"
    case .timerFailure:
      return "朗读计时器发生错误。当前朗读已停止，请重试。"
    case .monitorFailure:
      return "无法监控源文件变化。当前朗读已停止，请重试。"
    case .internalFailure:
      return "应用状态发生错误，已安全停止并重置。"
    }
  }

  private static func documentMessage(for error: DocumentLoadError) -> String {
    switch error {
    case .unsupportedFormat:
      return "不支持该格式；请选择 TXT、DOCX 或文本型 PDF。"
    case .notRegularFile:
      return "所选项目不是可读取的常规文件。"
    case .tooLarge:
      return "文件超过 20MB；请选择更小的文件。"
    case .notReadable:
      return "无法读取该文件；文件可能已移动或权限不足。"
    case .emptyContent:
      return "文件为空或没有可读取内容。"
    case .corrupted:
      return "文件已损坏或结构无效；请选择其他文件。"
    case .scannedPDF:
      return "该 PDF 没有可提取文字；扫描件和 OCR 暂不支持。"
    case .unsupportedEncoding:
      return "TXT 不是受支持的 UTF-8 编码。"
    case .noReadableEnglish:
      return "未发现可朗读的英文内容。"
    case .unsafeArchive:
      return "DOCX 内容超过安全限制或包含不安全结构。"
    }
  }
}

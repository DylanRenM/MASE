public enum DocumentKind: String, Equatable, Sendable {
  case txt
  case docx
  case pdf

  init(fileExtension: String) throws {
    guard let kind = Self(rawValue: fileExtension.lowercased()) else {
      throw DocumentLoadError.unsupportedFormat
    }
    self = kind
  }
}

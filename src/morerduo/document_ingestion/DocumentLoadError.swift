public enum DocumentLoadError: Error, Equatable, Sendable {
  case unsupportedFormat
  case notRegularFile
  case tooLarge
  case notReadable
  case emptyContent
  case corrupted
  case scannedPDF
  case unsupportedEncoding
  case noReadableEnglish
  case unsafeArchive
}

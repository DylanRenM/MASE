import Foundation
import PDFKit

public struct PDFParser: Sendable {
  public init() {}

  public func parse(url: URL) throws -> [String] {
    guard let document = PDFDocument(url: url), document.pageCount > 0 else {
      throw DocumentLoadError.corrupted
    }

    var paragraphs: [String] = []
    paragraphs.reserveCapacity(document.pageCount)
    for pageIndex in 0..<document.pageCount {
      guard let page = document.page(at: pageIndex) else {
        throw DocumentLoadError.corrupted
      }
      guard let text = page.string else {
        continue
      }
      let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
      if !trimmed.isEmpty {
        paragraphs.append(trimmed)
      }
    }

    guard !paragraphs.isEmpty else {
      throw DocumentLoadError.scannedPDF
    }
    return paragraphs
  }
}

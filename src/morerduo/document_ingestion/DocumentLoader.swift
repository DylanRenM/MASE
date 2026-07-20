import Foundation

public struct DocumentLoader: DocumentLoading {
  public init() {}

  public func load(url: URL) async throws -> ParsedDocument {
    let source = try FilePolicy.validate(url: url)
    let paragraphs: [String]
    switch source.kind {
    case .txt:
      paragraphs = try TXTParser().parse(url: url)
    case .docx:
      paragraphs = try DOCXParser().parse(url: url)
    case .pdf:
      paragraphs = try PDFParser().parse(url: url)
    }
    return ParsedDocument(source: source, paragraphs: paragraphs)
  }
}

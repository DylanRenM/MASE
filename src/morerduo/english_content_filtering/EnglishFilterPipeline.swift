public struct EnglishFilterPipeline: Sendable {
  private let filtering: any EnglishFiltering

  public init(filtering: any EnglishFiltering = EnglishTextFilter()) {
    self.filtering = filtering
  }

  public func filter(document: ParsedDocument) async throws -> [EnglishParagraph] {
    let rawParagraphs = document.paragraphs.enumerated().map { index, text in
      RawParagraph(text: text, ordinal: index)
    }
    return try filtering.filter(rawParagraphs)
  }
}

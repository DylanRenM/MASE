public struct ParsedDocument: Equatable, Sendable {
  public let source: ValidatedSource
  public let paragraphs: [String]

  public init(source: ValidatedSource, paragraphs: [String]) {
    self.source = source
    self.paragraphs = paragraphs
  }
}

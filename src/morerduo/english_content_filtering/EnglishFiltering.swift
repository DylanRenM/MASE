public protocol EnglishFiltering: Sendable {
  func filter(_ paragraphs: [RawParagraph]) throws -> [EnglishParagraph]
}

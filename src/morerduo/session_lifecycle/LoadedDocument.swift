public struct LoadedDocument: Equatable, Sendable {
  public let source: ValidatedSource
  public let paragraphs: [EnglishParagraph]

  public init(source: ValidatedSource, paragraphs: [EnglishParagraph]) {
    precondition(source.url.isFileURL, "LoadedDocument requires a file URL")
    precondition(
      (0...DocumentLimits.maximumSourceBytes).contains(source.fingerprint.size),
      "LoadedDocument source size exceeds the document contract"
    )
    precondition(!paragraphs.isEmpty, "LoadedDocument requires readable English")
    precondition(
      zip(paragraphs, paragraphs.dropFirst()).allSatisfy { pair in
        pair.0.ordinal < pair.1.ordinal
      },
      "LoadedDocument paragraph ordinals must increase"
    )
    self.source = source
    self.paragraphs = paragraphs
  }

  public var name: String {
    source.url.lastPathComponent
  }
}

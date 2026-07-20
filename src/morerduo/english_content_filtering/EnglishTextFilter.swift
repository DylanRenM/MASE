public struct EnglishTextFilter: EnglishFiltering {
  public init() {}

  public func filter(_ paragraphs: [RawParagraph]) throws -> [EnglishParagraph] {
    precondition(hasStrictlyIncreasingOrdinals(paragraphs))
    let output = paragraphs.compactMap { paragraph -> EnglishParagraph? in
      let text = filterEnglishASCII(paragraph.text)
      guard !text.isEmpty else {
        return nil
      }
      return EnglishParagraph(text: text, ordinal: paragraph.ordinal)
    }
    guard !output.isEmpty else {
      throw DocumentLoadError.noReadableEnglish
    }
    return output
  }

  private func filterEnglishASCII(_ text: String) -> String {
    var output: [UInt8] = []
    output.reserveCapacity(text.utf8.count)
    var hasPendingSpace = false

    for byte in text.utf8 {
      let isLetter = (65...90).contains(byte) || (97...122).contains(byte)
      if isLetter {
        if hasPendingSpace, !output.isEmpty {
          output.append(32)
        }
        output.append(byte)
        hasPendingSpace = false
      } else {
        hasPendingSpace = !output.isEmpty
      }
    }
    return String(decoding: output, as: UTF8.self)
  }

  private func hasStrictlyIncreasingOrdinals(_ paragraphs: [RawParagraph]) -> Bool {
    zip(paragraphs, paragraphs.dropFirst()).allSatisfy { previous, current in
      previous.ordinal < current.ordinal
    }
  }
}

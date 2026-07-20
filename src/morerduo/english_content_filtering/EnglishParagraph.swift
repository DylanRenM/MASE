public struct EnglishParagraph: Equatable, Sendable {
  public let text: String
  public let utf16Length: Int
  public let ordinal: Int

  public init(text: String, ordinal: Int) {
    precondition(Self.isValid(text), "EnglishParagraph text violates the ASCII contract")
    precondition(ordinal >= 0, "EnglishParagraph ordinal must be nonnegative")
    self.text = text
    self.utf16Length = text.utf16.count
    self.ordinal = ordinal
  }

  private static func isValid(_ text: String) -> Bool {
    guard !text.isEmpty else {
      return false
    }
    var previousWasSpace = true
    for byte in text.utf8 {
      let isLetter = (65...90).contains(byte) || (97...122).contains(byte)
      if isLetter {
        previousWasSpace = false
      } else if byte == 32, !previousWasSpace {
        previousWasSpace = true
      } else {
        return false
      }
    }
    return !previousWasSpace
  }
}

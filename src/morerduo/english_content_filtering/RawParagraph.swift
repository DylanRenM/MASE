public struct RawParagraph: Equatable, Sendable {
  public let text: String
  public let ordinal: Int

  public init(text: String, ordinal: Int) {
    precondition(ordinal >= 0, "RawParagraph ordinal must be nonnegative")
    self.text = text
    self.ordinal = ordinal
  }
}

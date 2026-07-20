public struct ReadingCursor: Equatable, Sendable {
  public static let zero = ReadingCursor(paragraphIndex: 0, utf16Offset: 0)

  public let paragraphIndex: Int
  public let utf16Offset: Int

  public init(paragraphIndex: Int, utf16Offset: Int) {
    self.paragraphIndex = paragraphIndex
    self.utf16Offset = utf16Offset
  }
}

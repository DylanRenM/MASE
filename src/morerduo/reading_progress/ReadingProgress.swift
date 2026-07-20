public struct ReadingProgress: Equatable, Sendable {
  public let fraction: Double
  public let currentParagraph: Int
  public let totalParagraphs: Int

  public init(fraction: Double, currentParagraph: Int, totalParagraphs: Int) {
    precondition(fraction.isFinite && (0...1).contains(fraction))
    precondition(totalParagraphs >= 0)
    precondition(
      totalParagraphs == 0
        ? currentParagraph == 0
        : (1...totalParagraphs).contains(currentParagraph)
    )
    self.fraction = fraction
    self.currentParagraph = currentParagraph
    self.totalParagraphs = totalParagraphs
  }
}

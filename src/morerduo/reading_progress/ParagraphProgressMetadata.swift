public struct ParagraphProgressMetadata: Equatable, Sendable {
  public let lengths: [Int]
  let prefixStarts: [Int]
  let totalLength: Int

  public init(lengths: [Int]) throws {
    guard !lengths.isEmpty, lengths.allSatisfy({ $0 > 0 }) else {
      throw ReadingProgressError.invalidLengths
    }
    var runningTotal = 0
    var starts: [Int] = []
    starts.reserveCapacity(lengths.count)
    for length in lengths {
      starts.append(runningTotal)
      let (nextTotal, overflowed) = runningTotal.addingReportingOverflow(length)
      guard !overflowed else {
        throw ReadingProgressError.invalidLengths
      }
      runningTotal = nextTotal
    }
    self.lengths = lengths
    self.prefixStarts = starts
    self.totalLength = runningTotal
  }
}

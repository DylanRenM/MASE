import Testing

@testable import MorerduoKit

@Suite("ProgressCalculator contract")
struct ProgressCalculatorContractTests {
  @Test("idle progress is zero of zero")
  func idleProgress() throws {
    let progress = try ProgressCalculator.progress(metadata: nil, cursor: .zero)
    #expect(progress == ReadingProgress(fraction: 0, currentParagraph: 0, totalParagraphs: 0))
  }

  @Test("advances within a paragraph using prefix metadata")
  func advancesWithinParagraph() throws {
    let metadata = try ParagraphProgressMetadata(lengths: [10, 10])
    let progress = try ProgressCalculator.progress(
      metadata: metadata,
      cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 5)
    )
    #expect(progress.fraction == 0.25)
    #expect(progress.currentParagraph == 1)
  }

  @Test("switches to a one-based next paragraph")
  func switchesParagraph() throws {
    let metadata = try ParagraphProgressMetadata(lengths: [10, 10])
    let progress = try ProgressCalculator.progress(
      metadata: metadata,
      cursor: ReadingCursor(paragraphIndex: 1, utf16Offset: 0)
    )
    #expect(progress.fraction == 0.5)
    #expect(progress.currentParagraph == 2)
  }

  @Test("pause retains the identical cursor projection")
  func pauseRetainsProgress() throws {
    let metadata = try ParagraphProgressMetadata(lengths: [7, 9])
    let cursor = ReadingCursor(paragraphIndex: 1, utf16Offset: 3)
    #expect(
      try ProgressCalculator.progress(metadata: metadata, cursor: cursor)
        == ProgressCalculator.progress(metadata: metadata, cursor: cursor)
    )
  }

  @Test("stop and loop reset to the first paragraph")
  func resetToStart() throws {
    let metadata = try ParagraphProgressMetadata(lengths: [4, 6])
    let progress = try ProgressCalculator.progress(metadata: metadata, cursor: .zero)
    #expect(progress.fraction == 0)
    #expect(progress.currentParagraph == 1)
    #expect(progress.totalParagraphs == 2)
  }

  @Test("rejects an out-of-range paragraph cursor")
  func rejectsParagraphOverflow() throws {
    let metadata = try ParagraphProgressMetadata(lengths: [5])
    #expect(throws: ReadingProgressError.invalidCursor) {
      try ProgressCalculator.progress(
        metadata: metadata,
        cursor: ReadingCursor(paragraphIndex: 1, utf16Offset: 0)
      )
    }
  }

  @Test("rejects an out-of-range UTF-16 offset")
  func rejectsOffsetOverflow() throws {
    let metadata = try ParagraphProgressMetadata(lengths: [5])
    #expect(throws: ReadingProgressError.invalidCursor) {
      try ProgressCalculator.progress(
        metadata: metadata,
        cursor: ReadingCursor(paragraphIndex: 0, utf16Offset: 6)
      )
    }
  }
}

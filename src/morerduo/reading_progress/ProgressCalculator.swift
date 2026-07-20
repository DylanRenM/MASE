public enum ProgressCalculator {
  public static func progress(
    metadata: ParagraphProgressMetadata?,
    cursor: ReadingCursor
  ) throws -> ReadingProgress {
    guard let metadata else {
      guard cursor == .zero else {
        throw ReadingProgressError.invalidCursor
      }
      return ReadingProgress(fraction: 0, currentParagraph: 0, totalParagraphs: 0)
    }
    guard metadata.lengths.indices.contains(cursor.paragraphIndex),
      cursor.utf16Offset >= 0,
      cursor.utf16Offset <= metadata.lengths[cursor.paragraphIndex]
    else {
      throw ReadingProgressError.invalidCursor
    }

    let consumed = metadata.prefixStarts[cursor.paragraphIndex] + cursor.utf16Offset
    let fraction = min(1, max(0, Double(consumed) / Double(metadata.totalLength)))
    return ReadingProgress(
      fraction: fraction,
      currentParagraph: cursor.paragraphIndex + 1,
      totalParagraphs: metadata.lengths.count
    )
  }
}

public struct SpeechProgress: Equatable, Sendable {
  public let paragraphOrdinal: Int
  public let sessionToken: ReadingSessionToken
  public let requestToken: SpeechRequestToken
  public let requestUTF16Range: Range<Int>
  public let originalParagraphUTF16Range: Range<Int>
  public let safeResumeUTF16Offset: Int

  public init(
    request: SpeechRequest,
    requestUTF16Range: Range<Int>
  ) {
    precondition(
      requestUTF16Range.lowerBound >= 0
        && requestUTF16Range.upperBound <= request.text.utf16.count,
      "Speech progress range must remain inside the request"
    )
    paragraphOrdinal = request.paragraphOrdinal
    sessionToken = request.sessionToken
    requestToken = request.requestToken
    self.requestUTF16Range = requestUTF16Range
    let originalLowerBound = request.baseUTF16Offset + requestUTF16Range.lowerBound
    let originalUpperBound = request.baseUTF16Offset + requestUTF16Range.upperBound
    originalParagraphUTF16Range = originalLowerBound..<originalUpperBound
    safeResumeUTF16Offset = originalLowerBound
  }
}

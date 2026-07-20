public struct SpeechRequest: Equatable, Sendable {
  public let paragraphOrdinal: Int
  public let text: String
  public let baseUTF16Offset: Int
  public let originalParagraphUTF16Length: Int
  public let speed: ReadingSpeed
  public let sessionToken: ReadingSessionToken
  public let requestToken: SpeechRequestToken

  public init(
    paragraph: EnglishParagraph,
    utf16Offset: Int,
    speed: ReadingSpeed,
    sessionToken: ReadingSessionToken,
    requestToken: SpeechRequestToken
  ) throws {
    let bytes = Array(paragraph.text.utf8)
    guard bytes.indices.contains(utf16Offset) else {
      throw SpeechRequestError.invalidUTF16Offset
    }
    var normalizedOffset = utf16Offset
    while normalizedOffset < bytes.count, bytes[normalizedOffset] == 0x20 {
      normalizedOffset += 1
    }
    guard normalizedOffset < bytes.count else {
      throw SpeechRequestError.invalidUTF16Offset
    }
    let suffix = String(decoding: bytes[normalizedOffset...], as: UTF8.self)
    let validatedSuffix = EnglishParagraph(
      text: suffix,
      ordinal: paragraph.ordinal
    )
    paragraphOrdinal = paragraph.ordinal
    text = validatedSuffix.text
    baseUTF16Offset = normalizedOffset
    originalParagraphUTF16Length = paragraph.utf16Length
    self.speed = speed
    self.sessionToken = sessionToken
    self.requestToken = requestToken
  }
}

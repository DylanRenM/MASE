import Foundation
import MorerduoTestSupport
import Testing

@testable import MorerduoKit

@Suite("SpeechRequest contract")
@MainActor
struct SpeechRequestContractTests {
  @Test("a request derives a strict English suffix and preserves identity")
  func derivesSuffix() throws {
    let paragraph = EnglishParagraph(text: "Hello world", ordinal: 7)
    let sessionToken = ReadingSessionToken(rawValue: uuid(1))
    let requestToken = SpeechRequestToken(rawValue: uuid(2))

    let request = try SpeechRequest(
      paragraph: paragraph,
      utf16Offset: 6,
      speed: .fast,
      sessionToken: sessionToken,
      requestToken: requestToken
    )

    #expect(request.paragraphOrdinal == 7)
    #expect(request.text == "world")
    #expect(request.baseUTF16Offset == 6)
    #expect(request.originalParagraphUTF16Length == 11)
    #expect(request.speed == .fast)
    #expect(request.sessionToken == sessionToken)
    #expect(request.requestToken == requestToken)
    #expect(EnglishParagraph(text: request.text, ordinal: 7).text == request.text)
  }

  @Test("an offset on whitespace advances only to the next readable letter")
  func normalizesLeadingWhitespace() throws {
    let request = try SpeechRequest(
      paragraph: EnglishParagraph(text: "Hello world", ordinal: 0),
      utf16Offset: 5,
      speed: .normal,
      sessionToken: ReadingSessionToken(rawValue: uuid(3)),
      requestToken: SpeechRequestToken(rawValue: uuid(4))
    )

    #expect(request.text == "world")
    #expect(request.baseUTF16Offset == 6)
  }

  @Test("end and out-of-bounds offsets are rejected", arguments: [-1, 11, 12])
  func rejectsInvalidOffsets(offset: Int) {
    #expect(throws: SpeechRequestError.invalidUTF16Offset) {
      try SpeechRequest(
        paragraph: EnglishParagraph(text: "Hello world", ordinal: 0),
        utf16Offset: offset,
        speed: .normal,
        sessionToken: ReadingSessionToken(rawValue: uuid(5)),
        requestToken: SpeechRequestToken(rawValue: uuid(6))
      )
    }
  }

  @Test("three centralized rates are ordered and distinct")
  func ratesAreCentralized() {
    #expect(SpeechRateConfiguration.rate(for: .slow) == 0.4)
    #expect(SpeechRateConfiguration.rate(for: .normal) == 0.5)
    #expect(SpeechRateConfiguration.rate(for: .fast) == 0.6)
  }

  @Test("the fake engine enforces one active request")
  func fakeEnforcesSingleActiveRequest() async throws {
    let engine = FakeSpeechEngine()
    let first = try makeRequest(requestID: 7)
    let second = try makeRequest(requestID: 8)

    try await engine.start(first)
    await #expect(throws: SpeechEngineError.alreadyActive) {
      try await engine.start(second)
    }
    #expect(engine.activeRequest == first)

    await engine.stop()
    #expect(engine.activeRequest == nil)
    try await engine.start(second)
    #expect(engine.activeRequest == second)
  }

  private func makeRequest(requestID: UInt8) throws -> SpeechRequest {
    try SpeechRequest(
      paragraph: EnglishParagraph(text: "Hello", ordinal: 0),
      utf16Offset: 0,
      speed: .normal,
      sessionToken: ReadingSessionToken(rawValue: uuid(9)),
      requestToken: SpeechRequestToken(rawValue: uuid(requestID))
    )
  }

  private func uuid(_ value: UInt8) -> UUID {
    let suffix = String(format: "%012x", value)
    return UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
  }
}

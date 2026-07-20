import Foundation
import MorerduoTestSupport
import Testing

@testable import MorerduoKit

@Suite("SpeechSynthesizing contract")
@MainActor
struct SpeechSynthesizingContractTests {
  @Test("pause resume and stop preserve one request lifecycle")
  func lifecycleControls() async throws {
    let engine = FakeSpeechEngine()
    let request = try makeRequest(requestID: 1, offset: 0)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(request)
    try await engine.pause()
    #expect(engine.isPaused)
    try await engine.pause()
    #expect(engine.activeRequest == request)

    try await engine.resume(rebuildingWith: nil)
    #expect(!engine.isPaused)
    await engine.stop()

    #expect(engine.activeRequest == nil)
    #expect(
      await events.next()
        == .cancelled(
          sessionToken: request.sessionToken,
          requestToken: request.requestToken
        )
    )
  }

  @Test("controls reject the absence of an active request")
  func missingActiveRequestIsTypedFailure() async {
    let engine = FakeSpeechEngine()

    await #expect(throws: SpeechEngineError.noActiveRequest) {
      try await engine.pause()
    }
    await #expect(throws: SpeechEngineError.noActiveRequest) {
      try await engine.resume(rebuildingWith: nil)
    }
    await engine.stop()
    #expect(engine.activeRequest == nil)
  }

  @Test("rebuild replaces identity with a suffix request")
  func rebuildReplacesIdentity() async throws {
    let engine = FakeSpeechEngine()
    let original = try makeRequest(requestID: 2, offset: 0)
    let replacement = try makeRequest(requestID: 3, offset: 6)
    var events = engine.events.makeAsyncIterator()

    try await engine.start(original)
    try await engine.pause()
    try await engine.resume(rebuildingWith: replacement)

    #expect(engine.activeRequest == replacement)
    #expect(engine.activeRequest?.text == "world")
    #expect(engine.activeRequest?.baseUTF16Offset == 6)
    await engine.stop()
    #expect(
      await events.next()
        == .cancelled(
          sessionToken: original.sessionToken,
          requestToken: original.requestToken
        )
    )
  }

  private func makeRequest(
    requestID: UInt8,
    offset: Int
  ) throws -> SpeechRequest {
    try SpeechRequest(
      paragraph: EnglishParagraph(text: "Hello world", ordinal: 0),
      utf16Offset: offset,
      speed: .normal,
      sessionToken: ReadingSessionToken(rawValue: uuid(1)),
      requestToken: SpeechRequestToken(rawValue: uuid(requestID))
    )
  }

  private func uuid(_ value: UInt8) -> UUID {
    let suffix = String(format: "%012x", value)
    return UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
  }
}

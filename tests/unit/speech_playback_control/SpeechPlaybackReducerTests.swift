import Foundation
import Testing

@testable import MorerduoKit

@Suite("Speech playback reducer integration")
struct SpeechPlaybackReducerTests {
  @Test("paragraph completion advances and the final paragraph loops to start")
  func paragraphCompletionLoops() throws {
    let document = makeDocument()
    let sessionToken = ReadingSessionToken(rawValue: uuid(1))
    let timer = try TimerConfiguration(minutes: nil)
    let reducer = ReadingSessionReducer(contractMode: .strict)
    let first = ReadingSessionState.playing(
      document: document,
      cursor: .zero,
      speed: .normal,
      timer: timer,
      sessionToken: sessionToken
    )

    let second = reducer.reduce(
      state: first,
      event: .paragraphFinished(token: sessionToken)
    )
    #expect(second.state.cursor == ReadingCursor(paragraphIndex: 1, utf16Offset: 0))
    #expect(second.effects.count == 1)

    let looped = reducer.reduce(
      state: second.state,
      event: .paragraphFinished(token: sessionToken)
    )
    #expect(looped.state.mode == .playing)
    #expect(looped.state.cursor == .zero)
    #expect(
      looped.effects == [
        .startSpeech(
          document: document,
          cursor: .zero,
          speed: .normal,
          token: sessionToken
        )
      ]
    )
  }

  private func makeDocument() -> LoadedDocument {
    LoadedDocument(
      source: ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/speech-loop.txt"),
        kind: .txt,
        fingerprint: SourceFingerprint(
          size: 11,
          modifiedAt: Date(timeIntervalSince1970: 0),
          resourceID: nil
        )
      ),
      paragraphs: [
        EnglishParagraph(text: "Hello", ordinal: 0),
        EnglishParagraph(text: "World", ordinal: 1),
      ]
    )
  }

  private func uuid(_ value: UInt8) -> UUID {
    let suffix = String(format: "%012x", value)
    return UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
  }
}

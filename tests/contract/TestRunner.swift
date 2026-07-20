import Darwin
import Foundation
import Testing

@testable import MorerduoKit

@main
struct ContractTestRunner {
  static func main() async {
    if let probe = ProcessInfo.processInfo.environment["MORERDUO_CONTRACT_PROBE"] {
      runStrictProbe(probe)
      exit(EXIT_SUCCESS)
    }
    await Testing.__swiftPMEntryPoint() as Never
  }

  private static func runStrictProbe(_ probe: String) {
    switch probe {
    case "require":
      Contract.require(false, "strict require probe", mode: .strict)
    case "ensure":
      Contract.ensure(false, "strict ensure probe", mode: .strict)
    case "invariant":
      Contract.invariantCheck(false, "strict invariant probe", mode: .strict)
    case "reducer-illegal":
      guard let timer = try? TimerConfiguration(minutes: nil) else {
        exit(EXIT_FAILURE)
      }
      let reducer = ReadingSessionReducer(contractMode: .strict)
      _ = reducer.reduce(state: .initial(timer: timer), event: .pause)
    case "reducer-invalid-cursor":
      guard
        let timer = try? TimerConfiguration(minutes: nil),
        let uuid = UUID(uuidString: "00000000-0000-0000-0000-000000000001")
      else {
        exit(EXIT_FAILURE)
      }
      let token = ReadingSessionToken(rawValue: uuid)
      let source = ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/contract-cursor.txt"),
        kind: .txt,
        fingerprint: SourceFingerprint(
          size: 5,
          modifiedAt: Date(timeIntervalSince1970: 0),
          resourceID: nil
        )
      )
      let document = LoadedDocument(
        source: source,
        paragraphs: [EnglishParagraph(text: "Hello", ordinal: 0)]
      )
      let state = ReadingSessionState.playing(
        document: document,
        cursor: .zero,
        speed: .normal,
        timer: timer,
        sessionToken: token
      )
      let reducer = ReadingSessionReducer(contractMode: .strict)
      _ = reducer.reduce(
        state: state,
        event: .cursorAdvanced(
          ReadingCursor(paragraphIndex: 1, utf16Offset: 0),
          token: token
        )
      )
    case "reducer-invalid-state":
      guard
        let timer = try? TimerConfiguration(minutes: nil),
        let uuid = UUID(uuidString: "00000000-0000-0000-0000-000000000002")
      else {
        exit(EXIT_FAILURE)
      }
      let invalidState = ReadingSessionState.unchecked(
        mode: .ready,
        document: nil,
        cursor: .zero,
        speed: .normal,
        timer: timer,
        sessionToken: ReadingSessionToken(rawValue: uuid),
        reloadPromptToken: nil
      )
      let reducer = ReadingSessionReducer(contractMode: .strict)
      _ = reducer.reduce(state: invalidState, event: .pause)
    default:
      exit(EXIT_FAILURE)
    }
  }
}

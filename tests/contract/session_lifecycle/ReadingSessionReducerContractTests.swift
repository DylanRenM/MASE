import Foundation
import Testing

@testable import MorerduoKit

@Suite("ReadingSessionReducer contract")
struct ReadingSessionReducerContractTests {
  @Test("relaxed mode returns a typed fail-safe transition")
  func relaxedIllegalTransitionIsFailSafe() throws {
    let timer = try TimerConfiguration(minutes: nil)
    let reducer = ReadingSessionReducer(contractMode: .relaxed)

    let transition = reducer.reduce(
      state: .initial(timer: timer),
      event: .pause
    )

    #expect(transition.state == .initial(timer: timer, error: .internalFailure))
    #expect(transition.effects == [.recordFault(.illegalTransition)])
  }

  @Test("strict mode traps an illegal transition with an invariant diagnostic")
  func strictIllegalTransitionTraps() throws {
    let result = try runProbe("reducer-illegal")

    #expect(result.status != 0)
    #expect(result.diagnostics.contains("illegal session transition"))
  }

  @Test("strict mode traps an out-of-bounds current-session cursor")
  func strictInvalidCursorTraps() throws {
    let result = try runProbe("reducer-invalid-cursor")

    #expect(result.status != 0)
    #expect(result.diagnostics.contains("cursor must remain in document bounds"))
  }

  @Test("relaxed mode recovers an invalid internal state with emergency cleanup")
  func relaxedInvalidStateIsFailSafe() throws {
    let timer = try TimerConfiguration(minutes: nil)
    let document = makeDocument()
    let sessionToken = ReadingSessionToken(
      rawValue: try #require(
        UUID(uuidString: "00000000-0000-0000-0000-000000000019")
      )
    )
    let invalidState = ReadingSessionState.unchecked(
      mode: .ready,
      document: document,
      cursor: .zero,
      speed: .normal,
      timer: timer,
      sessionToken: sessionToken,
      reloadPromptToken: nil
    )

    let transition = ReadingSessionReducer(contractMode: .relaxed).reduce(
      state: invalidState,
      event: .pause
    )

    #expect(
      transition.state
        == .ready(
          document: document,
          speed: .normal,
          timer: timer,
          error: .internalFailure
        )
    )
    #expect(
      transition.effects == [
        .emergencyCleanup,
        .recordFault(.invalidState),
      ]
    )
  }

  @Test("strict mode traps an invalid internal state before reduction")
  func strictInvalidStateTraps() throws {
    let result = try runProbe("reducer-invalid-state")

    #expect(result.status != 0)
    #expect(result.diagnostics.contains("input state must satisfy session invariants"))
  }

  private func runProbe(_ probe: String) throws -> (status: Int32, diagnostics: String) {
    let process = Process()
    let errorPipe = Pipe()
    process.executableURL = URL(fileURLWithPath: CommandLine.arguments[0])
    process.environment = ProcessInfo.processInfo.environment.merging(
      ["MORERDUO_CONTRACT_PROBE": probe],
      uniquingKeysWith: { _, new in new }
    )
    process.standardOutput = Pipe()
    process.standardError = errorPipe

    try process.run()
    process.waitUntilExit()
    let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
    let diagnostics = String(decoding: errorData, as: UTF8.self)

    return (process.terminationStatus, diagnostics)
  }

  private func makeDocument() -> LoadedDocument {
    LoadedDocument(
      source: ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/contract-invalid-state.txt"),
        kind: .txt,
        fingerprint: SourceFingerprint(
          size: 5,
          modifiedAt: Date(timeIntervalSince1970: 0),
          resourceID: nil
        )
      ),
      paragraphs: [EnglishParagraph(text: "Hello", ordinal: 0)]
    )
  }
}

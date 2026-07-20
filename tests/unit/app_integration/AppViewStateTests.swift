import Foundation
import MorerduoKit
import Testing

@Suite("AppViewState projection")
struct AppViewStateTests {
  @Test("projects first launch as an idle nonplaying workspace")
  func projectsIdleState() throws {
    let state = ReadingSessionState.initial(
      timer: try TimerConfiguration(minutes: nil)
    )

    let viewState = try AppViewState(session: state)

    #expect(viewState.statusText == "等待选择文件")
    #expect(viewState.fileName == "尚未选择文件")
    #expect(viewState.progressFraction == 0)
    #expect(viewState.progressText == "0% · 0 / 0 段")
    #expect(viewState.playPauseTitle == "播放")
    #expect(viewState.canChooseFile)
    #expect(!viewState.canPlayPause)
    #expect(!viewState.canStop)
    #expect(viewState.canEditSpeed)
    #expect(viewState.canEditTimer)
    #expect(!viewState.isReloadPromptPresented)
  }

  @Test("projects playing progress and disables mutable settings")
  func projectsPlayingState() throws {
    let state = ReadingSessionState.playing(
      document: makeDocument(),
      cursor: ReadingCursor(paragraphIndex: 1, utf16Offset: 5),
      speed: .fast,
      timer: try TimerConfiguration(minutes: 30),
      sessionToken: token(1)
    )

    let viewState = try AppViewState(session: state)

    #expect(viewState.statusText == "正在朗读")
    #expect(viewState.fileName == "lesson.txt")
    #expect(viewState.progressFraction > 0.5)
    #expect(viewState.progressText == "70% · 2 / 2 段")
    #expect(viewState.playPauseTitle == "暂停")
    #expect(viewState.canChooseFile)
    #expect(viewState.canPlayPause)
    #expect(viewState.canStop)
    #expect(!viewState.canEditSpeed)
    #expect(!viewState.canEditTimer)
    #expect(viewState.speed == .fast)
  }

  @Test("projects paused and reload-decision control semantics")
  func projectsPausedAndPromptStates() throws {
    let document = makeDocument()
    let timer = try TimerConfiguration(minutes: 1)
    let sessionToken = token(2)
    let paused = ReadingSessionState.paused(
      document: document,
      cursor: .zero,
      speed: .normal,
      timer: timer,
      sessionToken: sessionToken
    )
    let promptToken = ReloadPromptToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-000000000003")!
    )
    let awaiting = ReadingSessionState.awaitingReloadDecision(
      document: document,
      cursor: .zero,
      speed: .normal,
      timer: timer,
      sessionToken: sessionToken,
      promptToken: promptToken
    )

    let pausedViewState = try AppViewState(session: paused)
    let awaitingViewState = try AppViewState(session: awaiting)

    #expect(pausedViewState.playPauseTitle == "继续")
    #expect(pausedViewState.canEditSpeed)
    #expect(!pausedViewState.canEditTimer)
    #expect(awaitingViewState.statusText == "等待处理源文件变化")
    #expect(awaitingViewState.isReloadPromptPresented)
    #expect(awaitingViewState.reloadPromptToken == promptToken)
    #expect(!awaitingViewState.canChooseFile)
    #expect(!awaitingViewState.canPlayPause)
    #expect(!awaitingViewState.canStop)
  }

  @Test("maps typed errors to actionable local messages")
  func mapsTypedErrors() throws {
    let state = ReadingSessionState.initial(
      timer: try TimerConfiguration(minutes: nil),
      error: .document(.scannedPDF)
    )

    let viewState = try AppViewState(session: state)

    #expect(viewState.errorMessage == "该 PDF 没有可提取文字；扫描件和 OCR 暂不支持。")
  }

  private func makeDocument() -> LoadedDocument {
    LoadedDocument(
      source: ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/lesson.txt"),
        kind: .txt,
        fingerprint: SourceFingerprint(
          size: 25,
          modifiedAt: Date(timeIntervalSince1970: 0),
          resourceID: nil
        )
      ),
      paragraphs: [
        EnglishParagraph(text: "Hello world", ordinal: 0),
        EnglishParagraph(text: "Listen again", ordinal: 1),
      ]
    )
  }

  private func token(_ value: UInt8) -> ReadingSessionToken {
    let suffix = String(format: "%012x", value)
    return ReadingSessionToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
    )
  }
}

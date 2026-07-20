import Foundation
import MorerduoKit
import Testing

@MainActor
@Suite("Morerduo MVP native E2E", .serialized)
struct MorerduoMVPScenarioTests {
  @Test("[P0] TXT DOCX and text PDF become ready without autoplay")
  func supportedDocumentsMainFlow() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let fixtures = try E2EFixtureFactory(root: root)
    let urls = try [
      fixtures.textFile(name: "lesson.txt", contents: "Hello from TXT"),
      fixtures.docxFile(name: "lesson.docx", paragraphs: ["Hello from DOCX"]),
      fixtures.pdfFile(name: "lesson.pdf", pageTexts: ["Hello from PDF"]),
    ]

    try await E2ESpecSandbox(root: root).runAsync {
      for url in urls {
        let harness = NativeSessionE2EHarness()
        await harness.start()
        await harness.load(url)
        #expect(harness.viewState.mode == .ready)
        #expect(harness.viewState.fileName == url.lastPathComponent)
        #expect(harness.viewState.progressFraction == 0)
        #expect(harness.speech.activeRequest == nil)
        await harness.playPause()
        #expect(harness.viewState.mode == .playing)
        #expect(harness.speech.activeRequest != nil)
        await harness.terminate()
      }
    }
  }

  @Test("[P0] loop pause speed resume and independent stop preserve progress semantics")
  func playbackControlsAndLoop() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let url = try E2EFixtureFactory(root: root).textFile(
      name: "controls.txt",
      contents: "First listening paragraph\nSecond listening paragraph"
    )

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness()
      await harness.start()
      await harness.load(url)
      await harness.playPause()
      harness.emitProgress(6..<15)
      try await harness.awaitCondition { harness.viewState.progressFraction > 0 }
      await harness.playPause()
      let pausedProgress = harness.viewState.progressText
      try await Task.sleep(for: .milliseconds(30))
      #expect(harness.viewState.progressText == pausedProgress)

      await harness.changeSpeed(.fast)
      await harness.playPause()
      #expect(harness.speech.activeRequest?.speed == .fast)
      harness.finishParagraph()
      try await harness.awaitProgress(containing: "2 / 2")
      harness.finishParagraph()
      try await harness.awaitProgress(containing: "1 / 2")

      await harness.stop()
      #expect(harness.viewState.mode == .ready)
      #expect(harness.viewState.progressText == "0% · 1 / 2 段")
      #expect(harness.speech.activeRequest == nil)
      await harness.terminate()
    }
  }

  @Test("[P0] mixed and script-like content remains inert strict English data")
  func strictFilteringAndNoEnglish() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let fixtures = try E2EFixtureFactory(root: root)
    let mixed = try fixtures.textFile(
      name: "mixed.txt",
      contents: "Hello 123, 世界 <script>alert(\"XSS\")</script>"
    )
    let emptyEnglish = try fixtures.textFile(name: "no-english.txt", contents: "123，世界！")

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness()
      await harness.start()
      await harness.load(mixed)
      await harness.playPause()
      #expect(harness.speech.activeRequest?.text == "Hello script alert XSS script")
      await harness.stop()
      await harness.load(emptyEnglish)
      #expect(harness.viewState.mode == .idle)
      #expect(harness.viewState.errorMessage == "未发现可朗读的英文内容。")
      await harness.terminate()
    }
  }

  @Test("[P0] fake clock excludes paused time and expires once")
  func activeReadingTimer() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let url = try E2EFixtureFactory(root: root).textFile(
      name: "timer.txt",
      contents: "Keep listening for the timer"
    )

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness()
      await harness.start()
      await harness.load(url)
      #expect(await harness.configureTimer("1") == nil)
      await harness.playPause()
      await harness.playPause()
      harness.advanceClock(by: .seconds(60))
      try await Task.sleep(for: .milliseconds(30))
      #expect(harness.viewState.mode == .paused)
      await harness.playPause()
      harness.advanceClock(by: .seconds(60))
      try await harness.awaitMode(.ready)
      #expect(harness.viewState.progressText == "0% · 1 / 1 段")
      #expect(harness.speech.activeRequest == nil)
      await harness.terminate()
    }
  }

  @Test("[P0/P1] timer range validation and unlimited smoke")
  func timerConfigurationBoundaries() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let url = try E2EFixtureFactory(root: root).textFile(
      name: "timer-range.txt",
      contents: "Timer range validation"
    )

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness()
      await harness.start()
      await harness.load(url)
      for invalid in ["0", "241", "1.5", "one"] {
        #expect(await harness.configureTimer(invalid) != nil)
      }
      #expect(await harness.configureTimer("240") == nil)
      #expect(await harness.configureTimer("") == nil)
      await harness.playPause()
      harness.advanceClock(by: .seconds(600))
      try await Task.sleep(for: .milliseconds(30))
      #expect(harness.viewState.mode == .playing)
      await harness.terminate()
    }
  }

  @Test("[P0] real monotonic clock starts the one-minute minimum smoke")
  func realMinimumTimerSmoke() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let url = try E2EFixtureFactory(root: root).textFile(
      name: "real-clock.txt",
      contents: "Real monotonic clock smoke"
    )

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness(usesRealClock: true)
      await harness.start()
      await harness.load(url)
      #expect(await harness.configureTimer("1") == nil)
      await harness.playPause()
      try await Task.sleep(for: .milliseconds(100))
      #expect(harness.viewState.mode == .playing)
      #expect(harness.speech.activeRequest != nil)
      await harness.terminate()
    }
  }

  @Test("[P1] invalid corrupt oversized scanned and empty inputs stay recoverable")
  func invalidDocumentFailures() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let fixtures = try E2EFixtureFactory(root: root)
    let cases: [(URL, String)] = try [
      (fixtures.rawFile(name: "legacy.doc", data: Data("legacy".utf8)), "不支持该格式"),
      (fixtures.rawFile(name: "corrupt.docx", data: Data("broken".utf8)), "文件已损坏"),
      (fixtures.oversizedTextFile(name: "too-large.txt"), "文件超过 20MB"),
      (fixtures.pdfFile(name: "scan.pdf", pageTexts: [nil]), "扫描件和 OCR 暂不支持"),
      (fixtures.rawFile(name: "empty.txt", data: Data()), "文件为空"),
    ]

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness()
      await harness.start()
      for (url, messageFragment) in cases {
        await harness.load(url)
        #expect(harness.viewState.mode == .idle)
        #expect(harness.viewState.errorMessage?.contains(messageFragment) == true)
        #expect(harness.speech.activeRequest == nil)
        await harness.dismissError()
      }
      await harness.terminate()
    }
  }

  @Test("[P1] deleting a ready source makes play recover idle")
  func readySourceDeletion() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let url = try E2EFixtureFactory(root: root).textFile(
      name: "delete-me.txt",
      contents: "This source will disappear"
    )

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness()
      await harness.start()
      await harness.load(url)
      try FileManager.default.removeItem(at: url)
      await harness.playPause()
      #expect(harness.viewState.mode == .idle)
      #expect(harness.viewState.errorMessage?.contains("移动、删除或不可读") == true)
      await harness.terminate()
    }
  }

  @Test("[P1] source writes prompt within five seconds and both decisions work")
  func sourceModificationDecisions() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let url = try E2EFixtureFactory(root: root).textFile(
      name: "monitored.txt",
      contents: "Old listening content"
    )

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness(usesRealMonitor: true)
      await harness.start()
      await harness.load(url)
      await harness.playPause()
      try Data("Changed once".utf8).write(to: url)
      try await harness.awaitMode(.awaitingReloadDecision, timeout: .seconds(5))
      await harness.continueOldContent()
      #expect(harness.viewState.mode == .playing)
      #expect(harness.speech.activeRequest?.text == "Old listening content")

      try Data("Fresh replacement content".utf8).write(to: url, options: .atomic)
      try await harness.awaitMode(.awaitingReloadDecision, timeout: .seconds(5))
      await harness.reloadSource()
      try await harness.awaitMode(.playing)
      #expect(harness.speech.activeRequest?.text == "Fresh replacement content")
      await harness.terminate()
    }
  }

  @Test("[P1/P2] file replacement restart and rapid controls converge safely")
  func lifecycleAndCompetitionBoundaries() async throws {
    let root = try makeRoot()
    defer { try? FileManager.default.removeItem(at: root) }
    let fixtures = try E2EFixtureFactory(root: root)
    let first = try fixtures.textFile(name: "first.txt", contents: "First file content")
    let second = try fixtures.textFile(name: "第二 file &.txt", contents: "Second file content")

    try await E2ESpecSandbox(root: root).runAsync {
      let harness = NativeSessionE2EHarness()
      await harness.start()
      await harness.load(first)
      await harness.playPause()
      await harness.playPause()
      await harness.load(second)
      #expect(harness.viewState.mode == .ready)
      #expect(harness.viewState.fileName == second.lastPathComponent)
      #expect(harness.viewState.progressText == "0% · 1 / 1 段")

      await harness.playPause()
      await harness.playPause()
      await harness.playPause()
      await harness.playPause()
      #expect(harness.viewState.mode == .paused)
      await harness.terminate()

      let restarted = NativeSessionE2EHarness()
      await restarted.start()
      #expect(restarted.viewState.mode == .idle)
      #expect(restarted.viewState.progressText == "0% · 0 / 0 段")
      await restarted.terminate()
    }
  }

  private func makeRoot() throws -> URL {
    let root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-e2e-spec-\(UUID().uuidString)")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    return root
  }
}

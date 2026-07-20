import Foundation
import MorerduoKit
import MorerduoTestSupport
import Testing

@Suite("Morerduo application controller")
struct MorerduoApplicationControllerTests {
  @MainActor
  @Test("first launch stays idle and loading never autoplays")
  func firstLaunchAndFileSelection() async throws {
    let source = makeSource()
    let parsed = ParsedDocument(
      source: source,
      paragraphs: ["Hello, world", "Listen again"]
    )
    let executor = MorerduoEffectExecutor(
      documentLoader: ControllerDocumentLoader(document: parsed),
      speech: FakeSpeechEngine(),
      monitor: FakeSourceMonitor()
    )
    let controller = MorerduoApplicationController(
      initialState: .initial(timer: .unlimited),
      contractMode: .strict,
      effectExecutor: executor
    )

    #expect(controller.viewState.mode == .idle)
    await controller.start()
    await controller.selectFile(source.url)

    #expect(controller.viewState.mode == .ready)
    #expect(controller.viewState.fileName == "controller.txt")
    #expect(controller.viewState.playPauseTitle == "播放")
    await controller.terminate()
  }

  @MainActor
  @Test("play pause speed resume and stop remain serialized")
  func controlsRemainSerialized() async throws {
    let speech = FakeSpeechEngine()
    let sourceURL = FileManager.default.temporaryDirectory
      .appendingPathComponent("morerduo-controller-\(UUID().uuidString).txt")
    try Data("Hello world".utf8).write(to: sourceURL, options: .atomic)
    defer { try? FileManager.default.removeItem(at: sourceURL) }
    let source = makeSource(url: sourceURL)
    let executor = MorerduoEffectExecutor(
      documentLoader: ControllerDocumentLoader(
        document: ParsedDocument(source: source, paragraphs: ["Hello world"])
      ),
      speech: speech,
      monitor: FakeSourceMonitor()
    )
    let controller = MorerduoApplicationController(
      initialState: .initial(timer: .unlimited),
      contractMode: .strict,
      effectExecutor: executor
    )
    await controller.start()
    await controller.selectFile(source.url)

    await controller.playPause()
    #expect(controller.viewState.mode == .playing)
    await controller.playPause()
    #expect(controller.viewState.mode == .paused)
    await controller.changeSpeed(.fast)
    #expect(controller.viewState.speed == .fast)
    await controller.playPause()
    #expect(controller.viewState.mode == .playing)
    await controller.stop()

    #expect(controller.viewState.mode == .ready)
    #expect(controller.viewState.progressText == "0% · 1 / 1 段")
    #expect(speech.activeRequest == nil)
    await controller.terminate()
  }

  @MainActor
  @Test("timer input accepts blank or integer minutes and rejects decimals")
  func validatesTimerInput() async {
    let executor = MorerduoEffectExecutor(
      documentLoader: ControllerDocumentLoader(
        document: ParsedDocument(source: makeSource(), paragraphs: ["Hello"])
      ),
      speech: FakeSpeechEngine(),
      monitor: FakeSourceMonitor()
    )
    let controller = MorerduoApplicationController(
      initialState: .initial(timer: .unlimited),
      contractMode: .strict,
      effectExecutor: executor
    )

    #expect(await controller.updateTimerInput("") == nil)
    #expect(await controller.updateTimerInput("240") == nil)
    #expect(
      await controller.updateTimerInput("1.5")
        == "请输入 1 至 240 的整数分钟，或留空表示不限时。"
    )
    await controller.terminate()
  }

  private func makeSource(
    url: URL = URL(fileURLWithPath: "/tmp/controller.txt")
  ) -> ValidatedSource {
    ValidatedSource(
      url: url,
      kind: .txt,
      fingerprint: SourceFingerprint(
        size: 24,
        modifiedAt: Date(timeIntervalSince1970: 0),
        resourceID: nil
      )
    )
  }
}

private struct ControllerDocumentLoader: DocumentLoading {
  let document: ParsedDocument

  func load(url: URL) async throws -> ParsedDocument {
    document
  }
}

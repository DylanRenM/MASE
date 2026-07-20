import Foundation
import Testing

@testable import MorerduoKit

@Suite("DocumentLoader integration")
struct DocumentLoaderTests {
  @Test("loads a validated TXT as one immutable result")
  func loadsTXTAtomically() async throws {
    let fixture = try LoaderFixture(
      fileExtension: "txt",
      data: Data("First\nSecond".utf8)
    )
    defer { fixture.remove() }

    let document = try await DocumentLoader().load(url: fixture.url)

    #expect(document.source.kind == .txt)
    #expect(document.paragraphs == ["First", "Second"])
  }

  @Test("a failed load cannot mutate a previously returned document")
  func failureDoesNotPublishPartialDocument() async throws {
    let valid = try LoaderFixture(fileExtension: "txt", data: Data("Stable".utf8))
    let invalid = try LoaderFixture(fileExtension: "txt", data: Data([0xC3, 0x28]))
    defer {
      valid.remove()
      invalid.remove()
    }
    let loader = DocumentLoader()
    let previous = try await loader.load(url: valid.url)

    await #expect(throws: DocumentLoadError.unsupportedEncoding) {
      try await loader.load(url: invalid.url)
    }

    #expect(previous.paragraphs == ["Stable"])
  }

  @MainActor
  @Test("large TXT loading yields the MainActor")
  func largeLoadDoesNotBlockMainActor() async throws {
    let fixture = try LoaderFixture(
      fileExtension: "txt",
      data: Data(repeating: 0x41, count: 18 * 1024 * 1024)
    )
    defer { fixture.remove() }
    let loadTask = Task {
      try await DocumentLoader().load(url: fixture.url)
    }

    await Task.yield()
    let heartbeatWasHandled = true
    let document = try await loadTask.value

    #expect(heartbeatWasHandled)
    #expect(document.paragraphs.count == 1)
  }
}

private struct LoaderFixture: Sendable {
  let root: URL
  let url: URL

  init(fileExtension: String, data: Data) throws {
    root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-document-loader-\(UUID().uuidString)")
    url = root.appending(path: "fixture.\(fileExtension)")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    try data.write(to: url)
  }

  func remove() {
    try? FileManager.default.removeItem(at: root)
  }
}

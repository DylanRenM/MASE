import Foundation
import Testing

@testable import MorerduoKit

@Suite("TXTParser")
struct TXTParserTests {
  @Test("parses UTF-8 text into ordered non-empty lines")
  func parsesUTF8Paragraphs() throws {
    let fixture = try TextFixture(data: Data("First line.\n\nSecond line.".utf8))
    defer { fixture.remove() }

    let paragraphs = try TXTParser().parse(url: fixture.url)

    #expect(paragraphs == ["First line.", "Second line."])
  }

  @Test("rejects an empty TXT file")
  func rejectsEmptyFile() throws {
    let fixture = try TextFixture(data: Data())
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.emptyContent) {
      try TXTParser().parse(url: fixture.url)
    }
  }

  @Test("rejects invalid UTF-8")
  func rejectsInvalidUTF8() throws {
    let fixture = try TextFixture(data: Data([0xC3, 0x28]))
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.unsupportedEncoding) {
      try TXTParser().parse(url: fixture.url)
    }
  }

  @Test("maps an unreadable TXT to a typed error")
  func rejectsUnreadableFile() throws {
    let fixture = try TextFixture(data: Data("English".utf8))
    defer { fixture.remove() }
    try FileManager.default.setAttributes(
      [.posixPermissions: 0o000],
      ofItemAtPath: fixture.url.path
    )

    #expect(throws: DocumentLoadError.notReadable) {
      try TXTParser().parse(url: fixture.url)
    }
  }
}

private struct TextFixture {
  let root: URL
  let url: URL

  init(data: Data) throws {
    root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-txt-parser-\(UUID().uuidString)")
    url = root.appending(path: "fixture.txt")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    try data.write(to: url)
  }

  func remove() {
    try? FileManager.default.setAttributes(
      [.posixPermissions: 0o600],
      ofItemAtPath: url.path
    )
    try? FileManager.default.removeItem(at: root)
  }
}

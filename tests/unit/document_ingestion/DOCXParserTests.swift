import Foundation
import Testing
import ZIPFoundation

@testable import MorerduoKit

@Suite("DOCXParser")
struct DOCXParserTests {
  @Test("extracts ordered WordprocessingML paragraphs")
  func extractsParagraphs() throws {
    let fixture = try DOCXFixture(entries: [
      .file(path: "word/document.xml", data: Data(validDocumentXML.utf8))
    ])
    defer { fixture.remove() }

    let paragraphs = try DOCXParser().parse(url: fixture.url)

    #expect(paragraphs == ["Hello world", "Second paragraph"])
  }

  @Test("rejects a corrupt archive")
  func rejectsCorruptArchive() throws {
    let fixture = try DOCXFixture(rawData: Data("not a zip".utf8))
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.corrupted) {
      try DOCXParser().parse(url: fixture.url)
    }
  }

  @Test("rejects an archive without word/document.xml")
  func rejectsMissingDocumentXML() throws {
    let fixture = try DOCXFixture(entries: [
      .file(path: "[Content_Types].xml", data: Data("<Types/>".utf8))
    ])
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.corrupted) {
      try DOCXParser().parse(url: fixture.url)
    }
  }

  @Test("rejects a document.xml entry over 50MB before extraction")
  func rejectsOversizedEntry() throws {
    let fixture = try DOCXFixture(entries: [
      .repeatingFile(
        path: "word/document.xml",
        byte: 0x41,
        count: DocumentLimits.maximumDOCXEntryBytes + 1
      )
    ])
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.unsafeArchive) {
      try DOCXParser().parse(url: fixture.url)
    }
  }

  @Test("rejects a symbolic-link document entry")
  func rejectsMaliciousEntry() throws {
    let fixture = try DOCXFixture(entries: [
      .symbolicLink(path: "word/document.xml", destination: "../../outside")
    ])
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.unsafeArchive) {
      try DOCXParser().parse(url: fixture.url)
    }
  }

  private var validDocumentXML: String {
    """
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>Hello</w:t></w:r><w:r><w:t xml:space="preserve"> world</w:t></w:r></w:p>
        <w:p><w:r><w:t>Second paragraph</w:t></w:r></w:p>
      </w:body>
    </w:document>
    """
  }
}

private struct DOCXFixture {
  let root: URL
  let url: URL

  init(rawData: Data) throws {
    root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-docx-parser-\(UUID().uuidString)")
    url = root.appending(path: "fixture.docx")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    try rawData.write(to: url)
  }

  init(entries: [FixtureArchiveEntry]) throws {
    root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-docx-parser-\(UUID().uuidString)")
    url = root.appending(path: "fixture.docx")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    let archive = try Archive(url: url, accessMode: .create)
    for entry in entries {
      try archive.addEntry(
        with: entry.path,
        type: entry.type,
        uncompressedSize: entry.size,
        compressionMethod: .deflate,
        provider: entry.provider
      )
    }
  }

  func remove() {
    try? FileManager.default.removeItem(at: root)
  }
}

private struct FixtureArchiveEntry {
  let path: String
  let type: Entry.EntryType
  let size: Int64
  let provider: Provider

  static func file(path: String, data: Data) -> Self {
    Self(
      path: path,
      type: .file,
      size: Int64(data.count),
      provider: dataProvider(data)
    )
  }

  static func repeatingFile(path: String, byte: UInt8, count: Int64) -> Self {
    Self(
      path: path,
      type: .file,
      size: count,
      provider: { position, size in
        let remaining = count - position
        return Data(repeating: byte, count: min(size, Int(remaining)))
      }
    )
  }

  static func symbolicLink(path: String, destination: String) -> Self {
    let data = Data(destination.utf8)
    return Self(
      path: path,
      type: .symlink,
      size: Int64(data.count),
      provider: dataProvider(data)
    )
  }

  private static func dataProvider(_ data: Data) -> Provider {
    { position, size in
      let lowerBound = Int(position)
      let upperBound = min(lowerBound + size, data.count)
      return data.subdata(in: lowerBound..<upperBound)
    }
  }
}

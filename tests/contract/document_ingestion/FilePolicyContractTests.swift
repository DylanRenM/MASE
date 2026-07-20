import Foundation
import Testing

@testable import MorerduoKit

@Suite("FilePolicy contract")
struct FilePolicyContractTests {
  @Test(
    "accepts each supported extension",
    arguments: [
      ("txt", DocumentKind.txt),
      ("docx", DocumentKind.docx),
      ("pdf", DocumentKind.pdf),
    ]
  )
  func acceptsSupportedExtension(fileExtension: String, expectedKind: DocumentKind) throws {
    let fixture = try TemporaryFileFixture(fileExtension: fileExtension, size: 1)
    defer { fixture.remove() }

    let validated = try FilePolicy.validate(url: fixture.url)

    #expect(validated.kind == expectedKind)
    #expect(validated.fingerprint.size == 1)
  }

  @Test("accepts a file exactly at the 20MB boundary")
  func acceptsMaximumBoundary() throws {
    let fixture = try TemporaryFileFixture(
      fileExtension: "txt",
      size: DocumentLimits.maximumSourceBytes
    )
    defer { fixture.remove() }

    let validated = try FilePolicy.validate(url: fixture.url)

    #expect(validated.fingerprint.size == DocumentLimits.maximumSourceBytes)
  }

  @Test("rejects a file over 20MB before parsing")
  func rejectsFileOverMaximum() throws {
    let fixture = try TemporaryFileFixture(
      fileExtension: "pdf",
      size: DocumentLimits.maximumSourceBytes + 1
    )
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.tooLarge) {
      try FilePolicy.validate(url: fixture.url)
    }
  }

  @Test("rejects the legacy DOC format")
  func rejectsLegacyDOC() throws {
    let fixture = try TemporaryFileFixture(fileExtension: "doc", size: 1)
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.unsupportedFormat) {
      try FilePolicy.validate(url: fixture.url)
    }
  }

  @Test("rejects a directory even when its extension is supported")
  func rejectsDirectory() throws {
    let root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-directory-\(UUID().uuidString).txt")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: root) }

    #expect(throws: DocumentLoadError.notRegularFile) {
      try FilePolicy.validate(url: root)
    }
  }

  @Test("rejects an unreadable regular file")
  func rejectsUnreadableFile() throws {
    let fixture = try TemporaryFileFixture(fileExtension: "txt", size: 1)
    defer { fixture.remove() }
    try FileManager.default.setAttributes(
      [.posixPermissions: 0o000],
      ofItemAtPath: fixture.url.path
    )

    #expect(throws: DocumentLoadError.notReadable) {
      try FilePolicy.validate(url: fixture.url)
    }
  }
}

private struct TemporaryFileFixture {
  let root: URL
  let url: URL

  init(fileExtension: String, size: Int64) throws {
    root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-file-policy-\(UUID().uuidString)")
    url = root.appending(path: "fixture.\(fileExtension)")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    guard FileManager.default.createFile(atPath: url.path, contents: nil) else {
      throw CocoaError(.fileWriteUnknown)
    }
    let handle = try FileHandle(forWritingTo: url)
    defer { try? handle.close() }
    try handle.truncate(atOffset: UInt64(size))
  }

  func remove() {
    try? FileManager.default.setAttributes(
      [.posixPermissions: 0o600],
      ofItemAtPath: url.path
    )
    try? FileManager.default.removeItem(at: root)
  }
}

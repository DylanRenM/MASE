import Foundation
import Testing

@Suite("Native E2E sandbox")
struct NativeSandboxTests {
  @Test("snapshot restore returns the directory to byte-identical state")
  func snapshotRestoreIsByteIdentical() throws {
    let root = try makeSandboxDirectory()
    defer { try? FileManager.default.removeItem(at: root) }
    try write("original", to: root.appending(path: "nested/original.txt"))
    let sandbox = try NativeSandbox(root: root)
    let snapshot = try sandbox.snapshot()

    try write("changed", to: root.appending(path: "nested/original.txt"))
    try write("added", to: root.appending(path: "added.txt"))
    try sandbox.restore(snapshot)

    #expect(try sandbox.isIdentical(to: snapshot))
    #expect(!FileManager.default.fileExists(atPath: root.appending(path: "added.txt").path))
    #expect(
      try String(contentsOf: root.appending(path: "nested/original.txt"), encoding: .utf8)
        == "original"
    )
  }

  @Test("verification detects changed bytes")
  func verificationDetectsChangedBytes() throws {
    let root = try makeSandboxDirectory()
    defer { try? FileManager.default.removeItem(at: root) }
    try write("before", to: root.appending(path: "source.txt"))
    let sandbox = try NativeSandbox(root: root)
    let snapshot = try sandbox.snapshot()

    try write("after", to: root.appending(path: "source.txt"))

    #expect(try !sandbox.isIdentical(to: snapshot))
  }

  @Test("sandbox rejects roots outside the temporary directory")
  func sandboxRejectsUnsafeRoot() {
    #expect(throws: NativeSandboxError.unsafeRoot) {
      try NativeSandbox(root: URL(fileURLWithPath: "/Users"))
    }
  }

  @Test("spec wrapper restores and verifies after a successful scenario")
  func specWrapperRestoresAfterSuccess() throws {
    let root = try makeSandboxDirectory()
    defer { try? FileManager.default.removeItem(at: root) }
    let original = root.appending(path: "source.txt")
    try write("before", to: original)

    try E2ESpecSandbox(root: root).run {
      try write("changed", to: original)
      try write("added", to: root.appending(path: "added.txt"))
    }

    #expect(try String(contentsOf: original, encoding: .utf8) == "before")
    #expect(!FileManager.default.fileExists(atPath: root.appending(path: "added.txt").path))
  }

  @Test("spec wrapper restores before rethrowing a scenario failure")
  func specWrapperRestoresAfterFailure() throws {
    let root = try makeSandboxDirectory()
    defer { try? FileManager.default.removeItem(at: root) }
    let original = root.appending(path: "source.txt")
    try write("before", to: original)

    #expect(throws: FixtureFailure.expected) {
      try E2ESpecSandbox(root: root).run {
        try write("changed", to: original)
        throw FixtureFailure.expected
      }
    }

    #expect(try String(contentsOf: original, encoding: .utf8) == "before")
  }

  private func makeSandboxDirectory() throws -> URL {
    let root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-e2e-\(UUID().uuidString)", directoryHint: .isDirectory)
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    return root
  }

  private func write(_ value: String, to url: URL) throws {
    try FileManager.default.createDirectory(
      at: url.deletingLastPathComponent(),
      withIntermediateDirectories: true
    )
    try Data(value.utf8).write(to: url, options: .atomic)
  }
}

private enum FixtureFailure: Error {
  case expected
}

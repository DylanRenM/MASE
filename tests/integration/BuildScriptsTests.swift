import Foundation
import Testing

@Suite("Local build scripts")
struct BuildScriptsTests {
  @Test("bundle script reports a missing executable")
  func bundleScriptReportsMissingExecutable() throws {
    let script = repositoryRoot.appending(path: "scripts/build-morerduo-app.sh")
    try #require(FileManager.default.isExecutableFile(atPath: script.path))
    let temporaryDirectory = try temporaryDirectory()
    defer { try? FileManager.default.removeItem(at: temporaryDirectory) }

    let result = try run(
      script,
      arguments: [
        "--executable", repositoryRoot.appending(path: "missing/MorerduoApp").path,
        "--output", temporaryDirectory.appending(path: "磨耳朵.app").path,
      ]
    )

    #expect(result.status != 0)
    #expect(result.standardError.contains("executable not found"))
  }

  @Test("verify script rejects a directory without a package manifest")
  func verifyScriptRejectsMissingManifest() throws {
    let script = repositoryRoot.appending(path: "scripts/verify-morerduo.sh")
    try #require(FileManager.default.isExecutableFile(atPath: script.path))
    let temporaryDirectory = try temporaryDirectory()
    defer { try? FileManager.default.removeItem(at: temporaryDirectory) }

    let result = try run(
      script,
      arguments: ["--project-root", temporaryDirectory.path]
    )

    #expect(result.status != 0)
    #expect(result.standardError.contains("Package.swift not found"))
  }

  @Test("bundle script creates a valid ad-hoc signed app")
  func bundleScriptCreatesSignedApp() throws {
    let script = repositoryRoot.appending(path: "scripts/build-morerduo-app.sh")
    try #require(FileManager.default.isExecutableFile(atPath: script.path))
    let temporaryDirectory = try temporaryDirectory()
    defer { try? FileManager.default.removeItem(at: temporaryDirectory) }
    let app = temporaryDirectory.appending(path: "磨耳朵.app")

    let buildResult = try run(
      script,
      arguments: [
        "--executable", "/usr/bin/true",
        "--output", app.path,
      ]
    )

    #expect(buildResult.status == 0)
    #expect(
      FileManager.default.isExecutableFile(
        atPath: app.appending(path: "Contents/MacOS/MorerduoApp").path
      )
    )
    #expect(
      FileManager.default.fileExists(
        atPath: app.appending(path: "Contents/Info.plist").path
      )
    )
    #expect(
      try run(
        URL(fileURLWithPath: "/usr/bin/codesign"),
        arguments: ["--verify", "--deep", "--strict", app.path]
      ).status == 0
    )
  }

  private var repositoryRoot: URL {
    URL(fileURLWithPath: #filePath)
      .deletingLastPathComponent()
      .deletingLastPathComponent()
      .deletingLastPathComponent()
  }

  private func temporaryDirectory() throws -> URL {
    let directory = FileManager.default.temporaryDirectory
      .appending(path: UUID().uuidString, directoryHint: .isDirectory)
    try FileManager.default.createDirectory(
      at: directory,
      withIntermediateDirectories: true
    )
    return directory
  }

  private func run(_ executable: URL, arguments: [String]) throws -> ProcessResult {
    let process = Process()
    let standardOutput = Pipe()
    let standardError = Pipe()
    process.executableURL = executable
    process.arguments = arguments
    process.standardOutput = standardOutput
    process.standardError = standardError

    try process.run()
    process.waitUntilExit()

    return ProcessResult(
      status: process.terminationStatus,
      standardOutput: String(
        decoding: standardOutput.fileHandleForReading.readDataToEndOfFile(),
        as: UTF8.self
      ),
      standardError: String(
        decoding: standardError.fileHandleForReading.readDataToEndOfFile(),
        as: UTF8.self
      )
    )
  }
}

private struct ProcessResult {
  let status: Int32
  let standardOutput: String
  let standardError: String
}

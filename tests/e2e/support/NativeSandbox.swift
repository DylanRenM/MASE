import Darwin
import Foundation

enum NativeSandboxError: Error, Equatable {
  case unsafeRoot
  case rootMissing
  case snapshotRootMismatch
  case unsupportedEntry(String)
  case restorationMismatch
}

struct E2ESpecSandbox {
  private let sandbox: NativeSandbox

  init(root: URL, fileManager: FileManager = .default) throws {
    sandbox = try NativeSandbox(root: root, fileManager: fileManager)
  }

  func run<ResultValue>(_ scenario: () throws -> ResultValue) throws -> ResultValue {
    let snapshot = try sandbox.snapshot()
    let scenarioResult: Result<ResultValue, Error>
    do {
      scenarioResult = .success(try scenario())
    } catch {
      scenarioResult = .failure(error)
    }

    try sandbox.restore(snapshot)
    guard try sandbox.isIdentical(to: snapshot) else {
      throw NativeSandboxError.restorationMismatch
    }
    return try scenarioResult.get()
  }

  @MainActor
  func runAsync<ResultValue>(_ scenario: () async throws -> ResultValue) async throws
    -> ResultValue
  {
    let snapshot = try sandbox.snapshot()
    let scenarioResult: Result<ResultValue, Error>
    do {
      scenarioResult = .success(try await scenario())
    } catch {
      scenarioResult = .failure(error)
    }

    try sandbox.restore(snapshot)
    guard try sandbox.isIdentical(to: snapshot) else {
      throw NativeSandboxError.restorationMismatch
    }
    return try scenarioResult.get()
  }
}

struct NativeSandboxSnapshot: Equatable, Sendable {
  let rootPath: String
  let directories: [String]
  let files: [String: Data]
}

struct NativeSandbox {
  private let root: URL
  private let fileManager: FileManager

  init(root: URL, fileManager: FileManager = .default) throws {
    let standardizedRoot = root.standardizedFileURL
    let resolvedRoot = standardizedRoot.resolvingSymlinksInPath()
    let temporaryRoot = fileManager.temporaryDirectory
      .standardizedFileURL
      .resolvingSymlinksInPath()
    let allowedPrefix =
      temporaryRoot.path.hasSuffix("/")
      ? temporaryRoot.path
      : temporaryRoot.path + "/"

    guard resolvedRoot.path.hasPrefix(allowedPrefix) else {
      throw NativeSandboxError.unsafeRoot
    }
    self.root = standardizedRoot
    self.fileManager = fileManager
  }

  func snapshot() throws -> NativeSandboxSnapshot {
    var isDirectory: ObjCBool = false
    guard fileManager.fileExists(atPath: root.path, isDirectory: &isDirectory),
      isDirectory.boolValue
    else {
      throw NativeSandboxError.rootMissing
    }

    var directories: [String] = []
    var files: [String: Data] = [:]
    guard
      let enumerator = fileManager.enumerator(
        at: root,
        includingPropertiesForKeys: nil,
        options: []
      )
    else {
      throw NativeSandboxError.rootMissing
    }

    for case let entry as URL in enumerator {
      let kind = try entryKind(entry)
      if kind == .symbolicLink {
        throw NativeSandboxError.unsupportedEntry(entry.lastPathComponent)
      }
      let relativePath = try relativePath(for: entry)
      switch kind {
      case .symbolicLink:
        throw NativeSandboxError.unsupportedEntry(relativePath)
      case .directory:
        directories.append(relativePath)
      case .regularFile:
        files[relativePath] = try Data(contentsOf: entry, options: .mappedIfSafe)
      case .unsupported:
        throw NativeSandboxError.unsupportedEntry(relativePath)
      }
    }

    return NativeSandboxSnapshot(
      rootPath: root.path,
      directories: directories.sorted(),
      files: files
    )
  }

  func restore(_ snapshot: NativeSandboxSnapshot) throws {
    guard snapshot.rootPath == root.path else {
      throw NativeSandboxError.snapshotRootMismatch
    }

    if fileManager.fileExists(atPath: root.path) {
      try fileManager.removeItem(at: root)
    }
    try fileManager.createDirectory(at: root, withIntermediateDirectories: true)

    for relativePath in snapshot.directories.sorted(by: directoryOrder) {
      try fileManager.createDirectory(
        at: root.appending(path: relativePath, directoryHint: .isDirectory),
        withIntermediateDirectories: true
      )
    }
    for relativePath in snapshot.files.keys.sorted() {
      guard let data = snapshot.files[relativePath] else {
        continue
      }
      let destination = root.appending(path: relativePath)
      try fileManager.createDirectory(
        at: destination.deletingLastPathComponent(),
        withIntermediateDirectories: true
      )
      try data.write(to: destination, options: .atomic)
    }
  }

  func isIdentical(to snapshot: NativeSandboxSnapshot) throws -> Bool {
    try self.snapshot() == snapshot
  }

  private func relativePath(for entry: URL) throws -> String {
    let resolvedRootPath = root.resolvingSymlinksInPath().path
    let resolvedEntryPath = entry.resolvingSymlinksInPath().path
    let prefix =
      resolvedRootPath.hasSuffix("/")
      ? resolvedRootPath
      : resolvedRootPath + "/"
    guard resolvedEntryPath.hasPrefix(prefix) else {
      throw NativeSandboxError.unsupportedEntry(entry.lastPathComponent)
    }
    return String(resolvedEntryPath.dropFirst(prefix.count))
  }

  private func entryKind(_ entry: URL) throws -> EntryKind {
    var information = stat()
    let result = entry.path.withCString { path in
      lstat(path, &information)
    }
    guard result == 0 else {
      throw CocoaError(.fileReadUnknown)
    }

    switch information.st_mode & S_IFMT {
    case S_IFDIR:
      return .directory
    case S_IFREG:
      return .regularFile
    case S_IFLNK:
      return .symbolicLink
    default:
      return .unsupported
    }
  }

  private func directoryOrder(_ lhs: String, _ rhs: String) -> Bool {
    let lhsDepth = lhs.split(separator: "/").count
    let rhsDepth = rhs.split(separator: "/").count
    return lhsDepth == rhsDepth ? lhs < rhs : lhsDepth < rhsDepth
  }
}

private enum EntryKind: Equatable {
  case directory
  case regularFile
  case symbolicLink
  case unsupported
}

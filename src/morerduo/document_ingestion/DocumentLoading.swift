import Foundation

public protocol DocumentLoading: Sendable {
  func load(url: URL) async throws -> ParsedDocument
}

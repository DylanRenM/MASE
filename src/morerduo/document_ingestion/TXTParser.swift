import Foundation

public struct TXTParser: Sendable {
  public init() {}

  public func parse(url: URL) throws -> [String] {
    let data: Data
    do {
      data = try Data(contentsOf: url, options: .mappedIfSafe)
    } catch {
      throw DocumentLoadError.notReadable
    }

    guard !data.isEmpty else {
      throw DocumentLoadError.emptyContent
    }
    guard let text = String(data: data, encoding: .utf8) else {
      throw DocumentLoadError.unsupportedEncoding
    }

    let paragraphs = text.components(separatedBy: .newlines).filter { line in
      !line.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
    guard !paragraphs.isEmpty else {
      throw DocumentLoadError.emptyContent
    }
    return paragraphs
  }
}

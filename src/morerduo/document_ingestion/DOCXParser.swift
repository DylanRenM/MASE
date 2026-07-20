import Foundation
import ZIPFoundation

public struct DOCXParser: Sendable {
  private static let documentPath = "word/document.xml"

  public init() {}

  public func parse(url: URL) throws -> [String] {
    do {
      let archive = try Archive(url: url, accessMode: .read)
      try validateArchiveEntries(archive)
      guard let entry = archive[Self.documentPath] else {
        throw DocumentLoadError.corrupted
      }
      guard entry.type == .file else {
        throw DocumentLoadError.unsafeArchive
      }
      guard entry.uncompressedSize <= UInt64(DocumentLimits.maximumDOCXEntryBytes) else {
        throw DocumentLoadError.unsafeArchive
      }

      let data = try extract(entry: entry, from: archive)
      return try parseDocumentXML(data)
    } catch let error as DocumentLoadError {
      throw error
    } catch {
      throw DocumentLoadError.corrupted
    }
  }

  private func validateArchiveEntries(_ archive: Archive) throws {
    for entry in archive {
      let components = entry.path.split(separator: "/", omittingEmptySubsequences: false)
      let hasTraversal = components.contains("..") || components.contains(".")
      guard !entry.path.hasPrefix("/"), !entry.path.contains("\\"), !hasTraversal,
        entry.type != .symlink
      else {
        throw DocumentLoadError.unsafeArchive
      }
    }
  }

  private func extract(entry: Entry, from archive: Archive) throws -> Data {
    var data = Data()
    data.reserveCapacity(Int(entry.uncompressedSize))
    _ = try archive.extract(entry) { chunk in
      guard data.count + chunk.count <= DocumentLimits.maximumDOCXEntryBytes else {
        throw DocumentLoadError.unsafeArchive
      }
      data.append(chunk)
    }
    return data
  }

  private func parseDocumentXML(_ data: Data) throws -> [String] {
    let collector = DOCXTextCollector()
    let parser = XMLParser(data: data)
    parser.delegate = collector
    parser.shouldProcessNamespaces = true
    parser.shouldResolveExternalEntities = false
    parser.externalEntityResolvingPolicy = .never

    guard parser.parse() else {
      throw DocumentLoadError.corrupted
    }
    guard !collector.paragraphs.isEmpty else {
      throw DocumentLoadError.emptyContent
    }
    return collector.paragraphs
  }
}

private final class DOCXTextCollector: NSObject, XMLParserDelegate {
  private(set) var paragraphs: [String] = []
  private var currentParagraph = ""
  private var isInsideParagraph = false
  private var isInsideText = false

  func parser(
    _ parser: XMLParser,
    didStartElement elementName: String,
    namespaceURI: String?,
    qualifiedName qName: String?,
    attributes attributeDict: [String: String] = [:]
  ) {
    switch elementName {
    case "p":
      currentParagraph = ""
      isInsideParagraph = true
    case "t" where isInsideParagraph:
      isInsideText = true
    default:
      break
    }
  }

  func parser(_ parser: XMLParser, foundCharacters string: String) {
    guard isInsideParagraph, isInsideText else {
      return
    }
    currentParagraph.append(string)
  }

  func parser(
    _ parser: XMLParser,
    didEndElement elementName: String,
    namespaceURI: String?,
    qualifiedName qName: String?
  ) {
    switch elementName {
    case "t":
      isInsideText = false
    case "p":
      if !currentParagraph.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
        paragraphs.append(currentParagraph)
      }
      currentParagraph = ""
      isInsideParagraph = false
      isInsideText = false
    default:
      break
    }
  }
}

import AppKit
import CoreGraphics
import CoreText
import Foundation
import ZIPFoundation

struct E2EFixtureFactory {
  private static let oversizedFixtureBytes = 20 * 1024 * 1024 + 1
  private static let asciiCapitalA: UInt8 = 0x41

  let root: URL

  init(root: URL) throws {
    self.root = root
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
  }

  func textFile(name: String, contents: String) throws -> URL {
    let url = root.appending(path: name)
    try Data(contents.utf8).write(to: url, options: .atomic)
    return url
  }

  func docxFile(name: String, paragraphs: [String]) throws -> URL {
    let url = root.appending(path: name)
    let body = paragraphs.map {
      "<w:p><w:r><w:t>\(xmlEscaped($0))</w:t></w:r></w:p>"
    }.joined()
    let document = """
      <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
      <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>\(body)</w:body>
      </w:document>
      """
    let data = Data(document.utf8)
    let archive = try Archive(url: url, accessMode: .create)
    try archive.addEntry(
      with: "word/document.xml",
      type: .file,
      uncompressedSize: Int64(data.count),
      compressionMethod: .deflate
    ) { position, size in
      let lowerBound = Int(position)
      let upperBound = min(lowerBound + size, data.count)
      return data.subdata(in: lowerBound..<upperBound)
    }
    return url
  }

  func pdfFile(name: String, pageTexts: [String?]) throws -> URL {
    let url = root.appending(path: name)
    guard let consumer = CGDataConsumer(url: url as CFURL) else {
      throw CocoaError(.fileWriteUnknown)
    }
    var mediaBox = CGRect(x: 0, y: 0, width: 612, height: 792)
    guard let context = CGContext(consumer: consumer, mediaBox: &mediaBox, nil) else {
      throw CocoaError(.fileWriteUnknown)
    }
    for text in pageTexts {
      context.beginPDFPage(nil)
      if let text {
        draw(text: text, in: context)
      } else {
        context.setFillColor(NSColor.black.cgColor)
        context.fill(CGRect(x: 60, y: 650, width: 120, height: 40))
      }
      context.endPDFPage()
    }
    context.closePDF()
    return url
  }

  func rawFile(name: String, data: Data) throws -> URL {
    let url = root.appending(path: name)
    try data.write(to: url, options: .atomic)
    return url
  }

  func oversizedTextFile(name: String) throws -> URL {
    let url = root.appending(path: name)
    let data = Data(
      repeating: Self.asciiCapitalA,
      count: Self.oversizedFixtureBytes
    )
    try data.write(to: url, options: .atomic)
    return url
  }

  private func xmlEscaped(_ value: String) -> String {
    value
      .replacingOccurrences(of: "&", with: "&amp;")
      .replacingOccurrences(of: "<", with: "&lt;")
      .replacingOccurrences(of: ">", with: "&gt;")
  }

  private func draw(text: String, in context: CGContext) {
    let attributedText = NSAttributedString(
      string: text,
      attributes: [
        .font: NSFont.systemFont(ofSize: 18),
        .foregroundColor: NSColor.black,
      ]
    )
    let framesetter = CTFramesetterCreateWithAttributedString(attributedText)
    let path = CGPath(
      rect: CGRect(x: 60, y: 650, width: 492, height: 80),
      transform: nil
    )
    let frame = CTFramesetterCreateFrame(framesetter, CFRange(), path, nil)
    CTFrameDraw(frame, context)
  }
}

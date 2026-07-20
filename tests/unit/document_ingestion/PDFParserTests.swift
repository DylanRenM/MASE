import AppKit
import CoreGraphics
import CoreText
import Foundation
import Testing

@testable import MorerduoKit

@Suite("PDFParser")
struct PDFParserTests {
  @Test("extracts text from a text PDF")
  func extractsTextPDF() throws {
    let fixture = try PDFFixture(pageTexts: ["Readable English page"])
    defer { fixture.remove() }

    let paragraphs = try PDFParser().parse(url: fixture.url)

    #expect(paragraphs == ["Readable English page"])
  }

  @Test("preserves PDF page order")
  func preservesPageOrder() throws {
    let fixture = try PDFFixture(pageTexts: ["First page", "Second page"])
    defer { fixture.remove() }

    let paragraphs = try PDFParser().parse(url: fixture.url)

    #expect(paragraphs == ["First page", "Second page"])
  }

  @Test("rejects a scanned PDF without extractable text")
  func rejectsScannedPDF() throws {
    let fixture = try PDFFixture(pageTexts: [nil])
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.scannedPDF) {
      try PDFParser().parse(url: fixture.url)
    }
  }

  @Test("rejects a corrupt PDF")
  func rejectsCorruptPDF() throws {
    let fixture = try PDFFixture(rawData: Data("not a pdf".utf8))
    defer { fixture.remove() }

    #expect(throws: DocumentLoadError.corrupted) {
      try PDFParser().parse(url: fixture.url)
    }
  }
}

private struct PDFFixture {
  let root: URL
  let url: URL

  init(rawData: Data) throws {
    root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-pdf-parser-\(UUID().uuidString)")
    url = root.appending(path: "fixture.pdf")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    try rawData.write(to: url)
  }

  init(pageTexts: [String?]) throws {
    root = FileManager.default.temporaryDirectory
      .appending(path: "morerduo-pdf-parser-\(UUID().uuidString)")
    url = root.appending(path: "fixture.pdf")
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
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
  }

  func remove() {
    try? FileManager.default.removeItem(at: root)
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

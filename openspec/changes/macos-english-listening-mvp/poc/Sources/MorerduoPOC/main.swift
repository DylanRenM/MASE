import AppKit
import AVFoundation
import CoreGraphics
import CoreText
import Darwin
import Foundation
import PDFKit
import SwiftUI
import ZIPFoundation

enum POCError: Error, CustomStringConvertible {
    case failed(String)

    var description: String {
        switch self {
        case let .failed(message): message
        }
    }
}

func require(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    guard condition() else { throw POCError.failed(message) }
}

func measure<T>(_ operation: () throws -> T) rethrows -> (T, TimeInterval) {
    let start = ContinuousClock.now
    let value = try operation()
    let duration = start.duration(to: .now)
    return (value, Double(duration.components.seconds) + Double(duration.components.attoseconds) / 1e18)
}

struct ProbeView: View {
    var body: some View {
        VStack(alignment: .leading) {
            Text("磨耳朵")
                .font(.title)
            ProgressView(value: 0.25)
            Button("播放") {}
        }
        .padding()
        .frame(width: 360)
    }
}

@MainActor
func verifySwiftUI() throws {
    let hostingView = NSHostingView(rootView: ProbeView())
    hostingView.layoutSubtreeIfNeeded()
    try require(hostingView.fittingSize.width > 0, "SwiftUI hosting view did not produce a layout")
    print("PASS SwiftUI: native view compiled and laid out")
}

final class SpeechProbe: NSObject, AVSpeechSynthesizerDelegate, @unchecked Sendable {
    private let lock = NSLock()
    private var frames = 0
    private var ranges: [NSRange] = []

    func addFrames(_ count: Int) {
        lock.lock()
        frames += count
        lock.unlock()
    }

    func frameCount() -> Int {
        lock.lock()
        defer { lock.unlock() }
        return frames
    }

    func rangeCount() -> Int {
        lock.lock()
        defer { lock.unlock() }
        return ranges.count
    }

    func speechSynthesizer(
        _ synthesizer: AVSpeechSynthesizer,
        willSpeakRangeOfSpeechString characterRange: NSRange,
        utterance: AVSpeechUtterance
    ) {
        lock.lock()
        ranges.append(characterRange)
        lock.unlock()
    }
}

final class AudibleSpeechProbe: NSObject, AVSpeechSynthesizerDelegate, @unchecked Sendable {
    let completion = DispatchSemaphore(value: 0)
    private(set) var finished = false

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        finished = true
        completion.signal()
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        completion.signal()
    }
}

func synthesizeSpeech(
    text: String,
    voice: AVSpeechSynthesisVoice,
    rate: Float
) throws -> (frames: Int, ranges: Int) {
    let synthesizer = AVSpeechSynthesizer()
    let utterance = AVSpeechUtterance(string: text)
    utterance.voice = voice
    utterance.rate = rate

    let completion = DispatchSemaphore(value: 0)
    let probe = SpeechProbe()
    synthesizer.delegate = probe
    synthesizer.write(utterance) { buffer in
        guard let pcmBuffer = buffer as? AVAudioPCMBuffer else { return }
        if pcmBuffer.frameLength == 0 {
            completion.signal()
        } else {
            probe.addFrames(Int(pcmBuffer.frameLength))
        }
    }

    let deadline = Date().addingTimeInterval(12)
    var completed = false
    while Date() < deadline {
        if completion.wait(timeout: .now()) == .success {
            completed = true
            break
        }
        RunLoop.current.run(until: Date().addingTimeInterval(0.05))
    }

    try require(completed, "AVSpeechSynthesizer did not complete within 12 seconds")
    try require(probe.frameCount() > 0, "AVSpeechSynthesizer produced no audio frames")
    return (probe.frameCount(), probe.rangeCount())
}

func verifySpeechSynthesis() throws {
    guard
        let primaryVoice = AVSpeechSynthesisVoice(language: "en-US"),
        let secondaryVoice = AVSpeechSynthesisVoice(language: "en-GB"),
        primaryVoice.identifier != secondaryVoice.identifier
    else {
        throw POCError.failed("Two distinct macOS English system voices are required for exploration")
    }

    let text = "English listening feasibility check with reliable progress tracking"
    let exploredVoices = [primaryVoice, secondaryVoice]
    var normalResults: [(frames: Int, ranges: Int)] = []
    for voice in exploredVoices {
        let result = try synthesizeSpeech(
            text: text,
            voice: voice,
            rate: AVSpeechUtteranceDefaultSpeechRate
        )
        try require(result.ranges > 0, "TTS delegate produced no character-range callbacks")
        normalResults.append(result)
    }
    let slow = try synthesizeSpeech(text: text, voice: primaryVoice, rate: 0.4)
    let fast = try synthesizeSpeech(text: text, voice: primaryVoice, rate: 0.6)

    try require(slow.frames > fast.frames, "Slow and fast rates did not produce distinguishable durations")
    print(
        "PASS TTS voices: \(primaryVoice.identifier) "
        + "(\(normalResults[0].ranges) ranges), \(secondaryVoice.identifier) "
        + "(\(normalResults[1].ranges) ranges); slow/fast ratio "
        + String(format: "%.2f", Double(slow.frames) / Double(fast.frames))
    )
}

@MainActor
func verifyAudibleSpeech() throws {
    guard let voice = AVSpeechSynthesisVoice(language: "en-US") else {
        throw POCError.failed("No macOS English system voice is available")
    }

    let synthesizer = AVSpeechSynthesizer()
    let probe = AudibleSpeechProbe()
    synthesizer.delegate = probe
    let utterance = AVSpeechUtterance(
        string: "Morerduo audible speech check. If you can hear this sentence, audio playback is working."
    )
    utterance.voice = voice
    utterance.rate = AVSpeechUtteranceDefaultSpeechRate
    synthesizer.speak(utterance)

    let deadline = Date().addingTimeInterval(15)
    while Date() < deadline, !probe.finished {
        if probe.completion.wait(timeout: .now()) == .success { break }
        RunLoop.current.run(until: Date().addingTimeInterval(0.05))
    }

    try require(probe.finished, "Audible TTS did not finish within 15 seconds")
    print("PASS audible TTS: \(voice.identifier)")
}

func makeTextPDF(at url: URL) throws {
    guard let consumer = CGDataConsumer(url: url as CFURL) else {
        throw POCError.failed("Unable to create PDF data consumer")
    }
    var mediaBox = CGRect(x: 0, y: 0, width: 612, height: 792)
    guard let context = CGContext(consumer: consumer, mediaBox: &mediaBox, nil) else {
        throw POCError.failed("Unable to create PDF context")
    }

    context.beginPDFPage(nil)
    let text = NSAttributedString(
        string: "PDF English extraction feasibility check",
        attributes: [
            .font: NSFont.systemFont(ofSize: 18),
            .foregroundColor: NSColor.black
        ]
    )
    let framesetter = CTFramesetterCreateWithAttributedString(text)
    let path = CGPath(rect: CGRect(x: 60, y: 650, width: 492, height: 80), transform: nil)
    let frame = CTFramesetterCreateFrame(framesetter, CFRange(), path, nil)
    CTFrameDraw(frame, context)
    context.endPDFPage()
    context.closePDF()
}

func verifyPDFKit(in temporaryDirectory: URL) throws {
    let pdfURL = temporaryDirectory.appendingPathComponent("text-fixture.pdf")
    try makeTextPDF(at: pdfURL)
    guard let document = PDFDocument(url: pdfURL), let page = document.page(at: 0) else {
        throw POCError.failed("PDFKit could not open the generated text PDF")
    }
    let extracted = page.string ?? ""
    try require(extracted.contains("English extraction"), "PDFKit did not extract expected text")
    print("PASS PDFKit: extracted \(extracted.count) characters")
}

final class DOCXTextCollector: NSObject, XMLParserDelegate {
    private(set) var textRuns: [String] = []
    private var capturesText = false
    private var currentText = ""

    func parser(
        _ parser: XMLParser,
        didStartElement elementName: String,
        namespaceURI: String?,
        qualifiedName qName: String?,
        attributes attributeDict: [String: String] = [:]
    ) {
        if elementName == "w:t" || elementName == "t" {
            capturesText = true
            currentText = ""
        }
    }

    func parser(_ parser: XMLParser, foundCharacters string: String) {
        if capturesText { currentText += string }
    }

    func parser(
        _ parser: XMLParser,
        didEndElement elementName: String,
        namespaceURI: String?,
        qualifiedName qName: String?
    ) {
        if elementName == "w:t" || elementName == "t" {
            capturesText = false
            textRuns.append(currentText)
        }
    }
}

func createDOCXFixture(at docxURL: URL, in temporaryDirectory: URL) throws {
    let staging = temporaryDirectory.appendingPathComponent("docx-staging", isDirectory: true)
    let word = staging.appendingPathComponent("word", isDirectory: true)
    try FileManager.default.createDirectory(at: word, withIntermediateDirectories: true)
    let xml = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body><w:p><w:r><w:t>DOCX English extraction feasibility check</w:t></w:r></w:p></w:body>
    </w:document>
    """
    try xml.write(to: word.appendingPathComponent("document.xml"), atomically: true, encoding: .utf8)

    let zip = Process()
    zip.executableURL = URL(fileURLWithPath: "/usr/bin/zip")
    zip.currentDirectoryURL = staging
    zip.arguments = ["-q", "-r", docxURL.path, "word"]
    try zip.run()
    zip.waitUntilExit()
    try require(zip.terminationStatus == 0, "Unable to create DOCX fixture")
}

func verifyZIPFoundationDOCX(in temporaryDirectory: URL) throws {
    let docxURL = temporaryDirectory.appendingPathComponent("fixture.docx")
    try createDOCXFixture(at: docxURL, in: temporaryDirectory)

    let extraction = temporaryDirectory.appendingPathComponent("docx-extracted", isDirectory: true)
    try FileManager.default.createDirectory(at: extraction, withIntermediateDirectories: true)
    try FileManager.default.unzipItem(at: docxURL, to: extraction)

    let documentXML = extraction.appendingPathComponent("word/document.xml")
    let parser = XMLParser(contentsOf: documentXML)
    let collector = DOCXTextCollector()
    parser?.delegate = collector
    try require(parser?.parse() == true, "Unable to parse DOCX document.xml")
    let extracted = collector.textRuns.joined(separator: " ")
    try require(extracted.contains("English extraction"), "DOCX text run was not extracted")
    print("PASS ZIPFoundation: DOCX unpacked and XML text extracted")
}

func filterEnglishASCII(_ text: String) -> String {
    var output = [UInt8]()
    output.reserveCapacity(text.utf8.count)
    var previousWasSpace = true

    for byte in text.utf8 {
        let isLetter = (65...90).contains(byte) || (97...122).contains(byte)
        if isLetter {
            output.append(byte)
            previousWasSpace = false
        } else if (byte == 9 || byte == 10 || byte == 13 || byte == 32), !previousWasSpace {
            output.append(32)
            previousWasSpace = true
        }
    }
    if output.last == 32 { output.removeLast() }
    return String(decoding: output, as: UTF8.self)
}

func verifyEnglishFilterPerformance() throws {
    let input = String(repeating: "Hello 123 世界!\n", count: 1_050_000)
    try require(input.utf8.count <= 20 * 1024 * 1024, "Performance fixture exceeds the 20MB product limit")
    let (filtered, seconds) = measure { filterEnglishASCII(input) }
    try require(!filtered.isEmpty, "English filter returned empty output")
    try require(filtered.utf8.allSatisfy { (65...90).contains($0) || (97...122).contains($0) || $0 == 32 }, "Filter output contains forbidden bytes")
    try require(seconds < 3.0, "20MB-class English filtering exceeded 3 seconds: \(seconds)")
    print(String(format: "PASS filter: %.1fMB in %.3fs", Double(input.utf8.count) / 1_048_576, seconds))
}

func detectFileMutation(
    named name: String,
    in temporaryDirectory: URL,
    mutation: @escaping @Sendable (URL) -> Void
) throws -> TimeInterval {
    let fileURL = temporaryDirectory.appendingPathComponent(name)
    try Data("before".utf8).write(to: fileURL)
    let descriptor = open(fileURL.path, O_EVTONLY)
    try require(descriptor >= 0, "Unable to open fixture for file monitoring")

    let detected = DispatchSemaphore(value: 0)
    let source = DispatchSource.makeFileSystemObjectSource(
        fileDescriptor: descriptor,
        eventMask: [.write, .extend, .attrib, .rename, .delete],
        queue: DispatchQueue(label: "morerduo.poc.file-monitor")
    )
    source.setEventHandler { detected.signal() }
    source.setCancelHandler { close(descriptor) }
    source.resume()

    let start = Date()
    DispatchQueue.global().asyncAfter(deadline: .now() + 0.2) {
        mutation(fileURL)
    }

    let result = detected.wait(timeout: .now() + 5)
    let elapsed = Date().timeIntervalSince(start)
    source.cancel()
    try require(result == .success, "File change was not detected within 5 seconds")
    return elapsed
}

func verifyFileMonitoring(in temporaryDirectory: URL) throws {
    let appendElapsed = try detectFileMutation(named: "monitor-append.txt", in: temporaryDirectory) { fileURL in
        if let handle = try? FileHandle(forWritingTo: fileURL) {
            _ = try? handle.seekToEnd()
            try? handle.write(contentsOf: Data(" after".utf8))
            try? handle.synchronize()
            try? handle.close()
        }
    }
    let replaceElapsed = try detectFileMutation(named: "monitor-replace.txt", in: temporaryDirectory) { fileURL in
        try? Data("replacement".utf8).write(to: fileURL, options: .atomic)
    }
    print(
        String(
            format: "PASS file monitor: append %.3fs, atomic replacement %.3fs",
            appendElapsed,
            replaceElapsed
        )
    )
}

@main
enum MorerduoPOC {
    @MainActor
    static func main() {
        if CommandLine.arguments.contains("--audible") {
            do {
                try verifyAudibleSpeech()
            } catch {
                fputs("FAIL \(error)\n", stderr)
                exit(EXIT_FAILURE)
            }
            return
        }

        if CommandLine.arguments.contains("--english-filtering") {
            do {
                try verifyEnglishFilterPerformance()
            } catch {
                fputs("FAIL \(error)\n", stderr)
                exit(EXIT_FAILURE)
            }
            return
        }

        let isDocumentIngestionOnly = CommandLine.arguments.contains("--document-ingestion")

        let temporaryDirectory = FileManager.default.temporaryDirectory
            .appendingPathComponent("morerduo-poc-\(UUID().uuidString)", isDirectory: true)

        do {
            try FileManager.default.createDirectory(at: temporaryDirectory, withIntermediateDirectories: true)
            defer { try? FileManager.default.removeItem(at: temporaryDirectory) }

            if isDocumentIngestionOnly {
                try verifyPDFKit(in: temporaryDirectory)
                try verifyZIPFoundationDOCX(in: temporaryDirectory)
                print("PASS document-ingestion dependency checks")
                return
            }

            try verifySwiftUI()
            try verifySpeechSynthesis()
            try verifyPDFKit(in: temporaryDirectory)
            try verifyZIPFoundationDOCX(in: temporaryDirectory)
            try verifyEnglishFilterPerformance()
            try verifyFileMonitoring(in: temporaryDirectory)
            print("PASS all Design L1 feasibility checks")
        } catch {
            fputs("FAIL \(error)\n", stderr)
            exit(EXIT_FAILURE)
        }
    }
}

@preconcurrency import AVFoundation

@MainActor
protocol SystemSpeechSynthesizing: AnyObject {
  var delegate: AVSpeechSynthesizerDelegate? { get set }

  func speak(_ utterance: AVSpeechUtterance)
  func pauseSpeaking(at boundary: AVSpeechBoundary) -> Bool
  func continueSpeaking() -> Bool
  func stopSpeaking(at boundary: AVSpeechBoundary) -> Bool
}

extension AVSpeechSynthesizer: SystemSpeechSynthesizing {}

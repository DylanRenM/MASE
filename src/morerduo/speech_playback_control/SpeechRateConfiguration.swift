public enum SpeechRateConfiguration {
  public static func rate(for speed: ReadingSpeed) -> Float {
    switch speed {
    case .slow:
      return 0.4
    case .normal:
      return 0.5
    case .fast:
      return 0.6
    }
  }
}

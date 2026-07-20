public protocol ReadingClock: Sendable {
  var now: Duration { get }
}

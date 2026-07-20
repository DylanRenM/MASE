public struct ContinuousReadingClock: ReadingClock, Sendable {
  private let clock: ContinuousClock
  private let origin: ContinuousClock.Instant

  public init() {
    let clock = ContinuousClock()
    self.clock = clock
    origin = clock.now
  }

  public var now: Duration {
    origin.duration(to: clock.now)
  }
}

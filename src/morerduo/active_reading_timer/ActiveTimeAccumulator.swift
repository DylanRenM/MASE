public struct ActiveTimeAccumulator: Equatable, Sendable {
  private let configuration: TimerConfiguration
  private var accumulated: Duration = .zero
  private var segmentStartedAt: Duration?
  private var hasEmittedExpiry = false
  private var retiredTokens: Set<TimerSessionToken> = []

  public private(set) var currentToken: TimerSessionToken?

  public init(configuration: TimerConfiguration) {
    self.configuration = configuration
  }

  public var isActive: Bool {
    segmentStartedAt != nil
  }

  public mutating func beginPlaying(now: Duration, token: TimerSessionToken) {
    guard !retiredTokens.contains(token) else {
      return
    }
    if currentToken != token {
      if let currentToken {
        retiredTokens.insert(currentToken)
      }
      accumulated = .zero
      hasEmittedExpiry = false
      currentToken = token
      segmentStartedAt = nil
    }
    if segmentStartedAt == nil {
      segmentStartedAt = now
    }
  }

  public mutating func freeze(now: Duration) {
    settle(now: now)
  }

  public mutating func stop(now: Duration) {
    settle(now: now)
    if let currentToken {
      retiredTokens.insert(currentToken)
    }
    accumulated = .zero
    segmentStartedAt = nil
    currentToken = nil
    hasEmittedExpiry = false
  }

  public func elapsed(now: Duration) -> Duration {
    guard let segmentStartedAt else {
      return accumulated
    }
    precondition(now >= segmentStartedAt, "now must not precede segment start")
    return accumulated + (now - segmentStartedAt)
  }

  public func remaining(now: Duration) -> Duration? {
    guard let limit = configuration.limit else {
      return nil
    }
    return max(limit - elapsed(now: now), .zero)
  }

  public mutating func takeExpiry(now: Duration) -> TimerExpiry? {
    guard
      !hasEmittedExpiry,
      let limit = configuration.limit,
      elapsed(now: now) >= limit,
      let currentToken
    else {
      return nil
    }
    hasEmittedExpiry = true
    return TimerExpiry(token: currentToken)
  }

  private mutating func settle(now: Duration) {
    guard let segmentStartedAt else {
      return
    }
    precondition(now >= segmentStartedAt, "now must not precede segment start")
    accumulated += now - segmentStartedAt
    self.segmentStartedAt = nil
  }
}

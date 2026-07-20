public struct TimerExpiry: Equatable, Sendable {
  public let token: TimerSessionToken

  public init(token: TimerSessionToken) {
    self.token = token
  }
}

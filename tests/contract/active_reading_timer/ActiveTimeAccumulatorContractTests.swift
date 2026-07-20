import Foundation
import Testing

@testable import MorerduoKit

@Suite("ActiveTimeAccumulator contract")
struct ActiveTimeAccumulatorContractTests {
  @Test("a stopped session token cannot emit expiry again")
  func stoppedTokenCannotExpireAgain() throws {
    var clock = ContractReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    let sessionToken = token(1)
    accumulator.beginPlaying(now: clock.now, token: sessionToken)
    clock.advance(by: .seconds(60))
    #expect(accumulator.takeExpiry(now: clock.now) == TimerExpiry(token: sessionToken))
    accumulator.stop(now: clock.now)

    accumulator.beginPlaying(now: clock.now, token: sessionToken)
    clock.advance(by: .seconds(60))

    #expect(accumulator.takeExpiry(now: clock.now) == nil)
    #expect(accumulator.currentToken == nil)
    #expect(!accumulator.isActive)
  }

  @Test("a retired token cannot replace the current session")
  func retiredTokenCannotReplaceCurrentSession() throws {
    var clock = ContractReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    let retiredToken = token(2)
    let currentToken = token(3)
    accumulator.beginPlaying(now: clock.now, token: retiredToken)
    clock.advance(by: .seconds(10))
    accumulator.beginPlaying(now: clock.now, token: currentToken)

    accumulator.beginPlaying(now: clock.now, token: retiredToken)
    clock.advance(by: .seconds(15))

    #expect(accumulator.currentToken == currentToken)
    #expect(accumulator.elapsed(now: clock.now) == .seconds(15))
  }

  @Test("repeated freeze settles an active segment only once")
  func repeatedFreezeIsIdempotent() throws {
    var clock = ContractReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    accumulator.beginPlaying(now: clock.now, token: token(4))
    clock.advance(by: .seconds(12))

    accumulator.freeze(now: clock.now)
    accumulator.freeze(now: clock.now)

    #expect(accumulator.elapsed(now: clock.now) == .seconds(12))
    #expect(!accumulator.isActive)
  }

  @Test("remaining time is clamped to zero after the limit")
  func remainingNeverBecomesNegative() throws {
    var clock = ContractReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    accumulator.beginPlaying(now: clock.now, token: token(5))
    clock.advance(by: .seconds(75))

    #expect(accumulator.remaining(now: clock.now) == .zero)
  }

  private func token(_ value: UInt8) -> TimerSessionToken {
    let suffix = String(format: "%012x", value)
    return TimerSessionToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
    )
  }
}

private struct ContractReadingClock: ReadingClock {
  private(set) var now: Duration = .zero

  mutating func advance(by duration: Duration) {
    precondition(duration >= .zero)
    now += duration
  }
}

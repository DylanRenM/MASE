import Foundation
import Testing

@testable import MorerduoKit

@Suite("ActiveTimeAccumulator")
struct ActiveTimeAccumulatorTests {
  @Test("unlimited playback never expires")
  func unlimitedNeverExpires() throws {
    var clock = ManualReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: nil)
    )
    accumulator.beginPlaying(now: clock.now, token: token(1))
    clock.advance(by: .seconds(10_000))

    #expect(accumulator.remaining(now: clock.now) == nil)
    #expect(accumulator.takeExpiry(now: clock.now) == nil)
  }

  @Test("playing time accumulates and pause time freezes")
  func pauseFreezesElapsedTime() throws {
    var clock = ManualReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    accumulator.beginPlaying(now: clock.now, token: token(1))
    clock.advance(by: .seconds(10))
    accumulator.freeze(now: clock.now)
    clock.advance(by: .seconds(20))

    #expect(accumulator.elapsed(now: clock.now) == .seconds(10))
    #expect(accumulator.remaining(now: clock.now) == .seconds(50))
  }

  @Test("reload prompt time freezes and resume continues accumulation")
  func promptFreezeThenResume() throws {
    var clock = ManualReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    let sessionToken = token(2)
    accumulator.beginPlaying(now: clock.now, token: sessionToken)
    clock.advance(by: .seconds(12))
    accumulator.freeze(now: clock.now)
    clock.advance(by: .seconds(30))
    accumulator.beginPlaying(now: clock.now, token: sessionToken)
    clock.advance(by: .seconds(8))

    #expect(accumulator.elapsed(now: clock.now) == .seconds(20))
  }

  @Test("stop clears elapsed time and the active segment")
  func stopClearsState() throws {
    var clock = ManualReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    accumulator.beginPlaying(now: clock.now, token: token(3))
    clock.advance(by: .seconds(25))

    accumulator.stop(now: clock.now)

    #expect(accumulator.elapsed(now: clock.now) == .zero)
    #expect(!accumulator.isActive)
    #expect(accumulator.currentToken == nil)
  }

  @Test("expiry is emitted once per session token")
  func expiryIsEmittedOnce() throws {
    var clock = ManualReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    let sessionToken = token(4)
    accumulator.beginPlaying(now: clock.now, token: sessionToken)
    clock.advance(by: .seconds(60))

    #expect(accumulator.takeExpiry(now: clock.now) == TimerExpiry(token: sessionToken))
    #expect(accumulator.takeExpiry(now: clock.now) == nil)
    #expect(accumulator.remaining(now: clock.now) == .zero)
  }

  @Test("a new session token may expire independently")
  func newTokenGetsIndependentExpiry() throws {
    var clock = ManualReadingClock()
    var accumulator = ActiveTimeAccumulator(
      configuration: try TimerConfiguration(minutes: 1)
    )
    accumulator.beginPlaying(now: clock.now, token: token(5))
    clock.advance(by: .seconds(60))
    _ = accumulator.takeExpiry(now: clock.now)
    accumulator.stop(now: clock.now)

    let nextToken = token(6)
    accumulator.beginPlaying(now: clock.now, token: nextToken)
    clock.advance(by: .seconds(60))

    #expect(accumulator.takeExpiry(now: clock.now) == TimerExpiry(token: nextToken))
  }

  private func token(_ value: UInt8) -> TimerSessionToken {
    let suffix = String(format: "%012x", value)
    return TimerSessionToken(
      rawValue: UUID(uuidString: "00000000-0000-0000-0000-\(suffix)")!
    )
  }
}

private struct ManualReadingClock: ReadingClock {
  private(set) var now: Duration = .zero

  mutating func advance(by duration: Duration) {
    precondition(duration >= .zero)
    now += duration
  }
}

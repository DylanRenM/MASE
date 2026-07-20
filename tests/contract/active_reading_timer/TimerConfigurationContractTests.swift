import Testing

@testable import MorerduoKit

@Suite("TimerConfiguration contract")
struct TimerConfigurationContractTests {
  @Test("nil and blank input mean unlimited")
  func acceptsUnlimited() throws {
    #expect(try TimerConfiguration(minutes: nil).limit == nil)
    #expect(try TimerConfiguration.parse("").limit == nil)
    #expect(try TimerConfiguration.parse("   ").limit == nil)
  }

  @Test("accepts the one-minute minimum")
  func acceptsMinimum() throws {
    #expect(try TimerConfiguration(minutes: 1).limit == .seconds(60))
    #expect(try TimerConfiguration.parse("1").limit == .seconds(60))
  }

  @Test("accepts the 240-minute maximum")
  func acceptsMaximum() throws {
    #expect(try TimerConfiguration(minutes: 240).limit == .seconds(14_400))
    #expect(try TimerConfiguration.parse("240").limit == .seconds(14_400))
  }

  @Test("rejects integers outside 1 through 240", arguments: [-1, 0, 241])
  func rejectsOutOfRangeInteger(minutes: Int) {
    #expect(throws: TimerConfigurationError.invalidMinutes) {
      try TimerConfiguration(minutes: minutes)
    }
  }

  @Test(
    "rejects decimals and non-numeric input",
    arguments: ["1.5", "one", "-1", "241"]
  )
  func rejectsInvalidText(input: String) {
    #expect(throws: TimerConfigurationError.invalidMinutes) {
      try TimerConfiguration.parse(input)
    }
  }
}

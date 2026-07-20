import Foundation
import Testing

@testable import MorerduoKit

@Suite("Runtime contracts")
struct ContractTests {
  @Test("satisfied checks succeed", arguments: ContractCheckKind.allCases)
  func satisfiedChecksSucceed(kind: ContractCheckKind) {
    let result: ContractOutcome
    switch kind {
    case .requirement:
      result = Contract.require(true, "valid input", mode: .strict)
    case .postcondition:
      result = Contract.ensure(true, "valid output", mode: .strict)
    case .invariant:
      result = Contract.invariantCheck(true, "valid state", mode: .strict)
    }

    #expect(result == .satisfied)
  }

  @Test("relaxed checks return typed violations", arguments: ContractCheckKind.allCases)
  func relaxedChecksReturnTypedViolations(kind: ContractCheckKind) {
    let result: ContractOutcome
    switch kind {
    case .requirement:
      result = Contract.require(false, "invalid input", mode: .relaxed)
    case .postcondition:
      result = Contract.ensure(false, "invalid output", mode: .relaxed)
    case .invariant:
      result = Contract.invariantCheck(false, "invalid state", mode: .relaxed)
    }

    guard case .violation(let violation) = result else {
      Issue.record("expected a typed contract violation")
      return
    }
    #expect(violation.kind == kind)
    #expect(!violation.message.isEmpty)
  }

  @Test(
    "strict violations terminate the process",
    arguments: [
      (ContractCheckKind.requirement, "require"),
      (ContractCheckKind.postcondition, "ensure"),
      (ContractCheckKind.invariant, "invariant"),
    ])
  func strictViolationsTerminateProcess(kind: ContractCheckKind, probe: String) throws {
    let process = Process()
    let errorPipe = Pipe()
    process.executableURL = URL(fileURLWithPath: CommandLine.arguments[0])
    process.environment = ProcessInfo.processInfo.environment.merging(
      ["MORERDUO_CONTRACT_PROBE": probe],
      uniquingKeysWith: { _, new in new }
    )
    process.standardOutput = Pipe()
    process.standardError = errorPipe

    try process.run()
    process.waitUntilExit()

    #expect(process.terminationStatus != 0, "strict \(kind) must terminate")
  }
}

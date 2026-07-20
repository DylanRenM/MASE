import Darwin
import Foundation
import Testing

@testable import MorerduoKit

@main
struct ContractTestRunner {
  static func main() async {
    if let probe = ProcessInfo.processInfo.environment["MORERDUO_CONTRACT_PROBE"] {
      runStrictProbe(probe)
      exit(EXIT_SUCCESS)
    }
    await Testing.__swiftPMEntryPoint() as Never
  }

  private static func runStrictProbe(_ probe: String) {
    switch probe {
    case "require":
      Contract.require(false, "strict require probe", mode: .strict)
    case "ensure":
      Contract.ensure(false, "strict ensure probe", mode: .strict)
    case "invariant":
      Contract.invariantCheck(false, "strict invariant probe", mode: .strict)
    default:
      exit(EXIT_FAILURE)
    }
  }
}

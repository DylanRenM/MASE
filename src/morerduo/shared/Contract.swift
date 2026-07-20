public enum ContractMode: Sendable {
  case strict
  case relaxed
}

public enum ContractCheckKind: String, CaseIterable, Equatable, Sendable {
  case requirement
  case postcondition
  case invariant
}

public struct ContractViolation: Error, Equatable, Sendable {
  public let kind: ContractCheckKind
  public let message: String

  public init(kind: ContractCheckKind, message: String) {
    self.kind = kind
    self.message = message
  }
}

public enum ContractOutcome: Equatable, Sendable {
  case satisfied
  case violation(ContractViolation)
}

public enum Contract {
  @discardableResult
  public static func require(
    _ condition: @autoclosure () -> Bool,
    _ message: String,
    mode: ContractMode
  ) -> ContractOutcome {
    check(condition(), kind: .requirement, message: message, mode: mode)
  }

  @discardableResult
  public static func ensure(
    _ condition: @autoclosure () -> Bool,
    _ message: String,
    mode: ContractMode
  ) -> ContractOutcome {
    check(condition(), kind: .postcondition, message: message, mode: mode)
  }

  @discardableResult
  public static func invariantCheck(
    _ condition: @autoclosure () -> Bool,
    _ message: String,
    mode: ContractMode
  ) -> ContractOutcome {
    check(condition(), kind: .invariant, message: message, mode: mode)
  }

  private static func check(
    _ condition: Bool,
    kind: ContractCheckKind,
    message: String,
    mode: ContractMode
  ) -> ContractOutcome {
    guard !condition else {
      return .satisfied
    }

    let violation = ContractViolation(kind: kind, message: message)
    switch mode {
    case .strict:
      preconditionFailure("[\(kind.rawValue)] \(message)")
    case .relaxed:
      return .violation(violation)
    }
  }
}

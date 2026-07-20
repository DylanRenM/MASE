public struct SourceFileChange: OptionSet, Equatable, Sendable {
  public let rawValue: UInt8

  public init(rawValue: UInt8) {
    self.rawValue = rawValue
  }

  public static let write = Self(rawValue: 1 << 0)
  public static let extend = Self(rawValue: 1 << 1)
  public static let attribute = Self(rawValue: 1 << 2)
  public static let rename = Self(rawValue: 1 << 3)
  public static let delete = Self(rawValue: 1 << 4)
}

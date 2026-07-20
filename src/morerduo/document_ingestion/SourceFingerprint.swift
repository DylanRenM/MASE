import Foundation

public struct SourceFingerprint: Equatable, Sendable {
  public let size: Int64
  public let modifiedAt: Date
  public let resourceID: Data?

  public init(size: Int64, modifiedAt: Date, resourceID: Data?) {
    self.size = size
    self.modifiedAt = modifiedAt
    self.resourceID = resourceID
  }
}

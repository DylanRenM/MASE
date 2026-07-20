import Foundation

public struct ValidatedSource: Equatable, Sendable {
  public let url: URL
  public let kind: DocumentKind
  public let fingerprint: SourceFingerprint

  public init(url: URL, kind: DocumentKind, fingerprint: SourceFingerprint) {
    self.url = url
    self.kind = kind
    self.fingerprint = fingerprint
  }
}

import Foundation

public enum SourceAvailabilityVerifier {
  public static func verify(_ source: ValidatedSource) throws {
    let uncachedURL = URL(fileURLWithPath: source.url.path)
    _ = try FilePolicy.validate(url: uncachedURL)
  }
}

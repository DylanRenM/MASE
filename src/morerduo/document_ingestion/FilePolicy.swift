import Foundation

public enum FilePolicy {
  private static let resourceKeys: Set<URLResourceKey> = [
    .isRegularFileKey,
    .isReadableKey,
    .fileSizeKey,
    .contentModificationDateKey,
    .fileResourceIdentifierKey,
  ]

  public static func validate(url: URL) throws -> ValidatedSource {
    let values: URLResourceValues
    do {
      values = try url.resourceValues(forKeys: resourceKeys)
    } catch {
      throw DocumentLoadError.notReadable
    }
    return try validate(url: url, resourceValues: values)
  }

  public static func validate(
    url: URL,
    resourceValues: URLResourceValues
  ) throws -> ValidatedSource {
    guard url.isFileURL else {
      throw DocumentLoadError.notRegularFile
    }
    let kind = try DocumentKind(fileExtension: url.pathExtension)
    guard resourceValues.isRegularFile == true else {
      throw DocumentLoadError.notRegularFile
    }
    guard resourceValues.isReadable == true else {
      throw DocumentLoadError.notReadable
    }
    guard let fileSize = resourceValues.fileSize, fileSize >= 0,
      let modifiedAt = resourceValues.contentModificationDate
    else {
      throw DocumentLoadError.notReadable
    }
    let size = Int64(fileSize)
    guard size <= DocumentLimits.maximumSourceBytes else {
      throw DocumentLoadError.tooLarge
    }

    return ValidatedSource(
      url: url,
      kind: kind,
      fingerprint: SourceFingerprint(
        size: size,
        modifiedAt: modifiedAt,
        resourceID: resourceValues.fileResourceIdentifier as? Data
      )
    )
  }
}

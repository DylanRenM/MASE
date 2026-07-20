import Foundation
import Testing

@testable import MorerduoKit

@Suite("English filtering performance", .serialized)
struct EnglishFilterPipelineTests {
  @Test("filters an 18MB mixed paragraph within the POC budget")
  func filtersLargeInputWithinBudget() throws {
    let input = String(repeating: "Hello 123 世界!\n", count: 1_050_000)
    let start = ContinuousClock.now

    let output = try EnglishTextFilter().filter([
      RawParagraph(text: input, ordinal: 0)
    ])
    let elapsed = start.duration(to: .now)

    #expect(input.utf8.count <= 20 * 1024 * 1024)
    #expect(!output.isEmpty)
    #expect(elapsed < .seconds(3))
  }

  @MainActor
  @Test("background filtering yields the MainActor and publishes once")
  func backgroundFilteringYieldsMainActor() async throws {
    let input = String(repeating: "Hello 123 世界!\n", count: 1_050_000)
    let document = ParsedDocument(
      source: ValidatedSource(
        url: URL(fileURLWithPath: "/tmp/filter-fixture.txt"),
        kind: .txt,
        fingerprint: SourceFingerprint(
          size: Int64(input.utf8.count),
          modifiedAt: .distantPast,
          resourceID: nil
        )
      ),
      paragraphs: [input]
    )
    var publicationCount = 0
    let filteringTask = Task {
      let result = try await EnglishFilterPipeline().filter(document: document)
      publicationCount += 1
      return result
    }

    await Task.yield()
    let heartbeatWasHandled = true
    let output = try await filteringTask.value

    #expect(heartbeatWasHandled)
    #expect(publicationCount == 1)
    #expect(!output.isEmpty)
  }
}

import Testing

@testable import MorerduoKit

@Suite("EnglishTextFilter contract")
struct EnglishTextFilterContractTests {
  @Test("keeps only ASCII letters and necessary spaces")
  func filtersMixedUnicode() throws {
    let input = [RawParagraph(text: "Hello, 世界 123 café!\tGood", ordinal: 0)]

    let output = try EnglishTextFilter().filter(input)

    #expect(output.map(\.text) == ["Hello caf Good"])
    #expect(output[0].utf16Length == 14)
  }

  @Test("normalizes all ASCII whitespace to one space")
  func normalizesWhitespace() throws {
    let input = [RawParagraph(text: " \tHello   \r\nworld \n", ordinal: 0)]

    let output = try EnglishTextFilter().filter(input)

    #expect(output.map(\.text) == ["Hello world"])
  }

  @Test("removes empty results while retaining source order and ordinals")
  func retainsParagraphOrder() throws {
    let input = [
      RawParagraph(text: "First", ordinal: 0),
      RawParagraph(text: "中文 123", ordinal: 1),
      RawParagraph(text: "Third", ordinal: 2),
    ]

    let output = try EnglishTextFilter().filter(input)

    #expect(output.map(\.text) == ["First", "Third"])
    #expect(output.map(\.ordinal) == [0, 2])
  }

  @Test("returns a typed error when no readable English remains")
  func rejectsNoEnglishContent() {
    let input = [RawParagraph(text: "中文 123 !!!", ordinal: 0)]

    #expect(throws: DocumentLoadError.noReadableEnglish) {
      try EnglishTextFilter().filter(input)
    }
  }

  @Test("treats script markup as inert text data")
  func treatsScriptAsData() throws {
    let input = [
      RawParagraph(text: #"<script>alert("XSS")</script>"#, ordinal: 0)
    ]

    let output = try EnglishTextFilter().filter(input)

    #expect(output.map(\.text) == ["script alert XSS script"])
  }

  @Test("disallowed characters preserve adjacent word boundaries")
  func preservesWordBoundaries() throws {
    let input = [RawParagraph(text: "alpha-123-beta&gamma", ordinal: 0)]

    let output = try EnglishTextFilter().filter(input)

    #expect(output.map(\.text) == ["alpha beta gamma"])
  }

  @Test("produces deterministic values for identical inputs")
  func isDeterministic() throws {
    let input = [RawParagraph(text: "Repeat 42, 重复", ordinal: 0)]
    let filter = EnglishTextFilter()

    #expect(try filter.filter(input) == filter.filter(input))
  }
}

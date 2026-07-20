import Testing

@main
struct UnitTestRunner {
  static func main() async {
    await Testing.__swiftPMEntryPoint() as Never
  }
}

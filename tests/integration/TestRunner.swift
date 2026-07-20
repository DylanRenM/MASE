import Testing

@main
struct IntegrationTestRunner {
  static func main() async {
    await Testing.__swiftPMEntryPoint() as Never
  }
}

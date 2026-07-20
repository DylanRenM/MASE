// swift-tools-version: 6.0

import PackageDescription

let developerDirectory =
  Context.environment["DEVELOPER_DIR"]
  ?? "/Library/Developer/CommandLineTools"
let developerFrameworks = "\(developerDirectory)/Library/Developer/Frameworks"
let developerTestingRuntime = "\(developerDirectory)/Library/Developer/usr/lib"
let testingSwiftSettings: [SwiftSetting] = [
  .unsafeFlags(["-F", developerFrameworks])
]
let testingLinkerSettings: [LinkerSetting] = [
  .unsafeFlags([
    "-F", developerFrameworks,
    "-Xlinker", "-rpath",
    "-Xlinker", developerFrameworks,
    "-Xlinker", "-rpath",
    "-Xlinker", developerTestingRuntime,
    "-framework", "Testing",
  ])
]

let package = Package(
  name: "Morerduo",
  platforms: [
    .macOS(.v13)
  ],
  products: [
    .library(name: "MorerduoKit", targets: ["MorerduoKit"]),
    .executable(name: "MorerduoApp", targets: ["MorerduoApp"]),
    .executable(name: "MorerduoUnitTests", targets: ["MorerduoUnitTests"]),
    .executable(
      name: "MorerduoIntegrationTests",
      targets: ["MorerduoIntegrationTests"]
    ),
    .executable(
      name: "MorerduoContractTests",
      targets: ["MorerduoContractTests"]
    ),
    .executable(name: "MorerduoE2ERunner", targets: ["MorerduoE2ERunner"]),
  ],
  dependencies: [
    .package(
      url: "https://github.com/weichsel/ZIPFoundation.git",
      exact: "0.9.20"
    )
  ],
  targets: [
    .target(
      name: "MorerduoKit",
      dependencies: ["ZIPFoundation"],
      path: "src/morerduo"
    ),
    .executableTarget(
      name: "MorerduoApp",
      dependencies: ["MorerduoKit"],
      path: "src/morerduo_app"
    ),
    .executableTarget(
      name: "MorerduoUnitTests",
      dependencies: ["MorerduoKit", "ZIPFoundation"],
      path: "tests/unit",
      swiftSettings: testingSwiftSettings,
      linkerSettings: testingLinkerSettings
    ),
    .executableTarget(
      name: "MorerduoIntegrationTests",
      dependencies: ["MorerduoKit"],
      path: "tests/integration",
      swiftSettings: testingSwiftSettings,
      linkerSettings: testingLinkerSettings
    ),
    .executableTarget(
      name: "MorerduoContractTests",
      dependencies: ["MorerduoKit"],
      path: "tests/contract",
      swiftSettings: testingSwiftSettings,
      linkerSettings: testingLinkerSettings
    ),
    .executableTarget(
      name: "MorerduoE2ERunner",
      dependencies: ["MorerduoKit"],
      path: "tests/e2e",
      exclude: ["sandbox.test.js"],
      swiftSettings: testingSwiftSettings,
      linkerSettings: testingLinkerSettings
    ),
  ]
)

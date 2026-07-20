// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "MorerduoFeasibilityPOC",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "morerduo-poc", targets: ["MorerduoPOC"]),
        .executable(name: "morerduo-app-poc", targets: ["MorerduoAppPOC"])
    ],
    dependencies: [
        .package(
            url: "https://github.com/weichsel/ZIPFoundation.git",
            from: "0.9.20"
        )
    ],
    targets: [
        .executableTarget(
            name: "MorerduoPOC",
            dependencies: ["ZIPFoundation"]
        ),
        .executableTarget(
            name: "MorerduoAppPOC"
        )
    ]
)

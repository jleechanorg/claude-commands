// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "WorldArchitect",
    platforms: [
        .iOS(.v15),
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "WorldArchitect",
            targets: ["WorldArchitect"]
        )
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "WorldArchitect",
            dependencies: []
        )
    ]
)

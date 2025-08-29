#!/usr/bin/env swift

import Foundation

// Script to create iOS app bundle structure
print("📱 Creating iOS App Bundle for Simulator")
print("=======================================")

let fileManager = FileManager.default
let currentDirectory = fileManager.currentDirectoryPath

// Create app bundle structure
let appName = "WorldArchitect.app"
let appPath = "\(currentDirectory)/\(appName)"

do {
    // Remove existing app bundle
    if fileManager.fileExists(atPath: appPath) {
        try fileManager.removeItem(atPath: appPath)
    }
    
    // Create new app bundle directory
    try fileManager.createDirectory(atPath: appPath, withIntermediateDirectories: true, attributes: nil)
    
    print("✅ Created app bundle: \(appPath)")
    
    // Create Info.plist
    let infoPlistContent = """
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>CFBundleExecutable</key>
        <string>WorldArchitect</string>
        <key>CFBundleIdentifier</key>
        <string>com.worldarchitect.WorldArchitect</string>
        <key>CFBundleName</key>
        <string>WorldArchitect</string>
        <key>CFBundleDisplayName</key>
        <string>WorldArchitect</string>
        <key>CFBundleVersion</key>
        <string>1.0.0</string>
        <key>CFBundleShortVersionString</key>
        <string>1.0</string>
        <key>CFBundlePackageType</key>
        <string>APPL</string>
        <key>LSRequiresIPhoneOS</key>
        <true/>
        <key>UIRequiredDeviceCapabilities</key>
        <array>
            <string>armv7</string>
        </array>
        <key>UISupportedInterfaceOrientations</key>
        <array>
            <string>UIInterfaceOrientationPortrait</string>
            <string>UIInterfaceOrientationLandscapeLeft</string>
            <string>UIInterfaceOrientationLandscapeRight</string>
        </array>
        <key>UIApplicationSceneManifest</key>
        <dict>
            <key>UIApplicationSupportsMultipleScenes</key>
            <false/>
            <key>UISceneConfigurations</key>
            <dict>
                <key>UIWindowSceneSessionRoleApplication</key>
                <array>
                    <dict>
                        <key>UISceneConfigurationName</key>
                        <string>Default Configuration</string>
                        <key>UISceneDelegateClassName</key>
                        <string>SceneDelegate</string>
                    </dict>
                </array>
            </dict>
        </dict>
        <key>MinimumOSVersion</key>
        <string>15.0</string>
    </dict>
    </plist>
    """
    
    let infoPlistPath = "\(appPath)/Info.plist"
    try infoPlistContent.write(toFile: infoPlistPath, atomically: true, encoding: .utf8)
    print("✅ Created Info.plist")
    
    // Copy executable
    let executableSource = "\(currentDirectory)/WorldArchitect/.build/debug/WorldArchitect"
    let executableDest = "\(appPath)/WorldArchitect"
    
    if fileManager.fileExists(atPath: executableSource) {
        try fileManager.copyItem(atPath: executableSource, toPath: executableDest)
        
        // Make executable
        let attributes: [FileAttributeKey: Any] = [
            .posixPermissions: 0o755
        ]
        try fileManager.setAttributes(attributes, ofItemAtPath: executableDest)
        print("✅ Copied executable to app bundle")
    } else {
        print("❌ Executable not found at: \(executableSource)")
        print("   Run 'cd WorldArchitect && swift build' first")
    }
    
    print("\n📱 iOS App Bundle Ready!")
    print("Bundle Path: \(appPath)")
    print("Ready to install on simulator!")
    
} catch {
    print("❌ Error creating app bundle: \(error)")
}
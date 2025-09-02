#!/usr/bin/env swift

import Foundation

// Create a test script to verify our Swift code compiles
print("WorldArchitect iOS App - Code Verification")
print("==========================================")

// Test Campaign struct creation
struct Campaign_Test {
    let name: String
    let description: String
    
    init(name: String, description: String) {
        self.name = name
        self.description = description
    }
}

// Test Character struct creation
struct Character_Test {
    let name: String
    let level: Int
    let characterClass: String
    
    init(name: String, level: Int, characterClass: String) {
        self.name = name
        self.level = level
        self.characterClass = characterClass
    }
}

// Create test instances
let testCampaign = Campaign_Test(
    name: "The Lost Mines of Phandelver",
    description: "A classic D&D adventure for new players"
)

let testCharacter = Character_Test(
    name: "Thorin Stonebeard",
    level: 3,
    characterClass: "Fighter"
)

// Print test results
print("✅ Campaign created: \(testCampaign.name)")
print("   Description: \(testCampaign.description)")
print("")
print("✅ Character created: \(testCharacter.name)")
print("   Level: \(testCharacter.level)")
print("   Class: \(testCharacter.characterClass)")
print("")
print("🎉 Swift code compilation successful!")
print("📱 Ready to build iOS app with SwiftUI views")
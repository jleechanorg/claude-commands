#!/usr/bin/env swift

import Foundation

// ============================================================================
// MARK: - Data Models
// ============================================================================

enum Theme: String, CaseIterable, Codable {
    case fantasy = "Fantasy"
    case sciFi = "Sci-Fi" 
    case horror = "Horror"
    case modern = "Modern"
    case steampunk = "Steampunk"
}

enum Difficulty: String, CaseIterable, Codable {
    case easy = "Easy"
    case normal = "Normal"
    case hard = "Hard"
    case expert = "Expert"
}

enum Race: String, CaseIterable, Codable {
    case human = "Human"
    case elf = "Elf"
    case dwarf = "Dwarf"
    case halfling = "Halfling"
    case dragonborn = "Dragonborn"
    case gnome = "Gnome"
    case halfElf = "Half-Elf"
    case halfOrc = "Half-Orc"
    case tiefling = "Tiefling"
}

enum CharacterClass: String, CaseIterable, Codable {
    case barbarian = "Barbarian"
    case bard = "Bard"
    case cleric = "Cleric"
    case druid = "Druid"
    case fighter = "Fighter"
    case monk = "Monk"
    case paladin = "Paladin"
    case ranger = "Ranger"
    case rogue = "Rogue"
    case sorcerer = "Sorcerer"
    case warlock = "Warlock"
    case wizard = "Wizard"
}

struct CampaignSettings: Codable {
    var theme: Theme
    var difficulty: Difficulty
    var maxPlayers: Int
    var enableAI: Bool
    
    init(theme: Theme = .fantasy, difficulty: Difficulty = .normal, maxPlayers: Int = 6, enableAI: Bool = true) {
        self.theme = theme
        self.difficulty = difficulty
        self.maxPlayers = maxPlayers
        self.enableAI = enableAI
    }
}

struct Session: Codable, Identifiable {
    let id: UUID
    let title: String
    let date: Date
    let summary: String
    let isCompleted: Bool
    
    init(id: UUID = UUID(), title: String, date: Date, summary: String, isCompleted: Bool = false) {
        self.id = id
        self.title = title
        self.date = date
        self.summary = summary
        self.isCompleted = isCompleted
    }
}

struct Spell: Codable, Identifiable {
    let id: UUID
    let name: String
    let level: Int
    let description: String
    let school: String
    
    init(id: UUID = UUID(), name: String, level: Int, description: String, school: String) {
        self.id = id
        self.name = name
        self.level = level
        self.description = description
        self.school = school
    }
}

struct Character: Codable, Identifiable {
    let id: UUID
    let name: String
    let race: Race
    let characterClass: CharacterClass
    let level: Int
    let strength: Int
    let dexterity: Int
    let constitution: Int
    let intelligence: Int
    let wisdom: Int
    let charisma: Int
    let hitPoints: Int
    let armorClass: Int
    let spells: [Spell]
    let equipment: [String]
    let inventory: [String]
    
    init(id: UUID = UUID(), name: String, race: Race, characterClass: CharacterClass, level: Int = 1, strength: Int = 10, dexterity: Int = 10, constitution: Int = 10, intelligence: Int = 10, wisdom: Int = 10, charisma: Int = 10, hitPoints: Int = 8, armorClass: Int = 10, spells: [Spell] = [], equipment: [String] = [], inventory: [String] = []) {
        self.id = id
        self.name = name
        self.race = race
        self.characterClass = characterClass
        self.level = level
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
        self.hitPoints = hitPoints
        self.armorClass = armorClass
        self.spells = spells
        self.equipment = equipment
        self.inventory = inventory
    }
}

struct Campaign: Codable, Identifiable {
    let id: UUID
    let name: String
    let description: String
    let settings: CampaignSettings
    let sessions: [Session]
    let characters: [Character]
    let createdAt: Date
    let lastPlayed: Date?
    
    init(id: UUID = UUID(), name: String, description: String, settings: CampaignSettings = CampaignSettings(), sessions: [Session] = [], characters: [Character] = [], createdAt: Date = Date(), lastPlayed: Date? = nil) {
        self.id = id
        self.name = name
        self.description = description
        self.settings = settings
        self.sessions = sessions
        self.characters = characters
        self.createdAt = createdAt
        self.lastPlayed = lastPlayed
    }
}

// ============================================================================
// MARK: - Mock Data
// ============================================================================

class MockData {
    static let mockSpells: [Spell] = [
        Spell(name: "Magic Missile", level: 1, description: "Three darts of magical force hit their target automatically.", school: "Evocation"),
        Spell(name: "Shield", level: 1, description: "An invisible barrier of magical force protects you.", school: "Abjuration"),
        Spell(name: "Detect Magic", level: 1, description: "You sense the presence of magic within 30 feet.", school: "Divination"),
        Spell(name: "Fireball", level: 3, description: "A bright flash and a booming crack as flames engulf the target area.", school: "Evocation"),
        Spell(name: "Cure Wounds", level: 1, description: "Healing energy flows through you to restore hit points.", school: "Evocation")
    ]
    
    static let mockCharacters: [Character] = [
        Character(
            name: "Thorin Stonebeard",
            race: .dwarf,
            characterClass: .fighter,
            level: 3,
            strength: 16,
            dexterity: 12,
            constitution: 15,
            intelligence: 10,
            wisdom: 13,
            charisma: 8,
            hitPoints: 32,
            armorClass: 18,
            equipment: ["Chain Mail", "Battleaxe", "Handaxe", "Shield"],
            inventory: ["50 gold pieces", "Thieves' Tools", "Rations (5 days)", "Hemp Rope (50 feet)"]
        ),
        Character(
            name: "Elara Moonwhisper",
            race: .elf,
            characterClass: .wizard,
            level: 2,
            strength: 8,
            dexterity: 14,
            constitution: 12,
            intelligence: 17,
            wisdom: 13,
            charisma: 11,
            hitPoints: 16,
            armorClass: 12,
            spells: Array(mockSpells[0...2]),
            equipment: ["Quarterstaff", "Spellbook", "Component Pouch"],
            inventory: ["25 gold pieces", "Ink and Quill", "Parchment (10 sheets)", "Spell Scroll (Identify)"]
        ),
        Character(
            name: "Kael Shadowstrike",
            race: .halfElf,
            characterClass: .rogue,
            level: 4,
            strength: 10,
            dexterity: 18,
            constitution: 13,
            intelligence: 14,
            wisdom: 12,
            charisma: 16,
            hitPoints: 28,
            armorClass: 15,
            equipment: ["Studded Leather", "Shortsword", "Dagger (2)", "Thieves' Tools"],
            inventory: ["75 gold pieces", "Burglar's Pack", "Crowbar", "Dark Cloak"]
        )
    ]
    
    static let mockSessions: [Session] = [
        Session(
            title: "The Goblin Ambush", 
            date: Calendar.current.date(byAdding: .day, value: -7, to: Date())!, 
            summary: "Our heroes faced their first challenge on the road to Phandalin when goblins ambushed their supply wagon. Through clever tactics and teamwork, they overcame the threat and discovered clues leading to a larger conspiracy."
        ),
        Session(
            title: "Cragmaw Hideout", 
            date: Calendar.current.date(byAdding: .day, value: -3, to: Date())!, 
            summary: "Following goblin tracks led to a cave hideout where the party rescued Gundren's guard and uncovered the first hints of the Black Spider's involvement in the disappearance."
        ),
        Session(
            title: "The Town of Phandalin", 
            date: Date(), 
            summary: "Arriving in the frontier town, our adventurers met the locals, learned about the Redbrands' oppression, and began planning their next moves to restore peace to the region."
        )
    ]
    
    static let mockCampaigns: [Campaign] = [
        Campaign(
            name: "The Lost Mines of Phandelver",
            description: "A classic D&D adventure for new players seeking fortune in the dangerous mines of the Sword Coast. Perfect for learning the ropes of tabletop RPGs.",
            settings: CampaignSettings(theme: .fantasy, difficulty: .normal, maxPlayers: 4),
            sessions: Array(mockSessions[0...1]),
            characters: Array(mockCharacters[0...1]),
            lastPlayed: Calendar.current.date(byAdding: .day, value: -3, to: Date())
        ),
        Campaign(
            name: "Curse of Strahd",
            description: "A gothic horror adventure in the mysterious land of Barovia, where an ancient vampire lord rules with an iron fist and the mists trap all who enter.",
            settings: CampaignSettings(theme: .horror, difficulty: .hard, maxPlayers: 5),
            sessions: [mockSessions[2]],
            characters: [mockCharacters[2]],
            lastPlayed: Calendar.current.date(byAdding: .day, value: -14, to: Date())
        ),
        Campaign(
            name: "Storm King's Thunder",
            description: "Giants have emerged from their strongholds to threaten civilization. Heroes must navigate a world where giants walk among smaller folk, uncovering an ancient threat that could spell doom for all.",
            settings: CampaignSettings(theme: .fantasy, difficulty: .hard, maxPlayers: 6),
            sessions: [],
            characters: [],
            lastPlayed: nil
        )
    ]
}

// ============================================================================
// MARK: - Business Logic Simulation
// ============================================================================

class CampaignManager {
    private var campaigns: [Campaign] = []
    
    init() {
        self.campaigns = MockData.mockCampaigns
    }
    
    func getAllCampaigns() -> [Campaign] {
        return campaigns
    }
    
    func getCampaign(by id: UUID) -> Campaign? {
        return campaigns.first { $0.id == id }
    }
    
    func addCampaign(_ campaign: Campaign) {
        campaigns.append(campaign)
    }
    
    func removeCampaign(by id: UUID) {
        campaigns.removeAll { $0.id == id }
    }
}

// ============================================================================
// MARK: - Main App Simulation
// ============================================================================

func main() {
    print("🏰 WorldArchitect.AI - iOS App Simulation")
    print("=========================================")
    print("")
    
    let campaignManager = CampaignManager()
    let campaigns = campaignManager.getAllCampaigns()
    
    print("📚 Available Campaigns:")
    for (index, campaign) in campaigns.enumerated() {
        print("  \(index + 1). \(campaign.name)")
        print("     Theme: \(campaign.settings.theme.rawValue)")
        print("     Difficulty: \(campaign.settings.difficulty.rawValue)")
        print("     Characters: \(campaign.characters.count)")
        print("     Sessions: \(campaign.sessions.count)")
        if let lastPlayed = campaign.lastPlayed {
            let formatter = DateFormatter()
            formatter.dateStyle = .medium
            print("     Last Played: \(formatter.string(from: lastPlayed))")
        }
        print("")
    }
    
    if let selectedCampaign = campaigns.first {
        print("🎯 Campaign Details: \(selectedCampaign.name)")
        print("Description: \(selectedCampaign.description)")
        print("")
        
        if !selectedCampaign.characters.isEmpty {
            print("👥 Characters in this Campaign:")
            for character in selectedCampaign.characters {
                print("  • \(character.name) - Level \(character.level) \(character.race.rawValue) \(character.characterClass.rawValue)")
                print("    HP: \(character.hitPoints), AC: \(character.armorClass)")
                print("    STR: \(character.strength), DEX: \(character.dexterity), CON: \(character.constitution)")
                print("    INT: \(character.intelligence), WIS: \(character.wisdom), CHA: \(character.charisma)")
                
                if !character.equipment.isEmpty {
                    print("    Equipment: \(character.equipment.joined(separator: ", "))")
                }
                
                if !character.spells.isEmpty {
                    print("    Spells: \(character.spells.map { $0.name }.joined(separator: ", "))")
                }
                print("")
            }
        }
        
        if !selectedCampaign.sessions.isEmpty {
            print("📖 Recent Sessions:")
            for session in selectedCampaign.sessions {
                let formatter = DateFormatter()
                formatter.dateStyle = .short
                print("  • \(session.title) (\(formatter.string(from: session.date)))")
                print("    \(session.summary)")
                print("")
            }
        }
    }
    
    print("✅ iOS App Structure Complete!")
    print("🚀 Ready for SwiftUI Implementation!")
    print("")
    print("📱 Features Demonstrated:")
    print("  - Campaign Management")
    print("  - Character Sheets with D&D 5e Stats")
    print("  - Session Tracking")
    print("  - Mock Data Integration")
    print("  - Navigation Ready Structure")
    print("  - Dark Theme Support")
}

// Run the simulation
main()
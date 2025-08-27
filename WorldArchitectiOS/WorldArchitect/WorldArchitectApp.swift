import SwiftUI

// MARK: - Data Models
struct Campaign: Identifiable, Codable {
    let id = UUID()
    let name: String
    let description: String
    let dungeonMaster: String
    let players: [String]
    let status: String
    let startDate: Date
    let sessions: [Session]
}

struct Character: Identifiable, Codable {
    let id = UUID()
    let name: String
    let race: String
    let characterClass: String
    let level: Int
    let playerName: String
    let campaignName: String
    let stats: Stats
    let background: String
}

struct Stats: Codable {
    let strength: Int
    let dexterity: Int
    let constitution: Int
    let intelligence: Int
    let wisdom: Int
    let charisma: Int
}

struct Session: Identifiable, Codable {
    let id = UUID()
    let date: Date
    let title: String
    let description: String
    let participants: [String]
    let quests: [Quest]
}

struct Quest: Identifiable, Codable {
    let id = UUID()
    let name: String
    let status: String
    let description: String
    let reward: String
}

// MARK: - Sample Data
@MainActor
class WorldArchitectData: ObservableObject {
    @Published var campaigns: [Campaign] = [
        Campaign(
            name: "The Lost Temple of Zephyr",
            description: "An ancient temple has been uncovered in the desert sands, but something stirs within its forgotten halls...",
            dungeonMaster: "Gandalf",
            players: ["Aragorn", "Legolas", "Gimli"],
            status: "Active",
            startDate: Date(),
            sessions: [
                Session(
                    date: Date(),
                    title: "The Desert Expedition",
                    description: "The party ventures into the scorching desert in search of the lost temple.",
                    participants: ["Aragorn", "Legolas", "Gimli"],
                    quests: [
                        Quest(
                            name: "Map the Ruins",
                            status: "Completed",
                            description: "Explore and map the outer chambers of the temple",
                            reward: "Ancient Artifact"
                        )
                    ]
                )
            ]
        ),
        Campaign(
            name: "Shadows of the Undercity",
            description: "Beneath the bustling metropolis lies a forgotten network of tunnels filled with danger and intrigue.",
            dungeonMaster: "Merlin",
            players: ["Arthur", "Lancelot", "Guinevere"],
            status: "Paused",
            startDate: Date(),
            sessions: []
        )
    ]
    
    @Published var characters: [Character] = [
        Character(
            name: "Thorin Oakenshield",
            race: "Dwarf",
            characterClass: "Fighter",
            level: 5,
            playerName: "Aragorn",
            campaignName: "The Lost Temple of Zephyr",
            stats: Stats(strength: 16, dexterity: 12, constitution: 15, intelligence: 10, wisdom: 11, charisma: 13),
            background: "Noble"
        ),
        Character(
            name: "Elrond Half-Elven",
            race: "Elf",
            characterClass: "Wizard",
            level: 7,
            playerName: "Legolas",
            campaignName: "The Lost Temple of Zephyr",
            stats: Stats(strength: 8, dexterity: 15, constitution: 12, intelligence: 18, wisdom: 16, charisma: 14),
            background: "Sage"
        ),
        Character(
            name: "Gimli Stormcloak",
            race: "Dwarf",
            characterClass: "Cleric",
            level: 4,
            playerName: "Gimli",
            campaignName: "The Lost Temple of Zephyr",
            stats: Stats(strength: 15, dexterity: 10, constitution: 16, intelligence: 11, wisdom: 17, charisma: 9),
            background: "Acolyte"
        )
    ]
    
    @Published var sessions: [Session] = [
        Session(
            date: Date(),
            title: "The Desert Expedition",
            description: "The party ventures into the scorching desert in search of the lost temple.",
            participants: ["Aragorn", "Legolas", "Gimli"],
            quests: [
                Quest(
                    name: "Map the Ruins",
                    status: "Completed",
                    description: "Explore and map the outer chambers of the temple",
                    reward: "Ancient Artifact"
                )
            ]
        ),
        Session(
            date: Date(),
            title: "Into the Temple",
            description: "The party enters the temple and discovers its ancient secrets.",
            participants: ["Aragorn", "Legolas", "Gimli"],
            quests: [
                Quest(
                    name: "Activate the Altar",
                    status: "In Progress",
                    description: "Find the sacred gems to activate the temple's altar",
                    reward: "Divine Blessing"
                )
            ]
        )
    ]
}

@main
struct WorldArchitectApp: App {
    @StateObject private var gameData = WorldArchitectData()
    
    var body: some Scene {
        WindowGroup {
            MainAppView()
                .environmentObject(gameData)
                .preferredColorScheme(.dark)
        }
    }
}

struct MainAppView: View {
    @State private var selectedTab = 0
    @EnvironmentObject var gameData: WorldArchitectData
    
    var body: some View {
        TabView(selection: $selectedTab) {
            CampaignsView()
                .tabItem {
                    Image(systemName: "map.fill")
                    Text("Campaigns")
                }
                .tag(0)
            
            CharactersView()
                .tabItem {
                    Image(systemName: "person.3.fill")
                    Text("Characters")
                }
                .tag(1)
            
            SessionsView()
                .tabItem {
                    Image(systemName: "book.pages.fill")
                    Text("Sessions")
                }
                .tag(2)
            
            ProfileView()
                .tabItem {
                    Image(systemName: "gear")
                    Text("Settings")
                }
                .tag(3)
        }
        .accentColor(.orange)
    }
}

// MARK: - Campaign Views
struct CampaignsView: View {
    @EnvironmentObject var gameData: WorldArchitectData
    
    var body: some View {
        NavigationView {
            List {
                ForEach(gameData.campaigns) { campaign in
                    NavigationLink(destination: CampaignDetailView(campaign: campaign)) {
                        CampaignCardView(campaign: campaign)
                    }
                    .listRowBackground(Color.clear)
                }
            }
            .navigationTitle("Campaigns")
            .listStyle(PlainListStyle())
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
}

struct CampaignCardView: View {
    let campaign: Campaign
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(campaign.name)
                    .font(.headline)
                    .foregroundColor(.orange)
                Spacer()
                Text(campaign.status)
                    .font(.caption)
                    .padding(6)
                    .background(campaign.status == "Active" ? Color.green.opacity(0.2) : Color.gray.opacity(0.2))
                    .cornerRadius(8)
            }
            
            Text(campaign.description)
                .font(.subheadline)
                .foregroundColor(.gray)
                .lineLimit(3)
            
            HStack {
                Text("DM: \(campaign.dungeonMaster)")
                    .font(.caption)
                Spacer()
                Text("Players: \(campaign.players.count)")
                    .font(.caption)
            }
            .padding(.top, 4)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct CampaignDetailView: View {
    let campaign: Campaign
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(campaign.name)
                    .font(.largeTitle)
                    .foregroundColor(.orange)
                
                Text(campaign.description)
                    .font(.body)
                
                HStack {
                    Text("Dungeon Master:")
                        .fontWeight(.bold)
                    Text(campaign.dungeonMaster)
                }
                
                HStack {
                    Text("Status:")
                        .fontWeight(.bold)
                    Text(campaign.status)
                        .padding(6)
                        .background(campaign.status == "Active" ? Color.green.opacity(0.2) : Color.gray.opacity(0.2))
                        .cornerRadius(8)
                }
                
                Text("Players:")
                    .font(.headline)
                ForEach(campaign.players, id: \.self) { player in
                    Text("• \(player)")
                        .padding(.leading)
                }
                
                Text("Sessions:")
                    .font(.headline)
                if campaign.sessions.isEmpty {
                    Text("No sessions recorded yet")
                        .foregroundColor(.gray)
                } else {
                    ForEach(campaign.sessions) { session in
                        SessionCardView(session: session)
                    }
                }
            }
            .padding()
        }
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - Character Views
struct CharactersView: View {
    @EnvironmentObject var gameData: WorldArchitectData
    
    var body: some View {
        NavigationView {
            List {
                ForEach(gameData.characters) { character in
                    NavigationLink(destination: CharacterDetailView(character: character)) {
                        CharacterCardView(character: character)
                    }
                    .listRowBackground(Color.clear)
                }
            }
            .navigationTitle("Characters")
            .listStyle(PlainListStyle())
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
}

struct CharacterCardView: View {
    let character: Character
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(character.name)
                    .font(.headline)
                    .foregroundColor(.orange)
                
                Text("\(character.race) \(character.characterClass) (Level \(character.level))")
                    .font(.subheadline)
                    .foregroundColor(.gray)
                
                Text("Player: \(character.playerName)")
                    .font(.caption)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("STR: \(character.stats.strength)")
                    .font(.caption)
                Text("DEX: \(character.stats.dexterity)")
                    .font(.caption)
                Text("CON: \(character.stats.constitution)")
                    .font(.caption)
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct CharacterDetailView: View {
    let character: Character
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(character.name)
                    .font(.largeTitle)
                    .foregroundColor(.orange)
                
                Text("\(character.race) \(character.characterClass) (Level \(character.level))")
                    .font(.title2)
                    .foregroundColor(.gray)
                
                Text("Background: \(character.background)")
                    .font(.body)
                
                Text("Stats:")
                    .font(.headline)
                
                StatRowView(label: "Strength", value: character.stats.strength)
                StatRowView(label: "Dexterity", value: character.stats.dexterity)
                StatRowView(label: "Constitution", value: character.stats.constitution)
                StatRowView(label: "Intelligence", value: character.stats.intelligence)
                StatRowView(label: "Wisdom", value: character.stats.wisdom)
                StatRowView(label: "Charisma", value: character.stats.charisma)
                
                Text("Campaign: \(character.campaignName)")
                    .font(.body)
            }
            .padding()
        }
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct StatRowView: View {
    let label: String
    let value: Int
    
    var body: some View {
        HStack {
            Text(label)
                .fontWeight(.medium)
            Spacer()
            Text("\(value)")
                .fontWeight(.bold)
                .foregroundColor(.orange)
        }
        .padding(.vertical, 2)
    }
}

// MARK: - Session Views
struct SessionsView: View {
    @EnvironmentObject var gameData: WorldArchitectData
    
    var body: some View {
        NavigationView {
            List {
                ForEach(gameData.sessions) { session in
                    SessionCardView(session: session)
                        .listRowBackground(Color.clear)
                }
            }
            .navigationTitle("Sessions")
            .listStyle(PlainListStyle())
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
}

struct SessionCardView: View {
    let session: Session
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(session.title)
                    .font(.headline)
                    .foregroundColor(.orange)
                Spacer()
                Text("\(session.date, formatter: dateFormatter)")
                    .font(.caption)
            }
            
            Text(session.description)
                .font(.subheadline)
                .foregroundColor(.gray)
                .lineLimit(2)
            
            HStack {
                Text("Participants: \(session.participants.joined(separator: ", "))")
                    .font(.caption)
                Spacer()
            }
            .padding(.top, 4)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
    
    private var dateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        return formatter
    }
}

// MARK: - Profile View
struct ProfileView: View {
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Text("WorldArchitect")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .foregroundColor(.orange)
                    .padding()
                
                VStack(spacing: 15) {
                    Circle()
                        .fill(Color.orange)
                        .frame(width: 100, height: 100)
                        .overlay(
                            Text("🏰")
                                .font(.system(size: 40))
                        )
                    
                    Text("Dungeon Master")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("Creating Epic Adventures")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                HStack(spacing: 40) {
                    VStack {
                        Text("2")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.orange)
                        Text("Campaigns")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    VStack {
                        Text("3")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.orange)
                        Text("Characters")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    VStack {
                        Text("2")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.orange)
                        Text("Sessions")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .padding()
                
                Spacer()
                
                VStack(spacing: 15) {
                    Button("App Settings") {
                        // Settings action
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(10)
                    
                    Button("About WorldArchitect") {
                        // About action
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.orange.opacity(0.2))
                    .foregroundColor(.orange)
                    .cornerRadius(10)
                }
                .padding(.horizontal, 30)
                .padding(.bottom, 50)
            }
            .navigationTitle("Profile")
        }
        .navigationViewStyle(StackNavigationViewStyle())
    }
}
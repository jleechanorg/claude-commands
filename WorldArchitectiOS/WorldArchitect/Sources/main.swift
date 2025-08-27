import SwiftUI

@main
struct WorldArchitectApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.dark)
        }
    }
}

struct ContentView: View {
    var body: some View {
        VStack {
            Text("Hello WorldArchitect")
                .font(.largeTitle)
                .foregroundColor(.orange)
                .padding()
            
            Text("Welcome to your iOS app")
                .font(.body)
                .foregroundColor(.white)
                .padding()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.black)
    }
}
document.addEventListener('DOMContentLoaded', () => {
  console.log("DOM fully loaded and parsed");

  // Your actual Firebase configuration:
  const firebaseConfig = {
    apiKey: "AIzaSyARs7IekRptvhZIwtV7lwJh3axWFsn_4c8",
    authDomain: "worldarchitecture-ai.firebaseapp.com",
    projectId: "worldarchitecture-ai",
    storageBucket: "worldarchitecture-ai.firebasestorage.app",
    messagingSenderId: "754683067800",
    appId: "1:754683067800:web:3b38787c69de301c147fed",
    measurementId: "G-EFX5VFZ7CV"
  };

  try {
    firebase.initializeApp(firebaseConfig);
    console.log("Firebase Initialized Successfully");
  } catch (e) {
    console.error("Error initializing Firebase:", e);
    return; // Stop execution if initialization fails
  }
  
  const auth = firebase.auth();
  const provider = new firebase.auth.GoogleAuthProvider();

  // UI Elements
  const authContainer = document.getElementById('auth-container');
  const contentContainer = document.getElementById('content-container');
  const userNameElement = document.getElementById('user-name');

  // Functions
  const signIn = () => auth.signInWithPopup(provider).catch(e => console.error("Sign-in error:", e));
  const signOut = () => auth.signOut().catch(e => console.error("Sign-out error:", e));

  // Auth State Listener
  auth.onAuthStateChanged(user => {
    console.log("Auth state changed. User:", user);
    if (user) {
      // User is signed in
      authContainer.innerHTML = '<button class="btn btn-danger" id="signOutBtn">Sign Out</button>';
      document.getElementById('signOutBtn').onclick = signOut;
      userNameElement.textContent = user.displayName;
      contentContainer.style.display = 'block';
    } else {
      // User is signed out
      authContainer.innerHTML = '<button class="btn btn-primary" id="signInBtn">Sign in with Google</button>';
      document.getElementById('signInBtn').onclick = signIn;
      contentContainer.style.display = 'none';
    }
  });
});

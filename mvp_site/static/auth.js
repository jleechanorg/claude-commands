document.addEventListener('DOMContentLoaded', () => {
  const firebaseConfig = {
    apiKey: "AIzaSyARs7IekRptvhZIwtV7lwJh3axWFsn_4c8",
    authDomain: "worldarchitecture-ai.firebaseapp.com",
    projectId: "worldarchitecture-ai",
    storageBucket: "worldarchitecture-ai.firebasestorage.app",
    messagingSenderId: "754683067800",
    appId: "1:754683067800:web:3b38787c69de301c147fed",
    measurementId: "G-EFX5VFZ7CV"
  };
  try { firebase.initializeApp(firebaseConfig); } catch (e) { console.error("Error initializing Firebase:", e); return; }
  const auth = firebase.auth();
  const provider = new firebase.auth.GoogleAuthProvider();
  const authContainer = document.getElementById('auth-container');
  const signIn = () => auth.signInWithPopup(provider).catch(e => console.error("Sign-in error:", e));
  const signOut = () => auth.signOut().catch(e => console.error("Sign-out error:", e));
  auth.onAuthStateChanged(user => {
    if (user) {
      authContainer.innerHTML = `<p>Welcome, ${user.displayName}! <button class="btn btn-sm btn-danger" id="signOutBtn">Sign Out</button></p>`;
      document.getElementById('signOutBtn').onclick = signOut;
    } else {
      authContainer.innerHTML = '<button class="btn btn-primary" id="signInBtn">Sign in with Google</button>';
      document.getElementById('signInBtn').onclick = signIn;
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  // Check for test mode bypass
  const urlParams = new URLSearchParams(window.location.search);
  const testMode = urlParams.get('test_mode') === 'true';
  const testUserId = urlParams.get('test_user_id') || 'test-user';
  
  if (testMode) {
    console.log('🧪 Test mode enabled - bypassing authentication');
    // Set test user in window for API calls
    window.testAuthBypass = {
      enabled: true,
      userId: testUserId
    };
    // Dispatch custom event to signal test mode is ready (with a small delay to ensure listeners are set up)
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('testModeReady', { detail: { userId: testUserId } }));
    }, 100);
    return; // Skip Firebase initialization
  }

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
  // Get the new button
  const signOutBtnDashboard = document.getElementById('signOutBtnDashboard');

  const signIn = () => auth.signInWithPopup(provider).catch(e => console.error("Sign-in error:", e));
  const signOut = () => auth.signOut().catch(e => console.error("Sign-out error:", e));

  // Attach the signOut function to the new button's click event
  if (signOutBtnDashboard) {
      signOutBtnDashboard.onclick = signOut;
  }

  auth.onAuthStateChanged(user => {
    if (user) {
      // User is signed in, so the sign-in button should not be displayed.
      // We keep the container for layout purposes but ensure it's empty.
      authContainer.innerHTML = '';
    } else {
      // User is signed out, show the sign-in button.
      authContainer.innerHTML = '<button class="btn btn-primary" id="signInBtn">Sign in with Google</button>';
      document.getElementById('signInBtn').onclick = signIn;
    }
  });
});

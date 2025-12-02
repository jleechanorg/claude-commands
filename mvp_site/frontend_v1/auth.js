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
      userId: testUserId,
    };
    // Dispatch custom event to signal test mode is ready (with a small delay to ensure listeners are set up)
    setTimeout(() => {
      window.dispatchEvent(
        new CustomEvent('testModeReady', { detail: { userId: testUserId } }),
      );
    }, 100);
    return; // Skip Firebase initialization
  }

  const firebaseConfig = {
    apiKey: 'AIzaSyARs7IekRptvhZIwtV7lwJh3axWFsn_4c8',
    authDomain: 'worldarchitecture-ai.firebaseapp.com',
    projectId: 'worldarchitecture-ai',
    storageBucket: 'worldarchitecture-ai.firebasestorage.app',
    messagingSenderId: '754683067800',
    appId: '1:754683067800:web:3b38787c69de301c147fed',
    measurementId: 'G-EFX5VFZ7CV',
  };
  try {
    firebase.initializeApp(firebaseConfig);
  } catch (e) {
    console.error('Error initializing Firebase:', e);
    return;
  }

  const auth = firebase.auth();
  const provider = new firebase.auth.GoogleAuthProvider();

  const authContainer = document.getElementById('auth-container');
  // Get the new button
  const signOutBtnDashboard = document.getElementById('signOutBtnDashboard');

  let tokenRefreshTimeout = null;

  const clearTokenRefreshTimer = () => {
    if (tokenRefreshTimeout) {
      clearTimeout(tokenRefreshTimeout);
      tokenRefreshTimeout = null;
    }
  };

  const scheduleTokenRefresh = async (user) => {
    clearTokenRefreshTimer();
    if (!user) return;

    try {
      const tokenResult = await user.getIdTokenResult();
      const expirationTime = new Date(tokenResult.expirationTime).getTime();
      const now = Date.now();
      const refreshBufferMs = 5 * 60 * 1000; // Refresh 5 minutes before expiry
      const refreshIn = Math.max(0, expirationTime - now - refreshBufferMs);

      console.log(
        `🪙 Scheduling Firebase ID token refresh in ${Math.round(
          refreshIn / 1000,
        )}s (buffer ${refreshBufferMs / 60000}m)`,
      );

      tokenRefreshTimeout = setTimeout(async () => {
        try {
          console.log('🔄 Refreshing Firebase ID token before expiry');
          await user.getIdToken(true);
          await scheduleTokenRefresh(user); // Reschedule using new expiry
        } catch (error) {
          console.error('Failed to auto-refresh Firebase ID token:', error);
          // Retry in 1 minute to avoid leaving the user stranded
          tokenRefreshTimeout = setTimeout(() => scheduleTokenRefresh(user), 60000);
        }
      }, refreshIn);
    } catch (error) {
      console.error('Unable to schedule Firebase token refresh:', error);
      // Retry scheduling after a short delay in case of transient errors
      tokenRefreshTimeout = setTimeout(() => scheduleTokenRefresh(user), 60000);
    }
  };

  const getAuthHeaders = async (forceRefresh = false) => {
    if (window.testAuthBypass && window.testAuthBypass.enabled) {
      return {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': window.testAuthBypass.userId,
      };
    }

    const user = firebase.auth().currentUser;
    if (!user) throw new Error('User not authenticated');

    const token = await user.getIdToken(forceRefresh);
    return {
      Authorization: `Bearer ${token}`,
    };
  };

  window.authTokenManager = {
    scheduleTokenRefresh,
    clearTokenRefreshTimer,
    getAuthHeaders,
    getCurrentUser: () => firebase.auth().currentUser,
  };

  const signIn = () =>
    auth
      .signInWithPopup(provider)
      .catch((e) => console.error('Sign-in error:', e));
  const signOut = () =>
    auth.signOut().catch((e) => console.error('Sign-out error:', e));

  // Attach the signOut function to the new button's click event
  if (signOutBtnDashboard) {
    signOutBtnDashboard.onclick = signOut;
  }

  auth.onAuthStateChanged((user) => {
    if (user) {
      scheduleTokenRefresh(user);
      // User is signed in, so the sign-in button should not be displayed.
      // We keep the container for layout purposes but ensure it's empty.
      authContainer.innerHTML = '';
    } else {
      clearTokenRefreshTimer();
      // User is signed out, show the sign-in button.
      authContainer.innerHTML =
        '<button class="btn btn-primary" id="signInBtn">Sign in with Google</button>';
      document.getElementById('signInBtn').onclick = signIn;
    }
  });
});

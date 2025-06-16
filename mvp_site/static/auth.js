// PASTE YOUR FIREBASE CONFIG OBJECT HERE
const firebaseConfig = {
  apiKey: "PASTE_YOUR_API_KEY_HERE",
  authDomain: "PASTE_YOUR_AUTH_DOMAIN_HERE",
  projectId: "PASTE_YOUR_PROJECT_ID_HERE",
  storageBucket: "PASTE_YOUR_STORAGE_BUCKET_HERE",
  messagingSenderId: "PASTE_YOUR_MESSAGING_SENDER_ID_HERE",
  appId: "PASTE_YOUR_APP_ID_HERE"
};
firebase.initializeApp(firebaseConfig);const auth=firebase.auth();const provider=new firebase.auth.GoogleAuthProvider();const authContainer=document.getElementById('auth-container');const contentContainer=document.getElementById('content-container');const userNameElement=document.getElementById('user-name');const signIn=()=>auth.signInWithPopup(provider).catch(e=>console.error(e));const signOut=()=>auth.signOut().catch(e=>console.error(e));auth.onAuthStateChanged(user=>{if(user){authContainer.innerHTML='<button class="btn btn-danger" onclick="signOut()">Sign Out</button>';userNameElement.textContent=user.displayName;contentContainer.style.display='block';}else{authContainer.innerHTML='<button class="btn btn-primary" onclick="signIn()">Sign in with Google</button>';contentContainer.style.display='none';}});

#!/usr/bin/env node

/**
 * CLI Authentication Tool for AI Universe
 *
 * Implements browser-based OAuth flow with localhost callback server
 * Pattern used by: gcloud CLI, Firebase CLI, GitHub CLI
 *
 * Usage:
 *   node scripts/auth-cli.mjs login
 *   node scripts/auth-cli.mjs logout
 *   node scripts/auth-cli.mjs status
 *   node scripts/auth-cli.mjs token
 */

import express from 'express';
import { createServer } from 'http';
import { readFile, writeFile, unlink, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';
import { spawn } from 'child_process';

// Constants
const TOKEN_EXPIRATION_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
const AUTH_TIMEOUT_MS = 300000; // 5 minutes

// Configuration
const CONFIG = {
  // Firebase config for AI Universe (loaded from environment variables set by the setup script)
  firebaseConfig: {
    apiKey: process.env.FIREBASE_API_KEY,
    authDomain: process.env.FIREBASE_AUTH_DOMAIN,
    projectId: process.env.FIREBASE_PROJECT_ID
  },
  callbackPort: 9005,
  callbackPath: '/auth/callback',
  tokenPath: join(homedir(), '.ai-universe', 'auth-token.json'),
  productionMcpUrl: 'https://ai-universe-backend-final.onrender.com/mcp'
};

// Validate required configuration
function validateConfig() {
  const required = ['apiKey', 'authDomain', 'projectId'];
  const missing = required.filter(key => !CONFIG.firebaseConfig[key]);

  if (missing.length > 0) {
    console.error('❌ Firebase configuration missing. Please run:');
    console.error('   ./scripts/setup-firebase-config.sh');
    console.error('');
    console.error('Or set environment variables:');
    console.error('   FIREBASE_API_KEY');
    console.error('   FIREBASE_AUTH_DOMAIN');
    console.error('   FIREBASE_PROJECT_ID');
    process.exit(1);
  }
}

// Ensure token directory exists when needed
const tokenDir = join(homedir(), '.ai-universe');

async function ensureTokenDir() {
  if (!existsSync(tokenDir)) {
    await mkdir(tokenDir, { recursive: true, mode: 0o700 });
  }
  // Ensure directory has restricted permissions (best-effort on Windows)
  try {
    const { chmod } = await import('fs/promises');
    await chmod(tokenDir, 0o700);
  } catch (err) {
    // Ignore chmod errors on Windows
  }
}

/**
 * Open URL in default browser (cross-platform)
 */
function openBrowser(url) {
  const platform = process.platform;
  let command;
  let args;

  if (platform === 'darwin') {
    command = 'open';
    args = [url];
  } else if (platform === 'win32') {
    command = 'cmd';
    args = ['/c', 'start', '', url];
  } else {
    command = 'xdg-open';
    args = [url];
  }

  const child = spawn(command, args, { detached: true, stdio: 'ignore' });
  child.on('error', (err) => {
    console.error('⚠️  Failed to open browser automatically:', err.message);
    console.error(`   Please open ${url} manually in your browser.`);
  });
  child.unref();
  return child;
}

async function readTokenData({ allowExpired = false, returnNullIfMissing = false } = {}) {
  await ensureTokenDir();

  if (!existsSync(CONFIG.tokenPath)) {
    if (returnNullIfMissing) {
      return { tokenData: null, expiresAt: null, now: new Date(), expired: false };
    }
    throw new Error('Not authenticated. Run: node scripts/auth-cli.mjs login');
  }

  let rawToken;
  try {
    rawToken = await readFile(CONFIG.tokenPath, 'utf-8');
  } catch (err) {
    throw new Error(`Error reading token file: ${err.message}`);
  }

  let tokenData;
  try {
    tokenData = JSON.parse(rawToken);
  } catch (err) {
    throw new Error(`Corrupted token file: ${err.message}. Please login again.`);
  }

  const expiresAt = new Date(tokenData.expiresAt);
  if (Number.isNaN(expiresAt.getTime())) {
    throw new Error('Token has an invalid expiration timestamp. Please login again.');
  }

  const now = new Date();
  const expired = now > expiresAt;

  if (expired && !allowExpired) {
    throw new Error('Token expired. Run: node scripts/auth-cli.mjs login');
  }

  return { tokenData, expiresAt, now, expired };
}

/**
 * Generate authentication HTML page served on localhost
 */
function getAuthHtml(callbackUrl) {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AI Universe - Sign In</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
    .status { padding: 20px; border-radius: 8px; margin: 20px 0; }
    .success { background: #d4edda; color: #155724; }
    .error { background: #f8d7da; color: #721c24; }
    button { padding: 12px 24px; font-size: 16px; cursor: pointer;
             background: #4285f4; color: white; border: none; border-radius: 4px; }
    button:hover { background: #357ae8; }
  </style>
</head>
<body>
  <h1>🚀 AI Universe Authentication</h1>
  <p>Sign in with your Google account to access the AI Universe MCP server</p>
  <button onclick="signIn()">Sign in with Google</button>
  <div id="status"></div>

  <script type="module">
    // Firebase SDK version set to 'latest' to ensure security patches are applied automatically.
    import { initializeApp } from 'https://www.gstatic.com/firebasejs/latest/firebase-app.js';
    import { getAuth, signInWithPopup, GoogleAuthProvider } from 'https://www.gstatic.com/firebasejs/latest/firebase-auth.js';

    const firebaseConfig = ${JSON.stringify(CONFIG.firebaseConfig)};
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const provider = new GoogleAuthProvider();

    window.signIn = async function() {
      const statusDiv = document.getElementById('status');
      statusDiv.className = 'status';
      statusDiv.textContent = '⏳ Opening Google sign-in...';

      try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;
        const idToken = await user.getIdToken();

        // Send token back to CLI server
        const response = await fetch('${callbackUrl}', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            idToken,
            user: {
              uid: user.uid,
              email: user.email,
              displayName: user.displayName
            }
          })
        });

        if (response.ok) {
          statusDiv.className = 'status success';
          statusDiv.innerHTML = '✅ Authentication successful!<br>You can close this window and return to the terminal.';
        } else {
          throw new Error('Failed to save token');
        }
      } catch (error) {
        console.error('Authentication error:', error);
        statusDiv.className = 'status error';
        statusDiv.textContent = '❌ Authentication failed: ' + error.message;
      }
    };
  </script>
</body>
</html>`;
}

/**
 * Start local callback server and open browser for authentication
 */
async function login() {
  console.log('🔐 Starting authentication flow...\n');

  const app = express();
  app.use(express.json());

  let server;
  let tokenReceived = false;

  // Serve authentication page
  app.get('/', (req, res) => {
    const callbackUrl = `http://127.0.0.1:${CONFIG.callbackPort}${CONFIG.callbackPath}`;
    res.send(getAuthHtml(callbackUrl));
  });

  // Handle token callback
  app.post(CONFIG.callbackPath, async (req, res) => {
    try {
      const { idToken, user } = req.body;

      if (!idToken || typeof idToken !== 'string' || !idToken.trim()) {
        res.status(400).json({ error: 'Missing or invalid token' });
        return;
      }

      if (!user || !user.uid || !user.email) {
        res.status(400).json({ error: 'Invalid user data' });
        return;
      }

      // Save token to file
      await ensureTokenDir();
      const tokenData = {
        idToken,
        user,
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + TOKEN_EXPIRATION_MS).toISOString()
      };

      await writeFile(CONFIG.tokenPath, JSON.stringify(tokenData, null, 2), { mode: 0o600 });
      // Ensure token file has restricted permissions (best-effort on Windows)
      try {
        const { chmod } = await import('fs/promises');
        await chmod(CONFIG.tokenPath, 0o600);
      } catch (err) {
        // Ignore chmod errors on Windows
      }

      res.json({ success: true });
      tokenReceived = true;

      if (server?.authTimeout) {
        clearTimeout(server.authTimeout);
        server.authTimeout = null;
      }

      console.log('\n✅ Authentication successful!');
      console.log(`   User: ${user.displayName} (${user.email})`);
      console.log(`   Token saved to: ${CONFIG.tokenPath}\n`);
      console.log('You can now use authenticated MCP tools.');

      // Close server after successful auth
      setTimeout(() => {
        server.close(() => {
          process.exit(0);
        });
      }, 1000);

    } catch (error) {
      console.error('❌ Error saving token:', error);
      res.status(500).json({ error: error.message });
    }
  });

  // Start server (bind to localhost only for security)
  server = createServer(app);
  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`❌ Port ${CONFIG.callbackPort} is already in use.`);
      console.error('   Please close any other applications using this port and try again.');
    } else {
      console.error('❌ Failed to start server:', err.message);
    }
    process.exit(1);
  });

  server.listen(CONFIG.callbackPort, '127.0.0.1', () => {
    const authUrl = `http://127.0.0.1:${CONFIG.callbackPort}`;
    console.log(`📡 Local authentication server started on ${authUrl}`);
    console.log('🌐 Opening browser for Google sign-in...\n');

    // Open browser after short delay
    setTimeout(() => {
      openBrowser(authUrl);
    }, 500);
  });

  // Timeout after 5 minutes
  const timeoutId = setTimeout(() => {
    if (!tokenReceived) {
      console.log('\n⏱️  Authentication timeout. Please try again.');
      server.close(() => {
        process.exit(1);
      });
    }
  }, AUTH_TIMEOUT_MS);

  // Store timeoutId for potential cleanup
  server.authTimeout = timeoutId;
}

/**
 * Logout (remove saved token)
 */
async function logout() {
  try {
    if (existsSync(CONFIG.tokenPath)) {
      await unlink(CONFIG.tokenPath);
      console.log('✅ Logged out successfully. Token removed.');
    } else {
      console.log('ℹ️  No active session found.');
    }
  } catch (error) {
    console.error('❌ Error during logout:', error.message);
    process.exit(1);
  }
}

/**
 * Show authentication status
 */
async function status() {
  try {
    const { tokenData, expiresAt, expired } = await readTokenData({ allowExpired: true, returnNullIfMissing: true });

    if (!tokenData) {
      console.log('❌ Not authenticated. Run: node scripts/auth-cli.mjs login');
      return;
    }

    console.log('📊 Authentication Status:');
    console.log(`   User: ${tokenData.user.displayName} (${tokenData.user.email})`);
    console.log(`   UID: ${tokenData.user.uid}`);
    console.log(`   Created: ${new Date(tokenData.createdAt).toLocaleString()}`);
    console.log(`   Expires: ${expiresAt.toLocaleString()}`);
    console.log(`   Status: ${expired ? '❌ EXPIRED' : '✅ VALID'}\n`);

    if (expired) {
      console.log('⚠️  Token expired. Run: node scripts/auth-cli.mjs login');
    }
  } catch (error) {
    console.error('❌ Error reading status:', error.message);
    process.exit(1);
  }
}

/**
 * Get current token (for use in other scripts)
 */
async function getToken() {
  try {
    const { tokenData } = await readTokenData();

    // Output just the token (for piping to other commands)
    console.log(tokenData.idToken);
  } catch (error) {
    console.error('❌', error.message);
    process.exit(1);
  }
}

/**
 * Test authenticated MCP call
 */
async function testMcp() {
  try {
    const { tokenData } = await readTokenData();
    console.log('🧪 Testing authenticated MCP connection...\n');

    const response = await fetch(CONFIG.productionMcpUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': `Bearer ${tokenData.idToken}`
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
          name: 'rate-limit.status',
          arguments: {
            userId: tokenData.user.uid
          }
        },
        id: 1
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    // Validate response structure
    if (!result || typeof result !== 'object' ||
        !result.result || typeof result.result !== 'object' ||
        !Array.isArray(result.result.content) ||
        result.result.content.length === 0 ||
        typeof result.result.content[0]?.text !== 'string') {
      throw new Error('Unexpected MCP response structure. Cannot find rate limit data.');
    }

    let rateLimitData;
    try {
      rateLimitData = JSON.parse(result.result.content[0].text);
    } catch (err) {
      throw new Error(`Failed to parse rate limit data: ${err.message}`);
    }

    // Validate rate limit data structure
    if (!rateLimitData.userType || rateLimitData.limit === undefined) {
      throw new Error('Incomplete rate limit data in response');
    }

    console.log('✅ Authentication successful!\n');
    console.log('📊 Rate Limit Status:');
    console.log(`   User Type: ${rateLimitData.userType}`);
    console.log(`   Usage: ${rateLimitData.usage}/${rateLimitData.limit}`);
    console.log(`   Remaining: ${rateLimitData.remaining}`);
    console.log(`   Reset Time: ${new Date(rateLimitData.resetTime).toLocaleString()}\n`);

  } catch (error) {
    console.error('❌ MCP test failed:', error.message);
    process.exit(1);
  }
}

// Main CLI handler
const command = process.argv[2];

// Validate configuration for commands that need it
if (command === 'login' || command === 'test') {
  validateConfig();
}

switch (command) {
  case 'login':
    await login();
    break;
  case 'logout':
    await logout();
    break;
  case 'status':
    await status();
    break;
  case 'token':
    await getToken();
    break;
  case 'test':
    await testMcp();
    break;
  default:
    console.log(`
AI Universe CLI Authentication Tool

Usage:
  node scripts/auth-cli.mjs <command>

Commands:
  login    - Start browser-based authentication flow
  logout   - Remove saved authentication token
  status   - Show current authentication status
  token    - Output current token (for piping to other commands)
  test     - Test authenticated connection to MCP server

Examples:
  # Authenticate
  node scripts/auth-cli.mjs login

  # Check status
  node scripts/auth-cli.mjs status

  # Use token in HTTPie request
  TOKEN=$(node scripts/auth-cli.mjs token)
  echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}' | \\
    http POST ${CONFIG.productionMcpUrl} \\
    Accept:'application/json, text/event-stream' \\
    Authorization:"Bearer $TOKEN"
`);
    process.exit(command ? 1 : 0);
}

#!/usr/bin/env node

/**
 * AI Universe Authentication Wrapper
 *
 * Usage:
 *   node auth-aiuniverse.mjs login
 *   node auth-aiuniverse.mjs status
 *   node auth-aiuniverse.mjs token
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const args = process.argv.slice(2);
const mainScript = join(__dirname, 'auth-cli.mjs');

const firebaseApiKey = process.env.AI_UNIVERSE_FIREBASE_API_KEY || process.env.FIREBASE_API_KEY;

if (!firebaseApiKey) {
  console.error('❌ AI_UNIVERSE_FIREBASE_API_KEY or FIREBASE_API_KEY must be set for AI Universe');
  process.exit(1);
}

const child = spawn('node', [mainScript, ...args], {
  stdio: 'inherit',
  env: {
    ...process.env,
    FIREBASE_PROJECT_ID: 'ai-universe-b3551',
    FIREBASE_AUTH_DOMAIN: 'ai-universe-b3551.firebaseapp.com',
    FIREBASE_API_KEY: firebaseApiKey
  }
});

child.on('error', (err) => {
  console.error('❌ Failed to start auth-cli:', err.message);
  process.exit(1);
});

child.on('exit', (code) => {
  process.exit(code || 0);
});

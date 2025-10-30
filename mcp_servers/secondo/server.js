#!/usr/bin/env node

/**
 * MCP Server for Second Opinion Tool
 *
 * Implements Model Context Protocol (MCP) server specification
 * Wraps secondo-cli.sh for multi-model AI feedback
 *
 * Endpoints:
 *   GET  /tools   - Returns tool definitions (tools.json)
 *   POST /execute - Executes secondo-cli.sh with parameters
 */

const express = require('express');
const { spawn } = require('child_process');
const { readFile } = require('fs/promises');
const { join } = require('path');
const { existsSync } = require('fs');
const { version } = require('./package.json');

const app = express();
const port = process.env.MCP_SECONDO_PORT || 3003;
const host = process.env.MCP_SECONDO_HOST || 'localhost';
const DEFAULT_MAX_ERROR_OUTPUT = 2000;
const parsedMaxErrorOutput = Number.parseInt(process.env.MAX_ERROR_OUTPUT || `${DEFAULT_MAX_ERROR_OUTPUT}`, 10);
const maxErrorOutput = Number.isFinite(parsedMaxErrorOutput) && parsedMaxErrorOutput >= 100
  ? parsedMaxErrorOutput
  : DEFAULT_MAX_ERROR_OUTPUT;

app.use(express.json());

// Logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

/**
 * GET /tools - Serve tool definitions
 * Required by MCP specification for tool discovery
 */
app.get('/tools', async (req, res) => {
  try {
    const toolsPath = join(__dirname, 'tools.json');

    if (!existsSync(toolsPath)) {
      return res.status(500).json({
        error: 'tools.json not found',
        ...(process.env.NODE_ENV !== 'production' && { path: toolsPath })
      });
    }

    const toolsContent = await readFile(toolsPath, 'utf-8');
    const tools = JSON.parse(toolsContent);

    res.json(tools);
  } catch (error) {
    console.error('Error serving tools:', error);
    res.status(500).json({
      error: 'Failed to load tool definitions',
      message: process.env.NODE_ENV === 'production' ? 'An unexpected error occurred' : error.message
    });
  }
});

/**
 * POST /execute - Execute secondo-cli.sh tool
 * Required by MCP specification for tool execution
 */
app.post('/execute', async (req, res) => {
  const { tool_name, parameters: rawParameters } = req.body || {};
  const parameters = rawParameters == null ? {} : rawParameters;

  console.log(`Executing tool: ${tool_name}`, parameters);

  if (tool_name !== 'get_second_opinion') {
    return res.status(400).json({
      error: `Unknown tool: ${tool_name}`,
      available_tools: ['get_second_opinion']
    });
  }

  if (typeof parameters !== 'object' || Array.isArray(parameters)) {
    return res.status(400).json({
      error: 'Invalid parameters',
      message: 'Parameters must be an object'
    });
  }

  const allowedParameterKeys = new Set(['feedback_type', 'question']);
  const unexpectedKeys = Object.keys(parameters).filter((key) => !allowedParameterKeys.has(key));

  if (unexpectedKeys.length > 0) {
    return res.status(400).json({
      error: 'Invalid parameters',
      message: `Unexpected parameter(s): ${unexpectedKeys.join(', ')}`
    });
  }

  try {
    const result = await executeSecondoTool(parameters);

    // MCP format: return result as JSON string
    res.json({ result: JSON.stringify(result) });
  } catch (error) {
    console.error('Tool execution error:', error);
    res.status(500).json({
      error: 'Tool execution failed',
      message: process.env.NODE_ENV === 'production' ? 'An unexpected error occurred' : error.message,
      ...(process.env.NODE_ENV !== 'production' && { details: error.details || null })
    });
  }
});

/**
 * Execute secondo-cli.sh script
 * @param {Object} parameters - Tool parameters (feedback_type, question)
 * @returns {Promise<Object>} Execution result
 */
async function executeSecondoTool(parameters) {
  const { feedback_type = 'all', question = '' } = parameters || {};

  // Find project root (where scripts/ directory is)
  // Assumes server.js is located at mcp_servers/secondo/server.js relative to project root
  const projectRoot = join(__dirname, '..', '..');
  const secondoScript = join(projectRoot, 'scripts', 'secondo-cli.sh');

  if (!existsSync(secondoScript)) {
    throw {
      message: 'secondo-cli.sh not found',
      details: { path: secondoScript }
    };
  }

  // Check authentication first
  const authCheck = await checkAuthentication(projectRoot);
  if (!authCheck.authenticated) {
    throw {
      message: 'Authentication required',
      details: {
        help: 'Run: node scripts/auth-cli.mjs login',
        error: authCheck.error
      }
    };
  }

  // Build command arguments
  const normalizedFeedbackType = String(feedback_type || 'all').trim() || 'all';
  const normalizedQuestion = typeof question === 'string' ? question : String(question || '');

  const args = [normalizedFeedbackType];
  if (normalizedQuestion) {
    args.push(normalizedQuestion);
  }

  console.log(`Spawning: bash ${secondoScript} ${args.join(' ')}`);

  return new Promise((resolve, reject) => {
    const child = spawn('bash', [secondoScript, ...args], {
      cwd: projectRoot,
      shell: false,
      timeout: 180000 // 3 minutes timeout
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('error', (error) => {
      reject({
        message: 'Failed to spawn secondo-cli.sh',
        details: {
          error: error.message,
          script: secondoScript
        }
      });
    });

    child.on('close', (code, signal) => {
      if (signal === 'SIGTERM' && code === null) {
        return reject({
          message: 'secondo-cli.sh execution timed out after 3 minutes',
          details: {
            stdout: stdout.slice(0, maxErrorOutput),
            stderr: stderr.slice(0, maxErrorOutput)
          }
        });
      }

      if (code === 0) {
        resolve({
          success: true,
          output: stdout,
          feedback_type: normalizedFeedbackType,
          question: normalizedQuestion || 'default prompt'
        });
      } else {
        reject({
          message: `secondo-cli.sh exited with code ${code}`,
          details: {
            stdout: stdout.slice(0, maxErrorOutput),
            stderr: stderr.slice(0, maxErrorOutput)
          }
        });
      }
    });
  });
}

/**
 * Check if user is authenticated via auth-cli.mjs
 * @param {string} projectRoot - Project root directory
 * @returns {Promise<Object>} Authentication status
 */
async function checkAuthentication(projectRoot) {
  const authScript = join(projectRoot, 'scripts', 'auth-cli.mjs');

  if (!existsSync(authScript)) {
    return {
      authenticated: false,
      error: 'auth-cli.mjs not found'
    };
  }

  return new Promise((resolve) => {
    const child = spawn('node', [authScript, 'status'], {
      cwd: projectRoot,
      shell: false,
      timeout: 5000
    });

    let output = '';
    child.stdout.on('data', (data) => { output += data.toString(); });
    child.stderr.on('data', (data) => { output += data.toString(); });

    child.on('close', (code) => {
      const trimmedOutput = output.trim();
      const normalizedOutput = trimmedOutput.toLowerCase();
      const hasValidStatus = /status:\s*(✅\s*)?valid/i.test(trimmedOutput);
      const isNotAuthenticated = /not authenticated/.test(normalizedOutput);
      const isExpired = /expired/.test(normalizedOutput) && !hasValidStatus;

      const authenticated = code === 0 && hasValidStatus && !isExpired && !isNotAuthenticated;

      resolve({
        authenticated,
        error: authenticated ? null : (trimmedOutput || (code !== 0 ? 'Authentication check failed' : 'Not authenticated'))
      });
    });

    child.on('error', (error) => {
      resolve({
        authenticated: false,
        error: error.message
      });
    });
  });
}

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'secondo-mcp-server',
    version,
    timestamp: new Date().toISOString()
  });
});

/**
 * Root endpoint - MCP server info
 */
app.get('/', (req, res) => {
  res.json({
    name: 'Secondo MCP Server',
    description: 'Multi-model AI feedback via Model Context Protocol',
    version,
    endpoints: {
      tools: '/tools',
      execute: '/execute',
      health: '/health'
    },
    mcp_version: '1.0',
    documentation: 'https://docs.anthropic.com/en/docs/agents-and-tools/mcp'
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'production' ? 'An unexpected error occurred' : err.message
  });
});

// Start server
let server;

server = app.listen(port, host, () => {
  console.log(`🚀 Secondo MCP Server running on http://${host}:${port}`);
  console.log(`📋 Tools endpoint: http://${host}:${port}/tools`);
  console.log(`⚡ Execute endpoint: http://${host}:${port}/execute`);
  console.log(`💚 Health check: http://${host}:${port}/health`);
  console.log('');
  console.log('Ready to serve multi-model AI feedback via MCP protocol');
});

// Graceful shutdown
function gracefulShutdown(signal) {
  console.log(`${signal} received, shutting down gracefully...`);
  if (server) {
    server.close(() => {
      console.log('HTTP server closed, exiting');
      process.exit(0);
    });

    setTimeout(() => {
      console.warn('Force exiting after 30 seconds grace period');
      process.exit(1);
    }, 30000).unref();
  } else {
    process.exit(0);
  }
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

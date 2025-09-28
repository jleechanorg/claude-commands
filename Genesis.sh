
#!/bin/bash

# Create the main HTML file
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Swift Code Generator - Cerberus AI</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f7;
            color: #333;
        }
        .container {
            background-color: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        h1 {
            color: #0071e3;
            text-align: center;
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }
        textarea, input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        textarea {
            height: 120px;
            font-family: monospace;
            resize: vertical;
        }
        button {
            background-color: #0071e3;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 14px 20px;
            font-size: 18px;
            cursor: pointer;
            width: 100%;
            font-weight: 600;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #005bbd;
        }
        button:disabled {
            background-color: #a0c4e8;
            cursor: not-allowed;
        }
        .loading {
            text-align: center;
            color: #0071e3;
            font-weight: 500;
            display: none;
        }
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-left-color: #0071e3;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .error {
            color: #ff3b30;
            background-color: #ffebee;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }
        .code-container {
            margin-top: 25px;
        }
        pre {
            background-color: #2c2c2e;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin-top: 10px;
        }
        code {
            font-family: "SF Mono", Monaco, Menlo, Consolas, monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        .info {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .copy-btn {
            background-color: #34c759;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 15px;
            font-size: 14px;
            cursor: pointer;
            margin-top: 10px;
            font-weight: 500;
        }
        .copy-btn:hover {
            background-color: #2db44d;
        }
        .copy-success {
            color: #34c759;
            font-weight: 500;
            margin-top: 10px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Swift Code Generator</h1>
        <p style="text-align: center; color: #666;">Powered by Cerberus AI</p>

        <div class="info">
            <p><strong>How to get your Cerberus AI API key:</strong></p>
            <ol>
                <li>Visit <a href="https://www.cerberusai.com" target="_blank">cerberusai.com</a> and sign up</li>
                <li>Go to your dashboard to generate an API key</li>
                <li>Paste the key below to start generating Swift code</li>
            </ol>
        </div>

        <div class="input-group">
            <label for="apiKey">Cerberus AI API Key:</label>
            <input type="password" id="apiKey" placeholder="Enter your API key">
        </div>

        <div class="input-group">
            <label for="prompt">Code Generation Prompt:</label>
            <textarea id="prompt" placeholder="Describe the iOS feature you want to generate code for..."></textarea>
        </div>

        <button id="generateBtn">Generate Swift Code</button>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Generating code with Cerberus AI...</p>
        </div>

        <div class="error" id="error"></div>

        <div class="code-container">
            <label>Generated Swift Code:</label>
            <pre><code id="codeOutput">// Generated code will appear here</code></pre>
            <button class="copy-btn" id="copyBtn">Copy to Clipboard</button>
            <div class="copy-success" id="copySuccess">✓ Copied to clipboard!</div>
        </div>
    </div>

    <script>
        document.getElementById('generateBtn').addEventListener('click', generateCode);
        document.getElementById('copyBtn').addEventListener('click', copyCode);

        async function generateCode() {
            const apiKey = document.getElementById('apiKey').value;
            const prompt = document.getElementById('prompt').value;
            const loadingElement = document.getElementById('loading');
            const errorElement = document.getElementById('error');
            const outputElement = document.getElementById('codeOutput');
            const button = document.getElementById('generateBtn');

            if (!apiKey) {
                showError('Please enter your Cerberus AI API key');
                return;
            }

            if (!prompt) {
                showError('Please enter a code generation prompt');
                return;
            }

            // Reset UI
            errorElement.style.display = 'none';
            loadingElement.style.display = 'block';
            button.disabled = true;
            outputElement.textContent = '// Generating code...';

            try {
                const response = await fetch('https://api.cerberusai.com/v1/completions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${apiKey}`
                    },
                    body: JSON.stringify({
                        model: 'cerberus-1',
                        prompt: `Generate iOS Swift code for: ${prompt}. Only return the code without any explanations.`,
                        max_tokens: 1000,
                        temperature: 0.7
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`API Error: ${errorData.error?.message || response.statusText}`);
                }

                const data = await response.json();
                const generatedCode = data.choices[0].text.trim();

                outputElement.textContent = generatedCode || '// No code generated';
            } catch (error) {
                showError(`Error: ${error.message}`);
                outputElement.textContent = '// Failed to generate code';
            } finally {
                loadingElement.style.display = 'none';
                button.disabled = false;
            }
        }

        function copyCode() {
            const codeOutput = document.getElementById('codeOutput');
            const copySuccess = document.getElementById('copySuccess');

            navigator.clipboard.writeText(codeOutput.textContent)
                .then(() => {
                    copySuccess.style.display = 'block';
                    setTimeout(() => {
                        copySuccess.style.display = 'none';
                    }, 2000);
                })
                .catch(err => {
                    showError('Failed to copy: ' + err);
                });
        }

        function showError(message) {
            const errorElement = document.getElementById('error');
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    </script>
</body>
</html>
EOF

# Create README.md
cat > README.md << 'EOF'
# Swift Code Generator with Cerberus AI

This tool generates Swift iOS code using Cerberus AI's API. Simply enter your API key and describe what you want to build!

## How to Use

1. Get your Cerberus AI API key:
   - Visit [cerberusai.com](https://www.cerberusai.com) and sign up
   - Go to your dashboard to generate an API key

2. Open `index.html` in your browser

3. Enter your API key and describe the iOS feature you want to generate

4. Click "Generate Swift Code" and copy the result

## Features

- Real-time Swift code generation
- One-click copy to clipboard
- iOS-inspired UI design
- Error handling and loading indicators
EOF

# Create setup script for easy execution
cat > setup.sh << 'EOF'
#!/bin/bash
echo "Setting up Swift Code Generator..."
echo "Files created:"
echo "  - index.html"
echo "  - README.md"
echo ""
echo "To use:"
echo "1. Get your Cerberus AI API key from https://www.cerberusai.com"
echo "2. Open index.html in your browser"
echo "3. Enter your API key and prompt"
echo "4. Generate Swift code!"
EOF

chmod +x setup.sh

# Output completion message
echo "✅ Setup complete!"
echo "Created files:"
echo "  - index.html (main website)"
echo "  - README.md (project documentation)"
echo "  - setup.sh (this script)"
echo ""
echo "To get started:"
echo "1. Get your Cerberus AI API key from https://www.cerberusai.com"
echo "2. Open index.html in your browser"
echo "3. Enter your API key and describe what you want to build"
echo ""
echo "Optional: Run './setup.sh' to see this message again"

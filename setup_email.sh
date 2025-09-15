#!/bin/bash
# Email Setup for Backup System - Portable Configuration

# Auto-detect email from git config as default
DEFAULT_EMAIL="${EMAIL_USER:-$(git config user.email 2>/dev/null || echo '<your-email@example.com>')}"

echo "🔧 Setting up email configuration for backup system..."
echo ""
echo "Using account: ${DEFAULT_EMAIL}"
echo ""

# Interactive email setup if not already configured
if [[ "$DEFAULT_EMAIL" == *"example.com"* ]] || [[ -z "$EMAIL_USER" ]]; then
    echo "📧 Email not configured. Set EMAIL_USER environment variable or configure git:"
    echo "   git config user.email your-email@gmail.com"
    echo ""
fi

echo "To complete email setup, you need a Gmail App Password:"
echo "1. Go to: https://myaccount.google.com/apppasswords"
echo "2. Generate app password for 'Mail' application"
echo "3. Use the 16-character password below"
echo ""
echo "Set these environment variables (replace <your-email> with your Gmail address):"
echo 'export EMAIL_USER="<your-email@gmail.com>"'
echo 'export EMAIL_PASS="your-16-char-app-password"'
echo 'export BACKUP_EMAIL="<your-email@gmail.com>"'
echo ""
echo "Add to ~/.bashrc to persist (replace <your-email> with your Gmail address):"
echo 'echo "export EMAIL_USER=\"<your-email@gmail.com>\"" >> ~/.bashrc'
echo 'echo "export EMAIL_PASS=\"your-app-password\"" >> ~/.bashrc'
echo 'echo "export BACKUP_EMAIL=\"<your-email@gmail.com>\"" >> ~/.bashrc'
echo ""
echo "Test with: ./scripts/backup_validation.sh"

#!/bin/bash
# Email Setup for Backup System

echo "🔧 Setting up email configuration for backup system..."
echo ""
echo "Using account: jleechantest@gmail.com"
echo ""
echo "To complete email setup, you need a Gmail App Password:"
echo "1. Go to: https://myaccount.google.com/apppasswords"
echo "2. Generate app password for 'Mail' application"  
echo "3. Use the 16-character password below"
echo ""
echo "Set these environment variables:"
echo 'export EMAIL_USER="jleechantest@gmail.com"'
echo 'export EMAIL_PASS="your-16-char-app-password"'
echo 'export BACKUP_EMAIL="jleechantest@gmail.com"'
echo ""
echo "Add to ~/.bashrc to persist:"
echo 'echo "export EMAIL_USER=\"jleechantest@gmail.com\"" >> ~/.bashrc'
echo 'echo "export EMAIL_PASS=\"your-app-password\"" >> ~/.bashrc'  
echo 'echo "export BACKUP_EMAIL=\"jleechantest@gmail.com\"" >> ~/.bashrc'
echo ""
echo "Test with: ./scripts/backup_validation.sh"

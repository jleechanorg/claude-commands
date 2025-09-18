#!/bin/bash
# Delete all campaigns with specific name in batches

# Accept command-line arguments or use environment variables
if [ -n "$1" ]; then
    USER_ID="$1"
elif [ -n "$USER_ID" ]; then
    USER_ID="$USER_ID"
else
    echo "❌ Error: USER_ID not provided. Please provide as the first argument or set the USER_ID environment variable."
    echo "Usage: $0 <USER_ID> [CAMPAIGN_NAME]"
    echo "Example: $0 vnLp2G3m21PJL6kxcuAqmWSOtm73 'My Epic Adventure'"
    exit 1
fi

if [ -n "$2" ]; then
    CAMPAIGN_NAME="$2"
elif [ -n "$CAMPAIGN_NAME" ]; then
    CAMPAIGN_NAME="$CAMPAIGN_NAME"
else
    CAMPAIGN_NAME="My Epic Adventure"
fi

# Use environment variable for credentials or default location
CREDENTIALS_PATH="${GOOGLE_APPLICATION_CREDENTIALS:-$HOME/serviceAccountKey.json}"

if [ ! -f "$CREDENTIALS_PATH" ]; then
    echo "❌ Error: Credentials file not found at $CREDENTIALS_PATH"
    echo "Please set GOOGLE_APPLICATION_CREDENTIALS environment variable or place file at $HOME/serviceAccountKey.json"
    exit 1
fi

echo "🗑️ Starting batch deletion of all 'My Epic Adventure' campaigns"
echo "User: $USER_ID"
echo "Campaign Name: $CAMPAIGN_NAME"
echo ""

batch=1
while true; do
    echo "🔄 Running batch $batch..."
    
    # Run deletion script
    GOOGLE_APPLICATION_CREDENTIALS="$CREDENTIALS_PATH" python3 scripts/delete_campaigns_by_name.py "$USER_ID" "$CAMPAIGN_NAME" --confirm --force
    
    # Check if any campaigns were found to delete
    if [ $? -eq 0 ]; then
        echo "✅ Batch $batch completed"
        
        # Quick check to see if there are more campaigns
        echo "🔍 Checking for remaining campaigns..."
        GOOGLE_APPLICATION_CREDENTIALS="$CREDENTIALS_PATH" python3 scripts/query_campaigns_by_name.py "$USER_ID" "$CAMPAIGN_NAME" 2>/dev/null | grep -q "🎯 Found 0 campaigns"
        
        if [ $? -eq 0 ]; then
            echo "✅ All campaigns deleted! No more 'My Epic Adventure' campaigns found."
            break
        else
            echo "📊 More campaigns found, continuing..."
            batch=$((batch + 1))
            sleep 2  # Small delay between batches
        fi
    else
        echo "❌ Batch $batch failed"
        break
    fi
done

echo ""
echo "🎉 Batch deletion process completed!"
echo "📊 Total batches processed: $batch"
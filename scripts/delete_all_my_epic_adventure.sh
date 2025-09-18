#!/bin/bash
# Delete all "My Epic Adventure" campaigns in batches

USER_ID="vnLp2G3m21PJL6kxcuAqmWSOtm73"
CAMPAIGN_NAME="My Epic Adventure"

echo "🗑️ Starting batch deletion of all 'My Epic Adventure' campaigns"
echo "User: $USER_ID"
echo "Campaign Name: $CAMPAIGN_NAME"
echo ""

batch=1
while true; do
    echo "🔄 Running batch $batch..."
    
    # Run deletion script
    GOOGLE_APPLICATION_CREDENTIALS=/home/jeff/serviceAccountKey.json python3 scripts/delete_campaigns_by_name.py "$USER_ID" "$CAMPAIGN_NAME" --confirm --force
    
    # Check if any campaigns were found to delete
    if [ $? -eq 0 ]; then
        echo "✅ Batch $batch completed"
        
        # Quick check to see if there are more campaigns
        echo "🔍 Checking for remaining campaigns..."
        GOOGLE_APPLICATION_CREDENTIALS=/home/jeff/serviceAccountKey.json python3 scripts/query_campaigns_by_name.py "$USER_ID" "$CAMPAIGN_NAME" 2>/dev/null | grep -q "🎯 Found 0 campaigns"
        
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
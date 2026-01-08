
import json

try:
    with open('inline_comments.json', 'r') as f:
        comments = json.load(f)

    print(f"Found {len(comments)} inline comments.")
    for comment in comments:
        print(f"File: {comment['path']}")
        print(f"Line: {comment.get('line') or comment.get('original_line')}")
        print(f"User: {comment['user']['login']}")
        print(f"Body: {comment['body']}")
        print("-" * 20)

except Exception as e:
    print(f"Error parsing inline comments: {e}")

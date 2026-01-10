import json
import os

def print_comments(filename, label):
    if not os.path.exists(filename):
        print(f"No {label} file found.")
        return
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
            if not content:
                print(f"Empty {label} file.")
                return
            data = json.loads(content)
            
        print(f"--- {label} ---")
        for item in data:
            user = item.get('user', {}).get('login', 'Unknown')
            body = item.get('body', '')
            path = item.get('path', 'N/A')
            line = item.get('line', 'N/A')
            url = item.get('html_url', '')
            print(f"User: {user}")
            print(f"URL: {url}")
            if path != 'N/A':
                print(f"File: {path}:{line}")
            print(f"Body: {body}\n")
            print("-" * 20)
    except json.JSONDecodeError:
        print(f"Failed to parse {filename}")
    except Exception as e:
        print(f"Error reading {filename}: {e}")

print_comments('.gemini/tmp/issue_comments.json', 'Issue Comments')
print_comments('.gemini/tmp/reviews.json', 'Reviews')
print_comments('.gemini/tmp/inline_comments.json', 'Inline Comments')

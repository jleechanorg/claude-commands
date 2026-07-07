# remove-gamma-watermark

Remove the "Made with GAMMA" watermark badge from a Google Slides presentation exported from Gamma.

## When to use

When a presentation was created in Gamma and exported to Google Slides, a "Made with GAMMA" badge appears in the bottom-right corner of every slide. This skill removes it by deleting the watermark image element from all slide layouts via the Google Slides API.

## How it works

The watermark is stored as an image element in each **slide layout** (not on individual slides), so deleting it from the layouts removes it from all slides at once.

## Prerequisites

- `gog` CLI installed (`which gog` should return a path)
- Authenticated: `gog auth status` should show `$USER@gmail.com`
- Python 3 available

## Steps

### 1. Get presentation ID from URL

Extract from `https://docs.google.com/presentation/d/<PRES_ID>/edit`:

```bash
PRES_ID="<paste presentation ID here>"
```

### 2. Get a short-lived access token via gog

```bash
gog auth tokens export $USER@gmail.com --out /tmp/gog_token.json --overwrite

ACCESS_TOKEN=$(python3 - <<'PYEOF'
import json, urllib.request, urllib.parse

token_data = json.load(open('/tmp/gog_token.json'))
creds = json.load(open('$HOME/Library/Application Support/gogcli/credentials.json'))

data = urllib.parse.urlencode({
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'refresh_token': token_data['refresh_token'],
    'grant_type': 'refresh_token'
}).encode()

req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, method='POST')
with urllib.request.urlopen(req) as resp:
    print(json.loads(resp.read())['access_token'])
PYEOF
)
```

### 3. Find watermark elements in slide layouts

```bash
python3 - <<PYEOF
import json, urllib.request

access_token = "$ACCESS_TOKEN"
pres_id = "$PRES_ID"
SLIDE_W, SLIDE_H = 14630400, 8229600

req = urllib.request.Request(
    f"https://slides.googleapis.com/v1/presentations/{pres_id}",
    headers={"Authorization": f"Bearer {access_token}"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

wm_ids = []
for layout in data.get('layouts', []):
    for e in layout.get('pageElements', []):
        if 'image' in e:
            t = e.get('transform', {})
            x = t.get('translateX', 0) / SLIDE_W * 100
            y = t.get('translateY', 0) / SLIDE_H * 100
            if x > 70 and y > 80:
                wm_ids.append(e['objectId'])
                print(f"Found watermark: {e['objectId']} in layout {layout['objectId']} at ({x:.1f}%, {y:.1f}%)")

print(f"\nTotal watermark elements to delete: {len(wm_ids)}")
print("IDs:", wm_ids)
PYEOF
```

### 4. Delete all watermark elements

```bash
python3 - <<PYEOF
import json, urllib.request

access_token = "$ACCESS_TOKEN"
pres_id = "$PRES_ID"
SLIDE_W, SLIDE_H = 14630400, 8229600

# Rediscover IDs (or hardcode from step 3)
req = urllib.request.Request(
    f"https://slides.googleapis.com/v1/presentations/{pres_id}",
    headers={"Authorization": f"Bearer {access_token}"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

wm_ids = []
for layout in data.get('layouts', []):
    for e in layout.get('pageElements', []):
        if 'image' in e:
            t = e.get('transform', {})
            x = t.get('translateX', 0) / SLIDE_W * 100
            y = t.get('translateY', 0) / SLIDE_H * 100
            if x > 70 and y > 80:
                wm_ids.append(e['objectId'])

requests = [{"deleteObject": {"objectId": oid}} for oid in wm_ids]
payload = json.dumps({"requests": requests}).encode()

req = urllib.request.Request(
    f"https://slides.googleapis.com/v1/presentations/{pres_id}:batchUpdate",
    data=payload,
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    print(f"Done. {len(result.get('replies', []))} elements deleted.")
PYEOF
```

### 5. Verify (optional)

Fetch a slide thumbnail and confirm the badge is gone:

```bash
curl -s "https://slides.googleapis.com/v1/presentations/${PRES_ID}/pages/SLIDE_ID/thumbnail?thumbnailProperties.mimeType=PNG&thumbnailProperties.thumbnailSize=LARGE" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | python3 -c "
import json, sys, urllib.request
url = json.load(sys.stdin).get('contentUrl','')
urllib.request.urlretrieve(url, '/tmp/slide_after.png')
print('Saved /tmp/slide_after.png')
"
open /tmp/slide_after.png
```

### 6. Clean up

```bash
rm -f /tmp/gog_token.json
```

## Notes

- The watermark threshold (`x > 70 and y > 80`) targets the bottom-right corner where Gamma places its badge. Adjust if a future Gamma version moves it.
- This only works for presentations you own or have edit access to.
- Slide dimensions vary by template. The detection uses percentage positions so it's dimension-agnostic.

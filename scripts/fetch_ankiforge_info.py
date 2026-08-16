"""Fetch AnkiForge info from GitHub API and AnkiWeb."""
import json
import urllib.request

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

# Search GitHub for AnkiForge
print("=== GitHub Search: AnkiForge ===")
try:
    data = fetch_json("https://api.github.com/search/repositories?q=ankiforge+anki&per_page=5")
    for item in data.get("items", []):
        print(f"  {item['full_name']} | stars: {item['stargazers_count']} | forks: {item['forks_count']}")
        print(f"    desc: {item.get('description', 'N/A')}")
        print(f"    lang: {item.get('language', 'N/A')} | updated: {item.get('updated_at', 'N/A')}")
except Exception as e:
    print(f"  Error: {e}")

# Also search for AnkiForge specifically
print("\n=== GitHub Search: AnkiForge (exact) ===")
try:
    data = fetch_json("https://api.github.com/search/repositories?q=AnkiForge&per_page=5")
    for item in data.get("items", []):
        print(f"  {item['full_name']} | stars: {item['stargazers_count']} | forks: {item['forks_count']}")
        print(f"    desc: {item.get('description', 'N/A')}")
        print(f"    lang: {item.get('language', 'N/A')} | updated: {item.get('updated_at', 'N/A')}")
except Exception as e:
    print(f"  Error: {e}")

# Try AnkiWeb API endpoint
print("\n=== AnkiWeb API ===")
try:
    req = urllib.request.Request("https://ankiweb.net/shared/info/1482895298", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8")
        # Look for JSON data embedded in the page
        if "addon" in content.lower():
            print("  Found addon data in page")
        print(f"  Content length: {len(content)}")
except Exception as e:
    print(f"  Error: {e}")

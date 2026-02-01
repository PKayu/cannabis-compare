import requests
import time

print("Testing scraper API endpoint...")
print("=" * 60)

# Trigger the scraper
response = requests.post("http://localhost:8000/api/admin/scrapers/run/wholesomeco")

print(f"Status Code: {response.status_code}")
print(f"Response:")
print(response.json())

# Wait a bit and check the latest run
print("\nWaiting 5 seconds...")
time.sleep(5)

# Get the latest run
response = requests.get("http://localhost:8000/api/admin/scrapers/runs?scraper_id=wholesomeco&limit=1")
runs = response.json()

if runs:
    latest = runs[0]
    print("\nLatest run:")
    print(f"  Status: {latest['status']}")
    print(f"  Products Found: {latest['products_found']}")
    print(f"  Products Processed: {latest['products_processed']}")
    if latest.get('error_message'):
        print(f"  Error: {latest['error_message']}")

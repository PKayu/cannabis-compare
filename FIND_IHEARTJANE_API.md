# How to Find iHeartJane API Endpoints

**Goal:** Find the store IDs and API structure for WholesomeCo and Beehive Farmacy

---

## Step-by-Step Guide

### Step 1: Find WholesomeCo's iHeartJane Store ID

1. **Open WholesomeCo Website:**
   ```
   Search Google for: "WholesomeCo Utah cannabis"
   Or try: https://www.wholesomeco.com
   ```

2. **Open DevTools:**
   - Press `F12` or right-click → "Inspect"
   - Go to the **Network** tab
   - Filter by **Fetch/XHR** (shows API calls)

3. **Navigate to Menu Page:**
   - Click on their "Menu" or "Shop" link
   - Watch the Network tab for API requests

4. **Look for iHeartJane API Call:**
   - Look for URLs containing: `api.iheartjane.com`
   - Common patterns:
     ```
     https://api.iheartjane.com/v1/stores/{STORE_ID}/products
     https://api.iheartjane.com/v1/stores/{STORE_ID}/menu
     ```
   - **STORE_ID is what we need!** (e.g., `1234`, `abc-123`, etc.)

5. **Click on the API Request:**
   - Look at the **Headers** tab
   - Check the **Response** tab to see JSON structure
   - Copy the full URL

6. **Document What You Find:**
   ```
   Store ID: ____________
   API URL: ____________
   Any auth headers needed? ____________
   ```

### Step 2: Analyze API Response Structure

Click on one of the iHeartJane API requests and look at the **Response** tab. You should see JSON like:

```json
{
  "products": [
    {
      "id": "prod-123",
      "name": "Blue Dream 3.5g",
      "brand": {
        "name": "Tryke Companies"
      },
      "category": "Flower",
      "price": 45.00,
      "potency_thc": {
        "value": 22.5,
        "unit": "%"
      },
      "in_stock": true
    }
  ]
}
```

**Note the field names:** Do they use `products` or `items`? Is brand nested or flat? This helps us write the parser.

### Step 3: Repeat for Beehive Farmacy

1. **Find their website:**
   ```
   Search Google for: "Beehive Farmacy Utah"
   ```

2. **Follow same steps** as WholesomeCo
3. **Document their store ID and API structure**

### Step 4: Share Your Findings

Once you've inspected both sites, share:

```markdown
## WholesomeCo
- Website: [URL]
- iHeartJane Store ID: [FOUND_ID]
- API Endpoint: https://api.iheartjane.com/v1/stores/[FOUND_ID]/products
- Notes: [Any special observations]

## Beehive Farmacy
- Website: [URL]
- iHeartJane Store ID: [FOUND_ID]
- API Endpoint: https://api.iheartjane.com/v1/stores/[FOUND_ID]/products
- Notes: [Any special observations]
```

---

## Troubleshooting

### "I don't see api.iheartjane.com in Network tab"

**Possible reasons:**
1. They may use a different menu provider (Dutchie, custom, etc.)
2. Menu loads via JavaScript after page load - scroll through products
3. They embed iHeartJane in an iframe - check iframe requests

**Solutions:**
- Clear network log and reload page
- Try clicking on different product categories
- Search network requests for "jane" or "menu"

### "API requires authentication"

**Check:**
- Headers tab for API keys (if visible, note them)
- Most iHeartJane stores have public APIs
- If auth is needed, we'll handle it in the scraper

### "Response structure is different"

**That's okay!** Document what you see:
- Field names might vary (`potency_thc` vs `thc_percentage`)
- Brand might be string or object
- We'll adapt the parser to handle variations

---

## Alternative: Use Playwright to Inspect

If you have Playwright installed, you can run this script:

```python
# inspect_iheartjane.py
import asyncio
from playwright.async_api import async_playwright

async def inspect_site(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Monitor API calls
        async def log_request(request):
            if 'iheartjane' in request.url:
                print(f"\n📡 API Call: {request.url}")

        page.on('request', log_request)

        # Go to site
        await page.goto(url)
        print(f"Opened: {url}")
        print("Navigate to menu page and watch for API calls...")

        # Wait for user to inspect
        await page.wait_for_timeout(60000)  # 60 seconds
        await browser.close()

# Usage
asyncio.run(inspect_site("https://www.wholesomeco.com"))
```

---

## What to Look For (Checklist)

- [ ] WholesomeCo website URL found
- [ ] WholesomeCo uses iHeartJane (confirmed)
- [ ] WholesomeCo store ID extracted
- [ ] WholesomeCo API response structure documented
- [ ] Beehive Farmacy website URL found
- [ ] Beehive Farmacy uses iHeartJane (confirmed)
- [ ] Beehive Farmacy store ID extracted
- [ ] Beehive Farmacy API response structure documented
- [ ] Sample JSON response saved for both

---

**Once you have this info, we can:**
1. Create the iHeartJane scraper with correct store IDs
2. Test it immediately
3. Start getting real product data!

**Time required:** 10-15 minutes for both dispensaries

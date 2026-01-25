import json
from bs4 import BeautifulSoup

# This is the HTML snippet you found (I cleaned up the quotes for Python string)
html_snippet = """
<div data-controller="analytics" 
     data-analytics-rudderstack-event-value="Product Clicked" 
     data-analytics-rudderstack-payload-value='{"product_id":"70b23a80-29e0-4cb1-acf8-3b256f67ea0f","brand":"Hilight","categories":["Edibles","Gummies"],"category":"Edibles › Gummies","currency":"USD","discount":0.0,"image_url":"...","name":"Lemon Cream Limonene Terp Gummy – 1mg 30-pack","price":16.0,"quantity":1,"sku":"IBC3HILKSM000007","total":16.0,"url":"https://www.wholesome.co/shop/edibles/hilight-lemon-cream-limonene-terp-gummy-1mg-30-pack","variant":"1mg"}' 
     hidden="hidden">
</div>
"""

def test_parse():
    print("🧪 Testing WholesomeCo HTML Parser...")
    
    soup = BeautifulSoup(html_snippet, 'html.parser')
    
    # Find the element
    element = soup.find('div', attrs={'data-controller': 'analytics'})
    
    if element:
        # Extract the JSON string
        raw_json = element.get('data-analytics-rudderstack-payload-value')
        
        # Parse JSON
        data = json.loads(raw_json)
        
        print("\n✅ SUCCESS! Extracted Data:")
        print(f"Name:     {data.get('name')}")
        print(f"Brand:    {data.get('brand')}")
        print(f"Price:    ${data.get('price')}")
        print(f"Category: {data.get('category')}")
        print(f"Variant:  {data.get('variant')}")
    else:
        print("❌ Could not find element")

if __name__ == "__main__":
    test_parse()
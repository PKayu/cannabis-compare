import asyncio
from services.scrapers.playwright_scraper import WholesomeCoScraper

async def test():
    print('Testing new WholesomeCo scraper...')
    print('=' * 60)

    scraper = WholesomeCoScraper()

    print(f'Scraper ID: wholesomeco')
    print(f'Scraper Class: {scraper.__class__.__name__}')
    print(f'Scraper Module: {scraper.__class__.__module__}')
    print()

    print('Starting scrape...')
    products = await scraper.scrape_products()

    print(f'Products found: {len(products)}')

    if products:
        print()
        print('First 5 products:')
        for i, p in enumerate(products[:5], 1):
            print(f'{i}. {p.name}')
            print(f'   THC: {p.thc_percentage}%')
            print(f'   CBD: {p.cbd_percentage}%')
            print(f'   Price: ${p.price}')
            print()

asyncio.run(test())

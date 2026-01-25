from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
from services.scraper_runner import ScraperRunner

router = APIRouter(prefix="/scrapers", tags=["scrapers"])

@router.get("/dashboard", response_class=HTMLResponse)
async def scraper_dashboard():
    """Simple dashboard to trigger scrapers manually"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🕷️ Scraper Dashboard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; background: #f9f9f9; }
            .card { background: white; border: 1px solid #ddd; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 1rem; }
            h1 { color: #333; }
            button { background: #10b981; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
            button:hover { background: #059669; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .status { margin-top: 1rem; padding: 1rem; background: #f3f4f6; border-radius: 6px; display: none; }
            pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; }
        </style>
    </head>
    <body>
        <h1>🕷️ Scraper Control Center</h1>
        
        <div class="card">
            <h2>WholesomeCo</h2>
            <p>Scrape products directly from WholesomeCo website and save to database.</p>
            <button onclick="runScraper('wholesomeco')">🚀 Run Scraper</button>
            <div id="status-wholesomeco" class="status"></div>
        </div>

        <script>
            async function runScraper(name) {
                const btn = document.querySelector(`button[onclick="runScraper('${name}')"]`);
                const statusDiv = document.getElementById(`status-${name}`);
                
                btn.disabled = true;
                btn.textContent = "Running... (Please Wait)";
                statusDiv.style.display = "block";
                statusDiv.innerHTML = "⏳ Scraping in progress... check backend logs for details.";

                try {
                    const response = await fetch(`/scrapers/run/${name}`, { method: 'POST' });
                    const data = await response.json();
                    statusDiv.innerHTML = `<h3>✅ Result:</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
                } catch (e) {
                    statusDiv.innerHTML = `<h3>❌ Error:</h3><pre>${e.message}</pre>`;
                } finally {
                    btn.disabled = false;
                    btn.textContent = "🚀 Run Scraper";
                }
            }
        </script>
    </body>
    </html>
    """

@router.post("/run/wholesomeco")
async def run_wholesomeco(db: Session = Depends(get_db)):
    """Trigger the WholesomeCo scraper"""
    runner = ScraperRunner(db)
    result = await runner.run_wholesomeco()
    return result
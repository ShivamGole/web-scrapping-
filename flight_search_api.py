"""
FastAPI wrapper for Flight Search Automation
Endpoint: GET /flight-search?origin=Bangalore&destination=Delhi&journey_date=2025-10-18
Returns scraped flight details as JSON
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from flight_search_automation import FlightScraper
from typing import List, Dict

app = FastAPI(title="Flight Search API", description="Scrape flight details using Playwright")


@app.get("/flight-search")
async def flight_search(
    origin: str,
    destination: str,
    journey_date: str
) -> List[Dict]:
    """
    Search for flights and return scraped details

    - **origin**: Departure city (e.g., Bangalore)
    - **destination**: Arrival city (e.g., Delhi)
    - **journey_date**: Date in YYYY-MM-DD format (future date)
    """
    try:
        # Initialize scraper
        scraper = FlightScraper(use_mock=False)  # Attempt real scraping

        # Perform search
        flights = await scraper.search_flights(origin, destination, journey_date)

        if not flights:
            raise HTTPException(status_code=404, detail="No flights found")

        # Return as JSON response
        return JSONResponse(content=flights)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during flight search: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

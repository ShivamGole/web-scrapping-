"""
FastAPI wrapper for Flight Search Automation
Provides REST API endpoint for flight scraping
"""

import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging

# Import the FlightScraper class
from flight_search_automation import FlightScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Flight Search API",
    description="Playwright-based flight search automation API",
    version="1.0.0"
)


class FlightResponse(BaseModel):
    """Flight response model"""
    airline: str
    flight_number: str
    departure: str
    arrival: str
    price: str
    origin: str
    destination: str
    searchdatetime: str


class SearchRequest(BaseModel):
    """Flight search request model"""
    origin: str
    destination: str
    journey_date: str


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "running",
        "message": "Flight Search API is operational",
        "version": "1.0.0"
    }


@app.get("/flight-search", response_model=List[FlightResponse], tags=["Flight Search"])
async def flight_search(
    origin: str = Query(..., description="Origin city (e.g., Bangalore)"),
    destination: str = Query(..., description="Destination city (e.g., Delhi)"),
    journey_date: str = Query(..., description="Journey date (YYYY-MM-DD format)")
):
    """
    Search for flights between origin and destination
    
    Query Parameters:
    - origin: Source city name
    - destination: Destination city name
    - journey_date: Travel date in YYYY-MM-DD format
    
    Returns:
    - List of flight objects with airline, flight number, times, price, and search metadata
    
    Example:
    GET /flight-search?origin=Bangalore&destination=Delhi&journey_date=2025-10-25
    """
    
    try:
        # Validate inputs
        if not origin or not destination or not journey_date:
            raise HTTPException(
                status_code=400,
                detail="Missing required parameters: origin, destination, journey_date"
            )
        
        # Validate date format
        try:
            datetime.strptime(journey_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD format (e.g., 2025-10-25)"
            )
        
        logger.info(f"Processing flight search: {origin} → {destination} on {journey_date}")
        
        # Initialize scraper
        scraper = FlightScraper()
        
        # Run scraping
        flights = await scraper.search_flights(origin, destination, journey_date)
        
        logger.info(f"Successfully scraped {len(flights)} flights")
        
        # Return results
        return flights
    
    except HTTPException as e:
        logger.error(f"Validation error: {e.detail}")
        raise
    
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Flight search failed: {str(e)}"
        )


@app.post("/flight-search", response_model=List[FlightResponse], tags=["Flight Search"])
async def flight_search_post(request: SearchRequest):
    """
    Search for flights using POST request
    
    Request Body:
    {
        "origin": "Bangalore",
        "destination": "Delhi",
        "journey_date": "2025-10-25"
    }
    
    Returns:
    - List of flight objects
    """
    return await flight_search(
        origin=request.origin,
        destination=request.destination,
        journey_date=request.journey_date
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/test-flight-search", tags=["Testing"])
async def test_flight_search():
    """
    Test endpoint with hardcoded parameters
    Use this to verify the API is working correctly
    """
    return await flight_search(
        origin="Bangalore",
        destination="Delhi",
        journey_date="2025-10-25"
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("FLIGHT SEARCH API - Starting Server")
    print("=" * 60)
    print("API Documentation: http://localhost:8000/docs")
    print("Alternative Docs: http://localhost:8000/redoc")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
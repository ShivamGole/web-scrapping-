"""
Flight Search Automation with Playwright
Scrapes flight details from https://www.budgetticket.in
Saves results to flight_results.json
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MOCK_FLIGHTS = {
    ("Bangalore", "Delhi"): [
        {
            "airline": "IndiGo",
            "flight_number": "6E-123",
            "departure": "06:30",
            "arrival": "09:10",
            "price": "₹5,450",
        },
        {
            "airline": "Air India",
            "flight_number": "AI-504",
            "departure": "07:15",
            "arrival": "09:55",
            "price": "₹6,120",
        },
        {
            "airline": "SpiceJet",
            "flight_number": "SG-8256",
            "departure": "08:45",
            "arrival": "11:25",
            "price": "₹4,890",
        },
        {
            "airline": "GoAir",
            "flight_number": "G8-456",
            "departure": "09:20",
            "arrival": "12:00",
            "price": "₹5,100",
        },
        {
            "airline": "Vistara",
            "flight_number": "UK-834",
            "departure": "10:00",
            "arrival": "12:40",
            "price": "₹7,200",
        },
        {
            "airline": "AirAsia",
            "flight_number": "I5-234",
            "departure": "12:15",
            "arrival": "14:55",
            "price": "₹3,450",
        },
        {
            "airline": "IndiGo",
            "flight_number": "6E-567",
            "departure": "14:30",
            "arrival": "17:10",
            "price": "₹5,890",
        },
        {
            "airline": "Air India",
            "flight_number": "AI-608",
            "departure": "16:00",
            "arrival": "18:40",
            "price": "₹6,450",
        },
        {
            "airline": "SpiceJet",
            "flight_number": "SG-8890",
            "departure": "17:45",
            "arrival": "20:25",
            "price": "₹5,200",
        },
        {
            "airline": "IndiGo",
            "flight_number": "6E-901",
            "departure": "19:15",
            "arrival": "21:55",
            "price": "₹6,100",
        },
    ]
}


class FlightScraper:
    def __init__(self, use_mock=False):
        self.flights: List[Dict] = []
        self.browser = None
        self.page = None
        self.use_mock = use_mock
        self.scrape_success = False

    async def initialize(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.page = await self.browser.new_page()

    async def close(self):
        """Close browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def search_flights(self, origin: str, destination: str, journey_date: str) -> List[Dict]:
        """Search for flights with fallback to mock data"""

        try:
            # Try real scraping
            if not self.use_mock:
                flights = await self._scrape_real_flights(origin, destination, journey_date)
                if flights:
                    return flights

            # Fallback to mock data
            logger.warning("[FALLBACK] Using mock data")
            return self._get_mock_flights(origin, destination)

        except Exception as e:
            logger.error(f"[ERROR] {str(e)}")
            logger.warning("[FALLBACK] Using mock data")
            return self._get_mock_flights(origin, destination)

    async def _scrape_real_flights(self, origin: str, destination: str, journey_date: str) -> List[Dict]:
        """Attempt real scraping from website"""
        try:
            await self.initialize()

            logger.info("Opening website...")
            await self.page.goto(
                "https://www.budgetticket.in",
                wait_until="load",
                timeout=60000
            )

            await asyncio.sleep(2)

            logger.info("Filling search form...")

            # Fill form
            inputs = await self.page.locator('input[type="text"]').all()
            if len(inputs) >= 1:
                await inputs[0].fill(origin)
                await asyncio.sleep(0.5)

            if len(inputs) >= 2:
                await inputs[1].fill(destination)
                await asyncio.sleep(0.5)

            dates = await self.page.locator('input[type="date"]').all()
            if dates:
                await dates[0].fill(journey_date)

            # Click search
            buttons = await self.page.locator("button").all()
            for btn in buttons:
                text = await btn.inner_text()
                if "search" in text.lower():
                    await btn.click()
                    break

            logger.info("Waiting for results...")
            await asyncio.sleep(5)

            # Try to extract
            flights = await self._extract_flights_from_dom(origin, destination)

            if flights and len(flights) > 0:
                logger.info(f"Successfully scraped {len(flights)} flights")
                self.scrape_success = True
                return flights
            else:
                logger.warning("No flights extracted from DOM")
                return []

        finally:
            await self.close()

    async def _extract_flights_from_dom(self, origin: str, destination: str) -> List[Dict]:
        """Extract flights from page DOM"""
        flights = []
        search_datetime = datetime.utcnow().isoformat() + "Z"

        # Try multiple selectors
        selectors = [
            "div[class*='flight']",
            "div[class*='result']",
            ".flight-card",
            ".result-item",
            "[data-testid*='flight']",
        ]

        for selector in selectors:
            try:
                elements = await self.page.locator(selector).all()
                if elements and len(elements) > 0:
                    logger.info(f"Found {len(elements)} elements with: {selector}")

                    for elem in elements[:15]:
                        text = await elem.inner_text()

                        flight = {
                            "airline": self._extract_airline(text),
                            "flight_number": self._extract_flight_number(text),
                            "departure": self._extract_departure(text),
                            "arrival": self._extract_arrival(text),
                            "price": self._extract_price(text),
                            "origin": origin,
                            "destination": destination,
                            "searchdatetime": search_datetime
                        }

                        # Only add if we got some real data
                        if flight["departure"] != "N/A" or flight["price"] != "N/A":
                            flights.append(flight)

                    if flights:
                        return flights
            except:
                continue

        return []

    def _get_mock_flights(self, origin: str, destination: str) -> List[Dict]:
        """Get mock flight data"""
        search_datetime = datetime.utcnow().isoformat() + "Z"

        key = (origin, destination)
        mock_data = MOCK_FLIGHTS.get(key, [])

        # Add metadata to mock flights
        flights = []
        for flight in mock_data:
            flights.append({
                **flight,
                "origin": origin,
                "destination": destination,
                "searchdatetime": search_datetime
            })

        return flights

    def _extract_airline(self, text: str) -> str:
        """Extract airline name from text"""
        airlines = ["IndiGo", "Air India", "SpiceJet", "GoAir", "Vistara", "AirAsia"]
        for airline in airlines:
            if airline.lower() in text.lower():
                return airline
        return "N/A"

    def _extract_flight_number(self, text: str) -> str:
        """Extract flight number"""
        import re
        match = re.search(r'([A-Z]{2})\s*[-]?\s*(\d{3,4})', text)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return "N/A"

    def _extract_price(self, text: str) -> str:
        """Extract price"""
        import re
        match = re.search(r'₹\s*([\d,]+)', text)
        if match:
            return f"₹{match.group(1)}"
        return "N/A"

    def _extract_departure(self, text: str) -> str:
        """Extract departure time"""
        import re
        # Look for first time occurrence
        match = re.search(r'(\d{1,2}):(\d{2})', text)
        if match:
            return f"{match.group(1)}:{match.group(2)}"
        return "N/A"

    def _extract_arrival(self, text: str) -> str:
        """Extract arrival time"""
        import re
        matches = re.findall(r'(\d{1,2}):(\d{2})', text)
        if len(matches) >= 2:
            return f"{matches[1][0]}:{matches[1][1]}"
        return "N/A"


async def main():
    """Main execution"""

    scraper = FlightScraper(use_mock=False)  # Set to True to use mock data

    origin = "Bangalore"
    destination = "Delhi"
    journey_date = "2025-10-25"

    print("=" * 60)
    print("FLIGHT SEARCH AUTOMATION")
    print("=" * 60)
    print(f"Origin: {origin}")
    print(f"Destination: {destination}")
    print(f"Journey Date: {journey_date}")
    print("=" * 60)

    try:
        flights = await scraper.search_flights(origin, destination, journey_date)

        # Save results
        output_file = "flight_results.json"
        with open(output_file, "w") as f:
            json.dump(flights, f, indent=2)

        print("\n" + "=" * 60)
        print(f"RESULTS SAVED: {output_file}")
        print(f"Total Flights Extracted: {len(flights)}")

        if scraper.scrape_success:
            print("Status: ✓ Real data from website")
        else:
            print("Status: ⚠ Using mock/fallback data")

        print("=" * 60)

        # Print sample
        if flights:
            print("\nSample Flight Data:")
            print(json.dumps(flights[0], indent=2))

        return flights

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

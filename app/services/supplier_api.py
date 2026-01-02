"""Supplier price checking service for Gate Quote Pro."""
import re
import requests
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import threading


@dataclass
class PriceResult:
    """Result from a price lookup."""
    supplier: str
    product_name: str
    price: float
    url: str
    in_stock: bool = True
    last_checked: datetime = None

    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.now()


class SupplierAPI:
    """Service to check prices from various suppliers."""

    # Supported suppliers with their search URL patterns
    SUPPLIERS = {
        'homedepot': {
            'name': 'Home Depot',
            'search_url': 'https://www.homedepot.com/s/{query}',
            'base_url': 'https://www.homedepot.com'
        },
        'lowes': {
            'name': "Lowe's",
            'search_url': 'https://www.lowes.com/search?searchTerm={query}',
            'base_url': 'https://www.lowes.com'
        },
        'tractorsupply': {
            'name': 'Tractor Supply',
            'search_url': 'https://www.tractorsupply.com/tsc/search/{query}',
            'base_url': 'https://www.tractorsupply.com'
        },
        'walmart': {
            'name': 'Walmart',
            'search_url': 'https://www.walmart.com/search?q={query}',
            'base_url': 'https://www.walmart.com'
        }
    }

    # Price cache (url -> PriceResult)
    _cache: Dict[str, PriceResult] = {}
    _cache_duration = timedelta(hours=1)

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def get_price_from_url(self, url: str) -> Optional[PriceResult]:
        """Fetch price from a specific product URL."""
        # Check cache first
        if url in self._cache:
            cached = self._cache[url]
            if datetime.now() - cached.last_checked < self._cache_duration:
                return cached

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Determine supplier and extract price
            result = None

            if 'homedepot.com' in url:
                result = self._parse_homedepot(soup, url)
            elif 'lowes.com' in url:
                result = self._parse_lowes(soup, url)
            elif 'tractorsupply.com' in url:
                result = self._parse_tractorsupply(soup, url)
            elif 'walmart.com' in url:
                result = self._parse_walmart(soup, url)
            else:
                result = self._parse_generic(soup, url)

            if result:
                self._cache[url] = result

            return result

        except Exception as e:
            print(f"Error fetching price from {url}: {e}")
            return None

    def _parse_homedepot(self, soup: BeautifulSoup, url: str) -> Optional[PriceResult]:
        """Parse Home Depot product page."""
        try:
            # Try to find price
            price_elem = soup.find('span', {'class': re.compile(r'price', re.I)})
            if not price_elem:
                price_elem = soup.find('div', {'data-price': True})

            price = self._extract_price(price_elem.get_text() if price_elem else '')

            # Try to find product name
            title_elem = soup.find('h1', {'class': re.compile(r'product', re.I)})
            if not title_elem:
                title_elem = soup.find('h1')

            title = title_elem.get_text().strip() if title_elem else 'Home Depot Product'

            if price:
                return PriceResult(
                    supplier='Home Depot',
                    product_name=title[:100],
                    price=price,
                    url=url
                )
        except Exception:
            pass
        return None

    def _parse_lowes(self, soup: BeautifulSoup, url: str) -> Optional[PriceResult]:
        """Parse Lowe's product page."""
        try:
            price_elem = soup.find('span', {'class': re.compile(r'price', re.I)})
            price = self._extract_price(price_elem.get_text() if price_elem else '')

            title_elem = soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else "Lowe's Product"

            if price:
                return PriceResult(
                    supplier="Lowe's",
                    product_name=title[:100],
                    price=price,
                    url=url
                )
        except Exception:
            pass
        return None

    def _parse_tractorsupply(self, soup: BeautifulSoup, url: str) -> Optional[PriceResult]:
        """Parse Tractor Supply product page."""
        try:
            price_elem = soup.find('span', {'class': re.compile(r'price', re.I)})
            price = self._extract_price(price_elem.get_text() if price_elem else '')

            title_elem = soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else 'Tractor Supply Product'

            if price:
                return PriceResult(
                    supplier='Tractor Supply',
                    product_name=title[:100],
                    price=price,
                    url=url
                )
        except Exception:
            pass
        return None

    def _parse_walmart(self, soup: BeautifulSoup, url: str) -> Optional[PriceResult]:
        """Parse Walmart product page."""
        try:
            price_elem = soup.find('span', {'itemprop': 'price'})
            if not price_elem:
                price_elem = soup.find('span', {'class': re.compile(r'price', re.I)})

            price = self._extract_price(price_elem.get_text() if price_elem else '')

            title_elem = soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else 'Walmart Product'

            if price:
                return PriceResult(
                    supplier='Walmart',
                    product_name=title[:100],
                    price=price,
                    url=url
                )
        except Exception:
            pass
        return None

    def _parse_generic(self, soup: BeautifulSoup, url: str) -> Optional[PriceResult]:
        """Generic price parser for unknown sites."""
        try:
            # Look for common price patterns
            price_patterns = [
                soup.find('span', {'class': re.compile(r'price', re.I)}),
                soup.find('div', {'class': re.compile(r'price', re.I)}),
                soup.find('span', {'itemprop': 'price'}),
                soup.find('meta', {'property': 'product:price:amount'}),
            ]

            price = None
            for elem in price_patterns:
                if elem:
                    text = elem.get('content') or elem.get_text()
                    price = self._extract_price(text)
                    if price:
                        break

            title_elem = soup.find('h1')
            title = title_elem.get_text().strip()[:100] if title_elem else 'Product'

            # Extract domain for supplier name
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace('www.', '')

            if price:
                return PriceResult(
                    supplier=domain,
                    product_name=title,
                    price=price,
                    url=url
                )
        except Exception:
            pass
        return None

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract numeric price from text."""
        if not text:
            return None

        # Remove common non-price text
        text = text.replace(',', '')

        # Find price pattern (e.g., $123.45, 123.45, $123)
        patterns = [
            r'\$\s*(\d+\.?\d*)',
            r'(\d+\.\d{2})',
            r'USD\s*(\d+\.?\d*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def search_product(self, query: str, supplier: str = None) -> List[PriceResult]:
        """Search for a product across suppliers."""
        results = []

        suppliers_to_check = [supplier] if supplier else list(self.SUPPLIERS.keys())

        for sup in suppliers_to_check:
            if sup not in self.SUPPLIERS:
                continue

            info = self.SUPPLIERS[sup]
            search_url = info['search_url'].format(query=query.replace(' ', '+'))

            # Note: Full search would require JavaScript rendering
            # For now, return the search URL for manual lookup
            results.append(PriceResult(
                supplier=info['name'],
                product_name=f"Search: {query}",
                price=0.0,
                url=search_url
            ))

        return results

    def get_search_urls(self, product_name: str) -> Dict[str, str]:
        """Get search URLs for a product across all suppliers."""
        query = product_name.replace(' ', '+')
        return {
            info['name']: info['search_url'].format(query=query)
            for info in self.SUPPLIERS.values()
        }

    def compare_prices(self, urls: List[str], callback=None) -> List[PriceResult]:
        """Compare prices from multiple URLs.

        Args:
            urls: List of product URLs to check
            callback: Optional callback function(result) called as each price is fetched
        """
        results = []

        def fetch_price(url):
            result = self.get_price_from_url(url)
            if result:
                results.append(result)
                if callback:
                    callback(result)

        # Fetch prices in parallel
        threads = []
        for url in urls:
            thread = threading.Thread(target=fetch_price, args=(url,))
            thread.start()
            threads.append(thread)

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=15)

        # Sort by price
        results.sort(key=lambda x: x.price)

        return results

    def clear_cache(self):
        """Clear the price cache."""
        self._cache.clear()


# Global instance
_supplier_api = None


def get_supplier_api() -> SupplierAPI:
    """Get the global supplier API instance."""
    global _supplier_api
    if _supplier_api is None:
        _supplier_api = SupplierAPI()
    return _supplier_api

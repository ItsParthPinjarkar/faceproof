import os
import logging
import requests
from typing import List, Optional, Dict, Any
from serpapi import Client
from PIL import Image
import io

logger = logging.getLogger(__name__)


class SearchProvider:
    """
    Abstract base class for reverse image search providers.
    All providers implement search() which returns a list of matches.
    """

    def search(self, image_path: str, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError


class SerpApiGoogleLensProvider(SearchProvider):
    """
    SerpApi Google Lens reverse image search.
    Uses the proper Image API upload → image_id → Google Lens flow.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, image_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search using SerpApi's Image API + Google Lens.
        1. Upload the image to SerpApi's image API to get an image_id
        2. Query Google Lens with that image_id
        3. Return normalized results
        """
        image_id = self._upload_image(image_path)
        if not image_id:
            logger.error("Failed to upload image to SerpApi")
            return []

        results = self._query_lens(image_id)
        return self._normalize_results(results)

    def _upload_image(self, image_path: str) -> Optional[str]:
        """Upload image to SerpApi and return the temporary image_id."""
        try:
            with open(image_path, 'rb') as f:
                img_data = f.read()

            client = Client(api_key=self.api_key)
            response = client.upload_image(image=img_data, url=None, filename='face.jpg')

            if response and 'image_id' in response:
                return response['image_id']
        except Exception as e:
            logger.error(f"SerpApi upload failed: {e}")
        return None

    def _query_lens(self, image_id: str) -> Dict[str, Any]:
        """Query Google Lens with the image_id using serpapi Client."""
        client = Client(api_key=self.api_key)
        params = {
            'engine': 'google_lens',
            'google_lens_image_id': image_id,
            'hl': 'en',
            'gl': 'us',
        }
        try:
            results = client.search(**params)
            return results.get_dict() if hasattr(results, 'get_dict') else dict(results)
        except Exception as e:
            logger.error(f"Google Lens query failed: {e}")
            return {}

    def _normalize_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize search results into a consistent format."""
        matches = []

        # Try different result keys
        organic = results.get('results', results.get('organic_results', []))
        images = results.get('images_results', [])
        shopping = results.get('shopping_results', [])

        for item in organic + images + shopping:
            normalized = {
                'url': item.get('link', item.get('url', item.get('redirect', ''))),
                'title': item.get('title', item.get('name', 'N/A')),
                'domain': item.get('domain', item.get('source', '')),
                'snippet': item.get('snippet', item.get('description', '')),
                'image_url': item.get('image', item.get('thumbnail', '')),
                'match_type': item.get('type', 'visual_match'),
                'source': 'serpapi_google_lens',
            }
            matches.append(normalized)

        return matches


class DemoSearchProvider(SearchProvider):
    """
    Demo/mock search provider for testing without API keys.
    Returns clearly-labeled demo results from public data.
    """

    def __init__(self, demo_data_dir: str = 'demo'):
        self.demo_data_dir = demo_data_dir
        self._demo_results = self._load_demo_data()

    def _load_demo_data(self) -> List[Dict[str, Any]]:
        """Load demo search results from the demo directory."""
        # Default demo result pointing to a well-known public source
        return [
            {
                'url': 'https://example.com/demo-post',
                'title': 'Demo Post - Public Figure',
                'domain': 'example.com',
                'snippet': 'This is a demo search result for testing purposes.',
                'image_url': '',
                'match_type': 'visual_match',
                'source': 'demo_provider',
                'platform': 'Demo',
                '_is_demo': True
            }
        ]

    def search(self, image_path: str, **kwargs) -> List[Dict[str, Any]]:
        logger.info(f"Demo provider: returning labeled demo results for {image_path}")
        return self._demo_results


def create_provider(provider_name: str = 'serpapi', **kwargs) -> SearchProvider:
    """Factory function to create the appropriate search provider."""
    if provider_name == 'serpapi':
        return SerpApiGoogleLensProvider(kwargs.get('api_key', ''))
    elif provider_name == 'demo':
        return DemoSearchProvider(kwargs.get('demo_data_dir', 'demo'))
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 2:
        provider = create_provider(os.environ.get('SEARCH_PROVIDER', 'serpapi'), api_key=os.environ.get('SERPAPI_KEY', ''))
        results = provider.search(sys.argv[1])
        for r in results:
            print(f"URL: {r['url']}, Title: {r['title']}, Platform: {r.get('platform', 'N/A')}")

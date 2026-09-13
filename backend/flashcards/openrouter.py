"""
Thin OpenRouter client for image generation.

Transport only: no database access and no business rules, so it can be swapped
or faked wholesale in tests.
"""
import base64
import binascii
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Any failure talking to OpenRouter, including an unusable response."""


class GeneratedImage:
    """A decoded image plus whatever accounting the provider returned."""

    def __init__(self, content, content_type, cost_usd=None, response_id=''):
        self.content = content
        self.content_type = content_type
        self.cost_usd = cost_usd
        self.response_id = response_id

    @property
    def extension(self):
        return {
            'image/png': 'png',
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/webp': 'webp',
        }.get((self.content_type or '').lower(), 'png')


class OpenRouterClient:
    """Calls OpenRouter's image endpoint and hands back decoded bytes."""

    def __init__(self, api_key=None, base_url=None, timeout=None):
        self.api_key = api_key if api_key is not None else settings.OPENROUTER_API_KEY
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip('/')
        self.timeout = timeout or settings.OPENROUTER_TIMEOUT

    @property
    def is_configured(self):
        return bool(self.api_key)

    def generate_image(self, prompt, model):
        if not self.is_configured:
            raise OpenRouterError('OPENROUTER_API_KEY is not set.')

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        # Optional attribution headers; OpenRouter uses them for dashboard stats.
        if settings.OPENROUTER_SITE_URL:
            headers['HTTP-Referer'] = settings.OPENROUTER_SITE_URL
        if settings.OPENROUTER_SITE_NAME:
            headers['X-Title'] = settings.OPENROUTER_SITE_NAME

        try:
            response = requests.post(
                f'{self.base_url}/images',
                headers=headers,
                json={'model': model, 'prompt': prompt},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise OpenRouterError(f'Request to OpenRouter failed: {exc}') from exc

        if response.status_code >= 400:
            raise OpenRouterError(
                f'OpenRouter returned HTTP {response.status_code}: {response.text[:500]}'
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise OpenRouterError('OpenRouter returned a non-JSON response.') from exc

        return self._parse(payload)

    @staticmethod
    def _parse(payload):
        """
        Pull image bytes out of the response.

        Two shapes are accepted on purpose. OpenRouter documents the dedicated
        images endpoint (`data[].b64_json`), but several of its image models are
        also reachable through chat completions, which return the image as a
        data URL under `choices[].message.images[]`. Handling both means a model
        that only speaks one of them still works.
        """
        cost = None
        usage = payload.get('usage') or {}
        if isinstance(usage, dict) and usage.get('cost') is not None:
            try:
                cost = float(usage['cost'])
            except (TypeError, ValueError):
                cost = None
        response_id = str(payload.get('id') or '')[:200]

        # Shape 1: images endpoint
        for item in payload.get('data') or []:
            if not isinstance(item, dict):
                continue
            b64 = item.get('b64_json')
            if b64:
                return GeneratedImage(
                    OpenRouterClient._decode(b64),
                    item.get('media_type') or 'image/png',
                    cost,
                    response_id,
                )

        # Shape 2: chat completions with image modality
        for choice in payload.get('choices') or []:
            message = (choice or {}).get('message') or {}
            for image in message.get('images') or []:
                url = image.get('image_url')
                if isinstance(url, dict):
                    url = url.get('url')
                if isinstance(url, str) and url.startswith('data:'):
                    header, _, encoded = url.partition(',')
                    content_type = header[5:].split(';')[0] or 'image/png'
                    return GeneratedImage(
                        OpenRouterClient._decode(encoded), content_type, cost, response_id
                    )

        raise OpenRouterError(
            'OpenRouter response contained no image. Keys: '
            f'{sorted(payload.keys())[:10]}'
        )

    @staticmethod
    def _decode(b64):
        try:
            return base64.b64decode(b64, validate=False)
        except (binascii.Error, ValueError) as exc:
            raise OpenRouterError('Could not base64-decode the image payload.') from exc

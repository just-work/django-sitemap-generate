import os
from logging import getLogger
from urllib.parse import ParseResult, urlparse

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.servers import basehttp
from django.template.response import TemplateResponse
from django.urls import reverse

from sitemap_generate import defaults


class SitemapGenerator:
    def __init__(self, media_path='sitemaps', storage=default_storage,
                 index_url_name='sitemap-index', sitemaps=None):
        cls = self.__class__
        self.logger = getLogger(f'{cls.__module__}.{cls.__name__}')
        self.wsgi = basehttp.get_internal_wsgi_application()
        self.sitemap_root = os.path.join(settings.MEDIA_ROOT, media_path)
        self.storage = storage
        self.index_url_name = index_url_name
        self.sitemaps = sitemaps or {}

    def fetch_content(self, url: str) -> bytes:
        self.logger.debug(f"Fetching {url}...")

        # noinspection PyUnusedLocal
        def start_response(status, headers):
            if status != "200 OK":
                raise ValueError(status)

        url: ParseResult = urlparse(url)

        environ = {
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
            'SERVER_NAME': defaults.SITEMAP_HOST,
            'SERVER_PORT': defaults.SITEMAP_PORT,
            'PATH_INFO': url.path,
            'QUERY_STRING': url.query,
            'HTTP_X_FORWARDED_PROTO': defaults.SITEMAP_PROTO
        }

        response: TemplateResponse = self.wsgi(environ, start_response)
        return response.content

    def store_sitemap(self, filename: str, content: bytes):
        path = os.path.join(self.sitemap_root, filename)
        if self.storage.exists(path):
            self.storage.delete(path)
        self.storage.save(path, ContentFile(content))

    def generate(self, sitemap=None):
        self.logger.debug("Start sitemap generation.")
        url = reverse(self.index_url_name)

        index_content = self.fetch_content(url)
        self.store_sitemap('sitemap.xml', index_content)

        for name, sitemap_class in self.sitemaps.items():
            if sitemap and sitemap != name:
                continue
            self.logger.debug("Generating sitemap for %s", name)
            self.generate_pages(name, sitemap_class())

        self.logger.debug("Finish sitemap generation.")

    def generate_pages(self, section: str, sitemap: Sitemap):
        url = reverse('django.contrib.sitemaps.views.sitemap',
                      kwargs={'section': section})
        for page in sitemap.paginator.page_range:
            if page > 1:
                page_url = f'{url}?p={page}'
                filename = f'sitemap-{section}-{page}.xml'
            else:
                page_url = url
                filename = f'sitemap-{section}.xml'

            page_content = self.fetch_content(page_url)
            self.store_sitemap(filename, page_content)

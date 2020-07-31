import os
from io import StringIO
from logging import getLogger
from typing import Dict, Optional, Callable, Type
from urllib.parse import ParseResult, urlparse

from django.contrib.sitemaps import Sitemap
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage, Storage
from django.core.servers import basehttp
from django.http import HttpResponse
from django.urls import reverse

from sitemap_generate import defaults


class SitemapError(Exception):
    """ Sitemap generation error."""

    def __init__(self, status_code, content):
        super().__init__(status_code, content)
        self.status_code = status_code
        self.content = content


StartResponseFunc = Callable[[str, dict], None]
WSGIFunc = Callable[[dict, StartResponseFunc], HttpResponse]


class ResponseRecorder:
    """ Helper for fetching sitemaps over WSGI request."""

    def __init__(self, wsgi: WSGIFunc):
        """

        :param wsgi: Django wsgi application
        """
        self.wsgi = wsgi
        self.status: Optional[str] = None

    def record(self, url: str) -> bytes:
        """
        Fetches an url over WSGI request and returns response content.

        :param url: request url
        :returns: response content
        :raises SitemapError: if response status code is not 200.
        """
        url: ParseResult = urlparse(url)

        environ = {
            'REQUEST_METHOD': 'GET',
            'wsgi.errors': StringIO(),
            'wsgi.input': StringIO(),
            'wsgi.version': (1, 0),
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'wsgi.url_scheme': defaults.SITEMAP_PROTO,
            'SCRIPT_NAME': '',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'SERVER_NAME': defaults.SITEMAP_HOST,
            'SERVER_PORT': defaults.SITEMAP_PORT,
            'PATH_INFO': url.path,
            'QUERY_STRING': url.query,
            'HTTP_X_FORWARDED_PROTO': defaults.SITEMAP_PROTO
        }
        content = b''.join(self.wsgi(environ, self._start_response))
        if self.status != "200 OK":
            raise SitemapError(self.status, content)
        return content

    def _start_response(self, status, _):
        """ WSGI headers callback func."""
        self.status = status


class SitemapGenerator:
    """ Sitemap XML files generator."""

    def __init__(self,
                 media_path: str = 'sitemaps',
                 storage: Storage = default_storage,
                 index_url_name: str = 'sitemap-index',
                 sitemaps: Optional[Dict[str, Type[Sitemap]]] = None):
        """

        :param media_path: relative path on file storage
        :param storage: file storage implementation used for sitemaps
        :param index_url_name: name of view serving sitemap index xml file
        :param sitemaps: mapping: sitemap name -> sitemap implementation
        """
        cls = self.__class__
        self.logger = getLogger(f'{cls.__module__}.{cls.__name__}')
        self.sitemap_root = media_path
        self.storage = storage
        self.index_url_name = index_url_name
        self.sitemaps = sitemaps or {}
        self.recorder = ResponseRecorder(
            basehttp.get_internal_wsgi_application())

    def fetch_content(self, url: str) -> bytes:
        """ Fetch sitemap xml content with wsgi request recorder."""
        self.logger.debug(f"Fetching {url}...")
        return self.recorder.record(url)

    def store_sitemap(self, filename: str, content: bytes):
        """ Save sitemap content to file storage."""
        path = os.path.join(self.sitemap_root, filename)
        if self.storage.exists(path):
            self.storage.delete(path)
        self.storage.save(path, ContentFile(content))

    def generate(self, sitemap=None):
        """ Generate all sitemap files."""
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
        """ Generate sitemap section pages."""
        url = reverse('django.contrib.sitemaps.views.sitemap',
                      kwargs={'section': section})
        for page in sitemap.paginator.page_range:
            if page > 1:
                page_url = f'{url}?p={page}'
                filename = f'sitemap-{section}{page}.xml'
            else:
                page_url = url
                filename = f'sitemap-{section}.xml'

            page_content = self.fetch_content(page_url)
            self.store_sitemap(filename, page_content)

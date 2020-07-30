import os
from typing import cast

from django.core.files.storage import default_storage, Storage
from django.core.management import call_command
from django.test import TestCase

from sitemap_generate import defaults
from testproject.testapp import models


class GenerateSitemapCommandTestCase(TestCase):
    header = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    footer = ['</urlset>']

    empty = header + [''] + footer

    @classmethod
    def setUpTestData(cls):
        cls.videos = [models.Video.objects.create() for _ in range(2)]
        cls.storage = cast(Storage, default_storage)

    def tearDown(self) -> None:
        super().tearDown()
        _, files = self.storage.listdir('sitemaps')
        for path in files:
            self.storage.delete(os.path.join('sitemaps', path))

    def test_generate_sitemap(self):
        """ Checks sitemap xml files generation."""
        call_command('generate_sitemap')
        self.assertTrue(self.storage.exists('sitemaps/sitemap.xml'))
        self.assertTrue(self.storage.exists('sitemaps/sitemap-video.xml'))
        self.assertTrue(self.storage.exists('sitemaps/sitemap-video2.xml'))
        self.assertTrue(self.storage.exists('sitemaps/sitemap-articles.xml'))

        with self.storage.open('sitemaps/sitemap.xml') as f:
            content = f.read().decode('utf-8')
            links = [
                'sitemaps/sitemap-video.xml',
                'sitemaps/sitemap-video.xml?p=2',
                'sitemaps/sitemap-articles.xml',
            ]
            for link in links:
                self.assertIn(link, content)

        with self.storage.open('sitemaps/sitemap-articles.xml') as f:
            content = f.read().decode('utf-8').splitlines()
            self.assertListEqual(content, self.empty)

        with self.storage.open('sitemaps/sitemap-video.xml') as f:
            content = f.read().decode('utf-8').splitlines()
            scheme = defaults.SITEMAP_PROTO
            host = defaults.SITEMAP_HOST
            port = defaults.SITEMAP_PORT
            if (scheme, port) in [('https', '443'), ('http', '80')]:
                netloc = host
            else:
                netloc = f'{host}:{port}'
            url = f'{scheme}://{netloc}/videos/{self.videos[0].pk}/'
            url = f'<url><loc>{url}</loc><changefreq>daily</changefreq></url>'
            expected = self.header + [url] + self.footer
            self.assertListEqual(content, expected)

    def test_generate_single_sitemap(self):
        """ Management command allows to pass sitemap name."""
        call_command('generate_sitemap', sitemap='video')
        self.assertTrue(self.storage.exists('sitemaps/sitemap.xml'))
        self.assertTrue(self.storage.exists('sitemaps/sitemap-video.xml'))
        self.assertFalse(self.storage.exists('sitemaps/sitemap-articles.xml'))

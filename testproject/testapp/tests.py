import os
from typing import cast

import django
from django.core.files.storage import default_storage, Storage
from django.core.management import call_command
from django.test import TestCase, override_settings
from django_testing_utils.utils import override_defaults

from sitemap_generate import defaults
from sitemap_generate.generator import SitemapGenerator
from testproject.testapp import models, sitemaps


# noinspection PyAbstractClass
class TestStorage(Storage):
    pass


test_storage = TestStorage()


sitemap_mapping = {'videos': sitemaps.VideoSitemap}


class GenerateSitemapCommandTestCase(TestCase):
    if django.VERSION >= (3, 2):
        header = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    else:
        header = [
            '<?xml version="1.0" encoding="UTF-8"?>',
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


class SitemapGeneratorTestCase(TestCase):

    @override_defaults('sitemap_generate', SITEMAP_STORAGE='testproject.testapp.tests.test_storage')
    def test_init_storage_from_settings(self):
        sg = SitemapGenerator()
        self.assertIsInstance(sg.storage, TestStorage)

    def test_init_storage_from_args(self):
        sg = SitemapGenerator(storage=test_storage)
        self.assertIs(sg.storage, test_storage)

    @override_settings(SITEMAP_MAPPING='testproject.testapp.tests.sitemap_mapping')
    def test_init_sitemaps_from_settings(self):
        sg = SitemapGenerator()
        self.assertIs(sg.sitemaps['videos'], sitemaps.VideoSitemap)

    def test_init_sitemaps_from_args(self):
        sg = SitemapGenerator(sitemaps=sitemap_mapping)
        self.assertIs(sg.sitemaps['videos'], sitemaps.VideoSitemap)

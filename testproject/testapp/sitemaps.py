from django.contrib.sitemaps import Sitemap

from testproject.testapp import models


class VideoSitemap(Sitemap):
    name = 'video'
    changefreq = 'daily'
    limit = 1

    def items(self):
        return models.Video.objects.order_by('id')


class ArticleSitemap(Sitemap):
    name = 'articles'
    changefreq = 'daily'
    limit = 50000

    def items(self):
        return models.Article.objects.order_by('id')

from django.contrib.sitemaps import views
from django.urls import path

from testproject.testapp.sitemaps import VideoSitemap, ArticleSitemap

sitemaps = {
    VideoSitemap.name: VideoSitemap,
    ArticleSitemap.name: ArticleSitemap
}

urlpatterns = [
    path('sitemap.xml', views.index, {'sitemaps': sitemaps},
         name='sitemap-index'),
    path('sitemap-<section>.xml', views.sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]

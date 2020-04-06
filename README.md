Django Sitemap Generate
=======================

Background sitemap generation for Django.

[![Build Status](https://github.com/just-work/django-sitemap-generate/workflows/build/badge.svg?branch=master&event=push)](https://github.com/just-work/django-sitemap-generate/actions?query=event%3Apush+branch%3Amaster+workflow%3Abuild)
[![codecov](https://codecov.io/gh/just-work/django-sitemap-generate/branch/master/graph/badge.svg)](https://codecov.io/gh/just-work/django-sitemap-generate)
[![PyPI version](https://badge.fury.io/py/django-sitemap-generate.svg)](https://badge.fury.io/py/django-sitemap-generate)

Use case
--------

Almost every content site has a sitemap. Django provides an application serving
sitemap views, and it's OK if your website is small. If you have complicate 
logic in sitemap generation or if you have millions of items in sitemap - you'll
have a massive load spikes when Google and another search engines come with 
thousands of there indexer bots. These bots will request same sitemap pages in
parallel and those requests couldn't be cached because of large index interval 
and small hit rate. 

The solution is to re-generate sitemap files periodically, once per day and not
once per search engine indexer. These files could be served as static files 
which will not affect backend performance at all.

Prerequisites
-------------

These project uses index sitemap view and per-model sitemap views to generate
sitemap xml files. To provide it you will need following.

1. Add `django.contrib.sitemaps` to installed apps
    ```python
    INSTALLED_APPS.append('django.contrib.sitemaps')
    ```
2. Configure at least one sitemap
    ```python
    from django.contrib.sitemaps import Sitemap
    
    from testproject.testapp import models
    
    
    class VideoSitemap(Sitemap):
        name = 'video'
        changefreq = 'daily'
        limit = 50000
    
        def items(self):
            return models.Video.objects.order_by('id')
    ```
   
    Note that `changefreq` parameter is a hint for search engine indexer, it 
    does not affect sitemap files generation period.
   
3. Configure sitemap serving
    ```python
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
    ```

Now your website supports sitemap views.

Installation
------------

```shell script
pip install django-sitemap generate
```   

Working example is in `testproject.testapp`.

1. Add `sitemap_generate` application to installed apps in django settings:
    ```python
    INSTALLED_APPS.append('sitemap_generate')
    ```
2. Add a reference to sitemap mapping to django settings:
    ```python
    SITEMAP_MAPPING = 'testproject.testapp.urls.sitemaps'
    ```
3. You may need to override default sitemap index url name
    ```python
    SITEMAP_INDEX_URL = 'sitemap-index'
    ```
4. Also you may need to setup forwarded protocol handling in django settings:
    ```python
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    ```
5. Note that django paginates sitemap with `p` query parameter, but 
    corresponding sitemap files are named `sitemap-video.xml`, 
    `sitemap-video-2.xml` and so on. You'll need to configure some "rewrites".
    
Usage
-----

When you request sitemap over http, django substitutes website domain name from
request to links in sitemap xml. In background, you'll need some environment 
variables. By defaults link are generated for `localhost` over HTTPS.

```shell script
export \
  SITEMAP_PROTO=https \
  SITEMAP_HOST=github.com \
  SITEMAP_PORT=443

# generate all sitemaps
python manage.py generate_sitemap

# generate sitemap for single model
python manage.py generate_sitemap video
```

You may run sitemap generation from crontab:

```
0 0 * * * python manage.py generate_sitemap
```

You may run sitemap generation from celery:

```python 
@celery.task
def generate_sitemap():
    generator = SitemapGenerator(sitemaps={'video': VideoSitema[})
    generator.generate()
```

And you will need to configure xml files static responses, i.e. in nginx:

```
location ~* /sitemaps/(?<fn>sitemap(-(article|video)).xml {
    try_files /media/sitemaps/$fn$arg_p.xml @backend;
}

location /media/ {
    alias /app/media/;
}

location @backend {
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    set $app http://app:8000;
    proxy_pass $app;
}
``` 
from os import getenv

from django.conf import settings


def e(name, default):
    """
    Returns settings value from django settings or environment.

    :param name: setting name
    :param default: default value if setting is not specified in django
    settings module and environment.
    """
    try:
        return getattr(settings, name)
    except AttributeError:
        return getenv(name, default)


# Hostname used in sitemap links
SITEMAP_HOST = e('SITEMAP_HOST', 'localhost')
# Port used in sitemap links
SITEMAP_PORT = e('SITEMAP_PORT', '443')
# Protocol used in sitemap links
SITEMAP_PROTO = e('SITEMAP_PROTO', 'https')

# Default directory in media storage where sitemaps are stored
SITEMAP_MEDIA_PATH = e('SITEMAP_MEDIA_PATH', 'sitemaps')

# Default media storage for sitemaps
SITEMAP_STORAGE = e('SITEMAP_STORAGE',
                    'django.core.files.storage.default_storage')

# Default name of sitemap index view
SITEMAP_INDEX_NAME = e('SITEMAP_INDEX_NAME', 'sitemap-index')

# Default name of sitemaps view
SITEMAPS_VIEW_NAME = e('SITEMAPS_VIEW_NAME',
                       'django.contrib.sitemaps.views.sitemap')

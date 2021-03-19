from django.core.files.storage import default_storage


# Default directory in media storage where sitemaps are stored
SITEMAP_MEDIA_PATH = 'sitemaps'

# Default media storage for sitemaps
SITEMAP_STORAGE = default_storage

# Default name of sitemap index view
SITEMAP_INDEX_NAME = 'sitemap-index'

# Default name of sitemaps view
SITEMAPS_VIEW_NAME = 'django.contrib.sitemaps.views.sitemap'

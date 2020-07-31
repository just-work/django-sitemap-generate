from os import getenv as e

# Hostname used in sitemap links
SITEMAP_HOST = e('SITEMAP_HOST', 'localhost')
# Port used in sitemap links
SITEMAP_PORT = e('SITEMAP_PORT', '443')
# Protocol used in sitemap links
SITEMAP_PROTO = e('SITEMAP_PROTO', 'https')

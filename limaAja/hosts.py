# limaAja/hosts.py
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'shop', 'shop.urls', name='shop'),
    host(r'cooperative', 'cooperative.urls', name='cooperative'),
    host(r'api', 'authentication.urls', name='api'),
    host(r'admin', 'django.contrib.admin.urls', name='admin'),
    # Fallback to shop for any other subdomain or main domain
    host(r'.*', 'shop.urls', name='shop_fallback'),
)
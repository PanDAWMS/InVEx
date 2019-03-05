from django.core.cache import cache

def getCacheEntry(group_key):
    return cache.get(group_key)

def setCacheEntry(group_key, data, timeout):
    cache_key = '%s' % (group_key)
    cache.set(cache_key, data, timeout)
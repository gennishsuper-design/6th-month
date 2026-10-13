from django.core.cache import cache

CONFIRMATION_KEY_PREFIX = 'confirmation_code'
CONFIRMATION_TTL_SECONDS = 300
PRODUCT_CACHE_PREFIX = 'products'


def _confirmation_key(user_id):
    return f'{CONFIRMATION_KEY_PREFIX}:{user_id}'


def _product_cache_keys():
    backend = getattr(cache, '_cache', None)
    if backend is None:
        return []
    keys = []
    for key in list(backend.keys()):
        key_text = str(key)
        marker = f':{PRODUCT_CACHE_PREFIX}:'
        if marker in key_text:
            keys.append(f'{PRODUCT_CACHE_PREFIX}:{key_text.split(marker, 1)[1]}')
        elif key_text.startswith(f'{PRODUCT_CACHE_PREFIX}:'):
            keys.append(key_text)
    return list(dict.fromkeys(keys))


def save_confirmation_code(user_id, code):
    key = _confirmation_key(user_id)
    cache.set(key, code, timeout=CONFIRMATION_TTL_SECONDS)
    return key


def get_confirmation_code(user_id):
    return cache.get(_confirmation_key(user_id))


def confirm_confirmation_code(user_id, code):
    key = _confirmation_key(user_id)
    stored_code = cache.get(key)
    if stored_code == code:
        cache.delete(key)
        return True
    return False


def clear_product_cache():
    try:
        cache.delete_pattern(f'{PRODUCT_CACHE_PREFIX}:*')
    except AttributeError:
        keys = _product_cache_keys()
        if keys:
            cache.delete_many(keys)
            return
    for key in ('products:list', 'products:detail', 'products:detail:1'):
        cache.delete(key)

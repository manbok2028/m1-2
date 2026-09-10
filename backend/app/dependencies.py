from functools import lru_cache

from app.core.config import get_settings
from app.services.repository import get_repository


@lru_cache
def repository():
    return get_repository(get_settings())

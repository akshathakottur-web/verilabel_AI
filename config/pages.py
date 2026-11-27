from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404

PAGES_DIR = Path(settings.BASE_DIR) / 'frontend' / 'templates'


def page_view(request, page):
    path = PAGES_DIR / f'{page}.html'
    if not path.is_file():
        raise Http404('Page not found')
    return FileResponse(open(path, 'rb'), content_type='text/html; charset=utf-8')
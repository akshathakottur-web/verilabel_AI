from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from .pages import page_view

urlpatterns = [
    path('', RedirectView.as_view(url='/app/signin/')),
    path('app/<slug:page>/', page_view),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/scans/', include('scans.urls')),
    path('api/', include('reports.urls')),
    path('api/', include('dashboards.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
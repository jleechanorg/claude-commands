from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def api_health(request):
    return JsonResponse({'status': 'ok', 'tenant': getattr(request, 'tenant_slug', 'public')})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', api_health, name='api_health'),
    # GraphQL and other endpoints will be added later
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
import json
import os

def health_check(request):
    """Health check endpoint"""
    try:
        response_data = {
            "status": "healthy", 
            "service": "ryo-backend",
            "force_script_name": getattr(settings, 'FORCE_SCRIPT_NAME', ''),
            "static_url": getattr(settings, 'STATIC_URL', '/static/'),
            "static_root": getattr(settings, 'STATIC_ROOT', '/app/staticfiles'),
            "debug": getattr(settings, 'DEBUG', False),
            "timestamp": str(request.META.get('HTTP_DATE', 'N/A'))
        }
        return JsonResponse(response_data, safe=False)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e),
            "service": "ryo-backend"
        }, status=500)

def debug_static(request):
    """Debug static files"""
    try:
        static_root = settings.STATIC_ROOT
        static_url = settings.STATIC_URL
        test_file = os.path.join(static_root, 'admin', 'css', 'base.css')
        
        response_data = {
            "static_url": static_url,
            "static_root": static_root,
            "force_script_name": getattr(settings, 'FORCE_SCRIPT_NAME', ''),
            "test_file_path": test_file,
            "test_file_exists": os.path.exists(test_file),
            "static_patterns": str(static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)),
            "media_patterns": str(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
        }
        
        if os.path.exists(test_file):
            response_data["test_file_size"] = os.path.getsize(test_file)
            
        return JsonResponse(response_data, safe=False, indent=2)
    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)

main_urlpatterns = [
    path('4dm1nxXx/', admin.site.urls),
    path('health/', health_check),
    path('debug-static/', debug_static),
    path('office/', include('office.urls')),
    path('retailer/', include('retailer.urls')),
    path('wholesales/', include('wholesales.urls')),
    path('/', include('api.urls')),
]

# Check if we need to add subfolder support
if hasattr(settings, 'FORCE_SCRIPT_NAME') and settings.FORCE_SCRIPT_NAME:
    # Use the FORCE_SCRIPT_NAME from settings
    script_name = settings.FORCE_SCRIPT_NAME.strip('/')
    urlpatterns = [
        path(f'{script_name}/', include(main_urlpatterns)),
    ]
else:
    urlpatterns = main_urlpatterns

# Serve static and media files in development/WSGI mode
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

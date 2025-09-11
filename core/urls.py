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
from django.views.generic import RedirectView
import json
import os

# ✅ Get SUB_PATH
SUB_PATH = os.getenv('SUB_PATH', '').strip('/')
print(f"Core URLs - SUB_PATH: {SUB_PATH}")

def health_check(request):
    """ALB Health check endpoint"""
    return HttpResponse("healthy", content_type="text/plain", status=200)

def debug_static(request):
    """Debug static files"""
    try:
        static_root = settings.STATIC_ROOT
        static_url = settings.STATIC_URL
        test_file = os.path.join(static_root, 'admin', 'css', 'base.css')
        
        response_data = {
            "static_url": static_url,
            "static_root": static_root,
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

def metrics_view(request):
    """Prometheus metrics endpoint"""
    try:
        # Basic metrics in Prometheus format
        metrics = """# HELP django_up Application status
# TYPE django_up gauge
django_up 1

# HELP django_requests_total Total number of HTTP requests
# TYPE django_requests_total counter
django_requests_total 1

# HELP django_info Application information
# TYPE django_info gauge
django_info{{version="5.1",service="ryo-backend",environment="{environment}"}} 1
""".format(environment=getattr(settings, 'ENVIRONMENT', 'development'))
        
        return HttpResponse(metrics, content_type='text/plain; version=0.0.4; charset=utf-8')
    except Exception as e:
        error_metrics = """# HELP django_up Application status
# TYPE django_up gauge
django_up 0
"""
        return HttpResponse(error_metrics, content_type='text/plain; version=0.0.4; charset=utf-8', status=500)

urlpatterns = [
    path('4dm1nxXx/', admin.site.urls),
    path('health/', health_check),
    path('debug-static/', debug_static),
    path('metrics/', metrics_view),
    path('favicon.ico', RedirectView.as_view(url='/staticfiles/drf-yasg/swagger-ui-dist/favicon-32x32.png')),
    path('api/', include('api.urls')),
    path('office/', include('office.urls')),
    path('retailer/', include('retailer.urls')),
    path('wholesales/', include('wholesales.urls')),
    path('', include('api.urls')),
]

# ✅ Add API docs at root level for development
if hasattr(settings, 'DEBUG') and settings.DEBUG:
    try:
        from api.urls import schema_view
        if schema_view:
            urlpatterns += [
                path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
                path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
            ]
            print("Added docs URLs for development")
    except (ImportError, AttributeError):
        pass
    
# Serve static and media files in development/WSGI mode
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

print("URL patterns configured:")
for i, pattern in enumerate(urlpatterns):
    print(f"  {i+1}. {pattern}")
"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from .views import serve_react

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # Serve static files from the Vite build
    re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': settings.FRONTEND_BUILD_DIR / 'assets'}),
    re_path(r'^(?P<path>vite\.svg)$', serve, {'document_root': settings.FRONTEND_BUILD_DIR}),
    # Catch-all pattern for React frontend - must be last
    re_path(r'^.*$', serve_react, name='react-app'),
]

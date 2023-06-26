from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('home.urls')),
    path('', include('minhas_pastas.urls')),
    path('', include('usuario.urls')),
    path('', include('apresentacao.urls')),
    path('admin/', admin.site.urls)
] + static( settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
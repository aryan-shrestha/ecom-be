from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from backend.views import api_homepage, health_check

urlpatterns = [
    path('', api_homepage, name='api-homepage'),
    path('', include('cart.urls')),
    path('', include('product.urls')),
    path('', include('file_upload.urls')),
    path('admin/', admin.site.urls),
    path('health-check/', health_check, name='health-check'),
    path('orders/', include('orders.urls')),
    path('categories/', include('category.urls')),
    path('accounts/', include('account.urls')),
    # New API endpoints
    path('inventory/', include('inventory.urls')),
    path('discounts/', include('discount.urls')),
    # Djoser auth endpoints
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

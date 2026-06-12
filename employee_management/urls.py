from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Management App URLs
    path('', include('management_app.urls')),
]
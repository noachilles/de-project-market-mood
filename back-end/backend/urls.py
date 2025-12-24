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
from django.urls import path
from stocks.views import current_price, chart
from django.urls import path, include
from stocks.views import search_stocks


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/current-price/<str:code>", current_price, name="current_price"),
    path("api/current-price/<str:code>/", current_price, name="current_price_slash"),
    path("api/chart/<str:code>", chart, name="chart"),
    path("api/chart/<str:code>/", chart, name="chart_slash"), # 이 줄을 추가하세요!
    path("api/news/", include("news.urls")),
    path("api/stocks/search", search_stocks, name="search_stocks"),
    
]

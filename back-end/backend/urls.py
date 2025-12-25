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
from news.views import news_list, news_by_date, hot_keywords, chat


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/current-price/<str:code>", current_price, name="current_price"),
    path("api/chart/<str:code>", chart, name="chart"),
    path("api/news/", news_list, name="news_list"),
    path("api/news/by-date/", news_by_date, name="news_by_date"),
    path("api/news/hot-keywords/", hot_keywords, name="hot_keywords"),
    path("api/news/chat/", chat, name="chat"),
]

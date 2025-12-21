"""
URL configuration for marketmoodAPI project.

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
# back-end/config/urls.py

from django.contrib import admin
from django.urls import path
from stock import views  # 👈 stock 앱의 views를 가져옴

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. 아무것도 없는 주소('')로 들어오면 index 뷰를 보여줘라
    path('', views.index, name='index'), 
    
    # (혹은 path('stock/', views.index) 로 하면 localhost:8000/stock/ 으로 접속)
]
# back-end/stock/views.py

from django.shortcuts import render

def index(request):
    # templates 폴더 안의 index.html을 찾아서 보여줌
    return render(request, 'index.html')
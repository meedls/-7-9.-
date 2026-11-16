from django.shortcuts import render
from django.http import HttpResponse


def catalog(request):
    return render(request, 'rental/catalog.html')


def subscription(request):
    return HttpResponse('Страница подписки находится в разработке.', content_type='text/plain; charset=utf-8')


def login(request):
    return HttpResponse('Страница входа находится в разработке.', content_type='text/plain; charset=utf-8')

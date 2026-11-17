from django.shortcuts import render


def catalog(request):
    return render(request, 'rental/catalog.html')


def subscription(request):
    return render(request, 'rental/plans.html')


def login(request):
    return render(request, 'rental/login.html')


def item(request):
    return render(request, 'rental/item.html')


def loans(request):
    return render(request, 'rental/loans.html')


def search(request):
    return render(request, 'rental/search.html', {'query': request.GET.get('q', '').strip()})

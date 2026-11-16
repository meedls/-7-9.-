from django.shortcuts import render


def catalog(request):
    return render(request, 'rental/catalog.html')

# Create your views here.

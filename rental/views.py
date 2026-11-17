import re

from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from .models import Copy, Item, Loan, Plan


def available_copies():
    return Copy.objects.filter(is_serviceable=True).exclude(
        loans__status__in=[
            Loan.Status.RESERVED, Loan.Status.ACTIVE,
            Loan.Status.REQUESTED, Loan.Status.INSPECTION,
        ]
    ).distinct()


def catalog_items():
    return Item.objects.filter(is_published=True).select_related('category').prefetch_related(
        'platforms', Prefetch('copies', queryset=available_copies(), to_attr='free_copies')
    ).order_by('title', 'pk')


def paginate_items(request, items):
    page = Paginator(items, 20).get_page(request.GET.get('page'))
    for item in page:
        item.available_count = len(item.free_copies)
    return page


def catalog(request):
    return render(request, 'rental/catalog.html', {
        'page_obj': paginate_items(request, catalog_items()),
    })


def subscription(request):
    return render(request, 'rental/plans.html', {'plans': Plan.objects.filter(is_active=True)})


def login(request):
    return render(request, 'rental/login.html')


def item(request, pk):
    game = get_object_or_404(catalog_items(), pk=pk)
    game.available_count = len(game.free_copies)
    copies = game.copies.prefetch_related('composition__component')
    return render(request, 'rental/item.html', {'item': game, 'copies': copies})


def loans(request):
    user_loans = None
    if request.user.is_authenticated:
        user_loans = Loan.objects.filter(user=request.user).select_related('copy__item')
    return render(request, 'rental/loans.html', {'loans': user_loans})


def search(request):
    query = request.GET.get('q', '').strip()
    items = catalog_items().filter(title__iregex=re.escape(query)) if query else catalog_items().none()
    return render(request, 'rental/search.html', {
        'query': query,
        'page_obj': paginate_items(request, items),
    })

from django.urls import path

from . import views

app_name = 'rental'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('subscription/', views.subscription, name='subscription'),
    path('login/', views.login, name='login'),
]

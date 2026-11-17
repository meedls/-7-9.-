from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from rental.models import Category, Component, Copy, CopyComponent, Item, ItemPlatform, Plan, Platform


class Command(BaseCommand):
    help = 'Загрузить каталог занятия 5 в пустые таблицы без создания пользователей.'

    @transaction.atomic
    def handle(self, *args, **options):
        models = (Category, Platform, Item, ItemPlatform, Component, Copy, CopyComponent, Plan)
        if any(model.objects.exists() for model in models):
            raise CommandError('Каталог уже содержит данные. Загрузка отменена, чтобы не перезаписать записи.')
        call_command('loaddata', 'catalog25', verbosity=options['verbosity'])
        self.stdout.write(self.style.SUCCESS('Данные каталога занятия 5 загружены.'))

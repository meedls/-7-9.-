from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from PIL import Image


def validate_cover(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('Размер изображения не должен превышать 5 МиБ.')
    try:
        with Image.open(value) as img:
            if img.format not in ('JPEG', 'PNG'):
                raise ValidationError('Допустимы только JPEG и PNG.')
            img.verify()
    except (OSError, SyntaxError) as exc:
        raise ValidationError('Файл не является корректным изображением.') from exc
    finally:
        value.seek(0)


class Category(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    def __str__(self): return self.name


class Platform(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    class Meta:
        verbose_name = 'Платформа'
        verbose_name_plural = 'Платформы'
        ordering = ['name']
    def __str__(self): return self.name


class Item(models.Model):
    title = models.CharField('Название', max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items', verbose_name='Категория')
    platforms = models.ManyToManyField(Platform, through='ItemPlatform', related_name='items', verbose_name='Платформы', blank=True)
    description = models.TextField('Описание')
    daily_price = models.DecimalField('Цена за сутки', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    cover = models.ImageField('Фото', upload_to='covers/', blank=True, validators=[validate_cover])
    created_at = models.DateTimeField('Дата добавления', default=timezone.now)
    is_published = models.BooleanField('Опубликована', default=True)
    players_min = models.PositiveSmallIntegerField('Минимум игроков', null=True, blank=True)
    players_max = models.PositiveSmallIntegerField('Максимум игроков', null=True, blank=True)
    class Meta:
        verbose_name = 'Позиция каталога'
        verbose_name_plural = 'Позиции каталога'
        ordering = ['title', 'id']
        constraints = [
            models.CheckConstraint(condition=Q(daily_price__gte=0), name='item_price_nonnegative'),
            models.CheckConstraint(condition=(Q(players_min__isnull=True, players_max__isnull=True) |
                Q(players_min__isnull=False, players_max__isnull=False, players_min__gte=1, players_max__gte=F('players_min'))), name='item_players_range'),
        ]
    def __str__(self): return self.title


class ItemPlatform(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='platform_links', verbose_name='Позиция')
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, related_name='item_links', verbose_name='Платформа')
    class Meta:
        verbose_name = 'Платформа позиции'
        verbose_name_plural = 'Платформы позиций'
        ordering = ['item_id', 'platform_id']
        constraints = [models.UniqueConstraint(fields=['item', 'platform'], name='unique_item_platform')]
    def __str__(self): return f'{self.item} / {self.platform}'


class Component(models.Model):
    name = models.CharField('Название детали', max_length=100, unique=True)
    class Meta:
        verbose_name = 'Деталь'
        verbose_name_plural = 'Детали'
        ordering = ['name']
    def __str__(self): return self.name


class Copy(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='copies', verbose_name='Позиция')
    inventory_number = models.CharField('Инвентарный номер', max_length=30, unique=True)
    is_serviceable = models.BooleanField('Исправен', default=True)
    components = models.ManyToManyField(Component, through='CopyComponent', related_name='copies', verbose_name='Комплектация')
    class Meta:
        verbose_name = 'Экземпляр'
        verbose_name_plural = 'Экземпляры'
        ordering = ['inventory_number']
    def __str__(self): return self.inventory_number


class CopyComponent(models.Model):
    copy = models.ForeignKey(Copy, on_delete=models.PROTECT, related_name='composition', verbose_name='Экземпляр')
    component = models.ForeignKey(Component, on_delete=models.PROTECT, related_name='composition', verbose_name='Деталь')
    quantity = models.PositiveSmallIntegerField('Количество', validators=[MinValueValidator(1)])
    class Meta:
        verbose_name = 'Элемент комплектации'
        verbose_name_plural = 'Комплектация экземпляров'
        ordering = ['copy_id', 'component_id']
        constraints = [models.UniqueConstraint(fields=['copy', 'component'], name='unique_copy_component'),
                       models.CheckConstraint(condition=Q(quantity__gte=1), name='component_quantity_positive')]
    def __str__(self): return f'{self.copy}: {self.component} × {self.quantity}'


class Plan(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    limit = models.PositiveSmallIntegerField('Лимит', validators=[MinValueValidator(1)])
    price = models.DecimalField('Цена за месяц', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField('Доступен', default=True)
    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'
        ordering = ['price', 'id']
        constraints = [models.CheckConstraint(condition=Q(limit__gte=1), name='plan_limit_positive'),
                       models.CheckConstraint(condition=Q(price__gte=0), name='plan_price_nonnegative')]
    def __str__(self): return self.name


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='subscriptions', verbose_name='Игрок')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions', verbose_name='Тариф')
    starts_at = models.DateTimeField('Начало')
    ends_at = models.DateTimeField('Окончание')
    limit_snapshot = models.PositiveSmallIntegerField('Лимит при оформлении', validators=[MinValueValidator(1)])
    price_snapshot = models.DecimalField('Цена при оформлении', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-starts_at', '-id']
        constraints = [models.CheckConstraint(condition=Q(ends_at__gt=F('starts_at')), name='subscription_dates_order'),
                       models.CheckConstraint(condition=Q(limit_snapshot__gte=1), name='subscription_limit_positive'),
                       models.CheckConstraint(condition=Q(price_snapshot__gte=0), name='subscription_price_nonnegative')]
    def __str__(self): return f'Подписка {self.pk} — {self.user}'


class Loan(models.Model):
    class Status(models.TextChoices):
        RESERVED = 'reserved', 'К передаче'
        ACTIVE = 'active', 'На руках'
        REQUESTED = 'requested', 'Возврат запрошен'
        INSPECTION = 'inspection', 'Проверка'
        CLOSED = 'closed', 'Закрыта'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='loans', verbose_name='Игрок')
    copy = models.ForeignKey(Copy, on_delete=models.PROTECT, related_name='loans', verbose_name='Экземпляр')
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT, related_name='loans', verbose_name='Подписка', null=True, blank=True)
    daily_days = models.PositiveSmallIntegerField('Суток аренды', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(30)])
    daily_price_snapshot = models.DecimalField('Цена суток при выдаче', max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField('Статус', max_length=12, choices=Status.choices, default=Status.RESERVED)
    receipt_method = models.CharField('Способ получения', max_length=8, choices=[('pickup', 'Самовывоз'), ('delivery', 'Доставка')], default='pickup')
    created_at = models.DateTimeField('Заявка создана', default=timezone.now)
    handed_at = models.DateTimeField('Передано', null=True, blank=True)
    return_requested_at = models.DateTimeField('Возврат запрошен', null=True, blank=True)
    closed_at = models.DateTimeField('Закрыто', null=True, blank=True)
    class Meta:
        verbose_name = 'Выдача'
        verbose_name_plural = 'Выдачи'
        ordering = ['-created_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['copy'], condition=~Q(status='closed'), name='one_open_loan_per_copy'),
            models.CheckConstraint(condition=Q(status__in=['reserved','active','requested','inspection','closed']), name='loan_valid_status'),
            models.CheckConstraint(condition=Q(receipt_method__in=['pickup','delivery']), name='loan_valid_method'),
            models.CheckConstraint(condition=(Q(subscription__isnull=False, daily_days__isnull=True, daily_price_snapshot__isnull=True) |
                Q(subscription__isnull=True, daily_days__isnull=False, daily_days__gte=1, daily_days__lte=30, daily_price_snapshot__isnull=False, daily_price_snapshot__gte=0)), name='loan_mode_exclusive'),
            models.CheckConstraint(condition=(Q(status='closed',closed_at__isnull=False) | (~Q(status='closed') & Q(closed_at__isnull=True))), name='loan_closure_consistent'),
            models.CheckConstraint(condition=Q(closed_at__isnull=True) | Q(closed_at__gte=F('created_at')), name='loan_dates_order'),
        ]
    @property
    def total(self):
        return self.daily_days * self.daily_price_snapshot if self.subscription_id is None else 0
    def clean(self):
        if self.subscription_id and self.user_id != self.subscription.user_id:
            raise ValidationError('Подписка принадлежит другому игроку.')
    def __str__(self): return f'Выдача {self.pk} / {self.copy}'


class LoanComponent(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name='components', verbose_name='Выдача')
    component = models.ForeignKey(Component, on_delete=models.PROTECT, related_name='loan_components', verbose_name='Деталь')
    expected_quantity = models.PositiveSmallIntegerField('Выданное количество', validators=[MinValueValidator(1)])
    class Meta:
        verbose_name = 'Выданная деталь'
        verbose_name_plural = 'Комплектация при выдаче'
        ordering = ['loan_id', 'component_id']
        constraints = [models.UniqueConstraint(fields=['loan','component'], name='unique_loan_component'),
                       models.CheckConstraint(condition=Q(expected_quantity__gte=1), name='expected_quantity_positive')]
    def __str__(self): return f'{self.loan_id}: {self.component} × {self.expected_quantity}'


class ReturnAct(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name='acts', verbose_name='Выдача')
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='inspections', verbose_name='Сотрудник')
    checked_at = models.DateTimeField('Дата проверки', default=timezone.now)
    notes = models.TextField('Замечания', blank=True)
    class Meta:
        verbose_name = 'Акт приёма'
        verbose_name_plural = 'Акты приёма'
        ordering = ['-checked_at', '-id']
    def __str__(self): return f'Акт {self.pk} / выдача {self.loan_id}'


class InspectionLine(models.Model):
    act = models.ForeignKey(ReturnAct, on_delete=models.PROTECT, related_name='lines', verbose_name='Акт')
    loan_component = models.ForeignKey(LoanComponent, on_delete=models.PROTECT, related_name='checks', verbose_name='Выданная деталь')
    returned_quantity = models.PositiveSmallIntegerField('Возвращено')
    is_intact = models.BooleanField('Без повреждений')
    notes = models.TextField('Замечания', blank=True)
    class Meta:
        verbose_name = 'Строка проверки'
        verbose_name_plural = 'Строки проверки'
        ordering = ['act_id', 'loan_component_id']
        constraints = [models.UniqueConstraint(fields=['act','loan_component'], name='unique_act_component')]
    def clean(self):
        if self.act_id and self.loan_component_id:
            if self.act.loan_id != self.loan_component.loan_id:
                raise ValidationError('Деталь относится к другой выдаче.')
            if self.returned_quantity > self.loan_component.expected_quantity:
                raise ValidationError('Возвращено больше деталей, чем выдано.')
    def __str__(self): return f'Акт {self.act_id}: деталь {self.loan_component_id}'


class Fine(models.Model):
    line = models.ForeignKey(InspectionLine, on_delete=models.PROTECT, related_name='fines', verbose_name='Строка проверки')
    reason = models.CharField('Причина', max_length=250)
    amount = models.DecimalField('Сумма', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField('Начислен', default=timezone.now)
    paid_at = models.DateTimeField('Оплачен', null=True, blank=True)
    class Meta:
        verbose_name = 'Штраф'
        verbose_name_plural = 'Штрафы'
        ordering = ['-created_at', '-id']
        constraints = [models.CheckConstraint(condition=Q(amount__gte=0), name='fine_nonnegative'),
                       models.CheckConstraint(condition=Q(paid_at__isnull=True) | Q(paid_at__gte=F('created_at')), name='fine_dates_order')]
    def __str__(self): return f'Штраф {self.pk}: {self.amount} руб.'


class Delivery(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name='deliveries', verbose_name='Выдача')
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='deliveries', verbose_name='Курьер', null=True, blank=True)
    kind = models.CharField('Операция', max_length=8, choices=[('outbound', 'Доставка'), ('return', 'Забор')])
    address = models.CharField('Адрес', max_length=250)
    contact = models.CharField('Контакт получателя', max_length=100)
    scheduled_at = models.DateTimeField('Запланировано')
    transferred_at = models.DateTimeField('Передано', null=True, blank=True)
    class Meta:
        verbose_name = 'Доставка'
        verbose_name_plural = 'Доставки и заборы'
        ordering = ['scheduled_at', 'id']
        constraints = [models.CheckConstraint(condition=Q(kind__in=['outbound','return']), name='delivery_valid_kind'),
                       models.CheckConstraint(condition=Q(transferred_at__isnull=True) | Q(courier__isnull=False), name='delivery_transfer_has_courier')]
    def __str__(self): return f'{self.get_kind_display()} {self.pk} / выдача {self.loan_id}'

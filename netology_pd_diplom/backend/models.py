from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),

)


class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Модель пользователя
    """
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    objects = UserManager()

    email = models.EmailField(_('email address'), unique=True)
    company = models.CharField(verbose_name='company', max_length=40, blank=True)
    position = models.CharField(verbose_name='position', max_length=40, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    type = models.CharField(verbose_name='users type', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = "User's list"
        ordering = ('email',)


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='user',
                             related_name='contacts', blank=True,
                             on_delete=models.CASCADE)

    city = models.CharField(max_length=50, verbose_name='city')
    street = models.CharField(max_length=100, verbose_name='street')
    house = models.CharField(max_length=15, verbose_name='house', blank=True)
    structure = models.CharField(max_length=15, verbose_name='corpus', blank=True)
    building = models.CharField(max_length=15, verbose_name='building', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='flat', blank=True)
    phone = models.CharField(max_length=20, verbose_name='telephone number')

    class Meta:
        verbose_name = "User's contact"
        verbose_name_plural = "User's contact list"

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'


class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name='name')
    url = models.URLField(verbose_name='url', null=True, blank=True)
    user = models.OneToOneField(User, verbose_name='user',
                                blank=True, null=True,
                                on_delete=models.CASCADE)
    state = models.BooleanField(verbose_name='order receipt status', default=True)


    class Meta:
        verbose_name = 'Shop'
        verbose_name_plural = "Shops"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=40, verbose_name='name')
    shops = models.ManyToManyField(Shop, verbose_name='shops', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = "Categories"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=80, verbose_name='name')
    category = models.ForeignKey(Category, verbose_name='category', related_name='products', blank=True,
                                 on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Products'
        verbose_name_plural = "Product's list"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    model = models.CharField(max_length=80, verbose_name='model', blank=True)
    external_id = models.PositiveIntegerField(verbose_name='external ID')
    product = models.ForeignKey(Product, verbose_name='product', related_name='product_infos', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='shop', related_name='product_infos', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='quantity')
    price = models.PositiveIntegerField(verbose_name='price')
    price_rrc = models.PositiveIntegerField(verbose_name='recomended retail price')

    class Meta:
        verbose_name = 'Products info'
        verbose_name_plural = "Information list about products"
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop', 'external_id'], name='unique_product_info'),
        ]

    def __str__(self):
        return f'{self.product} {_("from")} {self.shop}'


class Parameter(models.Model):
    name = models.CharField(max_length=40, verbose_name='name')

    class Meta:
        verbose_name = 'Parameter name'
        verbose_name_plural = "List of parameter names"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='product information',
                                     related_name='product_parameters', blank=True,
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='parameter', related_name='product_parameters', blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(verbose_name='value', max_length=128)

    class Meta:
        verbose_name = 'Parameter'
        verbose_name_plural = "Parameter's list"
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter'),
        ]

    def __str__(self):
        return f'{self.product} - {self.parameter} {self.value}'


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='user',
                             related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    state = models.CharField(verbose_name='status', choices=STATE_CHOICES, max_length=15)
    contact = models.ForeignKey(Contact, verbose_name='contact',
                                blank=True, null=True,
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Orders'
        verbose_name_plural = "Order's list"
        ordering = ('-created',)

    def __str__(self):
        return str(self.created)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='order', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)

    product_info = models.ForeignKey(ProductInfo, verbose_name='product information', related_name='ordered_items',
                                     blank=True,
                                     on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='quantity')

    class Meta:
        verbose_name = 'Ordered item'
        verbose_name_plural = "List of ordered items"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_item'),
        ]


class ConfirmEmailToken(models.Model):
    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name=_("The User which is associated to this password reset token")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("When was this token generated")
    )

    key = models.CharField(
        _("Key"),
        max_length=64,
        db_index=True,
        unique=True
    )

    class Meta:
        verbose_name = 'Confirmation Token Email'
        verbose_name_plural = 'Confirmation Tokens Email'

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)
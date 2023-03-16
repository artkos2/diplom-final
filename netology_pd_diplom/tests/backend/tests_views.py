import pytest
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from django.urls import reverse
from backend.models import User


@pytest.mark.django_db
def test_user_create(api_client):
    user = {
        'first_name': 'Test1',
        'last_name': 'Test2',
        'email': 'Test1@gmail.com',
        'password': '&6tyuk3ede',
        'company': 'company',
        'position': 'SEO'
    }
    url = reverse('backend:user-register')
    res = api_client.post(url, data=user)

    assert res.json().get('Status') is True
    assert res.status_code == HTTP_201_CREATED


@pytest.mark.django_db
def test_user_confirm_token(api_client, user_factory, confirm_token_factory):
    user = user_factory()
    token = confirm_token_factory()
    user.confirm_email_tokens.add(token)
    url = reverse('backend:user-register-confirm')
    res = api_client.post(url, data={'email': user.email, 'token': 'token'})
    assert res.status_code == HTTP_200_OK
    assert res.json().get('Status') is False
    res = api_client.post(url, data={'email': user.email, 'token': token.key})
    assert res.status_code == HTTP_200_OK
    assert res.json().get('Status') is True


@pytest.mark.django_db
def test_user_login(api_client, user_factory):
    email = 'test@gmail.com'
    password = 'cdjndcbdbcdh12345'

    user = {
        'first_name': 'Test1',
        'last_name': 'Test2',
        'email': email,
        'password': password,
        'company': 'company',
        'position': 'SEO'
    }

    url = reverse('backend:user-register')
    res = api_client.post(url, data=user)
    assert res.json().get('Status') is True

    user = User.objects.get(email=email)
    user.is_active = True
    user.save()

    url = reverse('backend:user-login')
    res = api_client.post(url, data={'email': email, 'password': password})
    assert res.status_code == HTTP_200_OK
    assert res.json().get('Status') is True


@pytest.mark.django_db
def test_user_details(api_client, user_factory):
    user1 = {
        'first_name': 'Test1',
        'last_name': 'Test2',
        'email': 'Test1@gmail.com',
        'password': '&6tyuk3ede',
        'company': 'company',
        'position': 'SEO'
    }
    url = reverse('backend:user-details')
    user = user_factory()
    res = api_client.get(url)
    assert res.status_code == HTTP_403_FORBIDDEN
    api_client.force_authenticate(user=user)
    res = api_client.get(url)
    assert res.status_code == HTTP_200_OK
    assert res.json().get('email') == user.email
    api_client.post(url, data=user1)

    res = api_client.get(url)
    assert res.json().get('company') == 'company'
    res = api_client.post(url, data={'type': 'shop'})
    res = api_client.get(url)
    assert res.json().get('type') == 'shop'


@pytest.mark.django_db
def test_products(api_client, user_factory, shop_factory, order_factory,
                  product_info_factory, product_factory, category_factory):

    url = reverse('backend:shops')
    shop = shop_factory()
    user = user_factory()
    category = category_factory()
    api_client.force_authenticate(user=user)
    res = api_client.get(url, shop_id=shop.id, category_id=category.id)
    assert res.status_code == HTTP_200_OK
    assert res.json()['results'][0].get('id', False)


@pytest.mark.django_db
def test_category(api_client, category_factory):
    url = reverse('backend:categories')
    category_factory(_quantity=4)
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 4


@pytest.mark.django_db
def test_basket_by_anonymous(api_client):
    basket = {'items': [{'product_info': 1, 'quantity': 2}]}
    url = reverse('backend:basket')
    response = api_client.post(url, data=basket)
    assert response.status_code == HTTP_403_FORBIDDEN




from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ing_id):
    return reverse('recipe:ingredient-detail', args=[ing_id])


def create_user(email='test@example.com', password='testpass123'):
    return get_user_model().objects.create_user(email, password)


def create_ingredient(user, **params):
    defaults = {
        'name': 'Sample name',
    }
    defaults.update(params)

    ing = Ingredient.objects.create(user=user, **defaults)
    return ing


class PublicIngredientsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENTS_URL)

        ings = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ings, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_list_limited_to_user(self):
        other_user = create_user(email='other@example.com', password='pass123')
        create_ingredient(user=other_user)
        create_ingredient(user=self.user)

        res = self.client.get(INGREDIENTS_URL)

        ings = Ingredient.objects.filter(user=self.user)
        serializer = IngredientSerializer(ings, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_update_ingredient_detail(self):
        ing = Ingredient.objects.create(user=self.user, name='Salt')
        payload = {
            'name': 'Sugar'
        }
        url = detail_url(ing.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ing.refresh_from_db()
        self.assertEqual(payload['name'], ing.name)
        serializer = IngredientSerializer(ing)
        self.assertEqual(res.data, serializer.data)

    def test_filter_ingredients_assigned_to_recipes(self):
        in1 = Ingredient.objects.create(user=self.user, name='Salt')
        in2 = Ingredient.objects.create(user=self.user, name='Sugar')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample recipe desc',
            time_minutes=5,
            price=Decimal('5.50'),
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        in1 = Ingredient.objects.create(user=self.user, name='Salt')
        Ingredient.objects.create(user=self.user, name='Cheese')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample recipe desc',
            time_minutes=5,
            price=Decimal('5.50'),
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Second recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample recipe desc',
            time_minutes=5,
            price=Decimal('5.50'),
        )

        recipe.ingredients.add(in1)
        recipe2.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)

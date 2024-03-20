from django.test import SimpleTestCase
from app import calc


class CalcTests(SimpleTestCase):

    def test_add_numbers(self):
        """Add numbers together"""
        res = calc.add(6, 3)

        self.assertEqual(res, 9)

    def test_subtract(self):
        """subtract numbers"""
        res = calc.subtract(10, 6)

        self.assertEqual(res, 4)

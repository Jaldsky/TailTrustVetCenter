from unittest import TestCase

from app.bots.tail_trust.validator import Validator


class TestValidator(TestCase):
    def test_validate_name(self):
        test_cases = [
            ("John", True),  # Корректное имя
            ("John Doe", True),  # Корректное имя с пробелом
            ("John123", False),  # Не корректное имя с цифрами
            ("John-Doe", False)  # Не корректное имя с дефисом
        ]
        for name, expected_result in test_cases:
            with self.subTest(name=name):
                self.assertEqual(Validator.validate_name(name), expected_result)

    def test_validate_surname(self):
        test_cases = [
            ("Doe", True),  # Корректная фамилия
            ("John Doe", True),  # Корректная фамилия с пробелом
            ("Doe123", False),  # Не корректная фамилия с цифрами
            ("Doe_White", False)  # Не корректная фамилия с подчеркиванием
        ]
        for surname, expected_result in test_cases:
            with self.subTest(surname=surname):
                self.assertEqual(Validator.validate_surname(surname), expected_result)

    def test_validate_phone(self):
        test_cases = [
            ("+12345678901", True),  # Корректный номер телефона с плюсом
            ("12345678901", True),  # Корректный номер телефона без плюса
            ("+1234567890", False),  # Не корректный номер телефона без одной цифры
            ("+123456789012", False),  # Не корректный номер телефона с плюсом и лишней цифрой
            ("ABC4567890", False)  # Не корректный номер телефона с буквами
        ]
        for phone, expected_result in test_cases:
            with self.subTest(phone=phone):
                self.assertEqual(Validator.validate_phone(phone), expected_result)

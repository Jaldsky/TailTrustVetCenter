import re


class Validator(object):
    """Класс для валидации данных."""

    @staticmethod
    def validate_name(name: str) -> bool:
        """Валидация имени пользователя.
        Имя должно содержать буквы, допускаются пробелы.

        Args:
            name: имя пользователя.

        Return:
            True - имя корректно, False - не корректна.
        """
        return bool(re.match(r'^[a-zA-Zа-яА-я\s]+$', name))

    @staticmethod
    def validate_surname(surname: str) -> bool:
        """Валидация фамилии пользователя.
        Фамилия должна содержать буквы, допускаются пробелы.

        Args:
            surname: фамилия пользователя.

        Return:
            True - фамилия корректно, False - не корректна.
        """
        return bool(re.match(r'^[a-zA-Zа-яА-я\s]+$', surname))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Валидация номера телефона пользователя.
        Номер телефона должен быть в формате +12345678901 или 12345678901.

        Args:
            phone: фамилия номера телефона пользователя.

        Return:
            True - номера корректен, False - не корректен.
        """
        return bool(re.match(r'^(\+?\d{11}|\d{10})$', phone))

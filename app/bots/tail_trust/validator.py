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
            True - имя корректно, False - некорректна.
        """
        return bool(re.match(r'^[a-zA-Zа-яА-я\s]+$', name))

    @staticmethod
    def validate_surname(surname: str) -> bool:
        """Валидация фамилии пользователя.
        Фамилия должна содержать буквы, допускаются пробелы.

        Args:
            surname: фамилия пользователя.

        Return:
            True - фамилия корректно, False - некорректна.
        """
        return bool(re.match(r'^[a-zA-Zа-яА-я\s]+$', surname))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Валидация номера телефона пользователя.
        Номер телефона должен быть в формате +12345678901 или 12345678901.

        Args:
            phone: фамилия номера телефона пользователя.

        Return:
            True - номера корректен, False - некорректен.
        """
        return bool(re.match(r'^(\+?\d{11}|\d{10})$', phone))

    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Валидация даты в формате YYYY-MM-DD.

        Args:
            date_str: строка с датой в формате YYYY-MM-DD.

        Return:
            True - дата корректна, False - некорректна.
        """
        return bool(re.match(r'\d{4}-\d{2}-\d{2}', date_str))

    @staticmethod
    def validate_time(time_str: str) -> bool:
        """Валидация формата времени.

        Args:
            time_str: строка с временем.

        Return:
            True - формат времени корректен, False - некорректен.
        """
        return bool(re.match(r'^\d{2}:\d{2}$', time_str))

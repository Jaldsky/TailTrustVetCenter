import django


if __name__ == '__main__':
    """Инициализация Django и запуск бота."""
    django.setup()
    from app.bots.controller import Controller

    Controller().exec()

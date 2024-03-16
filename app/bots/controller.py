from abc import ABC, abstractmethod


from app.bots.tail_trust.tail_trust import TailTrustBot
from main.settings import BOT_TOKEN


class ControllerBase(ABC):
    """Базовый класс контроллера."""

    @abstractmethod
    def exec(self) -> None:
        """Метод для запуска контроллера."""


class Controller(ControllerBase):
    """Класс контроллера. Класс предназначен для котроля запуска ботов."""

    def exec(self) -> None:
        """Метод для запуска контроллера."""

        bot = TailTrustBot(api_token=BOT_TOKEN)
        bot.exec()


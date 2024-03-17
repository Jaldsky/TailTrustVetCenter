from unittest import TestCase
from unittest.mock import Mock, patch

from aiogram import types
from app.bots.tail_trust.tail_trust import BotBase, TextInterfaceBot
import asyncio


@patch('app.bots.tail_trust.tail_trust.Bot', spec=True)
class TestBotBase(TestCase):

    def test_cmd_start(self, mock_bot):
        loop = asyncio.new_event_loop()
        mock_bot.return_value.loop = loop

        bot = BotBase(api_token='')
        message = Mock(spec=types.Message)

        loop.run_until_complete(bot.cmd_start(message))

        message.answer.assert_called_once_with(TextInterfaceBot.WELLCOME_MSG)

        # TODO Добавить юнит-тесты на все команды + добавть интеграциональные тестны на бизнес логику

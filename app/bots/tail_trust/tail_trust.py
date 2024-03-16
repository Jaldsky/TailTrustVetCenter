from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional

from app.bots.lib.common import EnumBase
from app.bots.tail_trust.validator import Validator
from app.models import Client, Appointment
from aiogram import Bot, Dispatcher, types
from aiogram import executor
from asgiref.sync import sync_to_async


class CommandsBot(EnumBase):
    CMD_HELP = 'help'  # Команда для просмотра списка доступных команд
    CMD_RESET = 'reset'  # Команда для обнуления регистрации
    CMD_START = 'start'  # Команда для начала работы с ботом
    CMD_REGISTER = 'register'  # Команда для регистрации нового пользователя
    CMD_PROFILE = 'profile'  # Команда для просмотра информации о пользователе


# отдельный класс для ускорения быстродействия, иначе инициализировалась бы каждая строка как отдельный объект
class TextInterfaceBot(EnumBase):
    WELLCOME_MSG = 'Добро пожаловать!\nДля регистрации введите команду /register.'
    ALREADY_REGISTERED_MSG = 'Вы уже зарегистрированы.'
    NO_REGISTERED_MSG = 'Вы еще не зарегистрированы.'
    RESET_SUCCESS_MSG = 'Все данные сброшены.'

    USER_PROFILE_NAME = 'Введите Ваше имя:'
    USER_PROFILE_SURNAME = 'Теперь введите вашу фамилию:'
    USER_PROFILE_PHONE = 'Теперь введите ваш телефон:'
    REGISTRATION_COMPLETED = 'Регистрация завершена! Теперь Вы можете пользоваться полным функционалом.'
    USER_PROFILE_INFO = 'Ваш профиль:\nИмя: {name}\nФамилия: {surname}\nТелефон: {phone}'

    UNAUTHORIZED_HELP_MSG = ('Список доступных команд:\n/start - Начать работу с ботом\n'
                             '/register - Зарегистрироваться\n/reset - Обнулить регистрацию')
    AUTHORIZED_HELP_MSG = f'{UNAUTHORIZED_HELP_MSG}\n/profile - Посмотреть профиль'  # добавить все команды

    NO_USER_ID_ERROR = 'Не удалось получить идентификатор из базы данных.'
    INCORRECT_NAME_ERROR = ('Некорректное имя.\nИмя должно содержать буквы, допускаются пробелы.\n'
                            'Пожалуйста, введите имя заново.')
    INCORRECT_SURNAME_ERROR = ('Некорректная фамилия.\nФамилия должна содержать буквы, допускаются пробелы.\n'
                               'Пожалуйста, введите фамилию заново.')
    INCORRECT_PHONE_ERROR = ('Некорректный номер телефона.\nНомер телефона должен быть в'
                             'формате +12345678901 или 12345678901.\nПожалуйста, введите номер телефона заново.')


class BotInterface(ABC):
    @abstractmethod
    def configure_handlers(self):
        pass

    @abstractmethod
    def exec(self):
        pass


@dataclass
class BotBase(BotInterface):
    api_token: str
    bot: Bot = None
    dp: Dispatcher = None

    def __post_init__(self):
        self.bot = Bot(token=self.api_token)
        self.dp = Dispatcher(self.bot)
        self.configure_handlers()

    def configure_handlers(self):
        self.dp.register_message_handler(self.cmd_help, commands=[CommandsBot.CMD_HELP])
        self.dp.register_message_handler(self.cmd_start, commands=[CommandsBot.CMD_START])

    @staticmethod
    async def _get_user_data(personal_chat_id: int) -> Optional[Client]:
        try:
            return await sync_to_async(Client.objects.get)(telegram_chat_id=personal_chat_id)
        except Client.DoesNotExist:
            return None

    async def cmd_help(self, message: types.Message):
        personal_chat_id = message.chat.id

        user_data = await self._get_user_data(personal_chat_id)
        if user_data:
            await message.answer(TextInterfaceBot.AUTHORIZED_HELP_MSG)
        else:
            await message.answer(TextInterfaceBot.UNAUTHORIZED_HELP_MSG)

    async def cmd_start(self, message: types.Message):
        await message.answer(TextInterfaceBot.WELLCOME_MSG)

    def exec(self):
        executor.start_polling(self.dp, skip_updates=True)


@dataclass
class TailTrustBot(BotBase):

    def configure_handlers(self):
        super().configure_handlers()

        self.dp.register_message_handler(self.cmd_reset, commands=[CommandsBot.CMD_RESET])
        self.dp.register_message_handler(self.cmd_register, commands=[CommandsBot.CMD_REGISTER])
        self.dp.register_message_handler(self.cmd_view_profile, commands=[CommandsBot.CMD_PROFILE])

        self.dp.register_message_handler(self.process_registration)

    async def cmd_reset(self, message: types.Message):
        personal_chat_id = message.chat.id

        user_data = await self._get_user_data(personal_chat_id)
        if user_data:
            await sync_to_async(user_data.delete)()
            await message.answer(TextInterfaceBot.RESET_SUCCESS_MSG)
        else:
            await message.answer(TextInterfaceBot.NO_REGISTERED_MSG)

    async def cmd_register(self, message: types.Message):
        personal_chat_id = message.chat.id

        user_data = await self._get_user_data(personal_chat_id)

        if user_data and user_data.name and user_data.surname and user_data.phone:
            await message.answer(TextInterfaceBot.ALREADY_REGISTERED_MSG)
            return

        if not user_data or not user_data.telegram_chat_id:
            client = Client(telegram_chat_id=personal_chat_id)
            await sync_to_async(client.save)()
        await self.process_registration(message)

    async def process_registration(self, message: types.Message):
        personal_chat_id = message.chat.id

        user_data = await self._get_user_data(personal_chat_id)
        if not user_data:
            await message.answer(TextInterfaceBot.NO_USER_ID_ERROR)  # возникнет, если в БД не прилетит user id
            return

        if CommandsBot.CMD_REGISTER in message.text:
            await message.answer(TextInterfaceBot.USER_PROFILE_NAME)

        elif not user_data.name:
            name = message.text
            if Validator.validate_name(name):
                user_data.name = name
                await sync_to_async(user_data.save)()
                await message.answer(TextInterfaceBot.USER_PROFILE_SURNAME)
            else:
                await message.answer(TextInterfaceBot.INCORRECT_NAME_ERROR)

        elif not user_data.surname:
            surname = message.text
            if Validator.validate_surname(surname):
                user_data.surname = surname
                await sync_to_async(user_data.save)()
                await message.answer(TextInterfaceBot.USER_PROFILE_PHONE)
            else:
                await message.answer(TextInterfaceBot.INCORRECT_SURNAME_ERROR)

        elif not user_data.phone:
            phone = message.text
            if Validator.validate_phone(phone):
                user_data.phone = phone
                await sync_to_async(user_data.save)()
                await message.answer(TextInterfaceBot.REGISTRATION_COMPLETED)
            else:
                await message.answer(TextInterfaceBot.INCORRECT_PHONE_ERROR)

    async def cmd_view_profile(self, message: types.Message):
        personal_chat_id = message.chat.id

        user_data = await self._get_user_data(personal_chat_id)
        if user_data:
            await message.answer(TextInterfaceBot.USER_PROFILE_INFO.format(
                name=user_data.name,
                surname=user_data.surname,
                phone=user_data.phone))
        else:
            await message.answer(TextInterfaceBot.NO_REGISTERED_MSG)

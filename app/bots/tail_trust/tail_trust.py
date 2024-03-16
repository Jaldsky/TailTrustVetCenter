from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, Union

import datetime as datetime
from aiogram import Bot, Dispatcher, types
from aiogram import executor
from asgiref.sync import sync_to_async

from app.bots.lib.common import EnumBase
from app.bots.tail_trust.validator import Validator
from app.models import Client, Appointment
from main.settings import DATE_FORMAT


class CommandsBot(EnumBase):
    CMD_HELP = 'help'  # Команда для просмотра списка доступных команд
    CMD_RESET = 'reset'  # Команда для обнуления регистрации
    CMD_START = 'start'  # Команда для начала работы с ботом
    CMD_REGISTER = 'register'  # Команда для регистрации нового пользователя
    CMD_PROFILE = 'profile'  # Команда для просмотра информации о пользователе
    CMD_APPOINTMENT = 'appointment'  # Команда для записи зарегистрированного пользователя на прием
    CMD_APPLIST = 'applist'  # Команда для просмотра все записей на прием


# отдельный класс для ускорения быстродействия, иначе инициализировалась бы каждая строка как отдельный объект
class TextInterfaceBot(EnumBase):
    WELLCOME_MSG = 'Добро пожаловать!\nДля регистрации введите команду /register.'
    ALREADY_REGISTERED_MSG = 'Вы уже зарегистрированы.'
    NO_REGISTERED_MSG = 'Вы еще не зарегистрированы.'
    RESET_SUCCESS_MSG = 'Все данные сброшены.'

    UNAUTHORIZED_HELP_MSG = ('Список доступных команд:\n/start - Начать работу с ботом\n'
                             '/register - Зарегистрироваться\n/reset - Обнулить регистрацию')
    AUTHORIZED_HELP_MSG = (f'{UNAUTHORIZED_HELP_MSG}\n/profile - Посмотреть профиль\n'
                           '/appointment - Записаться на прием\n/applist - Список записей на прием')

    USER_PROFILE_NAME = 'Введите Ваше имя:'
    USER_PROFILE_SURNAME = 'Теперь введите вашу фамилию:'
    USER_PROFILE_PHONE = 'Теперь введите ваш телефон:'
    REGISTRATION_COMPLETED = ('Регистрация завершена! Теперь Вы можете пользоваться полным функционалом.\n'
                              'Для просмотра доступных команд введите /help')
    USER_PROFILE_INFO = 'Ваш профиль:\nИмя: {name}\nФамилия: {surname}\nТелефон: {phone}'

    USER_APPOINTMENT_DATE = 'Выберите дату записи на прием:'
    USER_APPOINTMENT_TIME = 'Выберите время записи на прием:'
    USER_APPOINTMENT_PET = 'Выберите категорию питомца:'
    USER_APPOINTMENT_COMPLETED = 'Регистрация на запись завершена! Проверить все записи можно введя /applist'
    USER_APPOINTMENT_INFO_ALL = 'Ваши записи на прием:\n'
    USER_APPOINTMENT_INFO_LIST = 'Дата: {date}, время {time}, тип питомца {pet}'

    NO_USER_ID_ERROR = ('Не найдена запись о пользователе в базе данных.\n'
                        'Обратитесь в службу технической поддержки или попробуйте пройти регистрацию заново /register')
    NO_APPOINTMENT_ID_ERROR = ('Не удалось найти заявку на запись в базе данных.\n'
                               'Обратитесь в службу технической поддержки или попробуйте записаться на'
                               ' прием заново /appointment')
    INCORRECT_NAME_ERROR = ('Некорректное имя.\nИмя должно содержать буквы, допускаются пробелы.\n'
                            'Пожалуйста, введите имя заново.')
    INCORRECT_SURNAME_ERROR = ('Некорректная фамилия.\nФамилия должна содержать буквы, допускаются пробелы.\n'
                               'Пожалуйста, введите фамилию заново.')
    INCORRECT_PHONE_ERROR = ('Некорректный номер телефона.\nНомер телефона должен быть в'
                             ' формате +12345678901 или 12345678901.\nПожалуйста, введите номер телефона заново.')
    NO_APPOINTMENTS_ERROR = 'Не найдена ни одна запись на прием.\nДля записи введите /appointment'


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

    async def _is_user_exists(self, personal_chat_id: int) -> bool:
        return bool(await self._get_user_data(personal_chat_id))

    async def cmd_help(self, message: types.Message):
        personal_chat_id = message.chat.id

        if await self._is_user_exists(personal_chat_id):
            await message.answer(TextInterfaceBot.AUTHORIZED_HELP_MSG)
        else:
            await message.answer(TextInterfaceBot.UNAUTHORIZED_HELP_MSG)

    async def cmd_start(self, message: types.Message):
        await message.answer(TextInterfaceBot.WELLCOME_MSG)

    def exec(self):
        executor.start_polling(self.dp, skip_updates=True)


@dataclass
class TailTrustBot(BotBase):

    def __post_init__(self):
        super().__post_init__()
        self.appointment_next_days: int = 7
        self.appointment_week_days: set = set(range(0, 5))  # суббота, воскресенье выходной
        self.appointment_hours: tuple = ('10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00', '18:00')
        self.appointment_pets: tuple = ('Собака', 'Кошка', 'Попугай', 'Рыбка')

    def configure_handlers(self):
        super().configure_handlers()

        self.dp.register_message_handler(self.cmd_reset, commands=[CommandsBot.CMD_RESET])
        self.dp.register_message_handler(self.cmd_register, commands=[CommandsBot.CMD_REGISTER])
        self.dp.register_message_handler(self.cmd_view_profile, commands=[CommandsBot.CMD_PROFILE])
        self.dp.register_message_handler(self.cmd_appointment, commands=[CommandsBot.CMD_APPOINTMENT])
        self.dp.register_message_handler(self.cmd_applist, commands=[CommandsBot.CMD_APPLIST])

        self.dp.register_message_handler(self.messages_handler)

    async def messages_handler(self, message):
        personal_chat_id = message.chat.id

        user_data = await self._get_user_data(personal_chat_id)
        if not user_data or not user_data.name or not user_data.surname or not user_data.phone:
            await self.process_registration(message)

        await self.process_register_appointment(message)

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

    async def cmd_appointment(self, message: types.Message):
        personal_chat_id = message.chat.id

        user_data = await self._get_user_data(personal_chat_id)
        if not user_data or not user_data.name or not user_data.surname or not user_data.phone:
            await message.answer(TextInterfaceBot.NO_REGISTERED_MSG)
            return

        user_appointment = Appointment(client=user_data)
        await sync_to_async(user_appointment.save)()
        await self.process_register_appointment(message)

    @staticmethod
    def _generate_slots_keyboard(slots):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for slot in slots:
            keyboard.add(types.KeyboardButton(slot))
        return keyboard

    def _pick_appointment_date(self):
        current_date = datetime.datetime.now()

        available_dates = [
            (current_date + datetime.timedelta(days=day)).strftime(DATE_FORMAT)
            for day in range(self.appointment_next_days)
            if (current_date + datetime.timedelta(days=day)).weekday() in self.appointment_week_days
        ]
        return self._generate_slots_keyboard(available_dates)

    def _pick_appointment_time(self):
        available_times = [
            time for time in self.appointment_hours
        ]
        return self._generate_slots_keyboard(available_times)

    @staticmethod
    async def _get_user_appointments_data(personal_chat_id: int,
                                          get_last_appointment: bool = False) -> Optional[Union[Client, list[Client]]]:
        try:
            appointments = await sync_to_async(list)(Appointment.objects.filter(client_id=personal_chat_id))
            sorted_appointments = sorted(appointments, key=lambda x: x.id, reverse=True)
            if sorted_appointments:
                if get_last_appointment:
                    return sorted_appointments[0]
                return sorted_appointments
            return None
        except Appointment.DoesNotExist:
            return None

    async def process_register_appointment(self, message):
        personal_chat_id = message.chat.id

        user_appointment_data = await self._get_user_appointments_data(personal_chat_id, get_last_appointment=True)
        if not user_appointment_data:
            await message.answer(TextInterfaceBot.NO_APPOINTMENT_ID_ERROR)
            return

        if CommandsBot.CMD_APPOINTMENT in message.text:
            await message.answer(TextInterfaceBot.USER_APPOINTMENT_DATE, reply_markup=self._pick_appointment_date())

        elif Validator.validate_date(message.text):
            user_appointment_data.date = message.text
            await sync_to_async(user_appointment_data.save)()
            await message.answer(TextInterfaceBot.USER_APPOINTMENT_TIME, reply_markup=self._pick_appointment_time())

        elif Validator.validate_time(message.text):
            user_appointment_data.time = message.text
            await sync_to_async(user_appointment_data.save)()
            await message.answer(
                TextInterfaceBot.USER_APPOINTMENT_PET,
                reply_markup=self._generate_slots_keyboard(self.appointment_pets)
            )

        elif message.text in self.appointment_pets:
            user_appointment_data.pet_type = message.text
            await sync_to_async(user_appointment_data.save)()

            await message.answer(TextInterfaceBot.USER_APPOINTMENT_COMPLETED)

    async def cmd_applist(self, message):
        personal_chat_id = message.chat.id

        if not await self._is_user_exists(personal_chat_id):
            await message.answer(TextInterfaceBot.NO_REGISTERED_MSG)
            return

        appointments = await self._get_user_appointments_data(personal_chat_id)
        if not appointments:
            await message.answer(TextInterfaceBot.NO_APPOINTMENTS_ERROR)
            return

        applist = []
        for app in appointments:
            if not app.date or not app.time or not app.pet_type:
                await sync_to_async(app.delete)()
            else:
                applist.append(
                    TextInterfaceBot.USER_APPOINTMENT_INFO_LIST.format(date=app.date, time=app.time, pet=app.pet_type))
        applist_text = TextInterfaceBot.USER_APPOINTMENT_INFO_ALL + "\n".join(applist)
        await message.answer(applist_text)

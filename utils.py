import logging
import os

# import openai
from aiogram import Bot, Dispatcher
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

"""
                        FOR ENV FILE
"""
_env_path = os.path.join(os.path.dirname(__file__), '.env')

with open(_env_path, 'r') as file:
    for line in file:
        key, value = line.strip().split('=')

        os.environ[key] = value

"""
                        FOR CONNECT TELEGRAM BOT
"""
_TOKEN = os.environ.get("TOKEN")
if _TOKEN is None:
    raise ValueError("Token not found in the .env file. Make sure you add it")

bot = Bot(token=_TOKEN)
_storage = MemoryStorage()
dp = Dispatcher(storage=_storage)

"""
                        FOR OPENAI
"""
# _OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
# if _OPENAI_API_KEY is None:
#     raise ValueError("OPENAI_API_KEY not found in the .env file. Make sure you add it")
#
# openai.api_key = _OPENAI_API_KEY

"""
                        ELSE
"""
logging.basicConfig(level=logging.INFO)

expected_locations = [
    'Ukraine',
    'Poland', 'USA',
    'Germany',
    'Israel'
]

_checklist_items = [
    "All clear",
    "Leave a comment"
]


class Form(StatesGroup):
    location: str = State()

    checklist: str = State()

    first_point: str = State()
    first_point_with_comment: str = State()
    check_first_photo: str = State()
    first_photo: str = State()

    second_point: str = State()
    second_point_with_comment: str = State()
    check_second_photo: str = State()
    second_photo: str = State()

    third_point: str = State()
    third_point_with_comment: str = State()
    check_third_photo: str = State()
    third_photo: str = State()

    fourth_point: str = State()
    fourth_point_with_comment: str = State()
    check_fourth_photo: str = State()
    fourth_photo: str = State()

    fifth_point: str = State()
    fifth_point_with_comment: str = State()
    check_fifth_photo: str = State()
    fifth_photo: str = State()

    report: str = State()

    OpenAI: str = State()


photos = [
    "first_photo",
    "second_photo",
    "third_photo",
    "fourth_photo",
    "fifth_photo"
]


async def get_points_option():
    points_option = []
    for item in _checklist_items:
        point_buttons = KeyboardButton(text=f"{item}")
        points_option.append(point_buttons)

    return points_option


async def handle_points(message, state, next_point, point_with_comment, next_point_num, current_state_name):
    if message.text not in _checklist_items:
        await message.answer("Please choose an answer from the given options")
        return

    if message.text == "All clear":
        if next_point_num is None:
            await message.answer(
                f"Cool, we're done with the checklist",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [
                            KeyboardButton(text="View your information")
                        ]
                    ],
                    resize_keyboard=True
                )
            )
        else:
            await message.answer(f"Moving on to the next point {next_point_num}:")

        data_to_update = {current_state_name: "All clear"}
        await state.update_data(**data_to_update)
        await state.set_state(next_point)

    if message.text == "Leave a comment":
        await message.answer(
            "Write your comment:",
            reply_markup=ReplyKeyboardRemove()
        )

        await state.set_state(point_with_comment)


async def handle_points_with_comment(message, state, next_point, current_state_name):
    if message.photo:
        await message.answer("Please send only messages")
        return

    if 250 >= len(message.text) >= 10:
        await message.answer(
            f"Maybe want to attach a photo to this comment?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="Yes"),
                        KeyboardButton(text="No")
                    ]
                ],
                resize_keyboard=True
            )
        )

        data_to_update = {current_state_name: message.text}
        await state.update_data(**data_to_update)
        await state.set_state(next_point)

    elif len(message.text) > 250:
        await message.answer("The maximum allowed number of characters is 250")
    elif len(message.text) < 10:
        await message.answer("The minimum allowed number of characters is 10")
    else:
        await message.answer("I don't understand you :(")


async def last_point(message, state, next_point, next_point_num):
    if next_point_num is None:
        await message.answer(
            f"Cool, we're done with the checklist",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="View your information")
                    ]
                ],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            f"Moving on to the next point {next_point_num}:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[await get_points_option()],
                resize_keyboard=True
            )
        )

    await state.set_state(next_point)


async def handle_check_photo(message, state, next_point, next_point_num, state_handle_photo):
    if message.text not in ["Yes", "No"]:
        await message.answer("Please choose an answer from the given options")
        return

    if message.text == "Yes":
        await message.answer(
            "Then send me a picture :)",
            reply_markup=ReplyKeyboardRemove()
        )

        await state.set_state(state_handle_photo)

    if message.text == "No":
        await last_point(message, state, next_point, next_point_num)


async def handle_photo(message, state, next_point_num, next_point, current_state_name):
    if message.photo:
        if len(message.photo) <= 4:
            photo = message.photo[-1]
            file_id = photo.file_id

            data_to_update = {current_state_name: file_id}
            await state.update_data(**data_to_update)
            await last_point(message, state, next_point, next_point_num)
        else:
            await message.answer("Please send only one photo.")
    else:
        await message.answer("Please send a photo.")


async def get_format_data(message, state):
    data = await state.get_data()
    text_to_send = " "
    current_state = await state.get_state()
    for key, value in data.items():
        if key in photos:
            key = key.replace('_', ' ').capitalize()

            if current_state == Form.report:
                await message.answer(f"{key}")
                await bot.send_photo(chat_id=message.chat.id, photo=value)
            text_to_send += f"{key}: {value}\n"
        else:
            key = key.replace('_', ' ').capitalize()

            if current_state == Form.report:
                await message.answer(f"{key}: {value}")
            text_to_send += f"{key}: {value}\n"

    return text_to_send

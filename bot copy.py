from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiosqlite import connect
import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

API_TOKEN = "7572620497:AAG-K8QRbtT82uCv6hovcThlRyZKx9Qjcjg"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Переменные для хранения пользовательских данных
user_data = {}

# Список разрешённых администраторов по user_id
ALLOWED_ADMINS = [314485159, 987654321]  # Замените на реальные user_id администраторов

# Состояния для админов
class AdminStates(StatesGroup):
    waiting_for_parameter_value = State()
    waiting_for_new_value = State()

# Получение административных настроек
async def get_admin_settings():
    async with connect("admin.db") as db:
        cursor = await db.execute("SELECT * FROM admin_settings WHERE id = 1")
        data = await cursor.fetchone()
        return {
            "reception": data[1],
            "sorting": data[2],
            "storage": data[3],
            "labeling": data[4],
            "picking": data[5],
            "logistics": data[6],
        }

# Обновление административных настроек
async def update_admin_settings(setting, value):
    async with connect("admin.db") as db:
        await db.execute(f"UPDATE admin_settings SET {setting} = ? WHERE id = 1", (value,))
        await db.commit()

# Клавиатуры
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Рассчитать стоимость")],
            [KeyboardButton(text="Рассчитать объём")],
            [KeyboardButton(text="Изменить Количество и Срок хранения")],
            [KeyboardButton(text="Административная панель")],
        ],
        resize_keyboard=True
    )

def parameters_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Изменить Количество")],
            [KeyboardButton(text="Изменить Срок хранения")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Изменить Приёмка")],
            [KeyboardButton(text="Изменить Сортировка")],
            [KeyboardButton(text="Изменить Хранение")],
            [KeyboardButton(text="Изменить Стикеровка")],
            [KeyboardButton(text="Изменить Отбор")],
            [KeyboardButton(text="Изменить Логистика")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True
    )

# обработчик для кнопки "Рассчитать объём"
@dp.message(lambda message: "Рассчитать объём" in message.text)
async def calculate_volume(message: types.Message):
    try:
        user_params = user_data.get(message.from_user.id)
        if not user_params or "volume" not in user_params:
            await message.answer("Сначала введите длину, ширину и высоту через пробел.")
            return

        volume = user_params["volume"]
        await message.answer(f"Рассчитанный объём: {volume:.3f} м³.\nЕсли хотите пересчитать, то в поле сообщения введите длину, ширину и высоту.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

# Состояния для изменения параметров
class UserParameterStates(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_storage_days = State()

@dp.message(lambda message: "Изменить Количество и Срок хранения" in message.text)
async def change_parameters_menu(message: types.Message):
    await message.answer(
        "Выберите параметр, который хотите изменить:",
        reply_markup=parameters_keyboard()
    )

@dp.message(lambda message: "Изменить Количество" in message.text)
async def change_quantity(message: types.Message, state: FSMContext):
    await message.answer("Введите новое значение для количества (целое число):")
    await state.set_state(UserParameterStates.waiting_for_quantity)

@dp.message(UserParameterStates.waiting_for_quantity)
async def set_quantity(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите корректное целое число.")
        return

    user_data[message.from_user.id]["quantity"] = int(message.text)
    await state.clear()
    await message.answer(
        f"Количество обновлено: {user_data[message.from_user.id]['quantity']}",
        reply_markup=main_keyboard()
    )

@dp.message(lambda message: "Изменить Срок хранения" in message.text)
async def change_storage_days(message: types.Message, state: FSMContext):
    await message.answer("Введите новое значение для срока хранения (целое число):")
    await state.set_state(UserParameterStates.waiting_for_storage_days)

@dp.message(UserParameterStates.waiting_for_storage_days)
async def set_storage_days(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите корректное целое число.")
        return

    user_data[message.from_user.id]["storage_days"] = int(message.text)
    await state.clear()
    await message.answer(
        f"Срок хранения обновлен: {user_data[message.from_user.id]['storage_days']} дней",
        reply_markup=main_keyboard()
    )

# Команда /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_data[message.from_user.id] = {"quantity": 1, "storage_days": 15}
    await message.answer(
        "Добро пожаловать! Напишите длину, ширину, высоту (в см) через пробел.",
        reply_markup=main_keyboard()
    )
# Обработка параметров
@dp.message(lambda message: "Рассчитать стоимость" in message.text)
async def calculate_cost(message: types.Message):
    try:
        user_params = user_data.get(message.from_user.id)
        if not user_params or "volume" not in user_params:
            await message.answer("Сначала введите длину, ширину и высоту.")
            return

        admin_settings = await get_admin_settings()

        # Данные пользователя
        volume = user_params["volume"]
        quantity = user_params["quantity"]
        storage_days = user_params["storage_days"]

        # Расчет стоимости
        cost = (
            admin_settings["reception"] * volume +
            admin_settings["sorting"] * quantity +
            admin_settings["storage"] * storage_days * volume +
            admin_settings["labeling"] * quantity +
            admin_settings["picking"] * quantity +
            admin_settings["logistics"] * volume
        )

        await message.answer(
            f"Объем: {volume:.3f} м³\n"
            f"Количество: {quantity}\n"
            f"Срок хранения: {storage_days} дней\n\n"
            f"Итоговая стоимость: {cost:.2f} руб."
        )
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

# Ввод размеров
@dp.message(lambda msg: len(msg.text.split()) == 3 and all(part.isdigit() for part in msg.text.split()))
async def set_dimensions(message: types.Message):
    try:
        length, width, height = map(float, message.text.split())
        volume = (length * width * height) / 1000000  # Объем в м³
        user_data[message.from_user.id]["volume"] = volume
        await message.answer(
            f"Объем рассчитан: {volume:.3f} м³.\nТеперь вы можете рассчитать стоимость.",
            reply_markup=main_keyboard()
        )
    except ValueError:
        await message.answer("Введите три числа: длина, ширина и высота через пробел.")

# Административная панель
@dp.message(lambda message: "Административная панель" in message.text)
async def admin_panel(message: types.Message):
    # Проверка, является ли пользователь администратором
    if message.from_user.id not in ALLOWED_ADMINS:
        await message.answer("У вас нет прав доступа к административной панели.")
        return

    # Получаем текущие настройки из базы данных
    admin_settings = await get_admin_settings()

    # Выводим текущие значения настроек
    await message.answer(
        f"Текущие настройки:\n"
        f"Приёмка: {admin_settings['reception']}\n"
        f"Сортировка: {admin_settings['sorting']}\n"
        f"Хранение: {admin_settings['storage']}\n"
        f"Стикеровка: {admin_settings['labeling']}\n"
        f"Отбор: {admin_settings['picking']}\n"
        f"Логистика: {admin_settings['logistics']}\n\n"
        f"Выберите параметр для изменения:",
        reply_markup=admin_keyboard()
    )

@dp.message(lambda message: "Изменить " in message.text)
async def admin_change_parameter(message: types.Message, state: FSMContext):
    # Проверка, является ли пользователь администратором
    if message.from_user.id not in ALLOWED_ADMINS:
        await message.answer("У вас нет прав доступа к административной панели.")
        return

    param = message.text.split()[-1].lower()

    # Проверяем, какой параметр был выбран
    if param in ["приёмка", "сортировка", "хранение", "стикеровка", "отбор", "логистика"]:
        await state.update_data(parameter=param)  # Сохраняем выбранный параметр в состоянии
        await message.answer(f"Введите новое значение для {param.capitalize()}:")

@dp.message(lambda msg: msg.text.replace(".", "").isdigit())
async def admin_set_parameter(message: types.Message, state: FSMContext):
    # Проверка, является ли пользователь администратором
    if message.from_user.id not in ALLOWED_ADMINS:
        await message.answer("У вас нет прав доступа к административной панели.")
        return

    # Получаем состояние
    user_data = await state.get_data()
    param = user_data.get("parameter")  # Получаем выбранный параметр

    if param:
        param_map = {
            "приёмка": "reception",
            "сортировка": "sorting",
            "хранение": "storage",
            "стикеровка": "labeling",
            "отбор": "picking",
            "логистика": "logistics"
        }

        if param in param_map:
            param_field = param_map[param]

            try:
                # Обновляем значение в базе данных
                await update_admin_settings(param_field, float(message.text))
                await message.answer(f"{param.capitalize()} обновлено на {message.text}.", reply_markup=admin_keyboard())
            except ValueError:
                await message.answer("Введите корректное числовое значение.")
        else:
            await message.answer("Неверный параметр для обновления.")
    else:
        await message.answer("Не удалось найти параметр для обновления.")

# Обработка команды Назад
@dp.message(lambda message: "Назад" in message.text)
async def go_back(message: types.Message):
    await message.answer(
        "Главное меню\n\nНапишите длину, ширину, высоту (в см) через пробел.",
        reply_markup=main_keyboard()
    )

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
from phrases import (
    random_between, random_right, random_wrong,
    random_start, random_end, random_joke
)
import glob

FINAL_IMAGES = glob.glob("final_images/*")

API_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8760426828:AAFIIGAsDhQMWVol6TjjUVGa0OFNOLI4i1M"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()



QUESTIONS = [
    {
        "image": "images/diskett.jpg",
        "question": "Что изображено на картинке?",
        "options": ["Дискета", "Флешка", "CD-ROM"],
        "answer": "Дискета"
    },
    {
        "image": "images/icq.jpg",
        "question": "Какой это логотип?",
        "options": ["ICQ", "WhatsApp", "Viber"],
        "answer": "ICQ"
    },
    {
        "image": "images/kasset.jpg",
        "question": "Что это за носитель?",
        "options": ["Аудиокассета", "Кассета VHS", "Кассета для фото"],
        "answer": "Аудиокассета"
    },
    {
        "image": "images/tamagochi.jpg",
        "question": "Что это?",
        "options": ["Тамагочи", "Калькулятор", "Пейджер"],
        "answer": "Тамагочи"
    },
    {
        "image": "images/tetris.jpeg",
        "question": "Какая это игра?",
        "options": ["Тетрис", "Пакман", "Сапёр"],
        "answer": "Тетрис"
    },
    {
        "image": "images/slinki.jpg",
        "question": "Ну вот это точно знаете?",
        "options": ["Лизун", "Пакман", "Радуга слинки"],
        "answer": "Радуга слинки"
    },
    {
        "image": "images/siphon.jpg",
        "question": "В детстве было у всех..Ну почти у всех ☺?",
        "options": ["Сифон", "Космическая ракета", "Фигня какая-то"],
        "answer": "Сифон"
    },
    {
        "image": "images/film.jpg",
        "question": "Что это за штука, без которой раньше не было ни одной фотки?",
        "options": ["Фотоплёнка", "Кассета VHS", "Батарейка AA"],
        "answer": "Фотоплёнка"
    },
    {
        "image": "images/pager.jpg",
        "question": "Как называлась эта маленькая коробочка для сообщений?",
        "options": ["Пейджер", "Мини-радио", "Калькулятор"],
        "answer": "Пейджер"
    },
    {
        "image": "images/dendy.jpg",
        "question": "С какой приставки начинались игры у многих?",
        "options": ["Dendy", "PlayStation 2", "Xbox"],
        "answer": "Dendy"
    }
]


GLOBAL_STATS = {
    "total_users": 0,
    "total_attempts": 0,
    "scores": [],
    "questions": {i: {"correct": 0, "total": 0} for i in range(len(QUESTIONS))}
}

ADMIN_ID = 315030219  # Мой ID


WRONG_REACTIONS = [
    "Ой, почти! Но правильный ответ был другой. Зато вы — как SSD: ускоряете всё вокруг. 💫",
    "Неверно, но вы всё равно — как стабильный Wi‑Fi: держите всех на связи. 📶",
    "Хм, не то... но вы — как тетрис: всегда находите своё место. 🧩",
    "Не угадали, но вы — как светлая тема интерфейса: с вами всё становится ярче. ☀️",
    "Ошибка? Какая ошибка — вы же как идеальный код: вдохновляете! ✨",
    "Неправильно, но вы — как пасхалка в коде: приятный сюрприз. 🐣",
    "Не тот вариант, но вы — как автозаполнение: понимаете с полуслова. ⌨️",
    "Неверно, но вы — как горячие клавиши: ускоряете всё вокруг. ⚡",
    "Не то, но вы — как обновление системы: делаете день лучше. 🆙",
    "Неправильно, но вы — как крутой монитор: смотреть на вас — одно удовольствие. 🖥️"
]



COMPLIMENTS = [
    "Вы — как идеальный код: понятная, красивая и вдохновляющая. ✨",
    "Ваше настроение — как стабильный Wi‑Fi: держит всех на плаву. 📶💖",
    "Вы — как SSD: ускоряете всё вокруг. ⚡🚀",
    "Вы — как светлая тема интерфейса: с вами всё становится ярче. ☀️🌈",
    "Вы — как обновление системы: делаете день лучше, чем он был. 🆙💎",
    "Вы — как хороший алгоритм: оптимизируете всё, к чему прикасаетесь. 🎯🧩",
    "Вы — как надёжный сервер: на вас можно положиться. 🛡️🦾",
    "Вы — как идеальный UI: стильная, понятная и приятная. 🎀🎨",
    "Вы — как 5G: с вами мир открывается на максимальной скорости. 🌐🔥",
    "Вы — как Retina-дисплей: в вас идеально проработана каждая деталь. 🌟👁️",
    "Вы — как автозаполнение: понимаете меня с полуслова. ⌨️❤️",
    "Вы — как Docker-контейнер: отлично выглядите в любой среде. 🐳👗",
    "Вы — как горячие клавиши: с вами любая задача решается в два клика. ⌨️⚡",
    "Вы — как чистая архитектура: в вас всё на своих местах. 🏛️🕊️",
    "Вы — как открытый API: с вами легко и приятно взаимодействовать. 🤝🌸",
    "Вы — как успешный билд: редкое и бесконечно приятное событие. ✅🎉",
    "Вы — как идеальный бэкап: с вами я чувствую себя в безопасности. 💾🔒",
    "Вы — как редкий домен: уникальная и вас невозможно заменить. 👑🌍",
    "Вы — как права суперпользователя: перед вами открыты все двери. 🔑🚪",
    "Вы — как пасхалка в коде: самый приятный сюрприз за день. 🐣🎁",
    "Вы — как нейросеть: становитесь лучше с каждым днем. 🧠📈",
    "Вы — как профессиональный CSS: выглядите безупречно на любом фоне. 👗✨",
    "Вы — как оптоволокно: передаете свет и радость мгновенно. 💡⚡",
    "Вы — как мощный GPU: рендерите реальность в лучших красках. 🎮📽️",
    "Вы — как бесконечный цикл счастья: с вами не хочется выходить из системы. 🔄💞",
    "Вы — как отсутствие багов: само совершенство. 🐞❌💯",
    "Вы — как кнопка 'Домой': к вам всегда хочется вернуться. 🏠🗝️",
    "Вы — как квантовый компьютер: решаете задачи, непосильные другим. ⚛️🧬",
    "Вы — как высокоуровневый язык: изящная и невероятно эффективная. 📜🔝",
    "Вы — как стабильный релиз: на вас всегда можно рассчитывать. 📦🤝",
    "Вы — как темная тема: стильная, глубокая и бережете глаза. 🌙🖤",
    "Вы — как облачное хранилище: ваше доброе сердце не имеет границ. ☁️💓",
    "Вы — как первый результат в Google: именно то, что я искал. 🔍🥇",
    "Вы — как крутой стартап: вдохновляете на великие дела. 🚀💡",
    "Вы — как двухфакторная аутентификация: двойная порция надежности. 📲🔐",
    "Вы — как современный фреймворк: упрощаете жизнь всем вокруг. 🛠️🌿",
    "Вы — как идеальный рефакторинг: делаете мир вокруг чище. 🧹💎",
    "Вы — как высокая доступность (High Availability): всегда рядом в нужный момент. 🕙🎈",
    "Вы — как пинг 1 мс: реагируете на всё мгновенно. ⚡️🎧",
    "Вы — как Markdown: простая, лаконичная и очень удобная. 📝🧸",
    "Вы — как зашифрованный канал: наши секреты под надежной защитой. 🔐🤫",
    "Вы — как свежий коммит: привносите в жизнь новые смыслы. ➕🍀",
    "Вы — как умный дом: создаете уют нажатием одной кнопки. 🏠☕",
    "Вы — как идеальный хэш: такая, как вы — только одна. 🆔⭐️",
    "Вы — как качественный софт: работаете без перебоев и лишних слов. 💻👌",
    "Вы — как дополненная реальность: делаете этот мир интереснее. 🕶️🪄",
    "Вы — как крутой монитор: смотреть на вас — одно удовольствие. 🖥️😍",
    "Вы — как лицензионный ключ: открываете доступ к счастью. 🔑🔓",
    "Вы — как синхронизация: мы с вами на одной волне. 🔄🌊",
    "Вы — как мощный Power Bank: заряжаете всех своей энергией. 🔋⚡",
    "Вы — как идеальный лог: с вами всё ясно и прозрачно. 📄☀️",
    "Вы — как микросервисы: независимая, сильная и функциональная. 🦾🧩",
    "Вы — как блокчейн: ваше доверие невозможно подделать. ⛓️🤝",
    "Вы — как топовая видеокарта: тянете на себе всё самое красивое. 🖼️💅",
    "Вы — как функция обратного вызова: всегда возвращаетесь с хорошими новостями. 📞🔔",
    "Вы — как хорошо настроенная база данных: помните всё самое важное. 📚💌",
    "Вы — как быстрый поиск: находите путь к любому сердцу. 🔎💘",
    "Вы — как идеальная документация: с вами не возникает лишних вопросов. 📖✅",
    "Вы — как бесконечный скролл: вами можно любоваться вечно. 📱😻",
    "Вы — как режим инкогнито: умеете хранить тайны. 🕵️‍♀️👤",
    "Вы — как кроссплатформенность: находите общий язык со всеми. 🌍🤝",
    "Вы — как автотест: подтверждаете, что всё будет хорошо. ✔️🌈",
    "Вы — как мощный процессор: думаете быстрее всех. 🧠💨",
    "Вы — как root-доступ: вы главная в моей системе ценностей. 👑🚩"
]

# В памяти храним состояние пользователей: {user_id: {"q": idx, "correct": n}}
user_state = {}

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer(random_start())
    random_questions = random.sample(QUESTIONS, len(QUESTIONS))

    user_state[message.from_user.id] = {
        "q": 0,
        "correct": 0,
        "questions": random_questions
    }

    GLOBAL_STATS["total_attempts"] += 1
    GLOBAL_STATS["total_users"] += 1

    await send_question(message.from_user.id)


async def send_question(user_id: int):
    state = user_state.get(user_id)
    if state is None:
        return

    if random.random() < 0.4:
        await bot.send_message(user_id, random_between())

    q = state["questions"][state["q"]]

    kb = InlineKeyboardBuilder()
    for opt in q["options"]:
        kb.button(text=opt, callback_data=f"opt|{opt}")
    kb.adjust(1)

    image_path = q["image"]  # например "images/diskett.jpg"
    # Диагностика: отправим путь в лог, чтобы убедиться в корректности
    print("send_question: image_path =", image_path, "abs:", os.path.abspath(image_path))

    if not os.path.exists(image_path):
        await bot.send_message(user_id, "Ошибка: не найден файл изображения. Проверь папку images/ и имена файлов.")
        return

    # Используем FSInputFile для локального файла
    file_for_send = FSInputFile(image_path)
    await bot.send_photo(chat_id=user_id, photo=file_for_send, caption=q["question"], reply_markup=kb.as_markup())

@dp.callback_query(lambda c: c.data and c.data.startswith("opt|"))
async def process_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = user_state.get(user_id)
    if not state:
        await callback.answer("Сначала отправьте /start")
        return

    choice = callback.data.split("|", 1)[1]
    q_index = state["q"]
    q = state["questions"][q_index]

    GLOBAL_STATS["questions"][q_index]["total"] += 1

    if choice == q["answer"]:
        state["correct"] += 1
        GLOBAL_STATS["questions"][q_index]["correct"] += 1
        await bot.send_message(user_id, f"✅ {random_right()}")

    else:
        reaction = random.choice(WRONG_REACTIONS)
        await bot.send_message(user_id, f"❌ {random_wrong()}")


    state["q"] += 1
    await callback.answer()

    if state["q"] < len(state["questions"]):
        await asyncio.sleep(0.7)
        await send_question(user_id)

    else:
        score = state["correct"]
        GLOBAL_STATS["scores"].append(score)

        compliment = random.choice(COMPLIMENTS)
        await bot.send_message(
            user_id,
            f"Квиз завершён!\nВаш результат: {score} из {len(state['questions'])}.\n\n{compliment}"
        )


        if FINAL_IMAGES:
            img = FSInputFile(random.choice(FINAL_IMAGES))
            await bot.send_photo(user_id, img)


        kb = InlineKeyboardBuilder()
        kb.button(text="📊 Статистика", callback_data="stats")
        kb.button(text="🔁 Пройти ещё раз", callback_data="restart")
        kb.adjust(1)

        await bot.send_message(user_id, "Что дальше?", reply_markup=kb.as_markup())

        user_state.pop(user_id, None)


@dp.callback_query(lambda c: c.data == "restart")
async def restart_quiz(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    random_questions = random.sample(QUESTIONS, len(QUESTIONS))
    user_state[user_id] = {
        "q": 0,
        "correct": 0,
        "questions": random_questions
    }

    GLOBAL_STATS["total_attempts"] += 1

    await callback.answer()
    await bot.send_message(user_id, "Начнём заново!")
    await send_question(user_id)


@dp.callback_query(lambda c: c.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    await callback.answer()

    total = GLOBAL_STATS["total_users"]
    attempts = GLOBAL_STATS["total_attempts"]
    avg = round(sum(GLOBAL_STATS["scores"]) / len(GLOBAL_STATS["scores"]), 2) if GLOBAL_STATS["scores"] else 0

    question_stats = ""
    for i, q in enumerate(QUESTIONS):
        t = GLOBAL_STATS["questions"][i]["total"]
        c = GLOBAL_STATS["questions"][i]["correct"]
        pct = int((c / t) * 100) if t > 0 else 0
        question_stats += f"{i+1}. {pct}%\n"

    text = (
        f"📊 Статистика квиза:\n"
        f"— Участников: {total}\n"
        f"— Всего попыток: {attempts}\n"
        f"— Средний результат: {avg} из {len(QUESTIONS)}\n"
        f"— Процент правильных по вопросам:\n{question_stats}"
    )

    await bot.send_message(callback.from_user.id, text)


@dp.message(Command("admin"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    total = GLOBAL_STATS["total_users"]
    attempts = GLOBAL_STATS["total_attempts"]
    avg = round(sum(GLOBAL_STATS["scores"]) / len(GLOBAL_STATS["scores"]), 2) if GLOBAL_STATS["scores"] else 0

    await message.answer(
        f"Админ‑панель:\n"
        f"Пользователей: {total}\n"
        f"Попыток: {attempts}\n"
        f"Средний результат: {avg}"
    )



async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

# bot.py
# Полный файл Telegram-бота для викторины, предсказаний, аффирмаций, обратной связи и статистики.
# Требования: aiogram v3.x, файлы quiz_runner.py, questions_bank.py, predictions.py рядом.
# Перед запуском установите переменную окружения TG_BOT_TOKEN и замените ADMIN_IDS на ваш Telegram user_id.

import os
import json
import logging
import random
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
)
from aiogram.filters import Command
from datetime import datetime, timezone
from aiogram.exceptions import TelegramBadRequest

from quiz_runner import QuizSession, aggregate_stats
from questions_bank import find_image_for_question, TRAIT_RU
from predictions import get_prediction, get_n_predictions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = os.environ.get("TG_BOT_TOKEN")
if not API_TOKEN:
    logger.error("Environment variable TG_BOT_TOKEN is not set. Exiting.")
    raise SystemExit("Set TG_BOT_TOKEN environment variable before running the bot.")

# --- configuration ---
START_IMAGES_DIR = Path(__file__).parent / "start_images"
FEEDBACK_FILE = Path(__file__).parent / "feedback.json"
RESULTS_FILE = Path(__file__).parent / "results.json"
# Замените на ваш Telegram user_id (целое число), например {123456789}
ADMIN_IDS = {123456789}

# --- persistent keyboard (добавлены кнопки "Написать автору" и "Статистика") ---
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пройти психологический тест"), KeyboardButton(text="Получить предсказание")],
        [KeyboardButton(text="Аффирмация дня"), KeyboardButton(text="Получить 3 предсказания")],
        [KeyboardButton(text="Написать автору ✉️"), KeyboardButton(text="Статистика 📊")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# --- results storage helpers (robust) ---
def load_results() -> Dict:
    default = {"total": 0, "profiles": [], "button_clicks": {}, "subscribers": []}
    try:
        if not RESULTS_FILE.exists():
            return default
        raw = RESULTS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            logger.warning("results.json has unexpected type %s, resetting to default.", type(data).__name__)
            return default
        data.setdefault("total", 0)
        data.setdefault("profiles", [])
        if not isinstance(data["profiles"], list):
            data["profiles"] = []
        data.setdefault("button_clicks", {})
        if not isinstance(data["button_clicks"], dict):
            data["button_clicks"] = {}
        data.setdefault("subscribers", [])
        if not isinstance(data["subscribers"], list):
            data["subscribers"] = []
        return data
    except Exception:
        logger.exception("Failed to read or parse results.json, returning default structure.")
        return default


def save_results(data: Dict):
    try:
        RESULTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write results.json")


def record_button_click(name: str):
    data = load_results()
    if not isinstance(data, dict):
        logger.warning("load_results returned non-dict (%s). Replacing with default dict.", type(data).__name__)
        data = {"total": 0, "profiles": [], "button_clicks": {}, "subscribers": []}
    if "button_clicks" not in data or not isinstance(data["button_clicks"], dict):
        data["button_clicks"] = {}
    data["button_clicks"][name] = data["button_clicks"].get(name, 0) + 1
    save_results(data)


def record_profile(profile: Dict):
    data = load_results()
    if not isinstance(data, dict):
        data = {"total": 0, "profiles": [], "button_clicks": {}, "subscribers": []}
    data.setdefault("profiles", [])
    if not isinstance(data["profiles"], list):
        data["profiles"] = []
    data["profiles"].append(profile)
    data["total"] = len(data["profiles"])
    save_results(data)


# --- helper utilities ---
def make_answer_keyboard(question_id: int) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(text=str(v), callback_data=f"ans:{question_id}:{v}") for v in range(1, 6)]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def split_text(text: str, max_len: int = 1000):
    words = text.split()
    chunks = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + 1 > max_len:
            chunks.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += len(w) + 1
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def format_prediction_local(pred: str, name: Optional[str]) -> str:
    if not pred:
        return pred
    if name:
        if "{name}" in pred:
            return pred.replace("{name}", name)
        return f"{pred}"
    else:
        return pred.replace("{name}", "").strip()


# --- image sending with fallback ---
async def send_question_with_optional_image(bot: Bot, chat_id: int, q: Dict, reply_markup: Optional[InlineKeyboardMarkup] = None):
    caption = f"Вопрос {q['position']}/{q['total']}:\n{q['text']}"
    img_path = find_image_for_question(q)
    logger.info("find_image_for_question: id=%s scale=%s -> %s", q.get("id"), q.get("scale"), img_path)

    if img_path:
        try:
            file_obj = FSInputFile(img_path)
            await bot.send_photo(chat_id, photo=file_obj, caption=caption, reply_markup=reply_markup)
            logger.info("Image sent successfully for question id=%s", q.get("id"))
            return
        except Exception as e:
            logger.exception("Failed to send image %s for question id=%s: %s", img_path, q.get("id"), e)
            try:
                await bot.send_message(chat_id, f"Не удалось отправить картинку для вопроса {q.get('id')}. Показываю текст.")
            except Exception:
                logger.exception("Failed to send diagnostic message to user %s", chat_id)

    logger.info("Falling back to text for question id=%s", q.get("id"))
    await bot.send_message(chat_id, caption, reply_markup=reply_markup)


# --- feedback storage helpers ---
def _load_feedback():
    if not FEEDBACK_FILE.exists():
        return {"feedback": []}
    try:
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to read feedback.json, returning empty structure.")
        return {"feedback": []}


def _save_feedback(data: Dict):
    try:
        FEEDBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write feedback.json")




# --- feedback helpers (обновлённые) ---
def add_feedback(text: str, anonymous: bool, user: Optional[Any] = None) -> Dict:
    data = _load_feedback()
    next_id = 1 + max((item.get("id", 0) for item in data.get("feedback", [])), default=0)
    entry = {
        "id": next_id,
        "time": datetime.now(timezone.utc).isoformat(),
        "anonymous": bool(anonymous),
        "user_id": None if anonymous else (user.id if user else None),
        "username": None if anonymous else (user.full_name if user else None),
        "text": text,
        "handled": False
    }
    data.setdefault("feedback", []).append(entry)
    _save_feedback(data)
    return entry

async def _is_admin_reachable(bot: Bot, admin_id: int) -> bool:
    """
    Проверяем, можно ли писать администратору. В разных версиях aiogram разные исключения,
    поэтому ловим TelegramBadRequest и любые другие ошибки безопасно.
    """
    try:
        await bot.get_chat(admin_id)
        return True
    except TelegramBadRequest:
        # покрывает "chat not found" и похожие ошибки в большинстве версий aiogram
        return False
    except Exception:
        # логируем неожиданную ошибку и считаем админа недоступным
        logger.exception("Unexpected error while checking admin chat %s", admin_id)
        return False

async def _notify_admins_short(bot: Bot, admin_note: str):
    """
    Попытка уведомить всех админов; не падает при ошибках доставки.
    """
    for aid in list(ADMIN_IDS):
        try:
            reachable = await _is_admin_reachable(bot, aid)
            if not reachable:
                logger.warning("Admin %s seems unreachable or bot cannot message them. Skipping.", aid)
                continue
            await bot.send_message(aid, admin_note)
        except TelegramBadRequest as e:
            logger.warning("TelegramBadRequest when notifying admin %s: %s", aid, e)
        except Exception:
            logger.exception("Failed to notify admin %s about feedback", aid)




# --- UI for feedback ---
FEEDBACK_KB = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Анонимно 🕶️", callback_data="fb_mode:anon"),
     InlineKeyboardButton(text="С именем 💌", callback_data="fb_mode:withname")]
])

# --- handlers ---
async def cmd_start(message: Message):
    name = (message.from_user.first_name or "").strip()
    if name:
        welcome_text = (
            f"🎉 *Сегодня праздник, {name}!* 🎉\n\n"
            "Этот бот создан специально для тебя — немного тестов, предсказаний и тёплых слов. "
            "Выбери действие на клавиатуре ниже и получай радость! 🌸✨"
        )
    else:
        welcome_text = (
            "🎉 *Сегодня праздник!* 🎉\n\n"
            "Этот бот создан специально для тебя — немного тестов, предсказаний и тёплых слов. "
            "Выбери действие на клавиатуре ниже и получай радость! 🌸✨"
        )

    try:
        if START_IMAGES_DIR.is_dir():
            imgs = [p for p in START_IMAGES_DIR.iterdir() if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
            if imgs:
                chosen = random.choice(imgs)
                try:
                    file_obj = FSInputFile(str(chosen))
                    await message.answer_photo(photo=file_obj, caption=welcome_text, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
                    return
                except Exception:
                    logger.exception("Failed to send start image %s", chosen)
        await message.answer(welcome_text, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
    except Exception:
        try:
            await message.answer("Привет! Этот бот создан специально для тебя. Выбери действие на клавиатуре.", reply_markup=MAIN_KEYBOARD)
        except Exception:
            logger.exception("Failed to send start message")


async def cmd_quiz(message: Message, sessions: Dict[int, QuizSession]):
    user_id = message.from_user.id
    session = QuizSession(num_questions=10)
    sessions[user_id] = session
    q = session.next_question()
    if not q:
        await message.answer("Не удалось сформировать вопросы. Попробуйте позже.")
        return
    await send_question_with_optional_image(message.bot, message.chat.id, q, reply_markup=make_answer_keyboard(q["id"]))


async def process_answer(callback: CallbackQuery, sessions: Dict[int, QuizSession], bot: Bot):
    user_id = callback.from_user.id
    try:
        _, qid_str, val_str = callback.data.split(":")
        qid = int(qid_str); val = int(val_str)
    except Exception:
        await callback.answer("Неверные данные.", show_alert=True)
        return

    session = sessions.get(user_id)
    if not session:
        await callback.answer("Сессия не найдена. Запустите тест.", show_alert=True)
        return

    try:
        compliment = session.record_answer(qid, val)
    except Exception as e:
        logger.exception("Error recording answer for user %s: %s", user_id, e)
        await callback.answer("Ошибка записи ответа.", show_alert=True)
        return

    await callback.answer()
    if compliment:
        await bot.send_message(user_id, f"→ {compliment}")

    if session.has_next():
        q = session.next_question()
        await send_question_with_optional_image(bot, user_id, q, reply_markup=make_answer_keyboard(q["id"]))
    else:
        result = session.finalize(name=callback.from_user.full_name or "anonymous")
        profile = result.get("profile_text", "Ошибка формирования профиля.")
        try:
            record_profile({"user_id": user_id, "profile": result})
        except Exception:
            logger.exception("Failed to record profile for user %s", user_id)
        for chunk in split_text(profile, 1000):
            await bot.send_message(user_id, chunk)
        sessions.pop(user_id, None)


async def handle_prediction(message: Message):
    record_button_click("Получить предсказание")
    name = (message.from_user.first_name or "").strip()
    pred = get_prediction()
    pred = format_prediction_local(pred, name)
    if name:
        reply = f"🔮 *Твоё предсказание, {name}*:\n\n{pred}\n\n✨ Совет от бота: улыбнись — это украшает любую ситуацию 😘"
    else:
        reply = f"🔮 *Твоё предсказание*:\n\n{pred}\n\n✨ Совет от бота: улыбнись — это украшает любую ситуацию 😘"
    await message.answer(reply, parse_mode="Markdown")


async def handle_prediction_three(message: Message):
    record_button_click("Получить 3 предсказания")
    name = (message.from_user.first_name or "").strip()
    preds = get_n_predictions(3)
    formatted = [format_prediction_local(p, name) for p in preds]
    header = f"🔮 *Три предсказания для {name}*:\n\n" if name else "🔮 *Три предсказания для тебя:*\n\n"
    text = header + "\n\n".join(f"• {p}" for p in formatted) + "\n\n💫 Выбери то, что греет душу."
    await message.answer(text, parse_mode="Markdown")


async def handle_affirmation(message: Message):
    record_button_click("Аффирмация дня")
    name = (message.from_user.first_name or "").strip()
    affs = [
        f"🌞 {name}, ты достойна любви и уважения. Сегодня — твой день." if name else "🌞 Ты достойна любви и уважения. Сегодня — твой день.",
        f"🌸 {name}, твоя мягкость — это сила. Доверься себе." if name else "🌸 Твоя мягкость — это сила. Доверься себе.",
        f"✨ {name}, каждый твой шаг — это движение вперёд. Горжусь тобой." if name else "✨ Каждый твой шаг — это движение вперёд. Горжусь тобой.",
        f"💪 {name}, ты справишься — у тебя есть всё, что нужно." if name else "💪 Ты справишься — у тебя есть всё, что нужно.",
        f"🌷 {name}, позволь себе отдых — это часть силы." if name else "🌷 Позволь себе отдых — это часть силы.",
        "🍵 Маленькая пауза с чаем делает день добрее. Побалуй себя.",
        "💅 Ты достойна заботы — начни с малого и почувствуешь разницу."
    ]
    await message.answer(random.choice(affs))


async def handle_gift_for_her(message: Message):
    record_button_click("Подарок для неё")
    tips = [
        "Мини‑ритуал: 10 минут без телефона с чаем и плейлистом 🎧🍵",
        "Совет: сделай мини‑спа — маска для лица и любимая музыка 🛁🎶",
        "Идея: напиши себе письмо благодарности и спрячь на неделю 💌"
    ]
    await message.answer(random.choice(tips))


async def cmd_stats(message: Message):
    stats = aggregate_stats()
    stored = load_results()
    total_saved = stored.get("total", 0)
    lines = [
        f"📌 Всего участников (сессии): {stats.get('total', 0)}",
        f"💾 Профилей сохранено: {total_saved}",
        "",
        "📈 Распределение доминирующих черт:"
    ]
    dominant_counts = stats.get("dominant_counts", {})
    total = stats.get("total", 0) or 0
    for eng_trait, count in dominant_counts.items():
        ru = TRAIT_RU.get(eng_trait, eng_trait)
        pct = round(count / total * 100, 1) if total else 0.0
        lines.append(f"  • {ru}: {count} ({pct}%)")
    lines.append("")
    lines.append("🔘 Клики по кнопкам (локально):")
    for k, v in load_results().get("button_clicks", {}).items():
        lines.append(f"  • {k}: {v}")
    await message.answer("\n".join(lines))



async def cmd_full_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    stats = aggregate_stats()
    total = stats.get("total", 0)
    dominant_counts = stats.get("dominant_counts", {})
    lines = [f"📊 Всего участников: {total}", ""]
    if total:
        max_trait = None
        max_count = 0
        lines.append("📈 Распределение доминирующих черт:")
        for trait, cnt in dominant_counts.items():
            ru = TRAIT_RU.get(trait, trait)
            pct = round(cnt / total * 100, 1) if total else 0
            lines.append(f"  • {ru}: {cnt} ({pct}%)")
            if cnt > max_count:
                max_count = cnt
                max_trait = trait
        if max_trait:
            ru_max = TRAIT_RU.get(max_trait, max_trait)
            lines.append("")
            lines.append(f"🏆 В большинстве: {ru_max} — {max_count} человек ({round(max_count/total*100,1)}%)")
    else:
        lines.append("Нет данных для анализа.")
    await message.answer("\n".join(lines))



# --- feedback flow state ---
sessions_feedback: Dict[int, Dict] = {}


async def cmd_feedback_start(message: Message):
    await message.answer("Выберите режим отправки сообщения автору:", reply_markup=FEEDBACK_KB)


async def cb_feedback_mode(callback: CallbackQuery):
    mode = callback.data.split(":")[1]
    await callback.answer()
    sessions_feedback[callback.from_user.id] = {"anonymous": (mode == "anon")}
    await callback.message.answer("Напишите ваше сообщение. Оно будет отправлено автору бота. Можно коротко и тепло ❤️")


async def handle_feedback_text(message: Message):
    s = sessions_feedback.pop(message.from_user.id, None)
    if not s:
        await message.answer("Сначала выберите режим через кнопку 'Написать автору' или команду /feedback.")
        return
    entry = add_feedback(message.text, anonymous=s.get("anonymous", True), user=message.from_user)
    if entry["anonymous"]:
        await message.answer("Спасибо! Ваше анонимное сообщение отправлено автору. 🌸")
    else:
        await message.answer("Спасибо! Ваше сообщение отправлено автору. 💌")
    # уведомление админу (короткое)
    try:
        admin_note = f"Новое сообщение #{entry['id']} (анонимно)" if entry["anonymous"] else f"Новое сообщение #{entry['id']} от {entry.get('username')}"
        bot = message.bot
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(aid, admin_note)
            except Exception:
                logger.exception("Failed to notify admin %s about feedback", aid)
    except Exception:
        logger.exception("Failed to send admin notification for feedback")


async def cmd_view_feedback(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    data = _load_feedback().get("feedback", [])
    if not data:
        await message.answer("Сообщений пока нет.")
        return
    lines = []
    for item in data[-20:]:
        if item.get("anonymous"):
            lines.append(f"#{item['id']} [{item['time']}] (анонимно): {item['text']}")
        else:
            lines.append(f"#{item['id']} [{item['time']}] from {item.get('username')} ({item.get('user_id')}): {item['text']}")
    text = "\n\n".join(lines)
    for chunk in split_text(text, 3000):
        await message.answer(chunk)


async def cmd_mark_handled(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Использование: /mark_handled <id>")
        return
    try:
        id_to_mark = int(parts[1])
    except Exception:
        await message.answer("Неверный id.")
        return
    data = _load_feedback()
    for item in data.get("feedback", []):
        if item.get("id") == id_to_mark:
            item["handled"] = True
            _save_feedback(data)
            await message.answer(f"Сообщение #{id_to_mark} помечено как обработанное.")
            return
    await message.answer("Сообщение не найдено.")


# --- main: create bot, dispatcher, register handlers, start polling ---
async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(bot=bot)
    sessions: Dict[int, QuizSession] = {}

    # register handlers
    dp.message.register(cmd_start, Command(commands=["start", "help"]))

    # quiz and buttons
    async def _quiz_wrapper(message: Message):
        await cmd_quiz(message, sessions)

    async def _prediction_wrapper(message: Message):
        await handle_prediction(message)

    async def _prediction3_wrapper(message: Message):
        await handle_prediction_three(message)

    async def _affirmation_wrapper(message: Message):
        await handle_affirmation(message)

    async def _gift_wrapper(message: Message):
        await handle_gift_for_her(message)

    dp.message.register(_quiz_wrapper, lambda m: getattr(m, "text", None) == "Пройти психологический тест")
    dp.message.register(_prediction_wrapper, lambda m: getattr(m, "text", None) == "Получить предсказание")
    dp.message.register(_prediction3_wrapper, lambda m: getattr(m, "text", None) == "Получить 3 предсказания")
    dp.message.register(_affirmation_wrapper, lambda m: getattr(m, "text", None) == "Аффирмация дня")
    dp.message.register(_gift_wrapper, lambda m: getattr(m, "text", None) == "Подарок для неё")

    # new menu buttons handlers
    dp.message.register(cmd_feedback_start, lambda m: getattr(m, "text", None) == "Написать автору ✉️")
    dp.message.register(cmd_stats, lambda m: getattr(m, "text", None) == "Статистика 📊")

    dp.message.register(cmd_stats, Command(commands=["stats"]))
    dp.message.register(cmd_full_stats, Command(commands=["full_stats"]))

    # feedback handlers
    dp.message.register(cmd_feedback_start, Command(commands=["feedback"]))
    dp.callback_query.register(cb_feedback_mode, lambda c: c.data and c.data.startswith("fb_mode:"))
    dp.message.register(handle_feedback_text, lambda m: m.text and m.from_user.id in sessions_feedback)
    dp.message.register(cmd_view_feedback, Command(commands=["view_feedback"]))
    dp.message.register(cmd_mark_handled, Command(commands=["mark_handled"]))

    # callback for answers
    async def _answer_wrapper(callback: CallbackQuery):
        await process_answer(callback, sessions, bot)
    dp.callback_query.register(_answer_wrapper, lambda c: c.data and c.data.startswith("ans:"))

    # callback for feedback mode (inline buttons)
    dp.callback_query.register(cb_feedback_mode, lambda c: c.data and c.data.startswith("fb_mode:"))

    # set bot commands (optional, best-effort)
    from aiogram.types import BotCommand
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="feedback", description="Написать автору"),
            BotCommand(command="stats", description="Краткая статистика"),
            BotCommand(command="full_stats", description="Полная статистика (админ)")
        ])
    except Exception:
        logger.exception("Failed to set bot commands")

    try:
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

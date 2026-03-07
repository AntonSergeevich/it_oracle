# quiz_runner.py
# Лёгкий игровой раннер для викторины Big Five (игривый стиль + комплименты)
# Полностью переписанный файл: устойчивый к разным форматам results.json,
# поддерживает оба варианта вызова save_result, аккуратно сохраняет и агрегирует статистику.

import random
import json
import os
from typing import List, Dict, Tuple, Any, Optional
from pathlib import Path

from questions_bank import QUESTIONS  # ожидается, что файл рядом

RESULTS_PATH = Path(__file__).parent / "results.json"
SCALES = ["Extraversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness"]


def select_questions_for_session(num_questions: int = 10) -> List[Dict]:
    if num_questions <= 0:
        raise ValueError("num_questions must be > 0")
    pool = QUESTIONS.copy()
    if num_questions >= len(pool):
        return pool.copy()
    return random.sample(pool, num_questions)


def answer_level_label(value: int) -> str:
    if value <= 2:
        return "low"
    if value == 3:
        return "mid"
    return "high"


def format_compliment_for_question(q: Dict, value: int) -> str:
    try:
        lvl = answer_level_label(value)
        comps = q.get("compliments", {}) or {}
        arr = comps.get(lvl) or comps.get("mid") or []
        if not arr:
            return ""
        return random.choice(arr)
    except Exception:
        return ""


def score_answers(answers: List[Tuple[Dict, int]]) -> Tuple[Dict[str, int], Dict[str, float]]:
    raw = {s: 0 for s in SCALES}
    counts = {s: 0 for s in SCALES}
    for q, val in answers:
        scale = q.get("scale")
        if scale not in SCALES:
            continue
        rev = q.get("reverse", False)
        if rev:
            val = 6 - val
        raw[scale] += val
        counts[scale] += 1
    percents: Dict[str, float] = {}
    for s in SCALES:
        max_possible = counts[s] * 5 if counts[s] else 1
        perc = round(raw[s] / max_possible * 100, 1) if max_possible else 0.0
        percents[s] = perc
    return raw, percents


def interpret_percents(percents: Dict[str, float]) -> Tuple[Dict[str, str], str]:
    desc: Dict[str, str] = {}
    for s, p in percents.items():
        if p <= 33:
            level = "Низкий"
        elif p <= 66:
            level = "Средний"
        else:
            level = "Высокий"
        desc[s] = level
    # Если percents пустой, доминирующая черта — пустая строка
    dominant = max(percents.items(), key=lambda x: x[1])[0] if percents else ""
    return desc, dominant


def generate_humorous_profile(percents: Dict[str, float],
                              desc_levels: Dict[str, str],
                              dominant: str,
                              name: Optional[str] = None) -> str:
    """
    Формирует шутливо‑поддерживающий профиль на русском с эмодзи.
    - percents: {"Extraversion": 80.0, ...}
    - desc_levels: {"Extraversion": "Высокий", ...}
    - dominant: ключ доминирующей черты, например "Openness"
    - name: опционально — имя пользователя
    Возвращает текст в Markdown.
    """
    TRAIT_RU = {
        "Extraversion": "Экстраверсия",
        "Agreeableness": "Доброжелательность",
        "Conscientiousness": "Добросовестность",
        "Neuroticism": "Невротизм",
        "Openness": "Открытость"
    }
    EMOJI = {
        "Extraversion": "✨",
        "Agreeableness": "🤍",
        "Conscientiousness": "📋",
        "Neuroticism": "🌀",
        "Openness": "🎨"
    }

    # Персонализация заголовка
    header_name = f", {name}" if name else ""
    lines = []
    lines.append(f"💖 *Твой профиль{header_name}*")
    lines.append("")  # пустая строка

    # Краткая сводка по шкалам (строго по порядку)
    order = ["Extraversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness"]
    for key in order:
        ru = TRAIT_RU.get(key, key)
        emoji = EMOJI.get(key, "")
        pct = percents.get(key, 0.0)
        level = desc_levels.get(key, "—")
        lines.append(f"{emoji} *{ru}*: {pct:.1f}% — _{level}_")

    lines.append("")  # пустая строка

    # Описание доминирующей черты — шутливо и поддерживающе
    profiles_ru = {
        "Extraversion": "Ты — источник энергии: в компании ты как лампочка — зажёгся, и всем светло. 😄",
        "Agreeableness": "Ты — тёплый плед в холодный день: рядом с тобой уютно и спокойно. 🤗",
        "Conscientiousness": "Ты — живой планировщик: списки у тебя в порядке, и мир тихо аплодирует. ✅",
        "Neuroticism": "Ты глубоко чувствуешь — это как иметь внутренний радар эмоций. Береги себя и включай паузу. 🌿",
        "Openness": "Ты — коллекционер идей: мир для тебя — большая творческая мастерская. ✨"
    }

    dom_ru = TRAIT_RU.get(dominant, dominant)
    lines.append(f"🏅 *Доминирующая черта*: *{dom_ru}*")
    lines.append(profiles_ru.get(dominant, "Ты — уникальный и замечательный человек. 🌟"))

    lines.append("")  # пустая строка

    # Шутливые комплименты и поддержка, зависящие от доминирующей черты
    compliments = {
        "Extraversion": [
            "Твоя энергия заразительна — используй её с умом (и с перерывами на чай). ☕️😄",
            "Ты умеешь заводить людей — даже кактус в углу начинает танцевать. 🌵🕺"
        ],
        "Agreeableness": [
            "Твоя доброта — как бесплатный Wi‑Fi: все тянутся и благодарят. 📶🤍",
            "Ты умеешь слушать — и это редкий супер‑навык. 👂✨"
        ],
        "Conscientiousness": [
            "Ты доводишь дела до конца — даже носки у тебя в порядке. 🧦🏆",
            "Планируешь так, что календарь просит автограф. 🗓️✍️"
        ],
        "Neuroticism": [
            "Твоя чувствительность — это глубина. Немного дыхалки и мемов — и всё ок. 😌🫧",
            "Ты замечаешь важные детали — мир благодаря этому богаче. 🔎💛"
        ],
        "Openness": [
            "Твои идеи — как фейерверк: ярко, неожиданно и красиво. 🎆🧠",
            "Ты видишь мир иначе — и это делает его интереснее. 🌈✨"
        ]
    }
    advices = {
        "Extraversion": "Совет: иногда выключай микрофон и включай плед — перезарядка творит чудеса. 🛋️",
        "Agreeableness": "Совет: заботься о своих границах — это тоже акт любви к себе. 🛡️💖",
        "Conscientiousness": "Совет: добавь немного спонтанности — маленькое приключение не повредит. 🎈",
        "Neuroticism": "Совет: глубокий вдох, любимая песня и 5 минут тишины — и ты снова в строю. 🎧🌬️",
        "Openness": "Совет: выбери одну идею и доведи её до конца — это даст радость и гордость. 📝🚀"
    }

    comp_list = compliments.get(dominant, ["Ты прекрасны именно такой, какая ты есть. 🌸"])
    comp = random.choice(comp_list)
    advice = advices.get(dominant, "Будь собой и улыбайся чаще — это уже много значит. 😊")

    lines.append(f"💬 *Комплимент*: {comp}")
    lines.append(f"💡 *Совет*: {advice}")

    lines.append("")  # пустая строка
    lines.append("🌸 *Ты заслуживаешь заботы и маленьких радостей каждый день.*")
    lines.append("✨ Если хочешь, могу прислать короткую аффирмацию прямо сейчас — скажи «да» и я подберу. 💌")

    return "\n".join(lines)




# ----------------------------
# Устойчивое сохранение результатов
# ----------------------------
def _write_results_data(data: Any) -> None:
    RESULTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_results_data() -> Optional[Any]:
    if not RESULTS_PATH.exists():
        return None
    try:
        raw = RESULTS_PATH.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


def save_result(*args, **kwargs) -> None:
    """
    Универсальная функция сохранения результата.
    Поддерживает:
      - save_result(entry_dict)
      - save_result(name, percents, dominant, answers_meta)
      - save_result(name=..., percents=..., dominant=..., answers_meta=...)
    Сохраняет в results.json, поддерживает существующие форматы (list или dict).
    """
    # Собираем entry из аргументов
    entry: Dict[str, Any]
    if len(args) == 1 and isinstance(args[0], dict):
        entry = args[0]
    elif len(args) == 4:
        name, percents, dominant, answers_meta = args
        entry = {
            "name": name,
            "percents": percents,
            "dominant": dominant,
            "answers_meta": answers_meta
        }
    elif {"name", "percents", "dominant", "answers_meta"}.issubset(set(kwargs.keys())):
        entry = {
            "name": kwargs.get("name"),
            "percents": kwargs.get("percents"),
            "dominant": kwargs.get("dominant"),
            "answers_meta": kwargs.get("answers_meta"),
        }
    else:
        # Неподдерживаемый формат вызова — логируем и выходим
        try:
            import logging
            logging.getLogger(__name__).warning("save_result: unsupported args %s %s", args, kwargs)
        except Exception:
            pass
        return

    data = _load_results_data()

    # Если файл пустой/невалидный — создаём корректную структуру (dict с profiles)
    if data is None:
        new_data = {"total": 0, "profiles": [entry], "button_clicks": {}, "subscribers": []}
        new_data["total"] = len(new_data["profiles"])
        _write_results_data(new_data)
        return

    # Если файл содержит список — добавляем запись в список
    if isinstance(data, list):
        data.append(entry)
        _write_results_data(data)
        return

    # Если файл содержит словарь — добавляем в profiles или results
    if isinstance(data, dict):
        if "profiles" in data and isinstance(data["profiles"], list):
            data["profiles"].append(entry)
            data["total"] = len(data["profiles"])
            _write_results_data(data)
            return
        if "results" in data and isinstance(data["results"], list):
            data["results"].append(entry)
            _write_results_data(data)
            return
        # иначе создаём поле "results"
        data.setdefault("results", [])
        if isinstance(data["results"], list):
            data["results"].append(entry)
            _write_results_data(data)
            return

    # На всякий случай: перезаписываем корректным списком
    _write_results_data([entry])


def aggregate_stats() -> Dict:
    """
    Возвращает агрегированную статистику:
      - total: количество записей
      - dominant_counts: словарь подсчёта доминирующих черт
      - avg_percents: средние проценты по шкалам
    Поддерживает разные форматы results.json (list или dict с profiles/results).
    """
    data = _load_results_data()
    if data is None:
        return {"total": 0, "dominant_counts": {}, "avg_percents": {}}

    # Нормализуем список записей
    records: List[Dict] = []
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        if "profiles" in data and isinstance(data["profiles"], list):
            records = data["profiles"]
        elif "results" in data and isinstance(data["results"], list):
            records = data["results"]
        else:
            # Попробуем найти любой список внутри словаря
            for v in data.values():
                if isinstance(v, list):
                    records = v
                    break

    total = len(records)
    dominant_counts = {s: 0 for s in SCALES}
    totals = {s: 0.0 for s in SCALES}

    for entry in records:
        if not isinstance(entry, dict):
            continue
        dom = entry.get("dominant") or entry.get("dominant_trait") or entry.get("dominant", "")
        if dom in dominant_counts:
            dominant_counts[dom] += 1
        perc = entry.get("percents") or entry.get("percentages") or {}
        for s in SCALES:
            try:
                totals[s] += float(perc.get(s, 0.0))
            except Exception:
                totals[s] += 0.0

    avg_percents = {s: round(totals[s] / total, 1) if total else 0.0 for s in SCALES}
    return {"total": total, "dominant_counts": dominant_counts, "avg_percents": avg_percents}


class QuizSession:
    def __init__(self, num_questions: int = 10):
        # Ограничиваем num_questions реальным количеством вопросов в банке
        max_q = min(num_questions, len(QUESTIONS))
        self.questions = select_questions_for_session(max_q)
        self.index = 0
        self.answers: List[Tuple[Dict, int]] = []
        self.answers_meta: List[Dict] = []

    def next_question(self) -> Dict:
        if self.index >= len(self.questions):
            return {}
        q = self.questions[self.index]
        payload = {
            "position": self.index + 1,
            "total": len(self.questions),
            "id": q.get("id"),
            "text": q.get("text", ""),
            "scale": q.get("scale", None),
            "reverse": q.get("reverse", False),
            "image_prompt": q.get("image_prompt", "")
        }
        return payload

    def record_answer(self, question_id: int, value: int) -> str:
        if self.index >= len(self.questions):
            raise IndexError("All questions already answered")
        q = self.questions[self.index]
        # Если id не совпадает — ищем вопрос в сессии (поддержка callback mismatch)
        if q.get("id") != question_id:
            found = next((x for x in self.questions if x.get("id") == question_id), None)
            if not found:
                raise ValueError("Question id not in this session")
            q = found
        if not (1 <= value <= 5):
            raise ValueError("Answer value must be 1..5")
        self.answers.append((q, value))
        self.answers_meta.append({"id": q.get("id"), "text": q.get("text"), "scale": q.get("scale"), "value": value})
        comp = format_compliment_for_question(q, value)
        self.index += 1
        return comp

    def has_next(self) -> bool:
        return self.index < len(self.questions)

    def finalize(self, name: str = "anonymous") -> Dict:
        raw, percents = score_answers(self.answers)
        levels, dominant = interpret_percents(percents)
        profile_text = generate_humorous_profile(percents, levels, dominant)
        # Сохраняем результат (save_result поддерживает разные сигнатуры)
        try:
            save_result(name, percents, dominant, self.answers_meta)
        except Exception:
            # В крайнем случае — сохраняем как единый словарь
            try:
                save_result({
                    "name": name,
                    "percents": percents,
                    "dominant": dominant,
                    "answers_meta": self.answers_meta
                })
            except Exception:
                pass
        return {
            "percents": percents,
            "levels": levels,
            "dominant": dominant,
            "profile_text": profile_text
        }

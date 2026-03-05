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


def generate_humorous_profile(percents: Dict[str, float], desc_levels: Dict[str, str], dominant: str) -> str:
    """
    Возвращает текст профиля с эмодзи и более «женскими» комплиментами.
    Подходит для вставки в Telegram (короткие строки, эмодзи, тёплый тон).
    """
    lines: List[str] = []
    lines.append("💖 *Твой игровой профиль (Big Five, шутливый формат):*\n")
    # краткая сводка по шкалам с эмодзи
    scale_emojis = {
        "Extraversion": "✨",
        "Agreeableness": "🌷",
        "Conscientiousness": "📋",
        "Neuroticism": "🕊️",
        "Openness": "🎨"
    }
    for s in SCALES:
        emoji = scale_emojis.get(s, "")
        pct = percents.get(s, 0.0)
        level = desc_levels.get(s, "—")
        lines.append(f"{emoji} *{s}*: {pct}% — _{level}_")

    lines.append("")  # пустая строка

    # более тёплые, женские описания
    profiles = {
        "Extraversion": (
            "✨ *Солнечная общительность*: Ты — душа компании и вдохновляешь людей вокруг. "
            "Твоя энергия заразительна; рядом с тобой хочется смеяться и жить ярче. 💃🌟"
        ),
        "Agreeableness": (
            "🌷 *Тёплая поддержка*: Ты умеешь слышать и обнимать словом. "
            "Твоя доброта делает мир мягче — и это редкий, ценный дар. 🤍🌸"
        ),
        "Conscientiousness": (
            "📋 *Чудо‑организатор*: Ты умеешь доводить дела до конца и при этом оставаться очаровательной. "
            "Твоя аккуратность — это забота о себе и о других. 🕯️✨"
        ),
        "Neuroticism": (
            "🕊️ *Чувствительная душа*: Ты глубоко чувствуешь мир — это делает тебя тонким и внимательным человеком. "
            "Немного заботы о себе — и твоя сила проявится ещё ярче. 🌿💗"
        ),
        "Openness": (
            "🎨 *Искренняя творческая*: Ты видишь мир иначе и умеешь превращать идеи в красоту. "
            "Твои мысли вдохновляют и пробуждают любопытство. ✨🖌️"
        )
    }

    lines.append(f"🏅 *Доминирующая черта*: *{dominant}*")
    lines.append(profiles.get(dominant, "Ты — уникальный коктейль качеств, и это прекрасно! 🌈"))

    lines.append("")  # пустая строка

    # персонализированные комплименты (женские акценты)
    compliments_for_dominant = {
        "Extraversion": [
            "Твоя улыбка — магнит для хороших людей. 😊",
            "Ты умеешь зажечь любую комнату — и это талант."
        ],
        "Agreeableness": [
            "Твоя доброта лечит — не забывай наполнять себя тоже. 🌸",
            "Ты — тот человек, к которому хочется вернуться."
        ],
        "Conscientiousness": [
            "Твоя аккуратность — это проявление любви к себе. 💅",
            "Ты умеешь превращать планы в маленькие праздники."
        ],
        "Neuroticism": [
            "Твоя чувствительность — это глубина, которая делает тебя настоящей. 🌊",
            "Ты замечаешь детали, которые другие пропускают — это дар."
        ],
        "Openness": [
            "Твоя фантазия делает мир ярче — не бойся делиться идеями. ✨",
            "Ты — вдохновение для тех, кто рядом."
        ]
    }

    # добавляем 1–2 комплимента и совет с эмодзи
    comps = compliments_for_dominant.get(dominant, ["Ты прекрасна именно такой, какая ты есть. 🌺"])
    lines.append("💬 *Комплимент для тебя:* " + random.choice(comps))
    advice = {
        "Extraversion": "Совет: выдели минуту для себя — и твоя энергия станет ещё чище. ☕🌿",
        "Agreeableness": "Совет: заботься о своих границах — это тоже акт любви. 🛡️💖",
        "Conscientiousness": "Совет: позволь себе спонтанность — маленькое приключение не повредит. 🍦✨",
        "Neuroticism": "Совет: дыхательная пауза и любимая песня — твоя мини‑перезагрузка. 🎧🌬️",
        "Openness": "Совет: выбери одну идею и доведи её до конца — это даст радость. 📝🌟"
    }
    lines.append(advice.get(dominant, "Совет: будь собой и улыбайся чаще. 😘"))

    # завершающая тёплая подпись
    lines.append("")
    lines.append("🌸 *Ты заслуживаешь заботы и маленьких радостей каждый день.*")

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

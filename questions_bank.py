# questions_bank.py
# Банк из 15 вопросов для лёгкого игрового теста Big Five.
# Поля каждого вопроса:
#  - id: int
#  - text: str
#  - scale: "Extraversion" | "Agreeableness" | "Conscientiousness" | "Neuroticism" | "Openness"
#  - reverse: bool
#  - compliments: dict with keys "low","mid","high"
#
# Утилиты:
#  - SCALE_SHORT: словарь для кратких меток шкал
#  - find_image_for_question(question, images_dir='images', exts=('.jpg','.png')) -> str|None
#    возвращает абсолютный путь к существующему файлу или None, если файл не найден.

import os
from typing import Dict, List, Optional

SCALE_SHORT = {
    "Extraversion": "extraversion",
    "Agreeableness": "agreeableness",
    "Conscientiousness": "conscientiousness",
    "Neuroticism": "neuroticism",
    "Openness": "openness",
}

# Русские названия шкал для вывода
TRAIT_RU = {
    "Extraversion": "Экстраверсия",
    "Agreeableness": "Доброжелательность",
    "Conscientiousness": "Добросовестность",
    "Neuroticism": "Невротизм",
    "Openness": "Открытость"
}

QUESTIONS: List[Dict] = [
    {
        "id": 1,
        "text": "Мне нравится быть в центре внимания. ✨",
        "scale": "Extraversion",
        "reverse": False,
        "compliments": {
            "low": ["Тихая сила — у тебя есть магия спокойствия. 🌙"],
            "mid": ["Ты умеешь и блистать, и слушать — золотая середина. 💫"],
            "high": ["Ты — душа компании! Даже кактус в углу аплодирует тебе. 🌵👏"]
        }
    },
    {
        "id": 2,
        "text": "Я легко сочувствую другим людям. 🤍",
        "scale": "Agreeableness",
        "reverse": False,
        "compliments": {
            "low": ["Твоя честность ценна — иногда прямота важнее улыбки. 🗝️"],
            "mid": ["Ты внимателен к людям и при этом сохраняешь границы — редкость. 🌿"],
            "high": ["Ты — ходячая аптека для души: люди идут к тебе за советом и печеньем. 🍪💌"]
        }
    },
    {
        "id": 3,
        "text": "Я люблю планировать и доводить дела до конца. 📋",
        "scale": "Conscientiousness",
        "reverse": False,
        "compliments": {
            "low": ["Спонтанность — твоё второе имя. Жизнь любит сюрпризы. 🎈"],
            "mid": ["Ты умеешь планировать, но оставляешь место для спонтанности — идеально. 🗓️✨"],
            "high": ["Ты — человек‑план: календарь у тебя знает больше, чем ты сам. 📅💪"]
        }
    },
    {
        "id": 4,
        "text": "Я часто переживаю и волнуюсь по пустякам. 🌧️",
        "scale": "Neuroticism",
        "reverse": False,
        "compliments": {
            "low": ["Ты — спокойный океан: штормы проходят мимо. 🌊"],
            "mid": ["Ты чувствуешь, но быстро отпускаешь — здоровый баланс. 🍃"],
            "high": ["Твой эмоциональный радар — суперсила. Немного мемов и дыхалки — и всё ок. 😂🧘‍♀️"]
        }
    },
    {
        "id": 5,
        "text": "Мне нравится пробовать новые идеи и занятия. 🎨",
        "scale": "Openness",
        "reverse": False,
        "compliments": {
            "low": ["Практичность — твой стиль. Новое можно и позже. 🛠️"],
            "mid": ["Ты открыт идеям, но выбираешь лучшее — мудро. 🧭"],
            "high": ["Ты — коллекционер идей: мир — твоя игровая площадка. ✨🧩"]
        }
    },
    {
        "id": 6,
        "text": "Я предпочитаю тихие вечера дома. 🕯️",
        "scale": "Extraversion",
        "reverse": True,
        "compliments": {
            "low": ["Ты — искра вечеринок, но и тишина тебе к лицу иногда. 🎉➡️🛋️"],
            "mid": ["Баланс: умеешь и тусить, и наслаждаться пледом. 🧣☕"],
            "high": ["Уют — твоё королевство. Плед и чай — идеальный план вечера. 🫖💤"]
        }
    },
    {
        "id": 7,
        "text": "Я доверяю людям, пока они не доказали обратное. 🛡️",
        "scale": "Agreeableness",
        "reverse": False,
        "compliments": {
            "low": ["Твоя осторожность — щит. Мир ценит бдительность. 🔒"],
            "mid": ["Ты доверяешь, но проверяешь — золотая середина. ✅🔍"],
            "high": ["Ты веришь в людей — это редкий и тёплый дар. 🤝🌞"]
        }
    },
    {
        "id": 8,
        "text": "Я аккуратен и слежу за порядком. 🧺",
        "scale": "Conscientiousness",
        "reverse": False,
        "compliments": {
            "low": ["Творческий хаос — источник вдохновения. Пусть будет немного беспорядка. 🎨😉"],
            "mid": ["Порядок у тебя в меру — удобно и красиво. 🧭✨"],
            "high": ["Ты — мастер порядка: даже носки у тебя в алфавитном порядке. 🧦📚"]
        }
    },
    {
        "id": 9,
        "text": "Я склонен к перепадам настроения. 🎭",
        "scale": "Neuroticism",
        "reverse": False,
        "compliments": {
            "low": ["Эмоциональная стабильность — твоя суперсила. 🛡️"],
            "mid": ["Ты чувствуешь, но умеешь возвращаться в ресурсное состояние. 🌤️"],
            "high": ["Твои эмоции — как погода: ярко и живо. Это делает тебя настоящим человеком. ☀️🌧️💫"]
        }
    },
    {
        "id": 10,
        "text": "Я люблю абстрактные рассуждения и философию. 🧠",
        "scale": "Openness",
        "reverse": False,
        "compliments": {
            "low": ["Практичность — твой компас. Философия подождёт. 🧭"],
            "mid": ["Ты любишь и идеи, и реальность — редкий баланс. ⚖️"],
            "high": ["Ты — мыслитель: мир для тебя — поле для вопросов и открытий. 🪄📚"]
        }
    },
    {
        "id": 11,
        "text": "Я легко завожу новые знакомства. 💬",
        "scale": "Extraversion",
        "reverse": False,
        "compliments": {
            "low": ["Твои близкие ценят глубину, а не количество знакомых. 🌱"],
            "mid": ["Ты умеешь и заводить, и хранить — отличный навык. 🤝💖"],
            "high": ["Ты заводила от бога: новые друзья появляются как по мановению палочки. ✨👯‍♀️"]
        }
    },
    {
        "id": 12,
        "text": "Я готов помочь даже незнакомцу. 🤲",
        "scale": "Agreeableness",
        "reverse": False,
        "compliments": {
            "low": ["Ты ценишь личные границы — это важно и правильно. 🚧"],
            "mid": ["Ты помогаешь, когда можешь — это делает мир лучше. 🌍💛"],
            "high": ["Ты — живой пример доброты: мир вокруг тебя теплее. 🌸🤍"]
        }
    },
    {
        "id": 13,
        "text": "Я часто откладываю дела на потом. ⏳",
        "scale": "Conscientiousness",
        "reverse": True,
        "compliments": {
            "low": ["Ты дисциплинированны — редкий и ценный навык. 🏅"],
            "mid": ["Иногда откладываешь, но всё равно успеваешь — мастер баланса. 🎯"],
            "high": ["Прокрастинация — твой талант. Главное — делать это с чувством юмора. 😅🍰"]
        }
    },
    {
        "id": 14,
        "text": "Я редко переживаю из‑за мелочей. 🕊️",
        "scale": "Neuroticism",
        "reverse": True,
        "compliments": {
            "low": ["Тебе свойственна чувствительность — это делает тебя внимательным. 🌿"],
            "mid": ["Ты умеешь переживать, но не тонешь в эмоциях — здорово. ⚖️"],
            "high": ["Спокойствие — твой козырь. Мир кажется проще рядом с тобой. 🌅"]
        }
    },
    {
        "id": 15,
        "text": "Я люблю придумывать новые способы решения задач. 💡",
        "scale": "Openness",
        "reverse": False,
        "compliments": {
            "low": ["Практичность помогает доводить дела до конца — это тоже талант. 🛠️"],
            "mid": ["Ты находишь свежие идеи и умеешь выбирать рабочие — редкость. 🧩"],
            "high": ["Ты — генератор идей: мир становится интереснее благодаря тебе. ✨🚀"]
        }
    }
]


def find_image_for_question(question: Dict, images_dirs: Optional[List[str]] = None,
                            exts: tuple = (".jpg", ".jpeg", ".png", ".webp")) -> Optional[str]:
    """
    Гибкий поиск картинки для вопроса.
    Ищет в нескольких папках (относительно questions_bank.py):
      - images/
      - final_images/images/
    Поддерживает имена:
      q_<id>_<scale_short>.<ext>
      q_<id>.<ext>
      q_<id>_*.ext  (любой суффикс)
      q_0<id>_...  (ведущий ноль)
    Возвращает абсолютный путь к первому найденному файлу или None.
    """
    if not isinstance(question, dict):
        return None

    qid = question.get("id")
    scale = question.get("scale")
    if not qid:
        return None

    # папки по умолчанию (относительно этого файла)
    base_module_dir = os.path.dirname(os.path.abspath(__file__))
    if images_dirs is None:
        images_dirs = [os.path.join(base_module_dir, "images"),
                       os.path.join(base_module_dir, "final_images", "images")]

    # подготовка вариантов имени: с и без ведущего нуля
    id_str = str(qid)
    id_zero = id_str.zfill(2)  # "1" -> "01" (поддержка q_01)
    scale_short = SCALE_SHORT.get(scale) if scale else None

    # собрать шаблоны (в нижнем регистре)
    patterns = []
    if scale_short:
        patterns.append(f"q_{id_str}_{scale_short}")
        patterns.append(f"q_{id_zero}_{scale_short}")
    patterns.append(f"q_{id_str}")
    patterns.append(f"q_{id_zero}")
    patterns.append(f"q_{id_str}_")   # любой суффикс
    patterns.append(f"q_{id_zero}_")

    # поиск по всем папкам, файлам и расширениям
    for images_dir in images_dirs:
        if not os.path.isdir(images_dir):
            continue
        try:
            files = os.listdir(images_dir)
        except Exception:
            continue
        files_lower = [f.lower() for f in files]

        # точные совпадения pattern + ext
        for pat in patterns:
            # если паттерн заканчивается на '_' — ищем префикс
            if pat.endswith("_"):
                prefix = pat.lower()
                for i, fname in enumerate(files_lower):
                    for ext in exts:
                        if fname.startswith(prefix) and fname.endswith(ext):
                            return os.path.join(images_dir, files[i])
                continue

            for ext in exts:
                target = (pat + ext).lower()
                for i, fname in enumerate(files_lower):
                    if fname == target:
                        return os.path.join(images_dir, files[i])

        # последний шанс: любой файл, начинающийся с "q_<id>"
        prefix = f"q_{id_str}".lower()
        prefix_zero = f"q_{id_zero}".lower()
        for i, fname in enumerate(files_lower):
            if fname.startswith(prefix) or fname.startswith(prefix_zero):
                return os.path.join(images_dir, files[i])

    return None


__all__ = ["QUESTIONS", "find_image_for_question", "SCALE_SHORT"]

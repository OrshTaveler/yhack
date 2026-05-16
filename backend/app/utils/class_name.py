from __future__ import annotations

import re


def parse_grade_from_class_name(name: str) -> int:
    """Извлекает номер параллели из начала названия класса (5А → 5, 10Б → 10)."""
    cleaned = name.strip()
    match = re.match(r"^(\d+)", cleaned)
    if not match:
        raise ValueError(
            f"Не удалось определить параллель из названия «{name}». "
            "Укажите номер в начале, например: 5А, 10Б."
        )
    grade = int(match.group(1))
    if grade < 1 or grade > 11:
        raise ValueError(f"Параллель {grade} вне допустимого диапазона (1–11).")
    return grade

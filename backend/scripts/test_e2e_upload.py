"""
Этап 4: Сквозной тест интеграции — загрузка ДЗ через API + опрос результата.

Запуск (бэкенд должен быть поднят):
    python scripts/test_e2e_upload.py путь/к/фото.jpg
"""

import json
import sys
import time
import urllib.request
import uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "http://localhost:8000/api"


def login() -> str:
    req = urllib.request.Request(
        f"{BASE}/auth/login",
        data=json.dumps({"email": "student@school.ru", "password": "student123"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


def get_subject(token: str) -> str:
    req = urllib.request.Request(f"{BASE}/subjects", headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req).read())["items"][0]["id"]


def upload(token: str, subject_id: str, image_path: str) -> str:
    """Загружает фото через multipart/form-data."""
    boundary = uuid.uuid4().hex
    with open(image_path, "rb") as f:
        image_data = f.read()

    parts = []
    parts.append(f"--{boundary}".encode())
    parts.append(b'Content-Disposition: form-data; name="subject_id"')
    parts.append(b"")
    parts.append(subject_id.encode())
    parts.append(f"--{boundary}".encode())
    parts.append(
        b'Content-Disposition: form-data; name="file"; filename="hw.jpg"'
    )
    parts.append(b"Content-Type: image/jpeg")
    parts.append(b"")
    parts.append(image_data)
    parts.append(f"--{boundary}--".encode())
    body = b"\r\n".join(parts)

    req = urllib.request.Request(
        f"{BASE}/homework/upload",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    result = json.loads(urllib.request.urlopen(req).read())
    return result["id"]


def poll(token: str, hw_id: str) -> dict:
    for i in range(1, 21):
        req = urllib.request.Request(
            f"{BASE}/homework/my", headers={"Authorization": f"Bearer {token}"}
        )
        items = json.loads(urllib.request.urlopen(req).read())["items"]
        hw = next((x for x in items if x["id"] == hw_id), None)
        if hw and hw["status"] != "pending":
            return hw
        print(f"  ...работа в проверке, опрос {i}/20")
        time.sleep(5)
    return hw or {}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/test_e2e_upload.py путь/к/фото.jpg")
        sys.exit(1)

    print("=" * 55)
    print("E2E ТЕСТ: загрузка ДЗ через приложение")
    print("=" * 55)

    token = login()
    print("✓ Вход выполнен")

    subject_id = get_subject(token)
    print("✓ Предмет получен")

    print("→ Загружаю фото...")
    hw_id = upload(token, subject_id, sys.argv[1])
    print(f"✓ Работа создана: {hw_id} (status=pending)")

    print("→ Жду завершения фоновой проверки...")
    hw = poll(token, hw_id)

    print("\n" + "=" * 55)
    print("РЕЗУЛЬТАТ:")
    print("=" * 55)
    print(f"Статус:        {hw.get('status')}")
    print(f"Уникальность:  {hw.get('text_unique')}%")
    print(f"Вероятность AI: {hw.get('ai_probability')}%")
    print(f"Причина AI:    {hw.get('ai_detector_reason')}")
    print(f"Комментарий:   {hw.get('ai_comment')}")
    print(f"\nOCR-текст:\n{hw.get('ocr_text')}")
    src = hw.get("plagiarism_sources") or []
    if src:
        print(f"\nИсточники ({len(src)}):")
        for s in src[:5]:
            print(f"  • {s.get('plagiat')}%  {s.get('url')}")
    print("=" * 55)

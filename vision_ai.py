from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import io

# путь к модели (как в твоём download_model.py)
MODEL_DIR = "./car_model"

print(f"[vision_ai] Загружаю модель из {MODEL_DIR}...")
processor = AutoImageProcessor.from_pretrained(MODEL_DIR)
model = AutoModelForImageClassification.from_pretrained(MODEL_DIR)
print("[vision_ai] Модель успешно загружена ✅")


def _normalize_model_name(model_name: str) -> str:
    """
    Приводит название модели к формату, который хранится в БД.
    Например: "5 Series" -> "5-Series"
    """
    replacements = {
        "3 Series": "3-Series",
        "4 Series": "4-Series",
        "5 Series": "5-Series",
        "6 Series": "6-Series",
        "7 Series": "7-Series",
        "8 Series": "8-Series",
        "E Class": "E-Class",
        "C Class": "C-Class",
        "S Class": "S-Class",
    }
    return replacements.get(model_name, model_name)


def predict_car(image_bytes: bytes):
    """
    Принимает байты фото из Telegram и возвращает (brand, model_name, confidence)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        inputs = processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            pred_id = int(torch.argmax(probs, dim=-1))
            confidence = float(probs[0, pred_id])

        label = model.config.id2label[pred_id]

        # Пример: "bmw_3_series" → "BMW", "3 Series"
        parts = label.replace("_", " ").split()

        brand_raw = parts[0].lower()

        brand_map = {
            "bmw": "BMW",
            "mercedes": "Mercedes",
            "mercedes-benz": "Mercedes",
            "mercedesbenz": "Mercedes",
        }
        brand = brand_map.get(brand_raw, parts[0].capitalize())

        model_name = " ".join(parts[1:]).title()

        # --- нормализация "Class" у Mercedes (Cla Class -> CLA, Gla Class -> GLA и т.п.) ---
        if model_name.endswith(" Class"):
            base = model_name[:-6].strip()  # убираем " Class"
            # если это аббревиатура (CLA/GLA/CLS/AMG и т.д.) — делаем капсом
            if 2 <= len(base) <= 5 and base.replace("-", "").isalpha():
                model_name = base.upper()
            else:
                model_name = base

        # --- твоя нормализация под БД для Series (5 Series -> 5-Series) оставь ниже ---

        # ВАЖНО: нормализация под формат БД
        model_name = _normalize_model_name(model_name)

        print(f"[vision_ai] Опознано: {brand} {model_name} ({confidence:.2%})")

        return brand, model_name, confidence

    except Exception as e:
        print("[vision_ai] Ошибка распознавания:", e)
        return None, None, 0.0

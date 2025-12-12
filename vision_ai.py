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
        brand = parts[0].capitalize()
        model_name = " ".join(parts[1:]).title()

        print(f"[vision_ai] Опознано: {brand} {model_name} ({confidence:.2%})")

        return brand, model_name, confidence

    except Exception as e:
        print("[vision_ai] Ошибка распознавания:", e)
        return None, None, 0.0

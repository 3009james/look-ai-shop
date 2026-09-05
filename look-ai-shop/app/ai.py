import json
import re
from typing import Iterable

import httpx

from .config import get_settings
from .models import Product


def _catalog_text(products: Iterable[Product]) -> str:
    return "\n".join(
        f"ID {p.id}: {p.name}; {p.category}; {int(p.price)} ₽; {p.description}; tags={p.tags}; sizes={p.sizes}"
        for p in products
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def ai_stylist(message: str, products: list[Product], profile: dict) -> dict:
    settings = get_settings()
    if not (settings.ai_base_url and settings.ai_api_key and settings.ai_model):
        return fallback_stylist(message, products, profile)

    system = f"""Ты персональный стилист магазина LOOK AI. Отвечай только на русском языке.
Ты можешь рекомендовать ТОЛЬКО товары из каталога ниже. Не выдумывай цены, размеры или товары.
Учитывай запрос, стиль, размер и бюджет пользователя. Выбери до 5 подходящих товаров.
Верни СТРОГО JSON без markdown вида:
{{"answer":"краткий дружелюбный совет", "product_ids":[1,2,3]}}

Профиль: style={profile.get('style') or 'не указан'}, size={profile.get('size') or 'не указан'}, budget={profile.get('budget') or 'не указан'}.
Каталог:
{_catalog_text(products)}
"""
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ],
        "temperature": 0.35,
    }
    url = settings.ai_base_url.rstrip("/") + "/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            data = _extract_json(content)
            valid_ids = {p.id for p in products}
            ids = [int(x) for x in data.get("product_ids", []) if int(x) in valid_ids][:5]
            return {
                "answer": str(data.get("answer") or "Я подобрал несколько вариантов."),
                "product_ids": ids,
                "mode": "ai",
            }
    except Exception:
        return fallback_stylist(message, products, profile)


def fallback_stylist(message: str, products: list[Product], profile: dict) -> dict:
    query = f"{message} {profile.get('style','')}".lower()
    budget = profile.get("budget")
    keyword_groups = {
        "офис": ["офис", "работ", "делов", "классик"],
        "вечер": ["вечер", "свидан", "празд", "день рождения", "ресторан"],
        "casual": ["повседнев", "casual", "каждый день", "гулять"],
        "осень": ["осен", "прохлад", "тренч", "кардиган"],
        "лето": ["лет", "жарк", "море", "отпуск"],
    }
    wanted = [tag for tag, words in keyword_groups.items() if any(word in query for word in words)]

    scored = []
    for product in products:
        if budget and product.price > budget:
            continue
        hay = f"{product.name} {product.category} {product.description} {product.tags}".lower()
        score = sum(4 for tag in wanted if tag in hay)
        score += sum(1 for token in re.findall(r"[а-яa-z0-9]+", query) if len(token) > 3 and token in hay)
        score += 1 if product.featured else 0
        scored.append((score, product.price, product.id))

    scored.sort(key=lambda x: (-x[0], x[1]))
    ids = [pid for _, _, pid in scored[:5]]
    answer = (
        "Я подобрал вещи из каталога под ваш запрос. "
        "Сейчас работает демо-стилист; добавьте AI_API_KEY, AI_BASE_URL и AI_MODEL в .env, "
        "чтобы включить полноценный ИИ-подбор."
    )
    return {"answer": answer, "product_ids": ids, "mode": "demo"}

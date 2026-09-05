import json
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from .ai import ai_stylist
from .auth import telegram_user
from .bot import start_bot, stop_bot
from .config import get_settings
from .db import Base, SessionLocal, engine, get_db
from .models import Order, Product
from .schemas import AIRequest, AIResponse, OrderCreate, OrderOut, ProductOut
from .seed import seed_products

settings = get_settings()
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_products(db)
    await start_bot()
    yield
    await stop_bot()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


def product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        name=p.name,
        category=p.category,
        description=p.description,
        price=p.price,
        image=p.image,
        sizes=[x.strip() for x in p.sizes.split(",") if x.strip()],
        tags=[x.strip() for x in p.tags.split(",") if x.strip()],
        featured=p.featured,
    )


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/products", response_model=list[ProductOut])
def products(db: Session = Depends(get_db)):
    rows = db.scalars(select(Product).where(Product.active.is_(True)).order_by(Product.id)).all()
    return [product_out(p) for p in rows]


@app.get("/api/me")
def me(user: dict = Depends(telegram_user)):
    return user


@app.post("/api/ai/stylist", response_model=AIResponse)
async def stylist(payload: AIRequest, user: dict = Depends(telegram_user), db: Session = Depends(get_db)):
    products = list(db.scalars(select(Product).where(Product.active.is_(True))).all())
    result = await ai_stylist(
        payload.message,
        products,
        {"style": payload.style, "size": payload.size, "budget": payload.budget},
    )
    return AIResponse(**result)


async def notify_admin(order: Order) -> None:
    if not settings.bot_token or not settings.admin_telegram_id:
        return
    try:
        lines = json.loads(order.items_json)
        items_text = "\n".join(
            f"• {item['name']} ×{item['quantity']} / {item.get('size') or '—'}" for item in lines
        )
    except Exception:
        items_text = "Состав заказа недоступен"
    text = (
        f"🛍 Новый заказ LOOK AI #{order.id}\n"
        f"Клиент: {order.customer_name or 'не указано'}\n"
        f"Telegram ID: {order.telegram_user_id}\n\n"
        f"{items_text}\n\n"
        f"Сумма: {int(order.total)} ₽"
    )
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": settings.admin_telegram_id, "text": text})
    except Exception:
        pass


@app.post("/api/orders", response_model=OrderOut)
async def create_order(payload: OrderCreate, user: dict = Depends(telegram_user), db: Session = Depends(get_db)):
    ids = [item.product_id for item in payload.items]
    products = list(db.scalars(select(Product).where(Product.id.in_(ids), Product.active.is_(True))).all())
    by_id = {p.id: p for p in products}
    if len(by_id) != len(set(ids)):
        raise HTTPException(status_code=400, detail="В корзине есть недоступный товар")

    total = 0.0
    lines = []
    for item in payload.items:
        p = by_id[item.product_id]
        allowed_sizes = {x.strip() for x in p.sizes.split(",") if x.strip()}
        if item.size and item.size not in allowed_sizes:
            raise HTTPException(status_code=400, detail=f"Недоступный размер для {p.name}")
        total += p.price * item.quantity
        lines.append({
            "product_id": p.id,
            "name": p.name,
            "price": p.price,
            "quantity": item.quantity,
            "size": item.size,
        })

    order = Order(
        telegram_user_id=int(user["id"]),
        customer_name=payload.customer_name or user.get("first_name", ""),
        items_json=json.dumps(lines, ensure_ascii=False),
        total=total,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    await notify_admin(order)
    return OrderOut(id=order.id, total=order.total, status=order.status)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{full_path:path}")
def spa(full_path: str):
    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(STATIC_DIR / "index.html")

# LOOK AI — Telegram Mini App магазин одежды с AI-стилистом

Готовый MVP интернет-магазина одежды внутри Telegram. Интерфейс адаптивный: на телефоне занимает доступный экран Mini App, а на Telegram Desktop раскрывается в широкий интерфейс без «макета смартфона».

## Что уже работает

- Telegram-бот на **aiogram 3** с `/start`, `/shop` и постоянной кнопкой **LOOK AI**.
- Telegram Mini App с `expand()` и запросом `requestFullscreen()` на клиентах Bot API 8.0+.
- Безопасная серверная проверка `Telegram.WebApp.initData` через HMAC-SHA-256.
- Адаптивная витрина: главная, каталог, категории, поиск, карточка товара, выбор размера.
- Корзина с сохранением на устройстве.
- Создание заказа в PostgreSQL.
- Уведомление администратору о новом заказе в Telegram.
- Профиль покупателя: стиль, размер и бюджет.
- AI-стилист: запрос свободным текстом → рекомендации **только из реального каталога**.
- Если AI-ключи не настроены, включается рабочий demo-стилист, поэтому проект можно запустить сразу.
- 12 демо-товаров и локальные SVG-изображения без внешних фотохостингов.
- Docker Compose: приложение + PostgreSQL + Caddy с автоматическим HTTPS.
- GitHub Actions с тестом проверки Telegram `initData`.

## Стек

- Python 3.12
- FastAPI
- aiogram 3
- SQLAlchemy 2
- PostgreSQL 17
- Vanilla HTML/CSS/JS (без отдельной Node-сборки)
- Caddy
- Docker Compose
- любой AI-провайдер с OpenAI-compatible `/chat/completions`

## Структура

```text
look-ai-shop/
├─ app/
│  ├─ main.py          # FastAPI, API каталога/AI/заказов
│  ├─ bot.py           # Telegram-бот
│  ├─ auth.py          # проверка Telegram initData
│  ├─ ai.py            # AI-стилист + demo fallback
│  ├─ db.py            # подключение БД
│  ├─ models.py        # Product, Order
│  ├─ schemas.py
│  ├─ seed.py          # начальный каталог
│  └─ static/          # Mini App
├─ tests/
├─ Dockerfile
├─ docker-compose.yml
├─ Caddyfile
├─ .env.example
└─ README.md
```

# 1. Быстрый локальный запуск без Telegram и без AI

Для проверки интерфейса на компьютере можно использовать SQLite и demo-авторизацию.

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DEV_MODE=true
export DATABASE_URL=sqlite:///./lookai.db
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DEV_MODE="true"
$env:DATABASE_URL="sqlite:///./lookai.db"
uvicorn app.main:app --reload
```

Откройте `http://127.0.0.1:8000`.

# 2. Создание Telegram-бота

1. Откройте **@BotFather**.
2. Выполните `/newbot` и получите `BOT_TOKEN`.
3. Для красивого профиля Mini App рекомендуется в BotFather открыть:
   `My Bots → ваш бот → Bot Settings → Configure Mini App` и включить Main Mini App.
4. После публикации укажите HTTPS-адрес Mini App, например `https://shop.example.com`.
5. При старте проекта бот сам установит menu button **LOOK AI** через Bot API.

Для Main Mini App можно также использовать ссылку вида:

```text
https://t.me/USERNAME_БОТА?startapp&mode=fullscreen
```

Сам интерфейс дополнительно вызывает `requestFullscreen()` при поддержке Telegram-клиентом.

# 3. Настройка `.env`

```bash
cp .env.example .env
```

Минимально для VPS измените:

```env
BOT_TOKEN=ВАШ_ТОКЕН_ОТ_BOTFATHER
WEBAPP_URL=https://shop.example.com
APP_DOMAIN=shop.example.com
DEV_MODE=false

POSTGRES_PASSWORD=очень_сложный_пароль
DATABASE_URL=postgresql+psycopg://lookai:очень_сложный_пароль@db:5432/lookai

# Telegram ID владельца магазина — необязательно.
# Если заполнить, сюда будут приходить новые заказы.
ADMIN_TELEGRAM_ID=123456789
```

Важно: `.env` уже находится в `.gitignore`; **не публикуйте токены и ключи на GitHub**.

# 4. Подключение настоящего AI

`app/ai.py` использует OpenAI-compatible endpoint `/chat/completions`. Это позволяет подключить подходящего совместимого провайдера без изменений фронтенда.

Заполните:

```env
AI_BASE_URL=https://provider.example/v1
AI_API_KEY=ваш_ключ
AI_MODEL=название_модели
```

Если эти три значения пустые, приложение автоматически использует demo-подбор по тегам каталога.

AI получает компактное описание текущего каталога и обязан возвращать ID существующих товаров. Сервер дополнительно отбрасывает несуществующие ID, поэтому модель не может «подложить» в выдачу выдуманный товар.

# 5. Размещение на VPS

Требования:

- Ubuntu 22.04/24.04 или аналогичный Linux;
- Docker + Docker Compose;
- домен, A-запись которого указывает на IP VPS;
- открытые порты `80` и `443`.

Пример:

```bash
git clone https://github.com/YOUR_USERNAME/look-ai-shop.git
cd look-ai-shop
cp .env.example .env
nano .env

docker compose up -d --build
```

Проверка:

```bash
docker compose ps
docker compose logs -f app
```

Caddy автоматически запросит TLS-сертификат для `APP_DOMAIN` и будет проксировать HTTPS на FastAPI.

После этого в BotFather укажите тот же адрес, который находится в `WEBAPP_URL`.

# 6. Загрузка проекта на GitHub

Создайте пустой репозиторий на GitHub, затем из папки проекта:

```bash
git init
git add .
git commit -m "Initial LOOK AI Telegram Mini App"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/look-ai-shop.git
git push -u origin main
```

# 7. Где менять товары

Демо-каталог находится в `app/seed.py`.

При **первом** старте он записывается в БД. Для реального магазина лучше следующим этапом добавить веб-админку или импорт товаров из CRM/1С/API поставщика.

Если вы меняете `seed.py` уже после первого запуска, существующая БД автоматически не перезаписывается.

# 8. Как заказ работает сейчас

1. Покупатель выбирает товары и размеры.
2. Нажимает «Оформить заказ».
3. Backend повторно берёт актуальные цены из БД — цена из браузера не считается доверенной.
4. Заказ записывается в PostgreSQL.
5. Если задан `ADMIN_TELEGRAM_ID`, владелец получает сообщение от бота.

В проект намеренно не зашит конкретный эквайринг, потому что для боевого магазина нужны реальные реквизиты и выбор провайдера. Его удобно подключить отдельным платежным модулем к уже существующей сущности `Order`.

# 9. Проверка тестов

```bash
pytest -q
```

# Полноэкранный режим Telegram

Telegram Mini Apps с Bot API 8.0+ поддерживают `requestFullscreen()` и safe-area. Скрипт проекта вызывает `ready()`, `expand()` и затем `requestFullscreen()` при наличии метода. На старых клиентах приложение останется в максимально доступной развёрнутой области без падения.

## Что стоит добавить перед настоящими продажами

- административную панель для CRUD товаров и заказов;
- загрузку реальных фотографий в S3/MinIO;
- выбранный платёжный провайдер;
- остатки по размерам;
- доставку и адрес покупателя;
- политику конфиденциальности/оферту;
- rate limit для AI API;
- резервное копирование PostgreSQL;
- аналитику и события продаж.

## Лицензия

MIT.

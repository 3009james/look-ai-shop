from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Product


PRODUCTS = [
    ("Жакет Sand", "Верх", "Свободный однобортный жакет в мягком песочном оттенке.", 8990, "/assets/jacket.svg", "XS,S,M,L,XL", "офис,минимализм,бежевый,капсула", True),
    ("Платье Noir Midi", "Платья", "Чёрное платье миди с чистой линией плеч и мягкой посадкой.", 7490, "/assets/dress-black.svg", "XS,S,M,L", "вечер,свидание,черный,миди", True),
    ("Рубашка Cloud", "Верх", "Белая хлопковая рубашка relaxed fit — основа повседневной капсулы.", 4590, "/assets/shirt.svg", "XS,S,M,L,XL", "белый,база,офис,минимализм", False),
    ("Джинсы Straight Blue", "Низ", "Прямые джинсы средней посадки из плотного денима.", 5990, "/assets/jeans.svg", "XS,S,M,L,XL", "джинсы,casual,синий,база", True),
    ("Юбка Silk Cocoa", "Низ", "Струящаяся юбка миди с сатиновым блеском.", 5690, "/assets/skirt.svg", "XS,S,M,L", "юбка,вечер,коричневый,женственный", False),
    ("Тренч Stone", "Верхняя одежда", "Лёгкий тренч прямого силуэта с поясом.", 11990, "/assets/trench.svg", "S,M,L,XL", "осень,тренч,бежевый,классика", True),
    ("Топ Ivory", "Верх", "Минималистичный топ из плотного трикотажа.", 2890, "/assets/top.svg", "XS,S,M,L", "топ,белый,лето,база", False),
    ("Брюки Wide Graphite", "Низ", "Широкие брюки со стрелками и высокой посадкой.", 6290, "/assets/trousers.svg", "XS,S,M,L,XL", "брюки,офис,графит,классика", True),
    ("Кардиган Oat", "Трикотаж", "Мягкий кардиган свободного кроя с акцентными пуговицами.", 6490, "/assets/cardigan.svg", "S,M,L,XL", "кардиган,уют,осень,бежевый", False),
    ("Кеды Milk", "Обувь", "Минималистичные молочные кеды на гибкой подошве.", 6990, "/assets/sneakers.svg", "36,37,38,39,40,41", "кеды,обувь,casual,белый", True),
    ("Сумка Mini Berry", "Аксессуары", "Компактная сумка на плечо в ягодном оттенке.", 4990, "/assets/bag.svg", "ONE", "сумка,акцент,бордовый,вечер", False),
    ("Платье Olive Air", "Платья", "Лёгкое платье миди свободного силуэта в оливковом цвете.", 6890, "/assets/dress-olive.svg", "XS,S,M,L,XL", "платье,лето,оливковый,повседневный", True),
]


def seed_products(db: Session) -> None:
    count = db.scalar(select(Product.id).limit(1))
    if count is not None:
        return
    for name, category, description, price, image, sizes, tags, featured in PRODUCTS:
        db.add(Product(
            name=name,
            category=category,
            description=description,
            price=price,
            image=image,
            sizes=sizes,
            tags=tags,
            featured=featured,
        ))
    db.commit()

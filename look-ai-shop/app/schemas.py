from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    description: str
    price: float
    image: str
    sizes: list[str]
    tags: list[str]
    featured: bool


class AIRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1200)
    style: str = Field(default="", max_length=120)
    size: str = Field(default="", max_length=20)
    budget: int | None = Field(default=None, ge=0, le=1_000_000)


class AIResponse(BaseModel):
    answer: str
    product_ids: list[int]
    mode: str


class OrderItem(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)
    size: str = Field(default="", max_length=20)


class OrderCreate(BaseModel):
    customer_name: str = Field(default="", max_length=160)
    items: list[OrderItem] = Field(min_length=1, max_length=50)


class OrderOut(BaseModel):
    id: int
    total: float
    status: str

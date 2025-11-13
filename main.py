import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Product, Variant

app = FastAPI(title="Mebella API", description="Catalog API for Мебелла furniture")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateProductRequest(Product):
    pass


@app.get("/", tags=["root"])
def read_root():
    return {"brand": "Мебелла", "message": "Добро пожаловать в каталог мебели"}


@app.get("/test", tags=["health"])
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


@app.post("/api/products", tags=["products"], response_model=dict)
def create_product(payload: CreateProductRequest):
    """Create a new product model with variants."""
    try:
        product_id = create_document("product", payload)
        return {"id": product_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products", tags=["products"]) 
def list_products(
    category: Optional[str] = Query(None, description="Category filter"),
    search: Optional[str] = Query(None, description="Text search in name/description"),
    limit: int = Query(50, ge=1, le=200)
):
    """List products with optional filters"""
    try:
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if search:
            # simple regex search in name or description
            filter_dict["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        docs = get_documents("product", filter_dict, limit)
        # Convert ObjectId and datetime to strings for JSON response
        def serialize(doc):
            doc["id"] = str(doc.pop("_id")) if doc.get("_id") else None
            for k in ["created_at", "updated_at"]:
                if k in doc:
                    doc[k] = str(doc[k])
            return doc
        return [serialize(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}", tags=["products"]) 
def get_product(product_id: str):
    try:
        from bson import ObjectId
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        doc["id"] = str(doc.pop("_id"))
        for k in ["created_at", "updated_at"]:
            if k in doc:
                doc[k] = str(doc[k])
        return doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories", tags=["products"]) 
def list_categories():
    """Return fixed categories used in the catalog"""
    return [
        {"key": "стулья", "label": "Стулья"},
        {"key": "шкафы", "label": "Шкафы"},
        {"key": "тумбы", "label": "Тумбы"},
        {"key": "столы", "label": "Столы"},
    ]


# --- Sample data seeding ---

def _sample_products() -> list[dict]:
    return [
        {
            "name": "Стул Nordica",
            "description": "Скандинавский стул с мягким сиденьем и деревянными ножками.",
            "category": "стулья",
            "base_price": 4990,
            "images": [
                "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=1200&q=80&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1503602642458-232111445657?w=1200&q=80&auto=format&fit=crop"
            ],
            "material": "Массив бука, ткань",
            "brand": "Мебелла",
            "color_family": ["бежевый", "серый", "черный"],
            "variants": [
                {"color": "бежевый", "color_hex": "#D8C3A5", "size": "стандарт", "sku": "CH-NOR-BE-STD", "price": 4990, "stock": 25},
                {"color": "серый", "color_hex": "#A0A0A0", "size": "стандарт", "sku": "CH-NOR-GR-STD", "price": 4990, "stock": 18},
                {"color": "черный", "color_hex": "#000000", "size": "стандарт", "sku": "CH-NOR-BK-STD", "price": 5290, "stock": 12}
            ]
        },
        {
            "name": "Шкаф Alto 3D",
            "description": "Трехдверный шкаф с отделениями для одежды и белья, спокойный минимализм.",
            "category": "шкафы",
            "base_price": 24990,
            "images": [
                "https://images.unsplash.com/photo-1598300183876-2b0b1f5b7c47?w=1200&q=80&auto=format&fit=crop"
            ],
            "material": "ЛДСП, МДФ",
            "brand": "Мебелла",
            "color_family": ["белый", "дуб"],
            "variants": [
                {"color": "белый", "color_hex": "#FFFFFF", "size": "200x120x60", "sku": "WR-AL3-WH-200", "price": 24990, "stock": 8},
                {"color": "дуб", "color_hex": "#C5A572", "size": "220x140x60", "sku": "WR-AL3-OK-220", "price": 28990, "stock": 5}
            ]
        },
        {
            "name": "Тумба Nova",
            "description": "Прикроватная тумба с плавным закрыванием, скрытые ручки.",
            "category": "тумбы",
            "base_price": 6990,
            "images": [
                "https://images.unsplash.com/photo-1549187774-b4e9b0445b06?w=1200&q=80&auto=format&fit=crop"
            ],
            "material": "МДФ",
            "brand": "Мебелла",
            "color_family": ["белый", "графит"],
            "variants": [
                {"color": "белый", "color_hex": "#FFFFFF", "size": "50x40x35", "sku": "NS-NOV-WH-50", "price": 6990, "stock": 20},
                {"color": "графит", "color_hex": "#3B3B3B", "size": "50x40x35", "sku": "NS-NOV-GR-50", "price": 7290, "stock": 14}
            ]
        },
        {
            "name": "Стол Loft+",
            "description": "Обеденный стол в стиле лофт, металлическое основание, столешница из дуба.",
            "category": "столы",
            "base_price": 19990,
            "images": [
                "https://images.unsplash.com/photo-1493666438817-866a91353ca9?w=1200&q=80&auto=format&fit=crop"
            ],
            "material": "Дуб, металл",
            "brand": "Мебелла",
            "color_family": ["дуб натуральный", "венге"],
            "variants": [
                {"color": "дуб натуральный", "color_hex": "#C8A97E", "size": "120x70", "sku": "TB-LOF-NA-120", "price": 19990, "stock": 10},
                {"color": "дуб натуральный", "color_hex": "#C8A97E", "size": "160x80", "sku": "TB-LOF-NA-160", "price": 23990, "stock": 7},
                {"color": "венге", "color_hex": "#3E2B23", "size": "160x80", "sku": "TB-LOF-WE-160", "price": 24990, "stock": 4}
            ]
        }
    ]


def seed_if_empty() -> dict:
    """Insert sample products if the collection is empty. Returns stats."""
    if db is None:
        return {"seeded": False, "reason": "database not available"}
    try:
        count = db["product"].count_documents({})
        if count > 0:
            return {"seeded": False, "reason": "already has data", "count": count}
        products = _sample_products()
        inserted = 0
        for p in products:
            try:
                create_document("product", p)
                inserted += 1
            except Exception:
                continue
        return {"seeded": True, "inserted": inserted}
    except Exception as e:
        return {"seeded": False, "reason": str(e)}


@app.post("/api/seed", tags=["admin"])
def seed_endpoint():
    """Manually trigger sample data seeding."""
    result = seed_if_empty()
    if not result.get("seeded") and result.get("reason") == "already has data":
        return result
    if not result.get("seeded"):
        raise HTTPException(status_code=500, detail=result)
    return result


# Auto-seed on startup if empty
@app.on_event("startup")
async def startup_event():
    seed_if_empty()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

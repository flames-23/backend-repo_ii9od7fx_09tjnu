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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

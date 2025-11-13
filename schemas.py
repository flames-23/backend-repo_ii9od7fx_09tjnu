"""
Database Schemas for Mebella furniture catalog

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- Product -> "product" collection

We model furniture with variants so one product (model) can have multiple
sizes and colors.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class Variant(BaseModel):
    """A purchasable variation of a product (e.g., color + size)."""
    color: str = Field(..., description="Color name (e.g., 'черный', 'бежевый')")
    color_hex: Optional[str] = Field(None, description="HEX color like #000000")
    size: Optional[str] = Field(None, description="Size label (e.g., 'S', 'M', 'L', '120x60')")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    price: float = Field(..., ge=0, description="Price for this variant")
    stock: int = Field(0, ge=0, description="Units available in stock")


class Product(BaseModel):
    """
    Furniture product model (a single design/model with multiple variants)
    Collection name: "product"
    """
    name: str = Field(..., description="Product name/model")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Category: стулья, шкафы, тумбы, столы")
    base_price: Optional[float] = Field(None, ge=0, description="Optional base price (fallback)")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    variants: List[Variant] = Field(default_factory=list, description="List of available variations")
    brand: str = Field("Мебелла", description="Brand name")
    material: Optional[str] = Field(None, description="Primary material")
    color_family: Optional[List[str]] = Field(None, description="List of color families for filtering")

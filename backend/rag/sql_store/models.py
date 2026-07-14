"""
backend/rag/sql_store/models.py

SQLAlchemy ORM Models — La traduction Python du schéma SQL.

CONCEPT CLÉ : ORM (Object Relational Mapper)
─────────────────────────────────────────────
Sans ORM :
    cursor.execute("SELECT * FROM products WHERE price < 300")
    rows = cursor.fetchall()
    product = {"id": rows[0][0], "name": rows[0][1], ...}

Avec SQLAlchemy ORM :
    products = await session.execute(
        select(Product).where(Product.price < 300)
    )
    product.name  # directement !

L'ORM mappe chaque table SQL → classe Python
Chaque colonne SQL → attribut Python
Chaque ligne SQL → instance de la classe
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Any

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text,
    func, Index
)
# func.now() = appel SQL NOW() depuis Python

from sqlalchemy.dialects.postgresql import JSONB
# JSONB est spécifique à PostgreSQL, donc dans dialects.postgresql

from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
# DeclarativeBase = classe de base pour tous nos modèles
# relationship = définit les relations entre tables
# Mapped, mapped_column = typing moderne SQLAlchemy 2.0


# ─────────────────────────────────────────────────────────────
# BASE CLASS
# Tous nos modèles héritent de cette classe
# ─────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Classe de base SQLAlchemy.
    
    Tous les modèles héritent de Base.
    SQLAlchemy utilise cette hiérarchie pour :
    - Créer les tables (Base.metadata.create_all)
    - Gérer les transactions
    - Mapper Python ↔ SQL
    """
    pass


# ─────────────────────────────────────────────────────────────
# MODEL 1 : CATEGORY
# ─────────────────────────────────────────────────────────────
class Category(Base):
    """
    Représente une catégorie de produits.
    
    SQL Table: categories
    """
    __tablename__ = "categories"
    # __tablename__ dit à SQLAlchemy quelle table SQL utiliser
    
    # Colonnes — syntaxe moderne SQLAlchemy 2.0
    id:          Mapped[int]            = mapped_column(Integer, primary_key=True)
    name:        Mapped[str]            = mapped_column(String(100), nullable=False)
    slug:        Mapped[str]            = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    parent_id:   Mapped[Optional[int]]  = mapped_column(
                                            Integer, 
                                            ForeignKey("categories.id"), 
                                            nullable=True
                                         )
    created_at:  Mapped[datetime]       = mapped_column(
                                            DateTime(timezone=True), 
                                            server_default=func.now()
                                         )
    
    # Relations
    products: Mapped[list["Product"]] = relationship(
        "Product", 
        back_populates="category",
        lazy="select"
        # lazy="select" = charge les produits seulement quand on y accède
    )
    
    def __repr__(self) -> str:
        return f"<Category id={self.id} name='{self.name}'>"


# ─────────────────────────────────────────────────────────────
# MODEL 2 : BRAND
# ─────────────────────────────────────────────────────────────
class Brand(Base):
    """
    Représente un fabricant (NVIDIA, AMD, Intel...).
    
    SQL Table: brands
    """
    __tablename__ = "brands"
    
    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:       Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    slug:       Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    country:    Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website:    Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime]      = mapped_column(
                                          DateTime(timezone=True),
                                          server_default=func.now()
                                        )
    
    # Relation vers les produits
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="brand"
    )
    
    def __repr__(self) -> str:
        return f"<Brand id={self.id} name='{self.name}'>"


# ─────────────────────────────────────────────────────────────
# MODEL 3 : PRODUCT (Principal)
# ─────────────────────────────────────────────────────────────
class Product(Base):
    """
    Représente un produit (GPU, CPU, RAM...).
    
    SQL Table: products
    
    La colonne 'specs' est un JSONB qui contient les
    attributs techniques spécifiques à chaque catégorie.
    """
    __tablename__ = "products"
    
    # ── Identification ───────────────────────────────────────
    id:   Mapped[int]           = mapped_column(Integer, primary_key=True)
    sku:  Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    name: Mapped[str]           = mapped_column(String(300), nullable=False)
    
    # ── Clés étrangères ──────────────────────────────────────
    brand_id:    Mapped[Optional[int]] = mapped_column(
                                           Integer,
                                           ForeignKey("brands.id"),
                                           nullable=True
                                         )
    category_id: Mapped[Optional[int]] = mapped_column(
                                           Integer,
                                           ForeignKey("categories.id"),
                                           nullable=True
                                         )
    
    # ── Prix et stock ─────────────────────────────────────────
    price: Mapped[Optional[Decimal]] = mapped_column(
                                         Numeric(10, 2),
                                         nullable=True
                                       )
    stock: Mapped[int]               = mapped_column(
                                         Integer,
                                         nullable=False,
                                         default=0
                                       )
    
    # ── Spécifications (JSONB) ────────────────────────────────
    specs: Mapped[dict[str, Any]] = mapped_column(
                                      JSONB,
                                      nullable=False,
                                      default=dict
                                      # default=dict → {} par défaut
                                    )
    
    # ── Texte ─────────────────────────────────────────────────
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ── Statut ────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
                                Boolean,
                                nullable=False,
                                default=True
                              )
    
    # ── Timestamps ────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
                                     DateTime(timezone=True),
                                     server_default=func.now()
                                   )
    updated_at: Mapped[datetime] = mapped_column(
                                     DateTime(timezone=True),
                                     server_default=func.now(),
                                     onupdate=func.now()
                                     # onupdate : mis à jour automatiquement
                                   )
    
    # ── Relations ─────────────────────────────────────────────
    brand: Mapped[Optional["Brand"]] = relationship(
        "Brand",
        back_populates="products"
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="products"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan"
        # cascade : si on supprime le produit, ses images sont supprimées
    )
    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Product id={self.id} name='{self.name[:30]}' price={self.price}>"
    
    def to_dict(self) -> dict:
        """Convertit le modèle en dictionnaire (pour l'API JSON)."""
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "price": float(self.price) if self.price else None,
            "stock": self.stock,
            "specs": self.specs,
            "description": self.description,
            "is_active": self.is_active,
            "brand": self.brand.name if self.brand else None,
            "category": self.category.name if self.category else None,
        }


# ─────────────────────────────────────────────────────────────
# MODEL 4 : PRODUCT IMAGE
# ─────────────────────────────────────────────────────────────
class ProductImage(Base):
    __tablename__ = "product_images"
    
    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int]           = mapped_column(
                                          Integer,
                                          ForeignKey("products.id"),
                                          nullable=False
                                        )
    url:        Mapped[str]           = mapped_column(String(500), nullable=False)
    alt_text:   Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_primary: Mapped[bool]          = mapped_column(Boolean, default=False)
    sort_order: Mapped[int]           = mapped_column(Integer, default=0)
    created_at: Mapped[datetime]      = mapped_column(
                                          DateTime(timezone=True),
                                          server_default=func.now()
                                        )
    
    product: Mapped["Product"] = relationship("Product", back_populates="images")


# ─────────────────────────────────────────────────────────────
# MODEL 5 : COMPATIBILITY RULE
# ─────────────────────────────────────────────────────────────
class CompatibilityRule(Base):
    __tablename__ = "compatibility_rules"
    
    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    category_a:   Mapped[str]           = mapped_column(String(50), nullable=False)
    spec_key_a:   Mapped[str]           = mapped_column(String(50), nullable=False)
    spec_val_a:   Mapped[str]           = mapped_column(String(100), nullable=False)
    category_b:   Mapped[str]           = mapped_column(String(50), nullable=False)
    spec_key_b:   Mapped[str]           = mapped_column(String(50), nullable=False)
    spec_val_b:   Mapped[str]           = mapped_column(String(100), nullable=False)
    is_compatible: Mapped[bool]         = mapped_column(Boolean, default=True)
    note:         Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:   Mapped[datetime]      = mapped_column(
                                            DateTime(timezone=True),
                                            server_default=func.now()
                                          )
    
    def __repr__(self) -> str:
        return (f"<CompatibilityRule {self.category_a}.{self.spec_key_a}="
                f"{self.spec_val_a} ↔ {self.category_b}.{self.spec_key_b}="
                f"{self.spec_val_b}>")


# ─────────────────────────────────────────────────────────────
# MODEL 6 : PRICE HISTORY
# ─────────────────────────────────────────────────────────────
class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id:          Mapped[int]      = mapped_column(Integer, primary_key=True)
    product_id:  Mapped[int]      = mapped_column(
                                      Integer,
                                      ForeignKey("products.id"),
                                      nullable=False
                                    )
    price:       Mapped[Decimal]  = mapped_column(Numeric(10, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
                                      DateTime(timezone=True),
                                      server_default=func.now()
                                    )
    
    product: Mapped["Product"] = relationship("Product", back_populates="price_history")
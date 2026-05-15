#!/usr/bin/env python3
"""
Cleanup script — smaže testovací data, zachová kategorie a typy konfigurátoru.

Spuštění (z adresáře jullsjewels/):
    python cleanup.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import (
    Attribute,
    AttributeOption,
    BlogPost,
    Category,
    ConfiguratorDimension,
    ConfiguratorType,
    CustomDesign,
    Modifier,
    Order,
    OrderItem,
    Product,
    ProductImage,
    ProductVariant,
    Tag,
    WishlistItem,
)
from app.models.tag import product_tags
from app.models.attribute import product_attribute_options


def main():
    db = SessionLocal()
    try:
        counts = {
            "Produkty":              db.query(Product).count(),
            "Blog příspěvky":        db.query(BlogPost).count(),
            "Objednávky":            db.query(Order).count(),
            "Tagy":                  db.query(Tag).count(),
            "Dimenze konfigurátoru": db.query(ConfiguratorDimension).count(),
            "Wishlist položky":      db.query(WishlistItem).count(),
            "Custom designs":        db.query(CustomDesign).count(),
        }
        kept = {
            "Kategorie":             db.query(Category).count(),
            "Typy konfigurátoru":    db.query(ConfiguratorType).count(),
        }

        print("\n=== CLEANUP SKRIPT — Jullsjewels ===\n")
        print("Bude SMAZÁNO:")
        for k, v in counts.items():
            print(f"  {k}: {v}")
        print("\nBude ZACHOVÁNO:")
        for k, v in kept.items():
            print(f"  {k}: {v}")

        print("\nPOZOR: Tato operace je nevratná!")
        confirm = input("Pokračovat? (napište 'ano'): ").strip().lower()
        if confirm != "ano":
            print("Zrušeno.")
            return

        print("\nMaže se...")

        db.query(OrderItem).delete(synchronize_session=False)
        db.query(Order).delete(synchronize_session=False)
        print("  ✓ Objednávky")

        db.query(WishlistItem).delete(synchronize_session=False)
        print("  ✓ Wishlist")

        db.query(CustomDesign).delete(synchronize_session=False)
        print("  ✓ Custom designs")

        db.execute(product_tags.delete())
        db.execute(product_attribute_options.delete())
        db.query(ProductImage).delete(synchronize_session=False)
        db.query(ProductVariant).delete(synchronize_session=False)
        db.query(Product).delete(synchronize_session=False)
        print("  ✓ Produkty (obrázky, varianty, tagy, atributy)")

        db.query(BlogPost).delete(synchronize_session=False)
        print("  ✓ Blog příspěvky")

        db.query(Tag).delete(synchronize_session=False)
        print("  ✓ Tagy")

        db.query(Modifier).delete(synchronize_session=False)
        db.query(ConfiguratorDimension).delete(synchronize_session=False)
        print("  ✓ Dimenze a volby konfigurátoru (typy zachovány)")

        db.commit()

        n_cats = db.query(Category).count()
        n_types = db.query(ConfiguratorType).count()
        print(f"\n✓ Hotovo! Zachováno: {n_cats} kategorií, {n_types} typů konfigurátoru.")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Chyba: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
Spuštění: python seed.py
Vytvoří databázi a naplní ji testovacími daty.
"""
import bcrypt

from app.database import engine, Base, SessionLocal
import app.models  # noqa: F401 — zajistí registraci všech modelů

from app.models import (
    Category, Product, ProductImage, ProductVariant,
    ConfiguratorType, ConfiguratorDimension, Modifier,
    BlogPost, User, UserRole,
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def add_dimension(db, ctype, name_cs, name_en, slug, sort_order, options, is_required=True):
    """Přidá dimenzi a její volby. options = [(name_cs, name_en, price, is_default, sort)]"""
    dim = ConfiguratorDimension(
        configurator_type_id=ctype.id,
        name_cs=name_cs,
        name_en=name_en,
        slug=slug,
        sort_order=sort_order,
        is_required=is_required,
    )
    db.add(dim)
    db.flush()
    for i, (cs, en, price, default) in enumerate(options):
        db.add(Modifier(
            dimension_id=dim.id,
            name_cs=cs,
            name_en=en,
            price_modifier=price,
            is_default=default,
            sort_order=i,
        ))
    return dim


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # --- Uživatelé ---
        admin = User(
            email="admin@jullsjewels.cz",
            hashed_password=hash_password("admin123"),
            role=UserRole.admin,
            first_name="Admin",
            last_name="Jewels",
        )
        db.add(admin)

        # --- Kategorie ---
        rings = Category(title_cs="Prsteny", title_en="Rings", slug="rings")
        necklaces_cat = Category(title_cs="Náhrdelníky", title_en="Necklaces", slug="necklaces")
        bracelets_cat = Category(title_cs="Náramky", title_en="Bracelets", slug="bracelets")
        db.add_all([rings, necklaces_cat, bracelets_cat])
        db.flush()

        # --- Produkty ---
        p1 = Product(
            category_id=rings.id,
            title_cs="Zlatý prsten s rubínem",
            title_en="Gold Ring with Ruby",
            slug="gold-ring-ruby",
            description_cs="Ručně vyráběný zlatý prsten s přírodním rubínem.",
            description_en="Handcrafted gold ring with a natural ruby.",
            base_price=2490.00,
        )
        p2 = Product(
            category_id=necklaces_cat.id,
            title_cs="Stříbrný náhrdelník s přívěskem",
            title_en="Silver Necklace with Pendant",
            slug="silver-necklace-pendant",
            description_cs="Jemný stříbrný náhrdelník s ručně rytým přívěskem.",
            description_en="Delicate silver necklace with a hand-engraved pendant.",
            base_price=1290.00,
        )
        db.add_all([p1, p2])
        db.flush()

        db.add(ProductImage(product_id=p1.id, image_url="/static/uploads/placeholder.jpg", sort_order=0))
        db.add(ProductImage(product_id=p2.id, image_url="/static/uploads/placeholder.jpg", sort_order=0))
        db.add(ProductVariant(product_id=p1.id, name_cs="Velikost 52", name_en="Size 52", price_modifier=0, stock=3))
        db.add(ProductVariant(product_id=p1.id, name_cs="Velikost 54", name_en="Size 54", price_modifier=0, stock=2))

        # ----------------------------------------------------------------
        # Konfigurátor — Náhrdelník na míru
        # ----------------------------------------------------------------
        necklace_type = ConfiguratorType(
            name_cs="Náhrdelník na míru",
            name_en="Custom Necklace",
            slug="custom-necklace",
            base_price=800.00,
        )
        db.add(necklace_type)
        db.flush()

        add_dimension(db, necklace_type, "Materiál", "Material", "material", sort_order=0, options=[
            ("Stříbro 925", "Silver 925",    0,   True),
            ("Zlato 14k",   "Gold 14k",      800, False),
            ("Rosé zlato",  "Rose Gold 14k", 900, False),
        ])
        add_dimension(db, necklace_type, "Délka řetízku", "Chain Length", "chain-length", sort_order=1, options=[
            ("40 cm", "40 cm", 0,   True),
            ("45 cm", "45 cm", 50,  False),
            ("50 cm", "50 cm", 80,  False),
            ("60 cm", "60 cm", 120, False),
        ])
        add_dimension(db, necklace_type, "Typ řetízku", "Chain Style", "chain-style", sort_order=2, options=[
            ("Kulatý (Rolo)",   "Round (Rolo)",   0,   True),
            ("Plochý (Figaro)", "Flat (Figaro)",  100, False),
            ("Venezia",         "Venezia",        150, False),
        ])
        add_dimension(db, necklace_type, "Přívěsek", "Pendant", "pendant", sort_order=3, options=[
            ("Bez přívěsku", "No pendant", 0,   True),
            ("Srdce",        "Heart",      250, False),
            ("Hvězda",       "Star",       250, False),
            ("Měsíc",        "Moon",       300, False),
            ("Kapka",        "Drop",       200, False),
        ])
        add_dimension(db, necklace_type, "Kámen", "Stone", "stone", sort_order=4, is_required=False, options=[
            ("Bez kamene", "No stone",  0,   True),
            ("Rubín",      "Ruby",      350, False),
            ("Safír",      "Sapphire",  350, False),
            ("Smaragd",    "Emerald",   400, False),
            ("Zirkon",     "Zircon",    150, False),
        ])
        add_dimension(db, necklace_type, "Gravírování", "Engraving", "engraving", sort_order=5, is_required=False, options=[
            ("Bez gravírování", "No engraving", 0,   True),
            ("Iniciály (2 písmena)", "Initials (2 letters)", 200, False),
            ("Krátký text (do 15 znaků)", "Short text (up to 15 chars)", 350, False),
        ])

        # ----------------------------------------------------------------
        # Konfigurátor — Náramek na míru
        # ----------------------------------------------------------------
        bracelet_type = ConfiguratorType(
            name_cs="Náramek na míru",
            name_en="Custom Bracelet",
            slug="custom-bracelet",
            base_price=600.00,
        )
        db.add(bracelet_type)
        db.flush()

        add_dimension(db, bracelet_type, "Materiál", "Material", "material", sort_order=0, options=[
            ("Stříbro 925", "Silver 925",    0,   True),
            ("Zlato 14k",   "Gold 14k",      600, False),
            ("Rosé zlato",  "Rose Gold 14k", 700, False),
        ])
        add_dimension(db, bracelet_type, "Délka náramku", "Bracelet Length", "bracelet-length", sort_order=1, options=[
            ("16 cm", "16 cm", 0,  True),
            ("18 cm", "18 cm", 30, False),
            ("20 cm", "20 cm", 60, False),
        ])
        add_dimension(db, bracelet_type, "Typ řetízku", "Chain Style", "chain-style", sort_order=2, options=[
            ("Kulatý (Rolo)",   "Round (Rolo)",  0,   True),
            ("Plochý (Figaro)", "Flat (Figaro)", 80,  False),
            ("Tenký (Snake)",   "Thin (Snake)",  100, False),
        ])
        add_dimension(db, bracelet_type, "Přívěsek / Charm", "Charm", "charm", sort_order=3, is_required=False, options=[
            ("Bez charmu",  "No charm", 0,   True),
            ("Srdce",       "Heart",    200, False),
            ("Hvězda",      "Star",     200, False),
            ("Čtyřlístek",  "Clover",   220, False),
            ("Motýl",       "Butterfly", 240, False),
        ])
        add_dimension(db, bracelet_type, "Zapínání", "Clasp", "clasp", sort_order=4, options=[
            ("Karabinka", "Lobster clasp", 0,  True),
            ("Magnetické", "Magnetic",     150, False),
        ])
        add_dimension(db, bracelet_type, "Gravírování", "Engraving", "engraving", sort_order=5, is_required=False, options=[
            ("Bez gravírování", "No engraving", 0,   True),
            ("Iniciály (2 písmena)", "Initials (2 letters)", 180, False),
            ("Krátký text (do 15 znaků)", "Short text (up to 15 chars)", 300, False),
        ])

        # --- Blog ---
        db.add(BlogPost(
            title_cs="Jak pečovat o stříbrné šperky",
            title_en="How to Care for Silver Jewelry",
            slug="care-for-silver-jewelry",
            excerpt_cs="Stříbrné šperky si zaslouží péči. Přečtěte si naše tipy.",
            excerpt_en="Silver jewelry deserves care. Read our tips.",
            is_published=True,
        ))

        db.commit()
        print("Seed dokoncen.")
        print(f"  Konfigurátor typy: náhrdelník ({necklace_type.id}), náramek ({bracelet_type.id})")
    except Exception as e:
        db.rollback()
        print(f"Chyba: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

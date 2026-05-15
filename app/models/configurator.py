from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ConfiguratorType(Base):
    """Druh šperku, který lze konfigurovat (náhrdelník, náramek, prsten…)."""
    __tablename__ = "configurator_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_cs: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # "layered" = vrstvené PNG preview | "bead_chain" = SVG korálkový řetěz
    layout_mode: Mapped[str] = mapped_column(String(20), default="layered", nullable=False)

    dimensions: Mapped[list["ConfiguratorDimension"]] = relationship(
        "ConfiguratorDimension",
        back_populates="configurator_type",
        order_by="ConfiguratorDimension.sort_order",
        cascade="all, delete-orphan",
    )
    designs: Mapped[list["CustomDesign"]] = relationship(
        "CustomDesign", back_populates="configurator_type", passive_deletes=True,
    )


class ConfiguratorDimension(Base):
    """Co lze na daném šperku konfigurovat (materiál, délka řetízku, přívěsek…).
    Admin přidává dimenze v panelu — frontend je renderuje dynamicky."""
    __tablename__ = "configurator_dimensions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    configurator_type_id: Mapped[int] = mapped_column(ForeignKey("configurator_types.id"), nullable=False)
    name_cs: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("configurator_type_id", "slug", name="uq_dimension_type_slug"),
    )

    configurator_type: Mapped["ConfiguratorType"] = relationship("ConfiguratorType", back_populates="dimensions")
    modifiers: Mapped[list["Modifier"]] = relationship(
        "Modifier",
        back_populates="dimension",
        order_by="Modifier.sort_order",
        cascade="all, delete-orphan",
    )


class Modifier(Base):
    """Jedna volba v rámci dimenze (např. 'Zlato' v dimenzi 'Materiál')."""
    __tablename__ = "modifiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dimension_id: Mapped[int] = mapped_column(ForeignKey("configurator_dimensions.id"), nullable=False)
    name_cs: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    price_modifier: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    image_asset_path: Mapped[Optional[str]] = mapped_column(String(500))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Bead chain builder pole
    color_hex: Mapped[Optional[str]] = mapped_column(String(7))     # barva korálu v SVG (#rrggbb)
    bead_count: Mapped[Optional[int]] = mapped_column(Integer)      # pro délkové modifikátory: počet korálků

    dimension: Mapped["ConfiguratorDimension"] = relationship("ConfiguratorDimension", back_populates="modifiers")


class CustomDesign(Base):
    """Uložená konfigurace zákazníka.
    configuration_json: {dimension_id: modifier_id, ...} — flexibilní pro libovolný počet dimenzí."""
    __tablename__ = "custom_designs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    configurator_type_id: Mapped[int] = mapped_column(ForeignKey("configurator_types.id"), nullable=False)
    configuration_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    customer_note: Mapped[Optional[str]] = mapped_column(Text)
    preview_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    final_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    configurator_type: Mapped["ConfiguratorType"] = relationship("ConfiguratorType", back_populates="designs")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="custom_design")

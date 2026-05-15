from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

product_attribute_options = Table(
    "product_attribute_options",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("attribute_option_id", ForeignKey("attribute_options.id", ondelete="CASCADE"), primary_key=True),
)


class Attribute(Base):
    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_cs: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    options: Mapped[list["AttributeOption"]] = relationship(
        "AttributeOption", back_populates="attribute",
        cascade="all, delete-orphan", order_by="AttributeOption.value_cs",
    )


class AttributeOption(Base):
    __tablename__ = "attribute_options"
    __table_args__ = (UniqueConstraint("attribute_id", "slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False
    )
    value_cs: Mapped[str] = mapped_column(String(100), nullable=False)
    value_en: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)

    attribute: Mapped["Attribute"] = relationship("Attribute", back_populates="options")
    products: Mapped[list["Product"]] = relationship(
        "Product", secondary=product_attribute_options, back_populates="attribute_options"
    )

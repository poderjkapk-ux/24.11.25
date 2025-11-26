# inventory_models.py
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import text
from datetime import datetime
from models import Base, Product  # Імпортуємо Base та Product з основного файлу

# --- ДОВІДНИКИ ---

class Unit(Base):
    """Одиниці виміру (кг, л, шт)"""
    __tablename__ = 'units'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(20), unique=True)  # кг, л, шт
    is_weighable: Mapped[bool] = mapped_column(sa.Boolean, default=True) # Чи можна ділити (кг - так, банка - ні)

class Warehouse(Base):
    """Склади (Кухня, Бар, Основний склад)"""
    __tablename__ = 'warehouses'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(100))
    
    stocks: Mapped[list["Stock"]] = relationship("Stock", back_populates="warehouse")

class Supplier(Base):
    """Контрагенти (Постачальники)"""
    __tablename__ = 'suppliers'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(100))
    phone: Mapped[str] = mapped_column(sa.String(50), nullable=True)
    contact_person: Mapped[str] = mapped_column(sa.String(100), nullable=True)

class Ingredient(Base):
    """Інгредієнти (Сировина: Борошно, Томати, М'ясо)"""
    __tablename__ = 'ingredients'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(100))
    unit_id: Mapped[int] = mapped_column(sa.ForeignKey('units.id'))
    
    # Поточна собівартість (середня або остання ціна закупівлі)
    current_cost: Mapped[float] = mapped_column(sa.Numeric(10, 2), default=0.00)
    
    unit: Mapped["Unit"] = relationship("Unit")
    stocks: Mapped[list["Stock"]] = relationship("Stock", back_populates="ingredient")

# --- ТЕХНОЛОГІЧНІ КАРТИ ---

class TechCard(Base):
    """Технологічна карта страви (Зв'язок Продукт -> Набір інгредієнтів)"""
    __tablename__ = 'tech_cards'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(sa.ForeignKey('products.id'), unique=True)
    
    # Інструкція (технологія приготування) для кухаря
    cooking_method: Mapped[str] = mapped_column(sa.Text, nullable=True) 
    
    product: Mapped["Product"] = relationship("Product")
    components: Mapped[list["TechCardItem"]] = relationship("TechCardItem", back_populates="tech_card", cascade="all, delete-orphan")

class TechCardItem(Base):
    """Рядок технологічної карти (Інгредієнт + кількість)"""
    __tablename__ = 'tech_card_items'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tech_card_id: Mapped[int] = mapped_column(sa.ForeignKey('tech_cards.id'))
    ingredient_id: Mapped[int] = mapped_column(sa.ForeignKey('ingredients.id'))
    
    gross_amount: Mapped[float] = mapped_column(sa.Numeric(10, 3)) # Брутто (скільки списати зі складу)
    net_amount: Mapped[float] = mapped_column(sa.Numeric(10, 3))   # Нетто (скільки йде в готову страву)
    
    tech_card: Mapped["TechCard"] = relationship("TechCard", back_populates="components")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient")

# --- СКЛАДСЬКИЙ ОБЛІК ---

class Stock(Base):
    """Залишки на складах"""
    __tablename__ = 'stocks'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(sa.ForeignKey('warehouses.id'))
    ingredient_id: Mapped[int] = mapped_column(sa.ForeignKey('ingredients.id'))
    quantity: Mapped[float] = mapped_column(sa.Numeric(10, 3), default=0.000)
    
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="stocks")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="stocks")

class InventoryDoc(Base):
    """Документ руху (Накладна)"""
    __tablename__ = 'inventory_docs'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Типи: supply (прихід), transfer (переміщення), writeoff (списання), deduction (авто-списання по чеку)
    doc_type: Mapped[str] = mapped_column(sa.String(20)) 
    
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.now)
    
    # Прапорець: чи проведено документ (чи вплинув він на залишки)
    is_processed: Mapped[bool] = mapped_column(sa.Boolean, default=False, server_default=text("false"))
    
    supplier_id: Mapped[int | None] = mapped_column(sa.ForeignKey('suppliers.id'), nullable=True)
    source_warehouse_id: Mapped[int | None] = mapped_column(sa.ForeignKey('warehouses.id'), nullable=True)
    target_warehouse_id: Mapped[int | None] = mapped_column(sa.ForeignKey('warehouses.id'), nullable=True)
    
    comment: Mapped[str] = mapped_column(sa.String(255), nullable=True)
    # Якщо це списання на основі продажу, тут буде ID замовлення
    linked_order_id: Mapped[int | None] = mapped_column(sa.ForeignKey('orders.id'), nullable=True) 
    
    items: Mapped[list["InventoryDocItem"]] = relationship("InventoryDocItem", back_populates="doc", cascade="all, delete-orphan")
    
    supplier: Mapped["Supplier"] = relationship("Supplier")
    source_warehouse: Mapped["Warehouse"] = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    target_warehouse: Mapped["Warehouse"] = relationship("Warehouse", foreign_keys=[target_warehouse_id])

class InventoryDocItem(Base):
    """Позиція в накладній"""
    __tablename__ = 'inventory_doc_items'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(sa.ForeignKey('inventory_docs.id'))
    ingredient_id: Mapped[int] = mapped_column(sa.ForeignKey('ingredients.id'))
    quantity: Mapped[float] = mapped_column(sa.Numeric(10, 3))
    price: Mapped[float] = mapped_column(sa.Numeric(10, 2), default=0.00) # Ціна закупівлі (для приходу)
    
    doc: Mapped["InventoryDoc"] = relationship("InventoryDoc", back_populates="items")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient")
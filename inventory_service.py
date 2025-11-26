# inventory_service.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from decimal import Decimal
from sqlalchemy.orm import joinedload

from inventory_models import (
    Stock, InventoryDoc, InventoryDocItem, TechCard, 
    TechCardItem, Ingredient, Warehouse
)
from models import Order, OrderItem

logger = logging.getLogger(__name__)

async def get_stock(session: AsyncSession, warehouse_id: int, ingredient_id: int) -> Stock:
    """
    Отримує запис про залишки товару на складі.
    Якщо запису немає, створює новий з нульовим залишком.
    """
    res = await session.execute(
        select(Stock).where(Stock.warehouse_id == warehouse_id, Stock.ingredient_id == ingredient_id)
    )
    stock = res.scalars().first()
    if not stock:
        stock = Stock(warehouse_id=warehouse_id, ingredient_id=ingredient_id, quantity=0)
        session.add(stock)
        await session.flush() # Щоб отримати ID
    return stock

async def process_movement(session: AsyncSession, doc_type: str, items: list, 
                           source_wh_id: int = None, target_wh_id: int = None, 
                           supplier_id: int = None, comment: str = "", order_id: int = None):
    """
    Універсальна функція для автоматичного створення та проведення документа.
    items = [{'ingredient_id': 1, 'qty': 1.5, 'price': 100}, ...]
    """
    doc = InventoryDoc(
        doc_type=doc_type,
        source_warehouse_id=source_wh_id,
        target_warehouse_id=target_wh_id,
        supplier_id=supplier_id,
        comment=comment,
        linked_order_id=order_id,
        is_processed=False # Спочатку створюємо непроведений документ
    )
    session.add(doc)
    await session.flush()

    for item in items:
        ing_id = int(item['ingredient_id'])
        qty = Decimal(str(item['qty']))
        price = Decimal(str(item.get('price', 0)))

        doc_item = InventoryDocItem(doc_id=doc.id, ingredient_id=ing_id, quantity=qty, price=price)
        session.add(doc_item)

    # Відразу проводимо документ (оновлюємо залишки)
    await apply_doc_stock_changes(session, doc.id)
    return doc

async def apply_doc_stock_changes(session: AsyncSession, doc_id: int):
    """
    Проводить документ: оновлює залишки на складах на основі позицій документа.
    Встановлює прапорець is_processed = True.
    """
    doc = await session.get(InventoryDoc, doc_id, options=[joinedload(InventoryDoc.items)])
    if not doc: raise ValueError("Документ не знайдено")
    if doc.is_processed: raise ValueError("Документ вже проведено")

    for item in doc.items:
        qty = Decimal(str(item.quantity))
        
        if doc.doc_type == 'supply': # Прихід
            if not doc.target_warehouse_id: raise ValueError("Не вказано склад отримувача")
            stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            stock.quantity += qty
            
            # Оновлюємо собівартість інгредієнта (спрощено - за останнім приходом)
            if item.price > 0:
                await session.execute(update(Ingredient).where(Ingredient.id == item.ingredient_id).values(current_cost=item.price))

        elif doc.doc_type == 'transfer': # Переміщення
            if not doc.source_warehouse_id or not doc.target_warehouse_id: raise ValueError("Потрібні обидва склади (джерело та ціль)")
            src_stock = await get_stock(session, doc.source_warehouse_id, item.ingredient_id)
            tgt_stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            src_stock.quantity -= qty
            tgt_stock.quantity += qty

        elif doc.doc_type in ['writeoff', 'deduction']: # Списання (в т.ч. по продажу)
            if not doc.source_warehouse_id: raise ValueError("Не вказано склад списання")
            stock = await get_stock(session, doc.source_warehouse_id, item.ingredient_id)
            stock.quantity -= qty

    doc.is_processed = True
    await session.commit()

async def deduct_products_by_tech_card(session: AsyncSession, order: Order):
    """
    Списання продуктів по замовленню на основі техкарт.
    Викликається при готовності/продажу страви.
    """
    if not order.items: return

    # Визначаємо склад списания.
    # Завантажуємо маппінг складів (Пошук за назвою)
    kitchen_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Кухня%')).limit(1))
    bar_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Бар%')).limit(1))
    
    wh_map = {
        'kitchen': kitchen_wh.id if kitchen_wh else None,
        'bar': bar_wh.id if bar_wh else None
    }

    deduction_items_by_wh = {} # {warehouse_id: [{ing_id, qty}, ...]}

    for order_item in order.items:
        # Шукаємо техкарту для продукту
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(select(TechCardItem).joinedload(TechCardItem.ingredient))
        )
        
        if not tech_card:
            logger.warning(f"Немає техкарти для {order_item.product_name}. Списання не проведено.")
            continue

        wh_id = wh_map.get(order_item.preparation_area)
        if not wh_id: 
            # Якщо не знайшли склад по зоні, списуємо з "Кухні" або першого-ліпшого (fallback)
            wh_id = kitchen_wh.id if kitchen_wh else 1 

        if wh_id not in deduction_items_by_wh:
            deduction_items_by_wh[wh_id] = []

        for component in tech_card.components:
            total_qty = Decimal(component.gross_amount) * order_item.quantity
            deduction_items_by_wh[wh_id].append({
                'ingredient_id': component.ingredient_id,
                'qty': total_qty
            })

    # Проводимо документи списання для кожного складу
    for wh_id, items in deduction_items_by_wh.items():
        if items:
            await process_movement(
                session, 'deduction', items, 
                source_wh_id=wh_id, 
                comment=f"Замовлення #{order.id}", 
                order_id=order.id
            )
            
async def generate_cook_ticket(session: AsyncSession, order_id: int) -> str:
    """Генерує HTML бігунка для кухаря (з рецептом)"""
    order = await session.get(Order, order_id)
    query = select(OrderItem).where(OrderItem.order_id == order_id)
    items = (await session.execute(query)).scalars().all()
    
    html = f"""
    <div style="font-family: 'Courier New', monospace; width: 300px; padding: 10px; border: 1px solid #000;">
        <h3 style="text-align:center; margin: 0;">👨‍🍳 БІГУНОК</h3>
        <div style="text-align:center; margin-bottom: 10px;">Замовлення #{order.id} | {order.delivery_time}</div>
        <hr style="border-top: 1px dashed #000;">
    """
    
    for item in items:
        # Підтягуємо рецепт
        tc = await session.scalar(select(TechCard).where(TechCard.product_id == item.product_id))
        
        html += f"<div style='font-size:1.2em; font-weight:bold; margin-top:10px;'>{item.product_name}</div>"
        html += f"<div style='font-size:1.1em;'>К-сть: {item.quantity}</div>"
        
        if tc and tc.cooking_method:
            html += f"<div style='font-size:0.8em; color:#333; margin-top:2px; font-style:italic;'>{tc.cooking_method}</div>"
            
    html += "<hr style='border-top: 1px dashed #000;'><div style='text-align:center; font-size:0.8em;'>Гарної роботи!</div></div>"
    html += "<script>window.print();</script>"
    return html
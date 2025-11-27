# inventory_service.py

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from decimal import Decimal
from sqlalchemy.orm import joinedload

from inventory_models import (
    Stock, InventoryDoc, InventoryDocItem, TechCard, 
    TechCardItem, Ingredient, Warehouse, Modifier
)
from models import Order, OrderItem

logger = logging.getLogger(__name__)

async def get_stock(session: AsyncSession, warehouse_id: int, ingredient_id: int) -> Stock:
    """
    Отримує запис про залишки товару на складі з блокуванням рядка для оновлення (FOR UPDATE).
    Якщо запису немає, створює новий з нульовим залишком.
    """
    res = await session.execute(
        select(Stock)
        .where(Stock.warehouse_id == warehouse_id, Stock.ingredient_id == ingredient_id)
        .with_for_update() # Блокуємо рядок від паралельних змін
    )
    stock = res.scalars().first()
    
    if not stock:
        # Якщо запису немає, створюємо новий
        stock = Stock(warehouse_id=warehouse_id, ingredient_id=ingredient_id, quantity=0)
        session.add(stock)
        await session.flush() # Щоб отримати ID
        
    return stock

async def process_movement(session: AsyncSession, doc_type: str, items: list, 
                           source_wh_id: int = None, target_wh_id: int = None, 
                           supplier_id: int = None, comment: str = "", order_id: int = None):
    """
    Універсальна функція для створення та проведення документа.
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
        # Безпечне перетворення в Decimal для уникнення помилок float
        qty = Decimal(str(item['qty']))
        price = Decimal(str(item.get('price', 0)))

        doc_item = InventoryDocItem(doc_id=doc.id, ingredient_id=ing_id, quantity=qty, price=price)
        session.add(doc_item)

    # Відразу проводимо документ (оновлюємо залишки)
    await apply_doc_stock_changes(session, doc.id)
    return doc

async def apply_doc_stock_changes(session: AsyncSession, doc_id: int):
    """
    Проводить документ: оновлює залишки на складах.
    Також перераховує собівартість за середньозваженою (Weighted Average) при приході.
    """
    doc = await session.get(InventoryDoc, doc_id, options=[joinedload(InventoryDoc.items)])
    if not doc: raise ValueError("Документ не знайдено")
    if doc.is_processed: raise ValueError("Документ вже проведено")

    for item in doc.items:
        qty = Decimal(str(item.quantity))
        
        if doc.doc_type == 'supply': # Прихід
            if not doc.target_warehouse_id: raise ValueError("Не вказано склад отримувач")
            
            # --- ЛОГІКА СЕРЕДНЬОЗВАЖЕНОЇ СОБІВАРТОСТІ ---
            if item.price > 0:
                # 1. Отримуємо поточний загальний залишок інгредієнта по ВСІХ складах
                total_qty_res = await session.execute(
                    select(func.sum(Stock.quantity)).where(Stock.ingredient_id == item.ingredient_id)
                )
                total_existing_qty = total_qty_res.scalar() or Decimal(0)
                
                # Якщо залишок мінусовий, вважаємо його як 0 для розрахунку ціни
                calc_existing_qty = total_existing_qty if total_existing_qty > 0 else Decimal(0)

                # 2. Отримуємо поточну собівартість
                ingredient = await session.get(Ingredient, item.ingredient_id)
                if ingredient:
                    old_cost = Decimal(str(ingredient.current_cost))
                    new_supply_price = Decimal(str(item.price))
                    
                    current_value = calc_existing_qty * old_cost
                    new_supply_value = qty * new_supply_price
                    
                    total_new_qty = calc_existing_qty + qty
                    
                    if total_new_qty > 0:
                        new_avg_cost = (current_value + new_supply_value) / total_new_qty
                        # Оновлюємо ціну в базі
                        ingredient.current_cost = new_avg_cost
                        session.add(ingredient)
            # ---------------------------------------------

            stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            stock.quantity += qty

        elif doc.doc_type == 'return': # Повернення на склад (скасування замовлення)
            if not doc.target_warehouse_id: raise ValueError("Не вказано склад для повернення")
            stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            stock.quantity += qty

        elif doc.doc_type == 'transfer': # Переміщення
            if not doc.source_warehouse_id or not doc.target_warehouse_id: raise ValueError("Потрібні обидва склади (джерело і ціль)")
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
    Автоматичне списання продуктів (і модифікаторів) зі складу на основі техкарт.
    Викликається при готовності/продажу страви.
    """
    # Перевірка на повторне списання
    if order.is_inventory_deducted:
        logger.info(f"Склад для замовлення #{order.id} вже був списаний раніше. Пропускаємо.")
        return

    if not order.items: 
        order.is_inventory_deducted = True
        await session.commit()
        return

    # Визначаємо склади списання
    kitchen_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Кухня%')).limit(1))
    bar_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Бар%')).limit(1))
    
    # Резервний склад (перший знайдений або ID 1), якщо Кухня/Бар не знайдені за назвою
    first_wh = await session.scalar(select(Warehouse).limit(1))
    fallback_wh_id = first_wh.id if first_wh else 1

    # Мапінг зон приготування до ID складів
    wh_map = {
        'kitchen': kitchen_wh.id if kitchen_wh else fallback_wh_id,
        'bar': bar_wh.id if bar_wh else fallback_wh_id
    }

    deduction_items_by_wh = {} # {warehouse_id: [{ingredient_id, qty}, ...]}

    def add_deduction(wh_id, ing_id, qty):
        if not wh_id: wh_id = fallback_wh_id
        if wh_id not in deduction_items_by_wh: deduction_items_by_wh[wh_id] = []
        deduction_items_by_wh[wh_id].append({'ingredient_id': ing_id, 'qty': qty})

    for order_item in order.items:
        # Визначаємо склад для цього товару
        wh_id = wh_map.get(order_item.preparation_area, fallback_wh_id)
        
        # 1. Списання компонентів страви (по Техкарті)
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(select(TechCardItem).joinedload(TechCardItem.ingredient))
        )
        
        if tech_card:
            for component in tech_card.components:
                # Decimal для точності
                gross = Decimal(str(component.gross_amount))
                qty_item = Decimal(str(order_item.quantity))
                total_qty = gross * qty_item
                add_deduction(wh_id, component.ingredient_id, total_qty)
        else:
            logger.warning(f"Для товару '{order_item.product_name}' (ID {order_item.product_id}) відсутня Техкарта. Списання інгредієнтів не відбудеться.")
        
        # 2. Списання компонентів МОДИФІКАТОРІВ
        if order_item.modifiers:
            for mod_data in order_item.modifiers:
                ing_id = mod_data.get('ingredient_id')
                ing_qty_val = mod_data.get('ingredient_qty')
                
                if ing_id and ing_qty_val:
                    total_mod_qty = Decimal(str(ing_qty_val)) * Decimal(str(order_item.quantity))
                    add_deduction(wh_id, ing_id, total_mod_qty)

    # Встановлюємо прапор списання (до коміту, щоб транзакція process_movement його захопила)
    order.is_inventory_deducted = True
    session.add(order)

    # Якщо нічого списувати
    if not deduction_items_by_wh:
        await session.commit()
        return

    # Проводимо документи списання для кожного складу
    for wh_id, items in deduction_items_by_wh.items():
        if items:
            await process_movement(
                session, 'deduction', items, 
                source_wh_id=wh_id, 
                comment=f"Замовлення #{order.id}", 
                order_id=order.id
            )
    
    logger.info(f"Списання продуктів для замовлення #{order.id} завершено успішно.")

async def reverse_deduction(session: AsyncSession, order: Order):
    """
    Повернення продуктів на склад при скасуванні замовлення.
    Створює документ типу 'return'.
    """
    if not order.is_inventory_deducted:
        logger.info(f"Замовлення #{order.id} ще не списано, повернення не потрібне.")
        return

    if not order.items:
        order.is_inventory_deducted = False
        await session.commit()
        return

    # Визначаємо склади (аналогічно списанню)
    kitchen_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Кухня%')).limit(1))
    bar_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Бар%')).limit(1))
    first_wh = await session.scalar(select(Warehouse).limit(1))
    fallback_wh_id = first_wh.id if first_wh else 1
    
    wh_map = {
        'kitchen': kitchen_wh.id if kitchen_wh else fallback_wh_id,
        'bar': bar_wh.id if bar_wh else fallback_wh_id
    }

    return_items_by_wh = {} 

    def add_return(wh_id, ing_id, qty):
        if not wh_id: wh_id = fallback_wh_id
        if wh_id not in return_items_by_wh: return_items_by_wh[wh_id] = []
        # Ціна 0, щоб не впливати на середньозважену собівартість при поверненні
        return_items_by_wh[wh_id].append({'ingredient_id': ing_id, 'qty': qty, 'price': 0})

    for order_item in order.items:
        wh_id = wh_map.get(order_item.preparation_area, fallback_wh_id)
        
        # 1. Техкарта
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(select(TechCardItem).joinedload(TechCardItem.ingredient))
        )
        
        if tech_card:
            for component in tech_card.components:
                total_qty = Decimal(str(component.gross_amount)) * Decimal(str(order_item.quantity))
                add_return(wh_id, component.ingredient_id, total_qty)
        
        # 2. Модифікатори
        if order_item.modifiers:
            for mod_data in order_item.modifiers:
                ing_id = mod_data.get('ingredient_id')
                ing_qty_val = mod_data.get('ingredient_qty')
                if ing_id and ing_qty_val:
                    total_mod_qty = Decimal(str(ing_qty_val)) * Decimal(str(order_item.quantity))
                    add_return(wh_id, ing_id, total_mod_qty)

    # Створюємо документи повернення
    for wh_id, items in return_items_by_wh.items():
        if items:
            await process_movement(
                session, 'return', items, 
                target_wh_id=wh_id, # Повертаємо НА склад (target)
                comment=f"Повернення (Скасування) замовлення #{order.id}", 
                order_id=order.id
            )

    # Скидаємо прапор списання
    order.is_inventory_deducted = False
    await session.commit()
    logger.info(f"Склад успішно повернуто для замовлення #{order.id}")

async def generate_cook_ticket(session: AsyncSession, order_id: int) -> str:
    """Генерує HTML чек/бігунок для повара"""
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
        tc = await session.scalar(select(TechCard).where(TechCard.product_id == item.product_id))
        
        mods_html = ""
        if item.modifiers:
            mods_names = [m.get('name', '') for m in item.modifiers]
            if mods_names:
                mods_html = f"<div style='font-size:0.9em; font-weight:bold; margin-top:2px;'>+ {', '.join(mods_names)}</div>"

        html += f"<div style='font-size:1.2em; font-weight:bold; margin-top:10px;'>{item.product_name}</div>"
        html += f"{mods_html}"
        html += f"<div style='font-size:1.1em;'>К-сть: {item.quantity}</div>"
        
        if tc and tc.cooking_method:
            html += f"<div style='font-size:0.8em; color:#333; margin-top:2px; font-style:italic;'>{tc.cooking_method}</div>"
            
    html += "<hr style='border-top: 1px dashed #000;'><div style='text-align:center; font-size:0.8em;'>Гарної роботи!</div></div>"
    html += "<script>window.print();</script>"
    return html
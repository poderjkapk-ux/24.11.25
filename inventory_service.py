# inventory_service.py

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from decimal import Decimal
from sqlalchemy.orm import joinedload, selectinload

from inventory_models import (
    Stock, InventoryDoc, InventoryDocItem, TechCard, 
    TechCardItem, Ingredient, Warehouse, Modifier, AutoDeductionRule
)
from models import Order, OrderItem, Product

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
        is_processed=False 
    )
    # Важливо: додаємо документ в сесію, але items додамо через append, щоб оновити стан об'єкта в пам'яті
    session.add(doc) 
    
    for item in items:
        ing_id = int(item['ingredient_id'])
        # Безпечне перетворення в Decimal
        qty = Decimal(str(item['qty']))
        price = Decimal(str(item.get('price', 0)))

        # Створюємо item і додаємо до списку doc.items
        doc_item = InventoryDocItem(ingredient_id=ing_id, quantity=qty, price=price)
        doc.items.append(doc_item)

    await session.flush() # Зберігаємо і отримуємо ID для doc та items

    # Відразу проводимо документ
    await apply_doc_stock_changes(session, doc.id)
    return doc

async def apply_doc_stock_changes(session: AsyncSession, doc_id: int):
    """
    Проводить документ: оновлює залишки на складах.
    """
    # Використовуємо selectinload для колекцій в async (краща практика)
    stmt = select(InventoryDoc).where(InventoryDoc.id == doc_id).options(selectinload(InventoryDoc.items))
    result = await session.execute(stmt)
    doc = result.scalars().first()

    if not doc: raise ValueError("Документ не знайдено")
    if doc.is_processed: raise ValueError("Документ вже проведено")

    # Тепер doc.items гарантовано завантажено
    for item in doc.items:
        qty = Decimal(str(item.quantity))
        
        if doc.doc_type == 'supply': # Прихід
            if not doc.target_warehouse_id: raise ValueError("Не вказано склад отримувач")
            
            # --- ЛОГІКА СЕРЕДНЬОЗВАЖЕНОЇ СОБІВАРТОСТІ ---
            if item.price > 0:
                total_qty_res = await session.execute(
                    select(func.sum(Stock.quantity)).where(Stock.ingredient_id == item.ingredient_id)
                )
                total_existing_qty = total_qty_res.scalar() or Decimal(0)
                calc_existing_qty = total_existing_qty if total_existing_qty > 0 else Decimal(0)

                ingredient = await session.get(Ingredient, item.ingredient_id)
                if ingredient:
                    old_cost = Decimal(str(ingredient.current_cost))
                    new_supply_price = Decimal(str(item.price))
                    
                    current_value = calc_existing_qty * old_cost
                    new_supply_value = qty * new_supply_price
                    
                    total_new_qty = calc_existing_qty + qty
                    
                    if total_new_qty > 0:
                        new_avg_cost = (current_value + new_supply_value) / total_new_qty
                        ingredient.current_cost = new_avg_cost
                        session.add(ingredient)
            # ---------------------------------------------

            stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            stock.quantity += qty

        elif doc.doc_type == 'return': # Повернення (наприклад, при скасуванні замовлення)
            if not doc.target_warehouse_id: raise ValueError("Не вказано склад для повернення")
            stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            stock.quantity += qty

        elif doc.doc_type == 'transfer': # Переміщення
            if not doc.source_warehouse_id or not doc.target_warehouse_id: raise ValueError("Потрібні обидва склади")
            src_stock = await get_stock(session, doc.source_warehouse_id, item.ingredient_id)
            tgt_stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            src_stock.quantity -= qty
            tgt_stock.quantity += qty

        elif doc.doc_type in ['writeoff', 'deduction']: # Списання
            if not doc.source_warehouse_id: raise ValueError("Не вказано склад списання")
            stock = await get_stock(session, doc.source_warehouse_id, item.ingredient_id)
            stock.quantity -= qty

    doc.is_processed = True
    await session.commit()

async def deduct_products_by_tech_card(session: AsyncSession, order: Order):
    """
    Автоматичне списання продуктів (і модифікаторів, і упаковки) з відповідних складів/цехів.
    Враховує, чи є інгредієнт "тільки на винос" (is_takeaway).
    """
    if order.is_inventory_deducted:
        logger.info(f"Склад для замовлення #{order.id} вже був списаний раніше.")
        return

    # Перевірка на наявність items
    if not order.items: 
        order.is_inventory_deducted = True
        await session.commit()
        return

    # Fallback склад (якщо у товара не вказано цех, беремо перший знайдений)
    first_wh = await session.scalar(select(Warehouse).limit(1))
    fallback_wh_id = first_wh.id if first_wh else 1

    # Групуємо інгредієнти для списання по складах: {warehouse_id: [items]}
    deduction_items_by_wh = {} 

    def add_deduction(wh_id, ing_id, qty):
        if not wh_id: wh_id = fallback_wh_id
        if wh_id not in deduction_items_by_wh: deduction_items_by_wh[wh_id] = []
        deduction_items_by_wh[wh_id].append({'ingredient_id': ing_id, 'qty': qty})

    # --- ВИЗНАЧАЄМО, ЧИ ЗАМОВЛЕННЯ "НА ВИНОС" ---
    is_takeaway_order = order.is_delivery or order.order_type == 'pickup'

    # --- 1. СПИСАННЯ СТРАВ ТА МОДИФІКАТОРІВ ---
    for order_item in order.items:
        # 1.1 Визначаємо склад списання (Цех) для основної страви
        product = await session.get(Product, order_item.product_id)
        
        # Склад страви
        prod_wh_id = product.production_warehouse_id if (product and product.production_warehouse_id) else fallback_wh_id
        
        # 1.2 Шукаємо техкарту
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(joinedload(TechCard.components).joinedload(TechCardItem.ingredient))
        )
        
        # 1.3 Списуємо інгредієнти страви
        if tech_card:
            for component in tech_card.components:
                # --- ЛОГІКА ТІЛЬКИ НА ВИНОС ---
                # Якщо компонент (упаковка) тільки на винос, а замовлення В ЗАЛІ -> пропускаємо
                if component.is_takeaway and not is_takeaway_order:
                    continue
                # -------------------------------

                gross = Decimal(str(component.gross_amount))
                qty_item = Decimal(str(order_item.quantity))
                total_qty = gross * qty_item
                add_deduction(prod_wh_id, component.ingredient_id, total_qty)
        else:
            logger.warning(f"Для товару '{order_item.product_name}' (ID {order_item.product_id}) відсутня Техкарта.")
        
        # 1.4 Списуємо інгредієнти модифікаторів
        if order_item.modifiers:
            for mod_data in order_item.modifiers:
                # Отримуємо дані модифікатора з БД, щоб знати його склад (warehouse_id)
                mod_id = mod_data.get('id')
                if mod_id:
                    modifier_db = await session.get(Modifier, mod_id)
                    
                    if modifier_db and modifier_db.ingredient_id:
                        ing_qty_val = modifier_db.ingredient_qty
                        
                        # Визначаємо склад для модифікатора
                        # Якщо у модифікатора є свій склад -> беремо його.
                        # Якщо ні -> беремо склад основної страви.
                        mod_wh_id = modifier_db.warehouse_id if modifier_db.warehouse_id else prod_wh_id
                        
                        if ing_qty_val:
                            total_mod_qty = Decimal(str(ing_qty_val)) * Decimal(str(order_item.quantity))
                            add_deduction(mod_wh_id, modifier_db.ingredient_id, total_mod_qty)

    # --- 2. СПИСАННЯ УПАКОВКИ (Auto Rules - Загальні правила) ---
    # Визначаємо тригер: delivery, pickup або in_house
    trigger = 'in_house'
    if order.is_delivery: trigger = 'delivery'
    elif order.order_type == 'pickup': trigger = 'pickup'
    
    # Шукаємо правила для цього типу + загальні правила ('all')
    rules_res = await session.execute(
        select(AutoDeductionRule).where(
            AutoDeductionRule.trigger_type.in_([trigger, 'all'])
        )
    )
    rules = rules_res.scalars().all()
    
    for rule in rules:
        # Логіка: 1 правило = 1 списання на замовлення (наприклад, пакет)
        add_deduction(rule.warehouse_id, rule.ingredient_id, Decimal(str(rule.quantity)))

    # --- 3. ПРОВЕДЕННЯ ---
    order.is_inventory_deducted = True
    session.add(order)

    if not deduction_items_by_wh:
        await session.commit()
        return

    # Створюємо документи списання для кожного складу окремо
    for wh_id, items in deduction_items_by_wh.items():
        if items:
            await process_movement(
                session, 'deduction', items, 
                source_wh_id=wh_id, 
                comment=f"Замовлення #{order.id} (Авто-списання: {trigger})", 
                order_id=order.id
            )
    
    logger.info(f"Списання продуктів для замовлення #{order.id} завершено успішно по складах.")

async def reverse_deduction(session: AsyncSession, order: Order):
    """
    Повернення продуктів на склад (при скасуванні замовлення).
    Дзеркальна логіка до deduct_products_by_tech_card.
    """
    if not order.is_inventory_deducted:
        return

    if not order.items:
        order.is_inventory_deducted = False
        await session.commit()
        return

    # Fallback склад
    first_wh = await session.scalar(select(Warehouse).limit(1))
    fallback_wh_id = first_wh.id if first_wh else 1
    
    return_items_by_wh = {} 

    def add_return(wh_id, ing_id, qty):
        if not wh_id: wh_id = fallback_wh_id
        if wh_id not in return_items_by_wh: return_items_by_wh[wh_id] = []
        return_items_by_wh[wh_id].append({'ingredient_id': ing_id, 'qty': qty, 'price': 0})

    # --- ВИЗНАЧАЄМО, ЧИ ЗАМОВЛЕННЯ БУЛО "НА ВИНОС" ---
    is_takeaway_order = order.is_delivery or order.order_type == 'pickup'

    # --- 1. ПОВЕРНЕННЯ СТРАВ ТА МОДИФІКАТОРІВ ---
    for order_item in order.items:
        product = await session.get(Product, order_item.product_id)
        prod_wh_id = product.production_warehouse_id if (product and product.production_warehouse_id) else fallback_wh_id
        
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(joinedload(TechCard.components).joinedload(TechCardItem.ingredient))
        )
        
        if tech_card:
            for component in tech_card.components:
                # --- ЛОГІКА ТІЛЬКИ НА ВИНОС ---
                # Якщо компонент тільки на винос, а замовлення не було таким -> не повертаємо (бо не списували)
                if component.is_takeaway and not is_takeaway_order:
                    continue
                # -------------------------------

                total_qty = Decimal(str(component.gross_amount)) * Decimal(str(order_item.quantity))
                add_return(prod_wh_id, component.ingredient_id, total_qty)
        
        if order_item.modifiers:
            for mod_data in order_item.modifiers:
                mod_id = mod_data.get('id')
                if mod_id:
                    modifier_db = await session.get(Modifier, mod_id)
                    if modifier_db and modifier_db.ingredient_id:
                        ing_qty_val = modifier_db.ingredient_qty
                        
                        # Визначаємо той самий склад
                        mod_wh_id = modifier_db.warehouse_id if modifier_db.warehouse_id else prod_wh_id
                        
                        if ing_qty_val:
                            total_mod_qty = Decimal(str(ing_qty_val)) * Decimal(str(order_item.quantity))
                            add_return(mod_wh_id, modifier_db.ingredient_id, total_mod_qty)

    # --- 2. ПОВЕРНЕННЯ УПАКОВКИ (Auto Rules) ---
    trigger = 'in_house'
    if order.is_delivery: trigger = 'delivery'
    elif order.order_type == 'pickup': trigger = 'pickup'
    
    rules_res = await session.execute(
        select(AutoDeductionRule).where(
            AutoDeductionRule.trigger_type.in_([trigger, 'all'])
        )
    )
    rules = rules_res.scalars().all()
    
    for rule in rules:
        add_return(rule.warehouse_id, rule.ingredient_id, Decimal(str(rule.quantity)))

    # --- 3. ПРОВЕДЕННЯ ---
    for wh_id, items in return_items_by_wh.items():
        if items:
            await process_movement(
                session, 'return', items, 
                target_wh_id=wh_id, # Повертаємо НА цей склад
                comment=f"Повернення (Скасування) замовлення #{order.id}", 
                order_id=order.id
            )

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
        # Для бігунка корисно знати технологію приготування
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
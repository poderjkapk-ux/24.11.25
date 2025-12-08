# inventory_service.py

import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload, selectinload

from inventory_models import (
    Stock, InventoryDoc, InventoryDocItem, TechCard, 
    TechCardItem, Ingredient, Warehouse, Modifier, AutoDeductionRule,
    IngredientRecipeItem
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
        .with_for_update()
    )
    stock = res.scalars().first()
    
    if not stock:
        stock = Stock(warehouse_id=warehouse_id, ingredient_id=ingredient_id, quantity=0)
        session.add(stock)
        await session.flush()
        
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
    session.add(doc) 
    
    for item in items:
        ing_id = int(item['ingredient_id'])
        # Безпечне перетворення в Decimal
        qty = Decimal(str(item['qty']))
        # ВАЖЛИВО: Отримуємо ціну, якщо вона передана, інакше 0
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

    # Перевірка на наявність товарів
    if not doc.items:
        raise ValueError("Неможливо провести порожній документ.")

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
    
    ОНОВЛЕНО: Враховує прив'язку цеху до складу зберігання (linked_warehouse_id) та ціну списання.
    Захист від відсутності складів.
    """
    if order.is_inventory_deducted:
        logger.info(f"Склад для замовлення #{order.id} вже був списаний раніше.")
        return

    # Перевірка на наявність items
    if not order.items: 
        order.is_inventory_deducted = True
        await session.commit()
        return

    # --- FIX ISSUE 1: Безпечний Fallback склад ---
    first_wh = await session.scalar(select(Warehouse).limit(1))
    if not first_wh:
        logger.error("КРИТИЧНА ПОМИЛКА: В базі даних немає жодного складу! Списання неможливе.")
        return 
    
    fallback_wh_id = first_wh.id

    # Групуємо інгредієнти для списання по складах: {warehouse_id: [items]}
    deduction_items_by_wh = {} 

    def add_deduction(wh_id, ing_id, qty, price):
        if not wh_id: wh_id = fallback_wh_id
        if wh_id not in deduction_items_by_wh: deduction_items_by_wh[wh_id] = []
        deduction_items_by_wh[wh_id].append({
            'ingredient_id': ing_id, 
            'qty': qty, 
            'price': price
        })

    # Допоміжна функція для визначення реального складу списання
    async def get_real_storage_id(wh_id: int) -> int:
        if not wh_id: return fallback_wh_id
        warehouse = await session.get(Warehouse, wh_id)
        if warehouse and warehouse.linked_warehouse_id:
            return warehouse.linked_warehouse_id
        return wh_id

    # --- ВИЗНАЧАЄМО, ЧИ ЗАМОВЛЕННЯ "НА ВИНОС" ---
    is_takeaway_order = order.is_delivery or order.order_type == 'pickup'

    # --- 1. СПИСАННЯ СТРАВ ТА МОДИФІКАТОРІВ ---
    for order_item in order.items:
        # 1.1 Визначаємо цех приготування для основної страви
        # Спочатку перевіряємо product_id, щоб уникнути помилок якщо товар видалено
        product = await session.get(Product, order_item.product_id)
        
        # Цех страви (вказаний в адмінці)
        prod_wh_id = product.production_warehouse_id if (product and product.production_warehouse_id) else fallback_wh_id
        
        # Визначаємо реальний склад списання (якщо цех прив'язаний до складу)
        real_prod_storage_id = await get_real_storage_id(prod_wh_id)
        
        # 1.2 Шукаємо техкарту
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(joinedload(TechCard.components).joinedload(TechCardItem.ingredient))
        )
        
        # 1.3 Списуємо інгредієнти страви
        if tech_card:
            for component in tech_card.components:
                # --- ЛОГІКА ТІЛЬКИ НА ВИНОС ---
                if component.is_takeaway and not is_takeaway_order:
                    continue
                # -------------------------------

                gross = Decimal(str(component.gross_amount))
                qty_item = Decimal(str(order_item.quantity))
                total_qty = gross * qty_item
                
                # Ціна списання (собівартість)
                cost = component.ingredient.current_cost if component.ingredient.current_cost else 0
                add_deduction(real_prod_storage_id, component.ingredient_id, total_qty, cost)
        else:
            logger.warning(f"Для товару '{order_item.product_name}' (ID {order_item.product_id}) відсутня Техкарта.")
        
        # 1.4 Списуємо інгредієнти модифікаторів
        if order_item.modifiers:
            for mod_data in order_item.modifiers:
                # Отримуємо дані модифікатора з БД
                mod_id = mod_data.get('id')
                if mod_id:
                    modifier_db = await session.get(Modifier, mod_id, options=[joinedload(Modifier.ingredient)])
                    
                    if modifier_db and modifier_db.ingredient_id:
                        ing_qty_val = modifier_db.ingredient_qty
                        
                        # Визначаємо цех для модифікатора (якщо не вказано, беремо цех страви)
                        mod_target_wh_id = modifier_db.warehouse_id if modifier_db.warehouse_id else prod_wh_id
                        
                        # Визначаємо реальний склад для цього цеху
                        real_mod_storage_id = await get_real_storage_id(mod_target_wh_id)
                        
                        if ing_qty_val:
                            total_mod_qty = Decimal(str(ing_qty_val)) * Decimal(str(order_item.quantity))
                            # Ціна списання (собівартість)
                            mod_cost = modifier_db.ingredient.current_cost if (modifier_db.ingredient and modifier_db.ingredient.current_cost) else 0
                            add_deduction(real_mod_storage_id, modifier_db.ingredient_id, total_mod_qty, mod_cost)

    # --- 2. СПИСАННЯ УПАКОВКИ (Auto Rules - Загальні правила) ---
    trigger = 'in_house'
    if order.is_delivery: trigger = 'delivery'
    elif order.order_type == 'pickup': trigger = 'pickup'
    
    rules_res = await session.execute(
        select(AutoDeductionRule).where(
            AutoDeductionRule.trigger_type.in_([trigger, 'all'])
        ).options(joinedload(AutoDeductionRule.ingredient))
    )
    rules = rules_res.scalars().all()
    
    for rule in rules:
        # Для правил також перевіряємо прив'язку складу
        real_rule_storage_id = await get_real_storage_id(rule.warehouse_id)
        # Ціна списання
        rule_cost = rule.ingredient.current_cost if rule.ingredient.current_cost else 0
        add_deduction(real_rule_storage_id, rule.ingredient_id, Decimal(str(rule.quantity)), rule_cost)

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
    if not first_wh: return 
    fallback_wh_id = first_wh.id
    
    return_items_by_wh = {} 

    def add_return(wh_id, ing_id, qty, price):
        if not wh_id: wh_id = fallback_wh_id
        if wh_id not in return_items_by_wh: return_items_by_wh[wh_id] = []
        return_items_by_wh[wh_id].append({'ingredient_id': ing_id, 'qty': qty, 'price': price})

    async def get_real_storage_id(wh_id: int) -> int:
        if not wh_id: return fallback_wh_id
        warehouse = await session.get(Warehouse, wh_id)
        if warehouse and warehouse.linked_warehouse_id:
            return warehouse.linked_warehouse_id
        return wh_id

    is_takeaway_order = order.is_delivery or order.order_type == 'pickup'

    # --- 1. ПОВЕРНЕННЯ СТРАВ ТА МОДИФІКАТОРІВ ---
    for order_item in order.items:
        product = await session.get(Product, order_item.product_id)
        prod_wh_id = product.production_warehouse_id if (product and product.production_warehouse_id) else fallback_wh_id
        
        real_prod_storage_id = await get_real_storage_id(prod_wh_id)
        
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(joinedload(TechCard.components).joinedload(TechCardItem.ingredient))
        )
        
        if tech_card:
            for component in tech_card.components:
                if component.is_takeaway and not is_takeaway_order:
                    continue

                total_qty = Decimal(str(component.gross_amount)) * Decimal(str(order_item.quantity))
                cost = component.ingredient.current_cost if component.ingredient.current_cost else 0
                add_return(real_prod_storage_id, component.ingredient_id, total_qty, cost)
        
        if order_item.modifiers:
            for mod_data in order_item.modifiers:
                mod_id = mod_data.get('id')
                if mod_id:
                    modifier_db = await session.get(Modifier, mod_id, options=[joinedload(Modifier.ingredient)])
                    if modifier_db and modifier_db.ingredient_id:
                        ing_qty_val = modifier_db.ingredient_qty
                        
                        mod_target_wh_id = modifier_db.warehouse_id if modifier_db.warehouse_id else prod_wh_id
                        real_mod_storage_id = await get_real_storage_id(mod_target_wh_id)
                        
                        if ing_qty_val:
                            total_mod_qty = Decimal(str(ing_qty_val)) * Decimal(str(order_item.quantity))
                            mod_cost = modifier_db.ingredient.current_cost if (modifier_db.ingredient and modifier_db.ingredient.current_cost) else 0
                            add_return(real_mod_storage_id, modifier_db.ingredient_id, total_mod_qty, mod_cost)

    # --- 2. ПОВЕРНЕННЯ УПАКОВКИ (Auto Rules) ---
    trigger = 'in_house'
    if order.is_delivery: trigger = 'delivery'
    elif order.order_type == 'pickup': trigger = 'pickup'
    
    rules_res = await session.execute(
        select(AutoDeductionRule).where(
            AutoDeductionRule.trigger_type.in_([trigger, 'all'])
        ).options(joinedload(AutoDeductionRule.ingredient))
    )
    rules = rules_res.scalars().all()
    
    for rule in rules:
        real_rule_storage_id = await get_real_storage_id(rule.warehouse_id)
        rule_cost = rule.ingredient.current_cost if rule.ingredient.current_cost else 0
        add_return(real_rule_storage_id, rule.ingredient_id, Decimal(str(rule.quantity)), rule_cost)

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

async def process_inventory_check(session: AsyncSession, doc_id: int):
    """
    Проводит документ инвентаризации (Доработанная версия)
    """
    stmt = select(InventoryDoc).where(InventoryDoc.id == doc_id).options(
        selectinload(InventoryDoc.items).joinedload(InventoryDocItem.ingredient)
    )
    result = await session.execute(stmt)
    inv_doc = result.scalars().first()

    if not inv_doc: raise ValueError("Документ не найден")
    if inv_doc.is_processed: raise ValueError("Инвентаризация уже проведена")
    if not inv_doc.source_warehouse_id: raise ValueError("Не указан склад инвентаризации")

    warehouse_id = inv_doc.source_warehouse_id
    
    surplus_items = []
    shortage_items = []

    for item in inv_doc.items:
        actual_qty = Decimal(str(item.quantity))
        ingredient_id = item.ingredient_id
        
        stock = await get_stock(session, warehouse_id, ingredient_id)
        system_qty = Decimal(str(stock.quantity))
        
        diff = actual_qty - system_qty
        
        current_cost = Decimal(str(item.ingredient.current_cost)) if item.ingredient.current_cost else Decimal(0)
        
        if diff > 0:
            surplus_items.append({
                'ingredient_id': ingredient_id, 
                'qty': diff, 
                'price': current_cost
            })
        elif diff < 0:
            shortage_items.append({
                'ingredient_id': ingredient_id, 
                'qty': abs(diff), 
                'price': current_cost 
            })

    date_str = datetime.now().strftime('%d.%m %H:%M')
    
    if surplus_items:
        await process_movement(
            session, 'supply', surplus_items, 
            target_wh_id=warehouse_id, 
            comment=f"Лишки інвентаризації #{inv_doc.id} от {date_str}"
        )
        
    if shortage_items:
        await process_movement(
            session, 'writeoff', shortage_items, 
            source_wh_id=warehouse_id, 
            comment=f"Нестача інвентаризації #{inv_doc.id} от {date_str}"
        )

    inv_doc.is_processed = True
    await session.commit()

async def process_production(session: AsyncSession, ingredient_id: int, quantity: float, warehouse_id: int):
    """
    Процесс производства полуфабриката.
    """
    qty_to_produce = Decimal(str(quantity))
    if qty_to_produce <= 0: raise ValueError("Кількість має бути більше 0")

    pf_ingredient = await session.get(Ingredient, ingredient_id, options=[
        selectinload(Ingredient.recipe_components).joinedload(IngredientRecipeItem.child_ingredient),
        joinedload(Ingredient.unit)
    ])
    
    if not pf_ingredient or not pf_ingredient.is_semi_finished:
        raise ValueError("Цей товар не є напівфабрикатом або не знайдений.")
        
    if not pf_ingredient.recipe_components:
        raise ValueError("У напівфабриката немає рецепту (складових).")

    raw_materials_to_deduct = []
    total_batch_cost = Decimal(0)

    for comp in pf_ingredient.recipe_components:
        needed_qty = Decimal(str(comp.gross_amount)) * qty_to_produce
        raw_cost = Decimal(str(comp.child_ingredient.current_cost or 0))
        total_batch_cost += needed_qty * raw_cost
        
        raw_materials_to_deduct.append({
            'ingredient_id': comp.child_ingredient_id,
            'qty': needed_qty,
            'price': raw_cost
        })

    if qty_to_produce > 0:
        new_unit_cost = total_batch_cost / qty_to_produce
    else:
        new_unit_cost = Decimal(0)

    # А) Списание сырья
    await process_movement(
        session, 'writeoff', raw_materials_to_deduct, 
        source_wh_id=warehouse_id, 
        comment=f"Виробництво: {pf_ingredient.name} ({qty_to_produce} {pf_ingredient.unit.name})"
    )
    
    # Б) Приход П/Ф
    pf_item = [{
        'ingredient_id': ingredient_id,
        'qty': qty_to_produce,
        'price': new_unit_cost
    }]
    
    await process_movement(
        session, 'supply', pf_item,
        target_wh_id=warehouse_id,
        supplier_id=None,
        comment=f"Вироблено: {pf_ingredient.name}"
    )
    
    return True
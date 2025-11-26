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
    Получает запись об остатках товара на складе.
    Если записи нет, создает новую с нулевым остатком.
    """
    res = await session.execute(
        select(Stock).where(Stock.warehouse_id == warehouse_id, Stock.ingredient_id == ingredient_id)
    )
    stock = res.scalars().first()
    if not stock:
        stock = Stock(warehouse_id=warehouse_id, ingredient_id=ingredient_id, quantity=0)
        session.add(stock)
        await session.flush() # Чтобы получить ID
    return stock

async def process_movement(session: AsyncSession, doc_type: str, items: list, 
                           source_wh_id: int = None, target_wh_id: int = None, 
                           supplier_id: int = None, comment: str = "", order_id: int = None):
    """
    Универсальная функция для автоматического создания и проведения документа.
    items = [{'ingredient_id': 1, 'qty': 1.5, 'price': 100}, ...]
    """
    doc = InventoryDoc(
        doc_type=doc_type,
        source_warehouse_id=source_wh_id,
        target_warehouse_id=target_wh_id,
        supplier_id=supplier_id,
        comment=comment,
        linked_order_id=order_id,
        is_processed=False # Сначала создаем непроведенный документ
    )
    session.add(doc)
    await session.flush()

    for item in items:
        ing_id = int(item['ingredient_id'])
        qty = Decimal(str(item['qty']))
        price = Decimal(str(item.get('price', 0)))

        doc_item = InventoryDocItem(doc_id=doc.id, ingredient_id=ing_id, quantity=qty, price=price)
        session.add(doc_item)

    # Сразу проводим документ (обновляем остатки)
    await apply_doc_stock_changes(session, doc.id)
    return doc

async def apply_doc_stock_changes(session: AsyncSession, doc_id: int):
    """
    Проводит документ: обновляет остатки на складах на основе позиций документа.
    Устанавливает флаг is_processed = True.
    Также пересчитывает себестоимость по средней (Weighted Average) при приходе.
    """
    doc = await session.get(InventoryDoc, doc_id, options=[joinedload(InventoryDoc.items)])
    if not doc: raise ValueError("Документ не найден")
    if doc.is_processed: raise ValueError("Документ уже проведен")

    for item in doc.items:
        qty = Decimal(str(item.quantity))
        
        if doc.doc_type == 'supply': # Приход
            if not doc.target_warehouse_id: raise ValueError("Не указан склад получателя")
            
            # --- ЛОГИКА СРЕДНЕВЗВЕШЕННОЙ СЕБЕСТОИМОСТИ ---
            # Формула: (Остаток * СтараяЦена + Приход * НоваяЦена) / (Остаток + Приход)
            if item.price > 0:
                # 1. Получаем текущий общий остаток ингредиента по ВСЕМ складам
                # (т.к. себестоимость в модели Ingredient одна на всю систему)
                total_qty_res = await session.execute(
                    select(func.sum(Stock.quantity)).where(Stock.ingredient_id == item.ingredient_id)
                )
                total_existing_qty = total_qty_res.scalar() or Decimal(0)
                
                # Если остаток отрицательный (пересорт/ошибка), считаем его как 0 для расчета цены, 
                # чтобы не искажать новую партию.
                calc_existing_qty = total_existing_qty if total_existing_qty > 0 else Decimal(0)

                # 2. Получаем текущую себестоимость
                ingredient = await session.get(Ingredient, item.ingredient_id)
                if ingredient:
                    old_cost = Decimal(str(ingredient.current_cost))
                    new_supply_price = Decimal(str(item.price))
                    
                    current_value = calc_existing_qty * old_cost
                    new_supply_value = qty * new_supply_price
                    
                    total_new_qty = calc_existing_qty + qty
                    
                    if total_new_qty > 0:
                        new_avg_cost = (current_value + new_supply_value) / total_new_qty
                        # Обновляем цену в базе
                        ingredient.current_cost = new_avg_cost
                        session.add(ingredient)
            # ---------------------------------------------

            stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            stock.quantity += qty

        elif doc.doc_type == 'transfer': # Перемещение
            if not doc.source_warehouse_id or not doc.target_warehouse_id: raise ValueError("Нужны оба склада (источник и цель)")
            src_stock = await get_stock(session, doc.source_warehouse_id, item.ingredient_id)
            tgt_stock = await get_stock(session, doc.target_warehouse_id, item.ingredient_id)
            src_stock.quantity -= qty
            tgt_stock.quantity += qty

        elif doc.doc_type in ['writeoff', 'deduction']: # Списание (в т.ч. по продаже)
            if not doc.source_warehouse_id: raise ValueError("Не указан склад списания")
            stock = await get_stock(session, doc.source_warehouse_id, item.ingredient_id)
            stock.quantity -= qty

    doc.is_processed = True
    await session.commit()

async def deduct_products_by_tech_card(session: AsyncSession, order: Order):
    """
    Автоматическое списание продуктов (и модификаторов) со склада на основе техкарт.
    Вызывается при готовности/продаже блюда.
    """
    if not order.items: return

    # Определяем склады списания (Поиск по названию)
    kitchen_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Кухня%')).limit(1))
    bar_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Бар%')).limit(1))
    
    # Маппинг зон приготовления к ID складов
    wh_map = {
        'kitchen': kitchen_wh.id if kitchen_wh else (1 if not bar_wh else bar_wh.id),
        'bar': bar_wh.id if bar_wh else (1 if not kitchen_wh else kitchen_wh.id)
    }

    deduction_items_by_wh = {} # {warehouse_id: [{ingredient_id, qty}, ...]}

    def add_deduction(wh_id, ing_id, qty):
        if not wh_id: wh_id = 1 # Fallback
        if wh_id not in deduction_items_by_wh: deduction_items_by_wh[wh_id] = []
        deduction_items_by_wh[wh_id].append({'ingredient_id': ing_id, 'qty': qty})

    for order_item in order.items:
        wh_id = wh_map.get(order_item.preparation_area)
        
        # 1. Списание компонентов блюда (по Техкарте)
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(select(TechCardItem).joinedload(TechCardItem.ingredient))
        )
        
        if tech_card:
            for component in tech_card.components:
                total_qty = Decimal(component.gross_amount) * order_item.quantity
                add_deduction(wh_id, component.ingredient_id, total_qty)
        
        # 2. Списание компонентов МОДИФИКАТОРОВ
        if order_item.modifiers:
            # modifiers это список dict: [{'id':..., 'name':..., 'ingredient_id':..., 'ingredient_qty':...}]
            for mod_data in order_item.modifiers:
                ing_id = mod_data.get('ingredient_id')
                ing_qty = mod_data.get('ingredient_qty')
                
                if ing_id and ing_qty:
                    # Модификатор списывается 1 раз на 1 порцию блюда.
                    # Если блюда 2 шт, то и модификаторов 2 шт.
                    total_mod_qty = Decimal(str(ing_qty)) * order_item.quantity
                    add_deduction(wh_id, ing_id, total_mod_qty)

    # Проводим документы списания для каждого склада
    for wh_id, items in deduction_items_by_wh.items():
        if items:
            await process_movement(
                session, 'deduction', items, 
                source_wh_id=wh_id, 
                comment=f"Замовлення #{order.id}", 
                order_id=order.id
            )

async def generate_cook_ticket(session: AsyncSession, order_id: int) -> str:
    """Генерирует HTML бегунка для повара (с рецептом и модификаторами)"""
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
        # Подтягиваем рецепт
        tc = await session.scalar(select(TechCard).where(TechCard.product_id == item.product_id))
        
        # Формируем строку модификаторов
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
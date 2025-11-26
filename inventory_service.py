# inventory_service.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from decimal import Decimal

from inventory_models import (
    Stock, InventoryDoc, InventoryDocItem, TechCard, 
    TechCardItem, Ingredient, Warehouse
)
from models import Order, OrderItem

logger = logging.getLogger(__name__)

async def get_stock(session: AsyncSession, warehouse_id: int, ingredient_id: int) -> Stock:
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
    Универсальная функция проведения документов.
    items = [{'ingredient_id': 1, 'qty': 1.5, 'price': 100}, ...]
    """
    doc = InventoryDoc(
        doc_type=doc_type,
        source_warehouse_id=source_wh_id,
        target_warehouse_id=target_wh_id,
        supplier_id=supplier_id,
        comment=comment,
        linked_order_id=order_id
    )
    session.add(doc)
    await session.flush()

    for item in items:
        ing_id = int(item['ingredient_id'])
        qty = Decimal(str(item['qty']))
        price = Decimal(str(item.get('price', 0)))

        doc_item = InventoryDocItem(doc_id=doc.id, ingredient_id=ing_id, quantity=qty, price=price)
        session.add(doc_item)

        # Логика пересчета остатков
        if doc_type == 'supply': # Приход
            if not target_wh_id: raise ValueError("Не указан склад получатель")
            stock = await get_stock(session, target_wh_id, ing_id)
            stock.quantity += qty
            
            # Обновляем себестоимость ингредиента (упрощенно - по последнему приходу)
            if price > 0:
                await session.execute(update(Ingredient).where(Ingredient.id == ing_id).values(current_cost=price))

        elif doc_type == 'transfer': # Перемещение
            if not source_wh_id or not target_wh_id: raise ValueError("Нужны оба склада")
            src_stock = await get_stock(session, source_wh_id, ing_id)
            tgt_stock = await get_stock(session, target_wh_id, ing_id)
            src_stock.quantity -= qty
            tgt_stock.quantity += qty

        elif doc_type in ['writeoff', 'deduction']: # Списание (в т.ч. по продаже)
            if not source_wh_id: raise ValueError("Не указан склад списания")
            stock = await get_stock(session, source_wh_id, ing_id)
            stock.quantity -= qty

    await session.commit()
    return doc

async def deduct_products_by_tech_card(session: AsyncSession, order: Order):
    """
    Списание продуктов по заказу на основе техкарт.
    Вызывается при готовности/продаже блюда.
    """
    if not order.items: return

    # Определяем склад списания. 
    # В идеале: у каждой OrderItem есть preparation_area. 
    # Надо мапить area -> warehouse_id.
    # Допустим: Kitchen -> ID 1, Bar -> ID 2.
    
    # Загружаем маппинг складов
    kitchen_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Кухня%')).limit(1))
    bar_wh = await session.scalar(select(Warehouse).where(Warehouse.name.ilike('%Бар%')).limit(1))
    
    wh_map = {
        'kitchen': kitchen_wh.id if kitchen_wh else None,
        'bar': bar_wh.id if bar_wh else None
    }

    deduction_items_by_wh = {} # {warehouse_id: [{ing_id, qty}, ...]}

    for order_item in order.items:
        # Ищем техкарту для продукта
        tech_card = await session.scalar(
            select(TechCard).where(TechCard.product_id == order_item.product_id)
            .options(select(TechCardItem).joinedload(TechCardItem.ingredient))
        )
        
        if not tech_card:
            logger.warning(f"Нет техкарты для {order_item.product_name}. Списание не произведено.")
            continue

        wh_id = wh_map.get(order_item.preparation_area)
        if not wh_id: continue # Нет склада - нет списания

        if wh_id not in deduction_items_by_wh:
            deduction_items_by_wh[wh_id] = []

        for component in tech_card.components:
            total_qty = Decimal(component.gross_amount) * order_item.quantity
            deduction_items_by_wh[wh_id].append({
                'ingredient_id': component.ingredient_id,
                'qty': total_qty
            })

    # Проводим документы списания для каждого склада
    for wh_id, items in deduction_items_by_wh.items():
        if items:
            await process_movement(
                session, 'deduction', items, 
                source_wh_id=wh_id, 
                comment=f"Заказ #{order.id}", 
                order_id=order.id
            )
            
async def generate_cook_ticket(session: AsyncSession, order_id: int) -> str:
    """Генерирует HTML для печати повару (с рецептом)"""
    order = await session.get(Order, order_id)
    query = select(OrderItem).where(OrderItem.order_id == order_id)
    items = (await session.execute(query)).scalars().all()
    
    html = f"""
    <div style="font-family: monospace; width: 300px;">
        <h3 style="text-align:center;">👨‍🍳 БЕГУНОК НА КУХНЮ</h3>
        <div><b>Заказ #{order.id}</b></div>
        <div>Стол: {order.table_id or 'Доставка'}</div>
        <hr>
    """
    
    for item in items:
        html += f"<div style='font-size:1.2em; font-weight:bold;'>{item.product_name} x {item.quantity}</div>"
        
        # Подтягиваем рецепт
        tc = await session.scalar(select(TechCard).where(TechCard.product_id == item.product_id))
        if tc and tc.cooking_method:
            html += f"<div style='font-size:0.8em; color:#555; margin-bottom:10px; border-left:2px solid #000; padding-left:5px;'><i>{tc.cooking_method}</i></div>"
        else:
            html += "<br>"
            
    html += "<hr><div style='text-align:center;'>Приятной работы!</div></div>"
    return html
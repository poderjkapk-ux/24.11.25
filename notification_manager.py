# notification_manager.py

import logging
import os
from aiogram import Bot, html
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from models import Order, OrderStatus, Employee, Role, OrderItem, StaffNotification
# --- СКЛАД: Импорт функций списания и возврата ---
from inventory_service import deduct_products_by_tech_card, reverse_deduction

# ДОДАНО: Імпорт менеджера WebSocket для відправки подій
from websocket_manager import manager

logger = logging.getLogger(__name__)

async def create_staff_notification(session: AsyncSession, employee_id: int, message: str):
    """
    Создает запись уведомления в БД для PWA (красная точка и Toast).
    """
    try:
        session.add(StaffNotification(employee_id=employee_id, message=message))
        # Важно: делаем коммит сразу, чтобы поллинг PWA увидел новое уведомление
        await session.commit() 
    except Exception as e:
        logger.error(f"Error creating PWA notification for emp {employee_id}: {e}")

async def notify_new_order_to_staff(admin_bot: Bot, order: Order, session: AsyncSession):
    """
    Отправляет уведомление о НОВОМ заказе:
    1. PWA: Операторам.
    2. Telegram: В админ-чат и операторам в личные.
    3. WebSocket: Мгновенное обновление интерфейса.
    """
    admin_chat_id_str = os.environ.get('ADMIN_CHAT_ID')
    
    # Загружаем связи
    query = select(Order).where(Order.id == order.id).options(
        selectinload(Order.items),
        joinedload(Order.status),
        joinedload(Order.table)
    )
    result = await session.execute(query)
    order = result.scalar_one()

    # --- 1. PWA NOTIFICATION (Операторам) ---
    operator_roles_res = await session.execute(select(Role.id).where(Role.can_manage_orders == True))
    operator_role_ids = operator_roles_res.scalars().all()
    
    if operator_role_ids:
        operators = (await session.execute(
            select(Employee).where(Employee.role_id.in_(operator_role_ids), Employee.is_on_shift == True)
        )).scalars().all()
        
        pwa_msg = f"🆕 Нове замовлення #{order.id} ({order.total_price} грн)"
        for emp in operators:
            await create_staff_notification(session, emp.id, pwa_msg)
    # ---------------------------------------

    # --- 2. TELEGRAM NOTIFICATION ---
    is_delivery = order.is_delivery 

    if order.order_type == 'in_house':
        delivery_info = f"📍 <b>В закладі</b> (Стіл: {html.quote(order.table.name if order.table else 'Невідомий')})"
        source = "Джерело: 🤵 Офіціант / QR"
    elif is_delivery:
        delivery_info = f"🚚 <b>Доставка</b>: {html.quote(order.address or 'Не вказана')}"
        source = f"Джерело: {'🌐 Веб-сайт' if order.user_id is None else '🤖 Telegram-бот'}"
    else:
        delivery_info = "🏃 <b>Самовивіз</b>"
        source = f"Джерело: {'🌐 Веб-сайт' if order.user_id is None else '🤖 Telegram-бот'}"

    status_name = order.status.name if order.status else 'Невідомий'
    time_info = f"Час: {html.quote(order.delivery_time)}"
    
    products_formatted = ""
    if order.items:
        lines = []
        for item in order.items:
            # Добавляем модификаторы в текст уведомления
            mods_str = ""
            if item.modifiers:
                mod_names = [m.get('name', '') for m in item.modifiers]
                if mod_names:
                    mods_str = f" (+ {', '.join(mod_names)})"
            
            lines.append(f"- {html.quote(item.product_name)}{mods_str} x {item.quantity}")
        products_formatted = "\n".join(lines)
    else:
        products_formatted = "- <i>Немає товарів</i>"
    
    admin_text = (f"<b>Замовлення #{order.id}</b>\n{source}\n\n"
                  f"<b>Клієнт:</b> {html.quote(order.customer_name or 'Не вказано')}\n<b>Телефон:</b> {html.quote(order.phone_number or 'Не вказано')}\n"
                  f"{delivery_info}\n<b>{time_info}</b>\n\n"
                  f"<b>Страви:</b>\n{products_formatted}\n\n"
                  f"<b>Сума:</b> {order.total_price} грн\n\n"
                  f"<b>Статус:</b> {status_name}")

    kb_admin = InlineKeyboardBuilder()
    statuses_res = await session.execute(
        select(OrderStatus).where(OrderStatus.visible_to_operator == True).order_by(OrderStatus.id)
    )
    status_buttons = [
        InlineKeyboardButton(text=s.name, callback_data=f"change_order_status_{order.id}_{s.id}")
        for s in statuses_res.scalars().all()
    ]
    for i in range(0, len(status_buttons), 2):
        kb_admin.row(*status_buttons[i:i+2])
    kb_admin.row(InlineKeyboardButton(text="👤 Призначити кур'єра", callback_data=f"select_courier_{order.id}"))
    kb_admin.row(InlineKeyboardButton(text="✏️ Редагувати замовлення", callback_data=f"edit_order_{order.id}"))

    target_chat_ids = set()
    if admin_chat_id_str:
        try:
            target_chat_ids.add(int(admin_chat_id_str))
        except ValueError:
            logger.warning(f"Некоректний ADMIN_CHAT_ID: {admin_chat_id_str}")

    if operator_role_ids:
        operators_tg = await session.execute(
            select(Employee).where(
                Employee.role_id.in_(operator_role_ids),
                Employee.is_on_shift == True,
                Employee.telegram_user_id.is_not(None)
            )
        )
        for operator in operators_tg.scalars().all():
            target_chat_ids.add(operator.telegram_user_id)
            
    for chat_id in target_chat_ids:
        try:
            await admin_bot.send_message(chat_id, admin_text, reply_markup=kb_admin.as_markup())
        except Exception as e:
            logger.error(f"Не вдалося відправити нове замовлення в TG {chat_id}: {e}")

    # 3. РОЗПОДІЛ НА ВИРОБНИЦТВО
    if order.status and order.status.requires_kitchen_notify:
        await distribute_order_to_production(admin_bot, order, session)
    else:
        logger.info(f"Замовлення #{order.id} створено, чекає обробки.")

    # --- 4. WEBSOCKET BROADCAST ---
    # Повідомляємо весь персонал (щоб оновити списки замовлень)
    await manager.broadcast_staff({
        "type": "new_order",
        "order_id": order.id,
        "message": f"Нове замовлення #{order.id}"
    })
    
    # Повідомляємо клієнта за столиком (щоб статус змінився на екрані)
    if order.table_id:
        await manager.broadcast_table(order.table_id, {
            "type": "order_update",
            "order_id": order.id,
            "status": "Новий"
        })


async def distribute_order_to_production(bot: Bot, order: Order, session: AsyncSession):
    """
    Распределяет товары заказа между Кухней и Баром для уведомлений.
    """
    query = select(Order).where(Order.id == order.id).options(
        selectinload(Order.items).joinedload(OrderItem.product)
    )
    result = await session.execute(query)
    loaded_order = result.scalar_one()

    kitchen_items = []
    bar_items = []

    for item in loaded_order.items:
        # Формируем строку с модификаторами
        mods_str = ""
        if item.modifiers:
            mod_names = [m.get('name', '') for m in item.modifiers]
            if mod_names:
                mods_str = f" (+ {', '.join(mod_names)})"

        item_str = f"- {html.quote(item.product_name)}{mods_str} x {item.quantity}"
        area = item.preparation_area
        
        if area == 'bar':
            bar_items.append(item_str)
        else:
            kitchen_items.append(item_str)

    # --- PWA NOTIFICATION ---
    if kitchen_items:
        chefs = (await session.execute(
            select(Employee).join(Role).where(Role.can_receive_kitchen_orders==True, Employee.is_on_shift==True)
        )).scalars().all()
        for emp in chefs:
            await create_staff_notification(session, emp.id, f"🍳 Кухня: Нове замовлення #{order.id}")
            
    if bar_items:
        barmen = (await session.execute(
            select(Employee).join(Role).where(Role.can_receive_bar_orders==True, Employee.is_on_shift==True)
        )).scalars().all()
        for emp in barmen:
            await create_staff_notification(session, emp.id, f"🍹 Бар: Нове замовлення #{order.id}")

    # --- TELEGRAM NOTIFICATION ---
    if kitchen_items:
        await send_group_notification(
            bot=bot, order=loaded_order, items=kitchen_items,
            role_filter=Role.can_receive_kitchen_orders == True,
            title="🧑‍🍳 ЗАМОВЛЕННЯ НА КУХНЮ", session=session, area="kitchen"
        )

    if bar_items:
        await send_group_notification(
            bot=bot, order=loaded_order, items=bar_items,
            role_filter=Role.can_receive_bar_orders == True,
            title="🍹 ЗАМОВЛЕННЯ НА БАР", session=session, area="bar"
        )


async def send_group_notification(bot: Bot, order: Order, items: list, role_filter, title: str, session: AsyncSession, area: str = "kitchen"):
    roles_res = await session.execute(select(Role.id).where(role_filter))
    role_ids = roles_res.scalars().all()

    if not role_ids: return

    employees_res = await session.execute(
        select(Employee).where(
            Employee.role_id.in_(role_ids),
            Employee.is_on_shift == True,
            Employee.telegram_user_id.is_not(None)
        )
    )
    employees = employees_res.scalars().all()

    if employees:
        is_delivery = order.is_delivery
        items_formatted = "\n".join(items)
        
        table_info = ""
        if order.order_type == 'in_house' and order.table:
             table_info = f" (Стіл: {html.quote(order.table.name)})"
        
        text = (f"{title}: <b>#{order.id}</b>{table_info}\n"
                f"<b>Тип:</b> {'Доставка' if is_delivery else 'В закладі / Самовивіз'}\n"
                f"<b>Час:</b> {html.quote(order.delivery_time)}\n\n"
                f"<b>СКЛАД:</b>\n{items_formatted}\n\n"
                f"<i>Натисніть 'Видача', коли буде готове.</i>")
        
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=f"✅ Видача #{order.id}", callback_data=f"chef_ready_{order.id}_{area}"))
        
        for emp in employees:
            try:
                await bot.send_message(emp.telegram_user_id, text, reply_markup=kb.as_markup())
            except Exception as e:
                logger.error(f"Не вдалося відправити в TG працівнику {emp.id}: {e}")


async def notify_station_completion(bot: Bot, order: Order, area: str, session: AsyncSession, employee_id: int = None):
    """
    Сповіщає офіціанта/кур'єра про готовність страв.
    Якщо вказано employee_id, визначаємо страви, які готуються в цехах, прив'язаних до цього співробітника.
    """
    # 1. Завантажуємо замовлення з усіма необхідними зв'язками для формування повідомлення
    # Використовуємо select для повного завантаження, щоб уникнути MissingGreenlet
    query = select(Order).where(Order.id == order.id).options(
        joinedload(Order.table),
        joinedload(Order.accepted_by_waiter),
        joinedload(Order.courier),
        # Важливо: завантажуємо items разом з product, щоб мати доступ до production_warehouse_id
        selectinload(Order.items).joinedload(OrderItem.product)
    )
    result = await session.execute(query)
    order = result.scalar_one()
    
    # 2. Визначаємо список готових страв
    ready_items_names = []
    
    if employee_id:
        # Якщо ми знаємо, хто натиснув кнопку, беремо його налаштування
        employee = await session.get(Employee, employee_id)
        
        # Перевіряємо, чи є у співробітника прив'язка до конкретних цехів (assigned_workshop_ids)
        if employee and employee.assigned_workshop_ids:
            workshop_ids = employee.assigned_workshop_ids
            
            # Фільтруємо страви замовлення: залишаємо тільки ті, що належать до цехів співробітника
            for item in order.items:
                if item.product and item.product.production_warehouse_id in workshop_ids:
                    # Додаємо назву + модифікатори
                    name = item.product_name
                    if item.modifiers:
                        mod_names = [m.get('name') for m in item.modifiers]
                        if mod_names:
                            name += f" ({', '.join(mod_names)})"
                    ready_items_names.append(f"{name} x{item.quantity}")
    
    # 3. Fallback: Якщо список порожній (немає прив'язки або employee_id не передано), використовуємо стару логіку по 'area'
    if not ready_items_names:
        if area == 'kitchen':
            # Всі страви НЕ з бару
            ready_items_names = [
                f"{i.product_name} x{i.quantity}" 
                for i in order.items if i.preparation_area != 'bar'
            ]
        elif area == 'bar':
            # Всі страви з бару
            ready_items_names = [
                f"{i.product_name} x{i.quantity}" 
                for i in order.items if i.preparation_area == 'bar'
            ]
        else:
            # Якщо area незрозуміла, беремо все
            ready_items_names = [f"{i.product_name} x{i.quantity}" for i in order.items]

    # 4. Формуємо текст повідомлення
    if not ready_items_names:
        # Захист від порожнього повідомлення (наприклад, якщо в замовленні немає страв для цього цеху)
        return

    items_list_str = "\n".join([f"- {name}" for name in ready_items_names])
    
    source_label = "✅ ГОТОВО"
    # Якщо визначили за employee_id, заголовок загальний, інакше по area
    if not employee_id:
        if area == 'kitchen': source_label = "🍳 КУХНЯ ГОТОВА"
        elif area == 'bar': source_label = "🍹 БАР ГОТОВИЙ"
    
    table_info = f" (Стіл: {html.quote(order.table.name)})" if order.table else ""
    
    message_text = (
        f"<b>{source_label}!</b>\n"
        f"Замовлення #{order.id}{table_info}\n\n"
        f"<b>Готові страви:</b>\n{items_list_str}\n\n"
        f"<i>Можна забирати.</i>"
    )
    
    # Коротке повідомлення для PWA (Toast)
    short_items = ", ".join(ready_items_names[:2])
    if len(ready_items_names) > 2: short_items += "..."
    pwa_msg = f"✅ Готово #{order.id}: {short_items}"

    # 5. Відправка повідомлень (PWA)
    # Офіціанту
    if order.accepted_by_waiter_id:
        await create_staff_notification(session, order.accepted_by_waiter_id, pwa_msg)
    # Кур'єру
    if order.courier_id:
        await create_staff_notification(session, order.courier_id, pwa_msg)

    # 6. Відправка повідомлень (Telegram)
    target_chat_ids = set()
    
    # Офіціант
    if order.order_type == 'in_house' and order.accepted_by_waiter and order.accepted_by_waiter.telegram_user_id:
        target_chat_ids.add(order.accepted_by_waiter.telegram_user_id)
        
    # Кур'єр
    if order.is_delivery and order.courier and order.courier.telegram_user_id:
        target_chat_ids.add(order.courier.telegram_user_id)

    # Якщо нікого немає (самовивіз без призначеного кур'єра або вільний стіл), шлемо в адмін-чат
    if not target_chat_ids:
        admin_chat_id_str = os.environ.get('ADMIN_CHAT_ID')
        if admin_chat_id_str:
             try: target_chat_ids.add(int(admin_chat_id_str))
             except ValueError: pass
             message_text += "\n(Виконавець не призначений)"

    for chat_id in target_chat_ids:
        try: await bot.send_message(chat_id, message_text)
        except Exception: pass

    # --- 7. WEBSOCKET BROADCAST ---
    # Сповіщаємо весь персонал про готовність (щоб у офіціанта/кур'єра з'явилися галочки)
    await manager.broadcast_staff({
        "type": "item_ready",
        "order_id": order.id,
        "area": area
    })


async def notify_all_parties_on_status_change(
    order: Order,
    old_status_name: str,
    actor_info: str,
    admin_bot: Bot,
    client_bot: Bot | None,
    session: AsyncSession
):
    """
    Централизованная функция уведомлений и логики склада при смене статуса.
    """
    await session.refresh(order, ['status', 'courier', 'accepted_by_waiter', 'table'])
    admin_chat_id_str = os.environ.get('ADMIN_CHAT_ID')
    
    new_status = order.status
    
    # --- 1. ЛОГИКА СКЛАДА (Списание и Возврат) ---
    
    # А. Возврат на склад при Отмене (если уже было списано)
    if new_status.is_cancelled_status and order.is_inventory_deducted:
        try:
            await reverse_deduction(session, order)
            # Логируем в админку, что произошел возврат
            if admin_chat_id_str:
                try: await admin_bot.send_message(admin_chat_id_str, f"♻️ <b>[Склад]</b> Товари замовлення #{order.id} повернуто на склад.")
                except Exception: pass
        except Exception as e:
            logger.error(f"Помилка повернення на склад для #{order.id}: {e}")

    # Б. Списание со склада
    # Исправлено: списываем, если "Готовий до видачі" ИЛИ если статус финальный (выполнен),
    # но списание еще не проводилось. Это покрывает случаи, когда заказ сразу закрывают как оплаченный.
    if new_status.name == "Готовий до видачі" or new_status.is_completed_status:
        is_deducted = getattr(order, 'is_inventory_deducted', False)
        if not is_deducted:
            try:
                await deduct_products_by_tech_card(session, order)
                order.is_inventory_deducted = True
                await session.commit()
                logger.info(f"Склад списан для заказа #{order.id}")
            except Exception as e:
                logger.error(f"Помилка списання складу для #{order.id}: {e}")
    # --------------------------------------------

    # --- 2. PWA NOTIFICATION ---
    pwa_msg = f"ℹ️ Заказ #{order.id}: Статус -> '{new_status.name}'"
    if order.accepted_by_waiter_id:
        await create_staff_notification(session, order.accepted_by_waiter_id, pwa_msg)
    if order.courier_id:
        await create_staff_notification(session, order.courier_id, pwa_msg)

    # --- 3. LOG TO ADMIN CHAT ---
    if admin_chat_id_str:
        log_message = (
            f"🔄 <b>[Статус змінено]</b> Замовлення #{order.id}\n"
            f"<b>Ким:</b> {html.quote(actor_info)}\n"
            f"<b>Статус:</b> `{html.quote(old_status_name)}` → `{html.quote(new_status.name)}`"
        )
        try: await admin_bot.send_message(admin_chat_id_str, log_message)
        except Exception: pass

    # --- 4. DISTRIBUTE TO PRODUCTION ---
    if new_status.requires_kitchen_notify:
        await distribute_order_to_production(admin_bot, order, session)

    # --- 5. READY FOR PICKUP MSG ---
    if new_status.name == "Готовий до видачі":
        source_label = ""
        if "Кухня" in actor_info: source_label = " (🍳 КУХНЯ)"
        elif "Бар" in actor_info: source_label = " (🍹 БАР)"
        
        ready_message = f"📢 <b>ГОТОВО ДО ВИДАЧІ{source_label}: #{order.id}</b>! \n"
        
        if not (order.kitchen_done and order.bar_done) and (order.kitchen_done or order.bar_done):
             ready_message += "⚠️ <b>УВАГА: Це лише частина замовлення!</b> Перевірте інший цех.\n"

        target_employees = []
        if order.order_type == 'in_house' and order.accepted_by_waiter and order.accepted_by_waiter.is_on_shift:
            target_employees.append(order.accepted_by_waiter)
            ready_message += f"Стіл: {html.quote(order.table.name if order.table else 'N/A')}"
        
        if order.is_delivery and order.courier and order.courier.is_on_shift:
            target_employees.append(order.courier)
            ready_message += f"Кур'єр: {html.quote(order.courier.full_name)}"

        # Если исполнителя нет, уведомляем операторов
        if not target_employees:
             operator_roles_res = await session.execute(select(Role.id).where(Role.can_manage_orders == True))
             op_ids = operator_roles_res.scalars().all()
             if op_ids:
                 ops = (await session.execute(select(Employee).where(Employee.role_id.in_(op_ids), Employee.is_on_shift==True))).scalars().all()
                 target_employees.extend(ops)
             ready_message += f"Тип: {'Самовивіз' if order.order_type == 'pickup' else 'Доставка'}. Потрібна видача."
             
        for employee in target_employees:
            if employee.telegram_user_id:
                try: await admin_bot.send_message(employee.telegram_user_id, ready_message)
                except Exception: pass

    # --- 6. NOTIFY STAFF (Status Change) ---
    if order.courier and order.courier.telegram_user_id and "Кур'єр" not in actor_info and new_status.name != "Готовий до видачі":
        if new_status.visible_to_courier:
            courier_text = f"❗️ Статус замовлення #{order.id} змінено на: <b>{new_status.name}</b>"
            try: await admin_bot.send_message(order.courier.telegram_user_id, courier_text)
            except Exception: pass

    if order.order_type != 'delivery' and order.accepted_by_waiter and order.accepted_by_waiter.telegram_user_id and "Офіціант" not in actor_info and new_status.name != "Готовий до видачі":
        waiter_text = f"📢 Замовлення #{order.id} (Стіл: {html.quote(order.table.name if order.table else 'N/A')}) має новий статус: <b>{new_status.name}</b>"
        try: await admin_bot.send_message(order.accepted_by_waiter.telegram_user_id, waiter_text)
        except Exception: pass

    # --- 7. NOTIFY CUSTOMER ---
    if new_status.notify_customer and order.user_id and client_bot:
        client_text = f"Статус вашого замовлення #{order.id} змінено на: <b>{new_status.name}</b>"
        try: await client_bot.send_message(order.user_id, client_text)
        except Exception: pass

    # --- 8. WEBSOCKET BROADCAST ---
    # Оновлення списків замовлень у персоналу
    await manager.broadcast_staff({
        "type": "order_updated",
        "order_id": order.id,
        "new_status": new_status.name
    })

    # Оновлення статусу у клієнта за столиком
    if order.table_id:
        await manager.broadcast_table(order.table_id, {
            "type": "order_update",
            "order_id": order.id,
            "status": new_status.name,
            "total_price": float(order.total_price)
        })
# staff_pwa.py

import html
import logging
import json
from decimal import Decimal
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, delete, and_
from sqlalchemy.orm import joinedload, selectinload

# Импорт моделей и зависимостей
from models import (
    Employee, Settings, Order, OrderStatus, Role, OrderItem, Table, 
    Category, Product, OrderStatusHistory, StaffNotification
)
# Импорт модели модификаторов
from inventory_models import Modifier
from dependencies import get_db_session
from auth_utils import verify_password, create_access_token, get_current_staff

# Импорт шаблонов
from staff_templates import (
    STAFF_LOGIN_HTML, STAFF_DASHBOARD_HTML, 
    STAFF_TABLE_CARD, STAFF_ORDER_CARD
)

# Импорт менеджеров оповещений и кассы
from notification_manager import (
    notify_all_parties_on_status_change, 
    notify_new_order_to_staff, 
    notify_station_completion,
    create_staff_notification
)
from cash_service import link_order_to_shift, register_employee_debt, unregister_employee_debt

# Настройка роутера и логгера
router = APIRouter(prefix="/staff", tags=["staff_pwa"])
logger = logging.getLogger(__name__)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def check_edit_permissions(employee: Employee, order: Order) -> bool:
    """
    Проверяет, имеет ли сотрудник право редактировать состав заказа.
    """
    # 1. Админ/Оператор может все
    if employee.role.can_manage_orders:
        return True
    
    # 2. Официант может редактировать только СВОИ заказы (или заказы со своих столов, если еще не приняты)
    if employee.role.can_serve_tables:
        # Если заказ "in_house" и принят этим официантом
        if order.accepted_by_waiter_id == employee.id:
            return True
        # Если заказ "in_house", никем не принят (разрешаем редактировать/принимать)
        if order.order_type == 'in_house' and order.accepted_by_waiter_id is None:
            return True
            
    # 3. Курьеры, Повара, Бармены не могут менять состав заказа
    return False

async def fetch_db_modifiers(session: AsyncSession, items_list: list) -> dict:
    """
    Собирает все ID модификаторов из списка и загружает их из БД.
    """
    all_mod_ids = set()
    for item in items_list:
        for mod in item.get('modifiers', []):
            if 'id' in mod:
                all_mod_ids.add(int(mod['id']))
    
    db_mods = {}
    if all_mod_ids:
        res = await session.execute(select(Modifier).where(Modifier.id.in_(all_mod_ids)))
        for m in res.scalars().all():
            db_mods[m.id] = m
    return db_mods

async def check_and_update_order_readiness(session: AsyncSession, order_id: int, bot):
    """
    Проверяет готовность всех блюд в заказе.
    Если все блюда Кухни готовы -> kitchen_done = True
    Если все блюда Бара готовы -> bar_done = True
    """
    order = await session.get(Order, order_id, options=[selectinload(Order.items).joinedload(OrderItem.product)])
    if not order: return

    kitchen_items = [i for i in order.items if i.preparation_area != 'bar']
    bar_items = [i for i in order.items if i.preparation_area == 'bar']

    # Проверка кухни
    all_kitchen_ready = all(i.is_ready for i in kitchen_items) if kitchen_items else True
    # Проверка бара
    all_bar_ready = all(i.is_ready for i in bar_items) if bar_items else True

    updated = False
    
    # Логика обновления статусов цехов
    if kitchen_items:
        if all_kitchen_ready and not order.kitchen_done:
            order.kitchen_done = True
            updated = True
            await notify_station_completion(bot, order, 'kitchen', session)
        elif not all_kitchen_ready and order.kitchen_done:
            # Если сняли галочку и стало не готово
            order.kitchen_done = False
            updated = True

    if bar_items:
        if all_bar_ready and not order.bar_done:
            order.bar_done = True
            updated = True
            await notify_station_completion(bot, order, 'bar', session)
        elif not all_bar_ready and order.bar_done:
            order.bar_done = False
            updated = True

    if updated:
        # Если ВСЕ готово, меняем глобальный статус заказа
        has_k = bool(kitchen_items)
        has_b = bool(bar_items)
        
        is_fully_done = False
        if has_k and has_b:
            if order.kitchen_done and order.bar_done: is_fully_done = True
        elif has_k:
            if order.kitchen_done: is_fully_done = True
        elif has_b:
            if order.bar_done: is_fully_done = True
            
        if is_fully_done:
            ready_status = await session.scalar(select(OrderStatus).where(OrderStatus.name == "Готовий до видачі").limit(1))
            # Меняем статус только если он еще не финальный и не "Готов"
            if ready_status and order.status_id != ready_status.id and not order.status.is_completed_status:
                old_status = order.status.name if order.status else "Unknown"
                order.status_id = ready_status.id
                session.add(OrderStatusHistory(order_id=order.id, status_id=ready_status.id, actor_info="Система (Авто-готовність)"))
                
                # Уведомляем всех о смене статуса
                await notify_all_parties_on_status_change(
                    order, old_status, "Система", bot, None, session
                )

        await session.commit()

# --- АВТОРИЗАЦИЯ ---

@router.get("/", include_in_schema=False)
async def staff_root_redirect():
    """Перенаправление с корня на дашборд."""
    return RedirectResponse(url="/staff/dashboard")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа. Если есть токен - редирект на дашборд."""
    token = request.cookies.get("staff_access_token")
    if token:
        return RedirectResponse(url="/staff/dashboard")
    return STAFF_LOGIN_HTML

@router.post("/login")
async def login_action(
    response: Response,
    phone: str = Form(...), 
    password: str = Form(...), 
    session: AsyncSession = Depends(get_db_session)
):
    """Обработка входа сотрудника."""
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    result = await session.execute(
        select(Employee).where(Employee.phone_number.ilike(f"%{clean_phone}%"))
    )
    employee = result.scalars().first()

    if not employee:
        return RedirectResponse(url="/staff/login?error=1", status_code=303)
    
    # Простая проверка пароля (или admin backdoor)
    if not employee.password_hash:
        if password == "admin": pass 
        else: return RedirectResponse(url="/staff/login?error=1", status_code=303)
    elif not verify_password(password, employee.password_hash):
        return RedirectResponse(url="/staff/login?error=1", status_code=303)

    access_token_expires = timedelta(minutes=60 * 12)
    
    access_token = create_access_token(
        data={"sub": str(employee.id)},
        expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/staff/dashboard", status_code=303)
    response.set_cookie(
        key="staff_access_token", 
        value=access_token, 
        httponly=True, 
        max_age=60*60*12,
        samesite="lax"
    )
    return response

@router.get("/logout")
async def logout():
    """Выход из системы."""
    response = RedirectResponse(url="/staff/login", status_code=303)
    response.delete_cookie("staff_access_token")
    return response

# --- ГЛАВНАЯ ПАНЕЛЬ (DASHBOARD) ---

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Отображение главной панели сотрудника."""
    try:
        employee = await get_current_staff(request, session)
    except HTTPException:
        response = RedirectResponse(url="/staff/login", status_code=303)
        response.delete_cookie("staff_access_token")
        return response

    settings = await session.get(Settings, 1) or Settings()
    
    if 'role' not in employee.__dict__:
        await session.refresh(employee, ['role'])

    shift_btn_class = "on" if employee.is_on_shift else "off"
    shift_btn_text = "🟢 На зміні" if employee.is_on_shift else "🔴 Почати зміну"

    # --- ГЕНЕРАЦИЯ ВКЛАДОК (TABS) СТРОГО ПО РОЛЯМ ---
    tabs_html = ""
    
    # Роли (флаги)
    is_admin_operator = employee.role.can_manage_orders
    is_waiter = employee.role.can_serve_tables
    is_courier = employee.role.can_be_assigned
    is_kitchen = employee.role.can_receive_kitchen_orders
    is_bar = employee.role.can_receive_bar_orders

    # 1. ОПЕРАТОР / АДМИН
    if is_admin_operator:
        tabs_html += '<button class="nav-item active" onclick="switchTab(\'orders\')"><i class="fa-solid fa-list-check"></i> Замовлення</button>'
        tabs_html += '<button class="nav-item" onclick="switchTab(\'delivery_admin\')"><i class="fa-solid fa-truck-fast"></i> Доставка (Всі)</button>'
    
    # 2. ОФИЦИАНТ
    if is_waiter:
        if not is_admin_operator:
            tabs_html += '<button class="nav-item active" onclick="switchTab(\'orders\')"><i class="fa-solid fa-list-ul"></i> Мої замовлення</button>'
        tabs_html += '<button class="nav-item" onclick="switchTab(\'tables\')"><i class="fa-solid fa-chair"></i> Столи</button>'
        
    # 3. КУХНЯ / БАР
    if is_kitchen or is_bar:
        active_cls = "active" if not (is_admin_operator or is_waiter) else ""
        tabs_html += f'<button class="nav-item {active_cls}" onclick="switchTab(\'production\')"><i class="fa-solid fa-fire-burner"></i> Черга</button>'
    
    # 4. КУРЬЕР
    if is_courier and not is_admin_operator:
        active_cls = "active" if not (is_waiter or is_kitchen or is_bar) else ""
        tabs_html += f'<button class="nav-item {active_cls}" onclick="switchTab(\'delivery_courier\')"><i class="fa-solid fa-motorcycle"></i> Мої доставки</button>'
    
    # 5. ФИНАНСЫ (Касса)
    if is_waiter or is_courier or is_admin_operator:
        tabs_html += '<button class="nav-item" onclick="switchTab(\'finance\')"><i class="fa-solid fa-wallet"></i> Каса</button>'

    # Уведомления (для всех)
    tabs_html += '<button class="nav-item" onclick="switchTab(\'notifications\')" style="position:relative;"><i class="fa-solid fa-bell"></i> Інфо<span id="nav-notify-badge" class="notify-dot" style="display:none;"></span></button>'

    content = f"""
    <div class="dashboard-header">
        <div class="user-info">
            <h3>{html.escape(employee.full_name)}</h3>
            <span class="role-badge">{html.escape(employee.role.name)}</span>
        </div>
        <button onclick="toggleShift()" id="shift-btn" class="shift-btn {shift_btn_class}">{shift_btn_text}</button>
    </div>
    
    <div id="main-view">
        <div id="loading-indicator"><i class="fa-solid fa-spinner fa-spin"></i> Завантаження...</div>
        <div id="content-area"></div>
    </div>

    <div class="bottom-nav" id="bottom-nav">
        {tabs_html}
        <button class="nav-item" onclick="window.location.href='/staff/logout'"><i class="fa-solid fa-right-from-bracket"></i> Вихід</button>
    </div>
    """
    
    return STAFF_DASHBOARD_HTML.format(
        site_title=settings.site_title or "Staff App",
        content=content
    )

@router.get("/manifest.json")
async def get_manifest(session: AsyncSession = Depends(get_db_session)):
    settings = await session.get(Settings, 1) or Settings()
    return JSONResponse({
        "name": f"{settings.site_title} Staff",
        "short_name": "Staff",
        "start_url": "/staff/dashboard",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": settings.primary_color or "#333333",
        "icons": [
            {"src": "/static/favicons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/favicons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/static/favicons/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}
        ]
    })

# --- API МЕТОДЫ ДЛЯ JS ---

@router.post("/api/shift/toggle")
async def toggle_shift_api(session: AsyncSession = Depends(get_db_session), employee: Employee = Depends(get_current_staff)):
    employee.is_on_shift = not employee.is_on_shift
    await session.commit()
    return JSONResponse({"status": "ok", "is_on_shift": employee.is_on_shift})

@router.get("/api/notifications")
async def get_notifications_api(session: AsyncSession = Depends(get_db_session), employee: Employee = Depends(get_current_staff)):
    notifs = (await session.execute(
        select(StaffNotification)
        .where(StaffNotification.employee_id == employee.id)
        .order_by(StaffNotification.created_at.desc())
        .limit(20)
    )).scalars().all()
    
    unread_count = sum(1 for n in notifs if not n.is_read)
    
    data = []
    for n in notifs:
        data.append({
            "id": n.id, 
            "message": n.message, 
            "time": n.created_at.strftime("%d.%m %H:%M"), 
            "is_read": n.is_read
        })
        if not n.is_read: 
            n.is_read = True
    
    if unread_count > 0: 
        await session.commit()
        
    return JSONResponse({"unread_count": unread_count, "list": data})

@router.get("/api/data")
async def get_staff_data(
    view: str = "orders",
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
    """Основной метод получения HTML-контента для вкладок."""
    try:
        if not employee.is_on_shift:
            return JSONResponse({"html": "<div class='empty-state'><i class='fa-solid fa-power-off'></i>🔴 Ви не на зміні. <br>Натисніть кнопку зверху для початку роботи.</div>"})

        # --- Вкладка СТОЛЫ ---
        if view == "tables" and employee.role.can_serve_tables:
            return await _render_tables_view(session, employee)

        # --- Вкладка ЗАКАЗЫ ---
        elif view == "orders":
            if employee.role.can_manage_orders:
                orders_data = await _get_general_orders(session, employee)
                return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-regular fa-folder-open'></i>Активних замовлень немає.</div>"})
            elif employee.role.can_serve_tables:
                orders_html = await _get_waiter_orders_grouped(session, employee)
                return JSONResponse({"html": orders_html if orders_html else "<div class='empty-state'><i class='fa-solid fa-utensils'></i>Ваших активних замовлень немає.</div>"})
            else:
                return JSONResponse({"html": "<div class='empty-state'>Немає доступу до списку замовлень.</div>"})

        # --- Вкладка ФИНАНСЫ (Касса) ---
        elif view == "finance":
            if employee.role.can_serve_tables or employee.role.can_be_assigned or employee.role.can_manage_orders:
                finance_html = await _get_finance_details(session, employee)
                return JSONResponse({"html": finance_html})
            else:
                return JSONResponse({"html": "<div class='empty-state'>Доступ заборонено.</div>"})

        # --- Вкладка ПРОИЗВОДСТВО (Кухня/Бар) ---
        elif view == "production":
            if employee.role.can_receive_kitchen_orders or employee.role.can_receive_bar_orders:
                orders_data = await _get_production_orders(session, employee)
                return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-solid fa-check-double'></i>Черга пуста. Всі страви готові.</div>"})
            else:
                return JSONResponse({"html": "<div class='empty-state'>У вас немає прав доступу до кухні/бару.</div>"})

        # --- Вкладка ДОСТАВКА (КУРЬЕР) ---
        elif view == "delivery_courier":
            if employee.role.can_be_assigned:
                orders_data = await _get_my_courier_orders(session, employee)
                return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-solid fa-motorcycle'></i>Немає призначених замовлень.</div>"})
            else:
                return JSONResponse({"html": "<div class='empty-state'>Ви не кур'єр.</div>"})

        # --- Вкладка ДОСТАВКА (АДМИН) ---
        elif view == "delivery_admin":
            if employee.role.can_manage_orders:
                orders_data = await _get_all_delivery_orders_for_admin(session, employee)
                return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-solid fa-truck'></i>Активних доставок немає.</div>"})
            else:
                return JSONResponse({"html": "<div class='empty-state'>Доступ заборонено.</div>"})
        
        elif view == "notifications":
            return JSONResponse({"html": "<div id='notification-list-container' style='text-align:center; color:#999;'>Оновлення...</div>"})

        return JSONResponse({"html": ""})
        
    except Exception as e:
        logger.error(f"API Error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

# --- РЕНДЕРИНГ КОНТЕНТА ---

async def _render_tables_view(session: AsyncSession, employee: Employee):
    tables = (await session.execute(
        select(Table)
        .where(Table.assigned_waiters.any(Employee.id == employee.id))
        .order_by(Table.name)
    )).scalars().all()
    
    if not tables: 
        return JSONResponse({"html": "<div class='empty-state'><i class='fa-solid fa-chair'></i>За вами не закріплено столиків.</div>"})
    
    html_content = "<div class='grid-container'>"
    for t in tables:
        final_ids = select(OrderStatus.id).where(or_(OrderStatus.is_completed_status==True, OrderStatus.is_cancelled_status==True))
        active_count = await session.scalar(
            select(func.count(Order.id)).where(Order.table_id == t.id, Order.status_id.not_in(final_ids))
        )
        
        badge_class = "alert" if active_count > 0 else "success"
        border_color = "#e74c3c" if active_count > 0 else "transparent"
        bg_color = "#fff"
        status_text = f"{active_count} активних" if active_count > 0 else "Вільний"
        
        html_content += STAFF_TABLE_CARD.format(
            id=t.id, 
            name_esc=html.escape(t.name), 
            badge_class=badge_class, 
            status_text=status_text,
            border_color=border_color, 
            bg_color=bg_color
        )
    html_content += "</div>"
    return JSONResponse({"html": html_content})

async def _get_waiter_orders_grouped(session: AsyncSession, employee: Employee):
    """Генерация списка заказов для официанта с группировкой по столам и статусами блюд."""
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    
    tables_sub = select(Table.id).where(Table.assigned_waiters.any(Employee.id == employee.id))
    
    q = select(Order).options(
        joinedload(Order.status), joinedload(Order.table), joinedload(Order.accepted_by_waiter),
        selectinload(Order.items)
    ).where(
        Order.status_id.not_in(final_ids),
        or_(Order.accepted_by_waiter_id == employee.id, Order.table_id.in_(tables_sub))
    ).order_by(Order.table_id, Order.id.desc())

    orders = (await session.execute(q)).scalars().all()
    if not orders: return ""

    grouped_orders = {} 
    for o in orders:
        t_id = o.table_id if o.table_id else 0 
        if t_id not in grouped_orders:
            t_name = o.table.name if o.table else "Інше"
            grouped_orders[t_id] = {"name": t_name, "orders": [], "total": Decimal(0)}
        
        grouped_orders[t_id]["orders"].append(o)
        grouped_orders[t_id]["total"] += o.total_price

    html_out = ""
    for t_id, group in grouped_orders.items():
        html_out += f"""
        <div class='table-group-header' style="justify-content: space-between;">
            <span><i class='fa-solid fa-chair'></i> {html.escape(group['name'])}</span>
            <span class="badge warning" style="font-size:0.9em; color:#333;">Σ {group['total']:.2f} грн</span>
        </div>
        """

        for o in group['orders']:
            items_html_list = []
            for item in o.items:
                mods_str = ""
                if item.modifiers:
                    mods_names = [m['name'] for m in item.modifiers]
                    mods_str = f" <small style='color:#666;'>({', '.join(mods_names)})</small>"
                
                # --- ЛОГИКА ГАЛОЧЕК ДЛЯ ОФИЦИАНТА ---
                # Используем поле is_ready
                is_ready = item.is_ready
                
                icon = "✅" if is_ready else "⏳"
                style = "color:green; font-weight:bold;" if is_ready else "color:#555;"
                
                items_html_list.append(f"<li style='{style}'>{icon} {html.escape(item.product_name)}{mods_str} x{item.quantity}</li>")
            
            items_html = f"<ul style='margin:5px 0; padding-left:20px; font-size:0.9rem;'>{''.join(items_html_list)}</ul>"

            content = f"""
            <div class="info-row"><i class="fa-solid fa-clock"></i> {o.created_at.strftime('%H:%M')}</div>
            <div class="info-row"><i class="fa-solid fa-money-bill-wave"></i> <b>{o.total_price} грн</b></div>
            {items_html}
            """
            
            btns = ""
            if not o.accepted_by_waiter_id: 
                btns += f"<button class='action-btn' onclick=\"performAction('accept_order', {o.id})\">🙋 Прийняти</button>"
            else: 
                btns += f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">✏️ Деталі / Оплата</button>"
            
            # Статус текста (Индикатор готовности цехов)
            status_parts = [o.status.name]
            if o.kitchen_done: status_parts.append("🍳Готово")
            if o.bar_done: status_parts.append("🍹Готово")
            
            badge_class = "success" if (o.kitchen_done or o.bar_done) else "info"
            color = "#27ae60" if (o.kitchen_done or o.bar_done) else "#333"

            html_out += STAFF_ORDER_CARD.format(
                id=o.id, 
                time=o.created_at.strftime('%H:%M'), 
                badge_class=badge_class, 
                status=" | ".join(status_parts), 
                content=content, 
                buttons=btns, 
                color=color
            )
        
    return html_out

async def _get_finance_details(session: AsyncSession, employee: Employee):
    current_debt = employee.cash_balance
    
    q = select(Order).options(joinedload(Order.table)).where(
        or_(
            Order.accepted_by_waiter_id == employee.id,
            Order.courier_id == employee.id
        ),
        Order.payment_method == 'cash',
        Order.is_cash_turned_in == False,
        Order.status.has(is_completed_status=True)
    ).order_by(Order.id.desc())
    
    orders = (await session.execute(q)).scalars().all()
    
    list_html = ""
    for o in orders:
        target = o.table.name if o.table else (o.address or "Самовивіз")
        list_html += f"""
        <div class="debt-item">
            <div>
                <div style="font-weight:bold;">#{o.id} - {html.escape(target)}</div>
                <div style="font-size:0.8rem; color:#777;">{o.created_at.strftime('%d.%m %H:%M')}</div>
            </div>
            <div style="font-weight:bold; color:#e74c3c;">{o.total_price} грн</div>
        </div>
        """
    
    if not list_html:
        list_html = "<div style='text-align:center; color:#999; padding:20px;'>Немає незакритих чеків</div>"

    color_class = "red-text" if current_debt > 0 else "green-text"
    
    return f"""
    <div class="finance-card">
        <div class="finance-header">Ваш баланс (Борг)</div>
        <div class="finance-amount {color_class}">{current_debt:.2f} грн</div>
        <div style="font-size:0.9rem; color:#666; margin-top:5px;">Готівка на руках</div>
    </div>
    
    <h4 style="margin: 20px 0 10px; padding-left: 5px;">Деталізація (Не здані в касу):</h4>
    <div class="debt-list">
        {list_html}
    </div>
    <div style="text-align:center; margin-top:20px; font-size:0.85rem; color:#888;">
        Щоб здати гроші, зверніться до адміністратора.
    </div>
    """

async def _get_production_orders(session: AsyncSession, employee: Employee):
    orders_data = []
    
    # Получаем ID цехов, назначенных сотруднику
    my_workshop_ids = employee.assigned_workshop_ids or []
    
    # Загружаем заказы "В работе"
    status_query = select(OrderStatus.id).where(
        or_(OrderStatus.visible_to_chef == True, OrderStatus.visible_to_bartender == True)
    )
    status_ids = (await session.execute(status_query)).scalars().all()
    
    if status_ids:
        q = select(Order).options(
            joinedload(Order.table), 
            selectinload(Order.items).joinedload(OrderItem.product), 
            joinedload(Order.status)
        ).where(
            Order.status_id.in_(status_ids), 
            Order.status.has(requires_kitchen_notify=True),
            # Показываем заказ, если хотя бы один из цехов еще не закончил
            or_(Order.kitchen_done == False, Order.bar_done == False)
        ).order_by(Order.id.asc())
        
        orders = (await session.execute(q)).scalars().all()
        
        if orders:
            for o in orders:
                active_items_html = ""
                done_items_html = ""
                count_active = 0
                count_total = 0
                
                for item in o.items:
                    # Проверяем, относится ли товар к цехам сотрудника
                    prod_wh_id = item.product.production_warehouse_id
                    is_my_item = not my_workshop_ids or (prod_wh_id in my_workshop_ids)
                    
                    # Также проверяем роль (Кухня vs Бар) для совместимости
                    is_bar_item = item.preparation_area == 'bar'
                    if is_bar_item and not employee.role.can_receive_bar_orders: is_my_item = False
                    if not is_bar_item and not employee.role.can_receive_kitchen_orders: is_my_item = False

                    if is_my_item:
                        count_total += 1
                        mods = f"<br><small>{', '.join([m['name'] for m in item.modifiers])}</small>" if item.modifiers else ""
                        
                        # --- ОТОБРАЖЕНИЕ БЛЮДА ---
                        if item.is_ready:
                            # Уже готовое блюдо (серое, зачеркнутое)
                            # При клике спрашиваем "Вернуть?"
                            done_items_html += f"""
                            <div onclick="if(confirm('Повернути цю страву в роботу?')) performAction('toggle_item', {o.id}, {item.id})" 
                                 style="padding:12px 15px; border-bottom:1px solid #eee; cursor:pointer; font-size:1rem; display:flex; align-items:center; background:#f9f9f9; color:#999; text-decoration:line-through;">
                                <i class="fa-solid fa-check-circle" style="margin-right:15px; color:#aaa;"></i> 
                                <div style="flex-grow:1;">{html.escape(item.product_name)} x{item.quantity}{mods}</div>
                            </div>
                            """
                        else:
                            # Активное блюдо (белое, большое)
                            # При клике спрашиваем "Готово?"
                            count_active += 1
                            active_items_html += f"""
                            <div onclick="if(confirm('Страва готова?')) performAction('toggle_item', {o.id}, {item.id})" 
                                 style="padding:18px 15px; border-bottom:1px solid #eee; cursor:pointer; font-size:1.15rem; display:flex; align-items:center; background:white; font-weight:500;">
                                <i class="fa-regular fa-square" style="margin-right:15px; color:#ccc; font-size:1.4rem;"></i> 
                                <div style="flex-grow:1;">{html.escape(item.product_name)} x{item.quantity}{mods}</div>
                            </div>
                            """
                
                # Показываем заказ только если есть хотя бы одно блюдо этого цеха
                if count_total > 0:
                    if count_active == 0: continue

                    table_info = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовивіз")
                    
                    # Собираем все вместе
                    full_content = f"""
                    <div class='info-row'><i class='fa-solid fa-utensils'></i> <b>{table_info}</b> <span style="color:#777; margin-left:10px;">#{o.id}</span></div>
                    <div style='border-radius:8px; overflow:hidden; border:1px solid #ddd; margin-top:5px;'>
                        {active_items_html}
                        {done_items_html}
                    </div>
                    """
                    
                    btns = "" # Кнопок не надо, все на кликах
                    
                    orders_data.append({"id": o.id, "html": STAFF_ORDER_CARD.format(
                        id=o.id, 
                        time=o.created_at.strftime('%H:%M'), 
                        badge_class="warning", 
                        status="В роботі", 
                        content=full_content,
                        buttons=btns, 
                        color="#f39c12"
                    )})

    return orders_data

async def _get_my_courier_orders(session: AsyncSession, employee: Employee):
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    q = select(Order).options(joinedload(Order.status), selectinload(Order.items)).where(Order.courier_id == employee.id, Order.status_id.not_in(final_ids)).order_by(Order.id.desc())
    orders = (await session.execute(q)).scalars().all()
    res = []
    for o in orders:
        # Формируем список с галочками
        items_html_list = []
        for item in o.items:
            # Используем is_ready
            is_ready = item.is_ready
            
            icon = "✅" if is_ready else "⏳"
            style = "color:#27ae60;" if is_ready else "color:#555;"
            items_html_list.append(f"<div style='{style}'>{icon} {html.escape(item.product_name)} x{item.quantity}</div>")
        
        items_block = "".join(items_html_list)

        content = f"""
        <div class="info-row"><i class="fa-solid fa-map-pin"></i> {html.escape(o.address or 'Не вказано')}</div>
        <div class="info-row"><i class="fa-solid fa-phone"></i> <a href="tel:{o.phone_number}">{html.escape(o.phone_number or '')}</a></div>
        <div class="info-row"><i class="fa-solid fa-money-bill"></i> <b>{o.total_price} грн</b></div>
        <div style="margin-top:10px; padding-top:5px; border-top:1px dashed #ccc; font-size:0.9rem;">
            {items_block}
        </div>
        """
        
        status_text = o.status.name
        if o.kitchen_done and o.bar_done: status_text = "📦 ВСЕ ГОТОВО"
        elif o.kitchen_done: status_text = "🍳 Кухня готова"
        
        btns = f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">⚙️ Статус / Інфо</button>"
        res.append({"id": o.id, "html": STAFF_ORDER_CARD.format(
            id=o.id, 
            time=o.created_at.strftime('%H:%M'), 
            badge_class="success" if (o.kitchen_done and o.bar_done) else "info", 
            status=status_text, 
            content=content, 
            buttons=btns, 
            color="#333"
        )})
    return res

async def _get_all_delivery_orders_for_admin(session: AsyncSession, employee: Employee):
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    
    q = select(Order).options(
        joinedload(Order.status), joinedload(Order.courier)
    ).where(
        Order.status_id.not_in(final_ids),
        Order.is_delivery == True
    ).order_by(Order.id.desc())

    orders = (await session.execute(q)).scalars().all()
    res = []
    for o in orders:
        courier_info = f"🚴 {o.courier.full_name}" if o.courier else "<span style='color:red'>🔴 Не призначено</span>"
        
        content = f"""
        <div class="info-row"><i class="fa-solid fa-truck"></i> <b>{html.escape(o.address or 'Адреса не вказана')}</b></div>
        <div class="info-row"><i class="fa-solid fa-user"></i> {courier_info}</div>
        <div class="info-row"><i class="fa-solid fa-money-bill-wave"></i> {o.total_price} грн</div>
        """
        
        btns = f"<button class='action-btn' onclick=\"openOrderEditModal({o.id})\">⚙️ Призначити / Змінити</button>"
        
        res.append({"id": o.id, "html": STAFF_ORDER_CARD.format(
            id=o.id, 
            time=o.created_at.strftime('%H:%M'), 
            badge_class="warning" if not o.courier else "info", 
            status=o.status.name, 
            content=content, 
            buttons=btns, 
            color="#e67e22" if not o.courier else "#3498db"
        )})
    return res

async def _get_general_orders(session: AsyncSession, employee: Employee):
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    
    q = select(Order).options(
        joinedload(Order.status), joinedload(Order.table), joinedload(Order.accepted_by_waiter), joinedload(Order.courier), selectinload(Order.items)
    ).where(Order.status_id.not_in(final_ids)).order_by(Order.id.desc())

    orders = (await session.execute(q)).scalars().all()
    res = []
    for o in orders:
        table_name = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовивіз")
        
        extra_info = ""
        if o.is_delivery:
            courier_name = o.courier.full_name if o.courier else "Не призначено"
            extra_info = f"<div class='info-row' style='font-size:0.85rem; color:#555;'>Кур'єр: {courier_name}</div>"
        
        items_list = []
        for item in o.items:
            mods_str = ""
            if item.modifiers:
                mods_names = [m['name'] for m in item.modifiers]
                mods_str = f" <small>({', '.join(mods_names)})</small>"
            items_list.append(f"{item.product_name}{mods_str}")
        items_preview = ", ".join(items_list)
        if len(items_preview) > 50: items_preview = items_preview[:50] + "..."

        content = f"""
        <div class="info-row"><i class="fa-solid fa-info-circle"></i> <b>{html.escape(table_name)}</b></div>
        <div class="info-row"><i class="fa-solid fa-money-bill-wave"></i> {o.total_price} грн</div>
        <div class="info-row" style="font-size:0.85rem; color:#666;"><i class="fa-solid fa-list"></i> {html.escape(items_preview)}</div>
        {extra_info}
        """
        
        btns = f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">⚙️ Керувати</button>"
        
        res.append({"id": o.id, "html": STAFF_ORDER_CARD.format(
            id=o.id, 
            time=o.created_at.strftime('%H:%M'), 
            badge_class="info", 
            status=o.status.name, 
            content=content, 
            buttons=btns, 
            color="#333"
        )})
    return res

@router.get("/api/order/{order_id}/details")
async def get_order_details(order_id: int, session: AsyncSession = Depends(get_db_session), employee: Employee = Depends(get_current_staff)):
    order = await session.get(Order, order_id, options=[selectinload(Order.items), joinedload(Order.status), joinedload(Order.courier)])
    if not order: return JSONResponse({"error": "Не знайдено"}, status_code=404)
    
    status_query = select(OrderStatus)
    if employee.role.can_manage_orders:
        status_query = status_query.where(OrderStatus.visible_to_operator == True)
    elif employee.role.can_be_assigned:
        status_query = status_query.where(OrderStatus.visible_to_courier == True)
    elif employee.role.can_serve_tables:
        status_query = status_query.where(OrderStatus.visible_to_waiter == True)
    else:
        status_query = status_query.where(OrderStatus.id == order.status_id)
    
    statuses = (await session.execute(status_query.order_by(OrderStatus.id))).scalars().all()
    
    if order.status_id not in [s.id for s in statuses]:
        current_s = await session.get(OrderStatus, order.status_id)
        if current_s: statuses.append(current_s)

    status_list = [{"id": s.id, "name": s.name, "selected": s.id == order.status_id, "is_completed": s.is_completed_status} for s in statuses]

    items = []
    for i in order.items:
        modifiers_str = ""
        if i.modifiers:
            mod_names = [m['name'] for m in i.modifiers]
            if mod_names:
                modifiers_str = f" + {', '.join(mod_names)}"
        
        items.append({
            "id": i.product_id, 
            "name": i.product_name + modifiers_str, 
            "qty": i.quantity, 
            "price": float(i.price_at_moment),
            "modifiers": i.modifiers 
        })
    
    couriers_list = []
    if employee.role.can_manage_orders and order.is_delivery:
        courier_role_res = await session.execute(select(Role.id).where(Role.can_be_assigned == True))
        courier_role_ids = courier_role_res.scalars().all()
        if courier_role_ids:
            couriers = (await session.execute(select(Employee).where(Employee.role_id.in_(courier_role_ids), Employee.is_on_shift == True))).scalars().all()
            couriers_list = [{"id": c.id, "name": c.full_name, "selected": c.id == order.courier_id} for c in couriers]

    return JSONResponse({
        "id": order.id,
        "total": float(order.total_price),
        "items": items,
        "statuses": status_list,
        "status_id": order.status_id,
        "is_delivery": order.is_delivery,
        "couriers": couriers_list,
        "can_assign_courier": employee.role.can_manage_orders,
        "can_edit_items": check_edit_permissions(employee, order)
    })

@router.post("/api/order/assign_courier")
async def assign_courier_api(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
    if not employee.role.can_manage_orders:
        return JSONResponse({"error": "Заборонено"}, status_code=403)
        
    data = await request.json()
    order_id = int(data.get("orderId"))
    courier_id = int(data.get("courierId")) 
    
    order = await session.get(Order, order_id)
    if not order: return JSONResponse({"error": "Замовлення не знайдено"}, 404)
    
    if order.status.is_completed_status:
        return JSONResponse({"error": "Замовлення закрите"}, 400)

    msg = ""
    if courier_id == 0:
        order.courier_id = None
        msg = "Кур'єра знято"
    else:
        courier = await session.get(Employee, courier_id)
        if not courier: return JSONResponse({"error": "Кур'єра не знайдено"}, 404)
        order.courier_id = courier_id
        msg = f"Призначено: {courier.full_name}"
        
        await create_staff_notification(session, courier.id, f"📦 Вам призначено замовлення #{order.id} ({order.address or 'Доставка'})")
    
    await session.commit()
    return JSONResponse({"success": True, "message": msg})

@router.post("/api/order/update_status")
async def update_order_status_api(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
    data = await request.json()
    order_id = int(data.get("orderId"))
    new_status_id = int(data.get("statusId"))
    payment_method = data.get("paymentMethod")
    
    order = await session.get(Order, order_id, options=[joinedload(Order.status)])
    if not order: return JSONResponse({"error": "Не знайдено"}, 404)
    
    can_edit = False
    if employee.role.can_manage_orders: can_edit = True
    elif employee.role.can_serve_tables and order.accepted_by_waiter_id == employee.id: can_edit = True
    elif employee.role.can_be_assigned and order.courier_id == employee.id: can_edit = True
    
    if not can_edit:
         return JSONResponse({"error": "Немає прав"}, 403)

    old_status = order.status.name
    new_status = await session.get(OrderStatus, new_status_id)
    
    # --- ВАЖЛИВО: Перевірка дозволу на зміну статусу ---
    # Дозволяємо перехід з "Виконано" в "Скасовано" або "Активний", щоб виправити помилку.
    # Забороняємо інші переходи для закритих замовлень.
    
    is_already_closed = order.status.is_completed_status or order.status.is_cancelled_status
    is_moving_to_cancelled = new_status.is_cancelled_status
    is_moving_to_active = not (new_status.is_completed_status or new_status.is_cancelled_status)

    if is_already_closed:
        if not (is_moving_to_cancelled or is_moving_to_active):
             return JSONResponse({"error": "Замовлення закрите. Зміна заборонена."}, 400)

    # --- ЛОГІКА КАСИ: СКАСУВАННЯ БОРГУ ---
    # Якщо переходимо з "Виконано" (де гроші повісили на кур'єра) в "Скасовано"
    if order.status.is_completed_status and new_status.is_cancelled_status:
        await unregister_employee_debt(session, order)
    # -------------------------------------

    order.status_id = new_status_id
    
    if payment_method:
        order.payment_method = payment_method

    # --- ЛОГІКА КАСИ: НАРАХУВАННЯ БОРГУ ---
    if new_status.is_completed_status:
        if order.is_delivery:
             if order.courier_id:
                 order.completed_by_courier_id = order.courier_id
             elif employee.role.can_be_assigned:
                 order.completed_by_courier_id = employee.id

        await link_order_to_shift(session, order, employee.id)
        if order.payment_method == 'cash':
            debtor_id = employee.id
            if employee.role.can_manage_orders:
                if order.courier_id: debtor_id = order.courier_id
                elif order.accepted_by_waiter_id: debtor_id = order.accepted_by_waiter_id
            
            await register_employee_debt(session, order, debtor_id)
    # -----------------------------------------------

    session.add(OrderStatusHistory(order_id=order.id, status_id=new_status_id, actor_info=f"{employee.full_name} (PWA)"))
    await session.commit()
    
    await notify_all_parties_on_status_change(
        order, old_status, f"{employee.full_name} (PWA)", 
        request.app.state.admin_bot, request.app.state.client_bot, session
    )
    return JSONResponse({"success": True})

@router.post("/api/order/update_items")
async def update_order_items_api(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
    data = await request.json()
    order_id = int(data.get("orderId"))
    items = data.get("items") 
    
    # ВАЖНО: Добавляем joinedload(Order.status), чтобы иметь доступ к свойствам статуса
    order = await session.get(Order, order_id, options=[joinedload(Order.status)])
    
    if not order: return JSONResponse({"error": "Замовлення не знайдено"}, 404)
    
    if not check_edit_permissions(employee, order):
        return JSONResponse({"error": "Немає прав на редагування"}, 403)

    if order.status.is_completed_status or order.status.is_cancelled_status:
        return JSONResponse({"error": "Замовлення закрите"}, 400)
        
    # --- НОВАЯ ПРОВЕРКА (Блокировка редактирования если на кухне) ---
    if order.status.requires_kitchen_notify:
        return JSONResponse({"error": "Замовлення вже на кухні. Редагування заборонено. Створіть нове замовлення для додаткових страв."}, 403)
    # ---------------------------------------------------------------
    
    if order.is_inventory_deducted:
        return JSONResponse({"error": "Склад вже списано. Редагування заборонено."}, 403)
    
    await session.execute(delete(OrderItem).where(OrderItem.order_id == order_id))
    
    total_price = Decimal(0)
    if items:
        prod_ids = [int(i['id']) for i in items]
        products = (await session.execute(select(Product).where(Product.id.in_(prod_ids)))).scalars().all()
        prod_map = {p.id: p for p in products}
        
        # --- FIX: Загружаем модификаторы из БД ---
        db_modifiers = await fetch_db_modifiers(session, items)
        # -------------------------------------------
        
        for item in items:
            pid = int(item['id'])
            qty = int(item['qty'])
            if pid in prod_map and qty > 0:
                p = prod_map[pid]
                
                # --- FIX: Реконструируем модификаторы ---
                final_mods = []
                mods_price = Decimal(0)
                for raw_mod in item.get('modifiers', []):
                    mid = int(raw_mod['id'])
                    if mid in db_modifiers:
                        m_db = db_modifiers[mid]
                        mods_price += m_db.price
                        final_mods.append({
                            "id": m_db.id,
                            "name": m_db.name,
                            "price": float(m_db.price),
                            "ingredient_id": m_db.ingredient_id,
                            "ingredient_qty": float(m_db.ingredient_qty)
                        })
                # ---------------------------------------
                
                item_price = p.price + mods_price
                total_price += item_price * qty
                
                session.add(OrderItem(
                    order_id=order_id,
                    product_id=p.id,
                    product_name=p.name,
                    quantity=qty,
                    price_at_moment=item_price,
                    preparation_area=p.preparation_area,
                    modifiers=final_mods
                ))
    
    # --- ЛОГИКА ДОСТАВКИ (Фикс потери стоимости доставки) ---
    if order.is_delivery:
        settings = await session.get(Settings, 1) or Settings()
        # Проверяем порог бесплатной доставки
        delivery_cost = settings.delivery_cost
        if settings.free_delivery_from is not None and total_price >= settings.free_delivery_from:
            delivery_cost = Decimal(0)
        total_price += delivery_cost
    # ---------------------------------------------------------

    order.kitchen_done = False
    order.bar_done = False
    order.total_price = total_price
    await session.commit()
    
    msg = f"🔄 Замовлення #{order.id} оновлено ({employee.full_name})"
    chefs = (await session.execute(
        select(Employee).join(Role).where(Role.can_receive_kitchen_orders==True, Employee.is_on_shift==True)
    )).scalars().all()
    for c in chefs:
        await create_staff_notification(session, c.id, msg)
        
    return JSONResponse({"success": True})

@router.post("/api/action")
async def handle_action_api(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
    try:
        data = await request.json()
        action = data.get("action")
        order_id = int(data.get("orderId"))
        
        # --- ЛОГИКА ПОШТУЧНОЙ ГОТОВНОСТИ ---
        if action == "toggle_item":
            item_id = int(data.get("extra"))
            item = await session.get(OrderItem, item_id)
            if item:
                # Toggle ready state
                item.is_ready = not item.is_ready
                await session.commit()
                
                # Проверяем, готов ли весь заказ (для конкретного цеха)
                await check_and_update_order_readiness(session, order_id, request.app.state.admin_bot)
                return JSONResponse({"success": True})
        
        elif action == "accept_order":
            order = await session.get(Order, order_id)
            if order and not order.accepted_by_waiter_id:
                order.accepted_by_waiter_id = employee.id
                proc_status = await session.scalar(select(OrderStatus).where(OrderStatus.name == "В обробці").limit(1))
                if proc_status: order.status_id = proc_status.id
                await session.commit()
                return JSONResponse({"success": True})

        return JSONResponse({"success": False, "error": "Unknown action"})
    except Exception as e:
        logger.error(f"Action Error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/menu/full")
async def get_full_menu(session: AsyncSession = Depends(get_db_session)):
    """
    Возвращает полное меню ресторана для PWA.
    """
    cats = (await session.execute(select(Category).where(Category.show_in_restaurant==True).order_by(Category.sort_order))).scalars().all()
    
    menu = []
    for c in cats:
        prods = (await session.execute(
            select(Product)
            .where(Product.category_id==c.id, Product.is_active==True)
            .options(selectinload(Product.modifiers))
        )).scalars().all()
        
        prod_list = []
        for p in prods:
            p_mods = []
            if p.modifiers:
                for m in p.modifiers:
                    price_val = m.price if m.price is not None else 0
                    p_mods.append({"id": m.id, "name": m.name, "price": float(price_val)})
            
            prod_list.append({
                "id": p.id, 
                "name": p.name, 
                "price": float(p.price), 
                "preparation_area": p.preparation_area,
                "modifiers": p_mods 
            })
            
        menu.append({
            "id": c.id, 
            "name": c.name, 
            "products": prod_list
        })
        
    return JSONResponse({"menu": menu})

@router.post("/api/order/create")
async def create_waiter_order(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
    if not employee.role.can_serve_tables:
        return JSONResponse({"error": "Forbidden"}, 403)

    try:
        data = await request.json()
        table_id = int(data.get("tableId"))
        cart = data.get("cart") 
        
        table = await session.get(Table, table_id)
        if not table or not cart: return JSONResponse({"error": "Invalid data"}, status_code=400)
        
        total = Decimal(0)
        items_obj = []
        
        prod_ids = [int(item['id']) for item in cart]
        products_res = await session.execute(select(Product).where(Product.id.in_(prod_ids)))
        products_map = {p.id: p for p in products_res.scalars().all()}
        
        # --- FIX: Загружаем модификаторы из БД ---
        db_modifiers = await fetch_db_modifiers(session, cart)
        # -------------------------------------------
        
        for item in cart:
            pid = int(item['id'])
            qty = int(item['qty'])
            
            if pid in products_map and qty > 0:
                prod = products_map[pid]
                
                # --- FIX: Реконструируем модификаторы ---
                final_mods = []
                mods_price = Decimal(0)
                for raw_mod in item.get('modifiers', []):
                    mid = int(raw_mod['id'])
                    if mid in db_modifiers:
                        m_db = db_modifiers[mid]
                        mods_price += m_db.price
                        final_mods.append({
                            "id": m_db.id,
                            "name": m_db.name,
                            "price": float(m_db.price),
                            "ingredient_id": m_db.ingredient_id,
                            "ingredient_qty": float(m_db.ingredient_qty)
                        })
                # ---------------------------------------
                
                item_price = prod.price + mods_price
                total += item_price * qty
                
                items_obj.append(OrderItem(
                    product_id=prod.id, 
                    product_name=prod.name, 
                    quantity=qty, 
                    price_at_moment=item_price,
                    preparation_area=prod.preparation_area,
                    modifiers=final_mods
                ))
        
        new_status = await session.scalar(select(OrderStatus).where(OrderStatus.name == "Новий").limit(1))
        status_id = new_status.id if new_status else 1
        
        order = Order(
            table_id=table_id, 
            customer_name=f"Стіл: {table.name}", 
            phone_number=f"table_{table_id}",
            total_price=total, 
            order_type="in_house", 
            is_delivery=False, 
            delivery_time="In House",
            accepted_by_waiter_id=employee.id, 
            status_id=status_id, 
            items=items_obj
        )
        session.add(order)
        await session.flush()

        for item_data in items_obj:
            item_data.order_id = order.id
            session.add(item_data)

        await session.commit()
        
        await session.refresh(order, ['status'])
        
        session.add(OrderStatusHistory(order_id=order.id, status_id=status_id, actor_info=f"{employee.full_name} (PWA)"))
        await session.commit()
        
        await notify_new_order_to_staff(request.app.state.admin_bot, order, session)
        return JSONResponse({"success": True, "orderId": order.id})
    except Exception as e:
        logger.error(f"Order create error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/print_recipe/{order_id}")
async def print_recipe(order_id: int, session: AsyncSession = Depends(get_db_session)):
    """Генерация HTML чека/бегунка для повара"""
    from inventory_service import generate_cook_ticket 
    
    try:
        html_content = await generate_cook_ticket(session, order_id)
        return HTMLResponse(html_content)
    except Exception as e:
        logger.error(f"Error generating receipt: {e}")
        return HTMLResponse(f"Ошибка печати: {e}", status_code=500)
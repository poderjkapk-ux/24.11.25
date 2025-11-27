# staff_pwa.py

import html
import logging
import json
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, delete
from sqlalchemy.orm import joinedload, selectinload

# Імпорт моделей та залежностей
from models import (
    Employee, Settings, Order, OrderStatus, Role, OrderItem, Table, 
    Category, Product, OrderStatusHistory, StaffNotification
)
# Імпорт модели модификаторов
from inventory_models import Modifier
from dependencies import get_db_session
from auth_utils import verify_password, create_access_token, get_current_staff

# Імпорт шаблонів
from staff_templates import (
    STAFF_LOGIN_HTML, STAFF_DASHBOARD_HTML, 
    STAFF_TABLE_CARD, STAFF_ORDER_CARD
)

# Імпорт менеджерів сповіщень та каси
from notification_manager import (
    notify_all_parties_on_status_change, 
    notify_new_order_to_staff, 
    notify_station_completion,
    create_staff_notification
)
from cash_service import link_order_to_shift, register_employee_debt

# Налаштування роутера та логера
router = APIRouter(prefix="/staff", tags=["staff_pwa"])
logger = logging.getLogger(__name__)

# --- ДОПОМІЖНІ ФУНКЦІЇ ---

def check_edit_permissions(employee: Employee, order: Order) -> bool:
    """
    Перевіряє, чи має співробітник право редагувати склад замовлення.
    """
    # 1. Адмін/Оператор може все
    if employee.role.can_manage_orders:
        return True
    
    # 2. Офіціант може редагувати тільки СВОЇ замовлення (або замовлення зі своїх столів, якщо ще не прийняті)
    if employee.role.can_serve_tables:
        # Якщо замовлення "in_house" і прийняте цим офіціантом
        if order.accepted_by_waiter_id == employee.id:
            return True
        # Якщо замовлення "in_house", ніким не прийняте (дозволяємо редагувати/приймати)
        if order.order_type == 'in_house' and order.accepted_by_waiter_id is None:
            return True
            
    # 3. Кур'єри, Повара, Бармени не можуть змінювати склад замовлення
    return False

# --- АВТОРИЗАЦІЯ ---

@router.get("/", include_in_schema=False)
async def staff_root_redirect():
    """Перенаправлення з кореня на дашборд."""
    return RedirectResponse(url="/staff/dashboard")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Сторінка входу. Якщо є токен - редірект на дашборд."""
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
    """Обробка входу співробітника."""
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    result = await session.execute(
        select(Employee).where(Employee.phone_number.ilike(f"%{clean_phone}%"))
    )
    employee = result.scalars().first()

    # --- ВИПРАВЛЕННЯ: Редірект з параметром помилки ---
    if not employee:
        return RedirectResponse(url="/staff/login?error=1", status_code=303)
    
    if not employee.password_hash:
        if password == "admin": pass 
        else: return RedirectResponse(url="/staff/login?error=1", status_code=303)
    elif not verify_password(password, employee.password_hash):
        return RedirectResponse(url="/staff/login?error=1", status_code=303)

    access_token = create_access_token(data={"sub": str(employee.id)})
    
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
    """Вихід із системи."""
    response = RedirectResponse(url="/staff/login", status_code=303)
    response.delete_cookie("staff_access_token")
    return response

# --- ГОЛОВНА ПАНЕЛЬ (DASHBOARD) ---

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Відображення головної панелі співробітника."""
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

    # --- ГЕНЕРАЦІЯ ВКЛАДОК (TABS) СТРОГО ЗА РОЛЯМИ ---
    tabs_html = ""
    
    # Ролі (прапорці)
    is_admin_operator = employee.role.can_manage_orders
    is_waiter = employee.role.can_serve_tables
    is_courier = employee.role.can_be_assigned
    is_kitchen = employee.role.can_receive_kitchen_orders
    is_bar = employee.role.can_receive_bar_orders

    # 1. ОПЕРАТОР / АДМІН
    if is_admin_operator:
        tabs_html += '<button class="nav-item active" onclick="switchTab(\'orders\')"><i class="fa-solid fa-list-check"></i> Замовлення</button>'
        tabs_html += '<button class="nav-item" onclick="switchTab(\'delivery_admin\')"><i class="fa-solid fa-truck-fast"></i> Доставка (Всі)</button>'
    
    # 2. ОФІЦІАНТ
    if is_waiter:
        if not is_admin_operator:
            tabs_html += '<button class="nav-item active" onclick="switchTab(\'orders\')"><i class="fa-solid fa-list-ul"></i> Мої замовлення</button>'
        tabs_html += '<button class="nav-item" onclick="switchTab(\'tables\')"><i class="fa-solid fa-chair"></i> Столи</button>'
        
    # 3. КУХНЯ / БАР
    if is_kitchen or is_bar:
        active_cls = "active" if not (is_admin_operator or is_waiter) else ""
        tabs_html += f'<button class="nav-item {active_cls}" onclick="switchTab(\'production\')"><i class="fa-solid fa-fire-burner"></i> Черга</button>'
    
    # 4. КУР'ЄР
    if is_courier and not is_admin_operator:
        active_cls = "active" if not (is_waiter or is_kitchen or is_bar) else ""
        tabs_html += f'<button class="nav-item {active_cls}" onclick="switchTab(\'delivery_courier\')"><i class="fa-solid fa-motorcycle"></i> Мої доставки</button>'
    
    # 5. ФІНАНСИ (Каса)
    if is_waiter or is_courier or is_admin_operator:
        tabs_html += '<button class="nav-item" onclick="switchTab(\'finance\')"><i class="fa-solid fa-wallet"></i> Каса</button>'

    # Сповіщення (для всіх)
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

# --- API МЕТОДИ ДЛЯ JS ---

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
    """Основний метод отримання HTML-контенту для вкладок."""
    try:
        if not employee.is_on_shift:
            return JSONResponse({"html": "<div class='empty-state'><i class='fa-solid fa-power-off'></i>🔴 Ви не на зміні. <br>Натисніть кнопку зверху для початку роботи.</div>"})

        # --- Вкладка СТОЛИ ---
        if view == "tables" and employee.role.can_serve_tables:
            return await _render_tables_view(session, employee)

        # --- Вкладка ЗАМОВЛЕННЯ ---
        elif view == "orders":
            if employee.role.can_manage_orders:
                orders_data = await _get_general_orders(session, employee)
                return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-regular fa-folder-open'></i>Активних замовлень немає.</div>"})
            elif employee.role.can_serve_tables:
                orders_html = await _get_waiter_orders_grouped(session, employee)
                return JSONResponse({"html": orders_html if orders_html else "<div class='empty-state'><i class='fa-solid fa-utensils'></i>Ваших активних замовлень немає.</div>"})
            else:
                return JSONResponse({"html": "<div class='empty-state'>Немає доступу до списку замовлень.</div>"})

        # --- Вкладка ФІНАНСИ (Каса) ---
        elif view == "finance":
            if employee.role.can_serve_tables or employee.role.can_be_assigned or employee.role.can_manage_orders:
                finance_html = await _get_finance_details(session, employee)
                return JSONResponse({"html": finance_html})
            else:
                return JSONResponse({"html": "<div class='empty-state'>Доступ заборонено.</div>"})

        # --- Вкладка ВИРОБНИЦТВО (Кухня/Бар) ---
        elif view == "production":
            if employee.role.can_receive_kitchen_orders or employee.role.can_receive_bar_orders:
                orders_data = await _get_production_orders(session, employee)
                return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-solid fa-check-double'></i>Черга пуста.</div>"})
            else:
                return JSONResponse({"html": "<div class='empty-state'>У вас немає прав доступу до кухні/бару.</div>"})

        # --- Вкладка ДОСТАВКА (КУР'ЄР) ---
        elif view == "delivery_courier":
            if employee.role.can_be_assigned:
                orders_data = await _get_my_courier_orders(session, employee)
                return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-solid fa-motorcycle'></i>Немає призначених замовлень.</div>"})
            else:
                return JSONResponse({"html": "<div class='empty-state'>Ви не кур'єр.</div>"})

        # --- Вкладка ДОСТАВКА (АДМІН) ---
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

# --- РЕНДЕРИНГ КОНТЕНТУ ---

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
            # Формування списку страв з модифікаторами
            items_html_list = []
            for item in o.items:
                mods_str = ""
                if item.modifiers:
                    mods_names = [m['name'] for m in item.modifiers]
                    mods_str = f" <small style='color:#666;'>({', '.join(mods_names)})</small>"
                items_html_list.append(f"<li>{html.escape(item.product_name)}{mods_str} x{item.quantity}</li>")
            
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
            
            badge_class = "success" if o.status.name == "Готовий до видачі" else "info"
            color = "#27ae60" if o.status.name == "Готовий до видачі" else "#333"

            status_display = o.status.name
            if o.kitchen_done: status_display += " 🍳"
            if o.bar_done: status_display += " 🍹"

            html_out += STAFF_ORDER_CARD.format(
                id=o.id, 
                time=o.created_at.strftime('%H:%M'), 
                badge_class=badge_class, 
                status=status_display, 
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
    
    # Допоміжна функція для форматування рядка
    def format_prod_item(item):
        mods_html = ""
        if item.modifiers:
            names = [m['name'] for m in item.modifiers]
            mods_html = f"<div style='font-size:0.85em; color:#555; padding-left:10px;'>+ {', '.join(names)}</div>"
        return f"<li><b>{html.escape(item.product_name)}</b> x{item.quantity}{mods_html}</li>"

    # --- КУХНЯ ---
    if employee.role.can_receive_kitchen_orders:
        status_ids = (await session.execute(select(OrderStatus.id).where(OrderStatus.visible_to_chef == True))).scalars().all()
        if status_ids:
            q = select(Order).options(
                joinedload(Order.table), 
                selectinload(Order.items), 
                joinedload(Order.status)
            ).where(
                Order.status_id.in_(status_ids), 
                Order.kitchen_done == False,
                Order.status.has(requires_kitchen_notify=True)
            ).order_by(Order.id.asc())
            
            orders = (await session.execute(q)).scalars().all()
            
            if orders:
                orders_data.append({"html": "<div class='table-group-header'>🍳 КУХНЯ</div>"})
                for o in orders:
                    items = [i for i in o.items if i.preparation_area != 'bar'] 
                    if items:
                        items_html = "".join([format_prod_item(i) for i in items])
                        table_info = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовивіз")
                        content = f"<div class='info-row'><i class='fa-solid fa-utensils'></i> {table_info}</div><ul style='padding-left:20px; margin:5px 0;'>{items_html}</ul>"
                        
                        btns = f"""
                        <div style="display:flex; gap:5px;">
                            <button class='action-btn' onclick=\"performAction('chef_ready', {o.id}, 'kitchen')\" style="flex-grow:1;">✅ Готово</button>
                            <a href='/staff/print_recipe/{o.id}' target='_blank' class='action-btn secondary' style='width:auto;' title='Друк чека'><i class="fa-solid fa-print"></i></a>
                        </div>
                        """
                        
                        orders_data.append({"id": o.id, "html": STAFF_ORDER_CARD.format(
                            id=o.id, 
                            time=o.created_at.strftime('%H:%M'), 
                            badge_class="warning", 
                            status="В роботі", 
                            content=content, 
                            buttons=btns, 
                            color="#f39c12"
                        )})

    # --- БАР ---
    if employee.role.can_receive_bar_orders:
        status_ids = (await session.execute(select(OrderStatus.id).where(OrderStatus.visible_to_bartender == True))).scalars().all()
        if status_ids:
            q = select(Order).options(
                joinedload(Order.table), 
                selectinload(Order.items), 
                joinedload(Order.status)
            ).where(
                Order.status_id.in_(status_ids), 
                Order.bar_done == False,
                Order.status.has(requires_kitchen_notify=True)
            ).order_by(Order.id.asc())
            
            orders = (await session.execute(q)).scalars().all()
            
            if orders:
                orders_data.append({"html": "<div class='table-group-header'>🍹 БАР</div>"})
                for o in orders:
                    items = [i for i in o.items if i.preparation_area == 'bar'] 
                    if items:
                        items_html = "".join([format_prod_item(i) for i in items])
                        table_info = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовивіз")
                        content = f"<div class='info-row'><i class='fa-solid fa-martini-glass'></i> {table_info}</div><ul style='padding-left:20px; margin:5px 0;'>{items_html}</ul>"
                        
                        btns = f"""
                        <div style="display:flex; gap:5px;">
                            <button class='action-btn' onclick=\"performAction('chef_ready', {o.id}, 'bar')\" style="flex-grow:1;">✅ Готово</button>
                            <a href='/staff/print_recipe/{o.id}' target='_blank' class='action-btn secondary' style='width:auto;'><i class="fa-solid fa-print"></i></a>
                        </div>
                        """
                        
                        orders_data.append({"id": o.id, "html": STAFF_ORDER_CARD.format(
                            id=o.id, 
                            time=o.created_at.strftime('%H:%M'), 
                            badge_class="info", 
                            status="В роботі", 
                            content=content, 
                            buttons=btns, 
                            color="#3498db"
                        )})
    return orders_data

async def _get_my_courier_orders(session: AsyncSession, employee: Employee):
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    q = select(Order).options(joinedload(Order.status), selectinload(Order.items)).where(Order.courier_id == employee.id, Order.status_id.not_in(final_ids)).order_by(Order.id.desc())
    orders = (await session.execute(q)).scalars().all()
    res = []
    for o in orders:
        content = f"""
        <div class="info-row"><i class="fa-solid fa-map-pin"></i> {html.escape(o.address or 'Не вказано')}</div>
        <div class="info-row"><i class="fa-solid fa-phone"></i> <a href="tel:{o.phone_number}">{html.escape(o.phone_number or '')}</a></div>
        <div class="info-row"><i class="fa-solid fa-money-bill"></i> <b>{o.total_price} грн</b> ({'Готівка' if o.payment_method=='cash' else 'Картка'})</div>
        <div class="info-row"><i class="fa-solid fa-user"></i> {html.escape(o.customer_name or '')}</div>
        """
        btns = f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">⚙️ Статус / Інфо</button>"
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
        
        # Формуємо список товарів з модифікаторами
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
        # Збираємо модифікатори в читабельну строку
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
            "modifiers": i.modifiers  # --- ВИПРАВЛЕННЯ: Повертаємо масив модифікаторів для редагування ---
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
    order.status_id = new_status_id
    
    if payment_method:
        order.payment_method = payment_method

    # Логика каси та фіксації кур'єра
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
    items = data.get("items") # Очікується список об'єктів, що може містити modifiers
    
    order = await session.get(Order, order_id)
    if not order: return JSONResponse({"error": "Замовлення не знайдено"}, 404)
    
    if not check_edit_permissions(employee, order):
        return JSONResponse({"error": "Немає прав на редагування"}, 403)

    if order.status.is_completed_status or order.status.is_cancelled_status:
        return JSONResponse({"error": "Замовлення закрите"}, 400)
    
    if order.is_inventory_deducted:
        return JSONResponse({"error": "Склад вже списано. Редагування заборонено."}, 403)
    
    await session.execute(delete(OrderItem).where(OrderItem.order_id == order_id))
    
    total_price = Decimal(0)
    if items:
        prod_ids = [int(i['id']) for i in items]
        products = (await session.execute(select(Product).where(Product.id.in_(prod_ids)))).scalars().all()
        prod_map = {p.id: p for p in products}
        
        for item in items:
            pid = int(item['id'])
            qty = int(item['qty'])
            if pid in prod_map and qty > 0:
                p = prod_map[pid]
                
                modifiers_data = item.get('modifiers', [])
                item_price = p.price
                for mod in modifiers_data:
                    price_val = mod.get('price', 0)
                    if price_val is None: price_val = 0
                    item_price += Decimal(str(price_val))
                
                total_price += item_price * qty
                
                session.add(OrderItem(
                    order_id=order_id,
                    product_id=p.id,
                    product_name=p.name,
                    quantity=qty,
                    price_at_moment=item_price,
                    preparation_area=p.preparation_area,
                    modifiers=modifiers_data
                ))
    
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
        extra = data.get("extra")

        order = await session.get(Order, order_id, options=[joinedload(Order.status), joinedload(Order.table)])
        if not order: return JSONResponse({"error": "Не знайдено"}, status_code=404)

        if action == "chef_ready":
            if extra == 'kitchen' and not employee.role.can_receive_kitchen_orders: return JSONResponse({"error": "Forbidden"}, 403)
            if extra == 'bar' and not employee.role.can_receive_bar_orders: return JSONResponse({"error": "Forbidden"}, 403)

            if extra == 'kitchen': order.kitchen_done = True
            elif extra == 'bar': order.bar_done = True
            await notify_station_completion(request.app.state.admin_bot, order, extra, session)
            await session.commit()
            return JSONResponse({"success": True})

        elif action == "accept_order":
            if not employee.role.can_serve_tables: return JSONResponse({"error": "Forbidden"}, 403)
            if order.accepted_by_waiter_id: return JSONResponse({"error": "Вже зайнято"}, status_code=400)
            
            order.accepted_by_waiter_id = employee.id
            proc_status = await session.scalar(select(OrderStatus).where(OrderStatus.name == "В обробці").limit(1))
            if proc_status:
                order.status_id = proc_status.id
                session.add(OrderStatusHistory(order_id=order.id, status_id=proc_status.id, actor_info=employee.full_name))
            await session.commit()
            return JSONResponse({"success": True})

        return JSONResponse({"success": False, "error": "Unknown action"})
    except Exception as e:
        logger.error(f"Action Error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/menu/full")
async def get_full_menu(session: AsyncSession = Depends(get_db_session)):
    """
    Повертає повне меню ресторану для PWA.
    Завантажує продукти разом з модифікаторами.
    """
    cats = (await session.execute(select(Category).where(Category.show_in_restaurant==True).order_by(Category.sort_order))).scalars().all()
    
    menu = []
    for c in cats:
        # Завантажуємо продукти разом з прив'язаними модифікаторами
        prods = (await session.execute(
            select(Product)
            .where(Product.category_id==c.id, Product.is_active==True)
            .options(selectinload(Product.modifiers))
        )).scalars().all()
        
        prod_list = []
        for p in prods:
            # Формуємо список модифікаторів для продукту
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
        cart = data.get("cart") # Очікуємо список об'єктів: [{id, qty, modifiers: [...]}, ...]
        
        table = await session.get(Table, table_id)
        if not table or not cart: return JSONResponse({"error": "Invalid data"}, status_code=400)
        
        total = Decimal(0)
        items_obj = []
        
        prod_ids = [int(item['id']) for item in cart]
        products_res = await session.execute(select(Product).where(Product.id.in_(prod_ids)))
        products_map = {p.id: p for p in products_res.scalars().all()}
        
        for item in cart:
            pid = int(item['id'])
            qty = int(item['qty'])
            
            if pid in products_map and qty > 0:
                prod = products_map[pid]
                
                modifiers_data = item.get('modifiers', [])
                modifiers_price = Decimal(0)
                if modifiers_data:
                    for m in modifiers_data:
                        price_val = m.get('price', 0)
                        if price_val is None: price_val = 0
                        modifiers_price += Decimal(str(price_val))
                
                item_price = prod.price + modifiers_price
                total += item_price * qty
                
                items_obj.append(OrderItem(
                    product_id=prod.id, 
                    product_name=prod.name, 
                    quantity=qty, 
                    price_at_moment=item_price, 
                    preparation_area=prod.preparation_area,
                    modifiers=modifiers_data
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
        await session.flush() # Отримуємо ID замовлення

        # Створюємо OrderItems
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
    """Генерація HTML чека/бігунка для повара"""
    from inventory_service import generate_cook_ticket 
    
    try:
        html_content = await generate_cook_ticket(session, order_id)
        return HTMLResponse(html_content)
    except Exception as e:
        logger.error(f"Error generating receipt: {e}")
        return HTMLResponse(f"Ошибка печати: {e}", status_code=500)
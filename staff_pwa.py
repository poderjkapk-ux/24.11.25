# staff_pwa.py

import html
import logging
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import joinedload, selectinload

# Импорт моделей и зависимостей
from models import (
    Employee, Settings, Order, OrderStatus, Role, OrderItem, Table, 
    Category, Product, OrderStatusHistory, StaffNotification
)
from dependencies import get_db_session
from auth_utils import verify_password, create_access_token, get_current_staff

# Импорт шаблонов
from staff_templates import (
    STAFF_LOGIN_HTML, STAFF_DASHBOARD_HTML, 
    STAFF_TABLE_CARD, STAFF_ORDER_CARD
)

# Импорт менеджеров уведомлений и кассы
from notification_manager import (
    notify_all_parties_on_status_change, 
    notify_new_order_to_staff, 
    notify_station_completion,
    create_staff_notification
)
from cash_service import link_order_to_shift, register_employee_debt

# Настройка роутера и логгера
router = APIRouter(prefix="/staff", tags=["staff_pwa"])
logger = logging.getLogger(__name__)

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
        return HTMLResponse("Користувача не знайдено", status_code=400)
    
    if not employee.password_hash:
        if password == "admin": pass 
        else: return HTMLResponse("Пароль ще не встановлено.", status_code=400)
    elif not verify_password(password, employee.password_hash):
        return HTMLResponse("Невірний пароль", status_code=400)

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

    # Генерация вкладок навигации (Накопительная логика для мульти-ролей)
    tabs_html = ""
    
    # 1. Оператор/Админ (Видит всё + может назначать)
    if employee.role.can_manage_orders:
        tabs_html += '<button class="nav-item active" onclick="switchTab(\'orders\')"><i class="fa-solid fa-list-check"></i> Замовлення</button>'
    
    # 2. Официант
    if employee.role.can_serve_tables:
        # Если уже добавили кнопку "Замовлення" для админа, не дублируем, но добавляем столы
        if 'switchTab(\'orders\')' not in tabs_html:
             tabs_html += '<button class="nav-item" onclick="switchTab(\'orders\')"><i class="fa-solid fa-list-ul"></i> Замовлення</button>'
        tabs_html += '<button class="nav-item" onclick="switchTab(\'tables\')"><i class="fa-solid fa-chair"></i> Столи</button>'
        
    # 3. Кухня/Бар
    if employee.role.can_receive_kitchen_orders or employee.role.can_receive_bar_orders:
        tabs_html += '<button class="nav-item" onclick="switchTab(\'production\')"><i class="fa-solid fa-fire-burner"></i> Черга</button>'
    
    # 4. Курьер
    if employee.role.can_be_assigned:
        tabs_html += '<button class="nav-item" onclick="switchTab(\'delivery\')"><i class="fa-solid fa-motorcycle"></i> Доставка</button>'
    
    # 5. Финансы (для всех, кто работает с деньгами)
    if employee.role.can_serve_tables or employee.role.can_be_assigned or employee.role.can_manage_orders:
        tabs_html += '<button class="nav-item" onclick="switchTab(\'finance\')"><i class="fa-solid fa-wallet"></i> Каса</button>'

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

        # --- Вкладка ЗАКАЗЫ (С разделением логики для Официанта и Админа) ---
        elif view == "orders":
            if employee.role.can_serve_tables:
                # Официант видит свои столы и заказы с группировкой
                orders_html = await _get_waiter_orders_grouped(session, employee)
                return JSONResponse({"html": orders_html if orders_html else "<div class='empty-state'><i class='fa-solid fa-utensils'></i>Активних замовлень немає.</div>"})
            else:
                # Админ/Оператор видит общий список
                orders_data = await _get_general_orders(session, employee)
                return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-regular fa-folder-open'></i>Активних замовлень немає.</div>"})

        # --- Вкладка ФИНАНСЫ (Официант/Курьер/Админ) ---
        elif view == "finance" and (employee.role.can_serve_tables or employee.role.can_be_assigned or employee.role.can_manage_orders):
            finance_html = await _get_finance_details(session, employee)
            return JSONResponse({"html": finance_html})

        # --- Вкладка ПРОИЗВОДСТВО ---
        elif view == "production":
            orders_data = await _get_production_orders(session, employee)
            return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-solid fa-check-double'></i>Черга пуста.</div>"})

        # --- Вкладка ДОСТАВКА ---
        elif view == "delivery" and employee.role.can_be_assigned:
            orders_data = await _get_courier_orders(session, employee)
            return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'><i class='fa-solid fa-motorcycle'></i>Немає призначених замовлень.</div>"})
        
        elif view == "notifications":
            return JSONResponse({"html": "<div id='notification-list-container' style='text-align:center; color:#999;'>Оновлення...</div>"})

        return JSONResponse({"html": "<div class='empty-state'>Невідомий режим перегляду.</div>"})
        
    except Exception as e:
        logger.error(f"API Error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def _get_waiter_orders_grouped(session: AsyncSession, employee: Employee):
    """Группировка заказов по столикам для официанта с подсчетом общей суммы."""
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    
    tables_sub = select(Table.id).where(Table.assigned_waiters.any(Employee.id == employee.id))
    
    q = select(Order).options(
        joinedload(Order.status), joinedload(Order.table), joinedload(Order.accepted_by_waiter)
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
            t_name = o.table.name if o.table else "Інше / Самовивіз"
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
            content = f"""
            <div class="info-row"><i class="fa-solid fa-clock"></i> {o.created_at.strftime('%H:%M')}</div>
            <div class="info-row"><i class="fa-solid fa-money-bill-wave"></i> <b>{o.total_price} грн</b></div>
            """
            
            btns = ""
            if not o.accepted_by_waiter_id: 
                btns += f"<button class='action-btn' onclick=\"performAction('accept_order', {o.id})\">🙋 Прийняти</button>"
            else: 
                btns += f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">✏️ Деталі / Оплата</button>"
            
            badge_class = "success" if o.status.name == "Готовий до видачі" else "info"
            color = "#27ae60" if o.status.name == "Готовий до видачі" else "#333"

            html_out += STAFF_ORDER_CARD.format(
                id=o.id, 
                time=o.created_at.strftime('%H:%M'), 
                badge_class=badge_class, 
                status=o.status.name, 
                content=content, 
                buttons=btns, 
                color=color
            )
        
    return html_out

async def _get_finance_details(session: AsyncSession, employee: Employee):
    """Детализация долга сотрудника."""
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
    # Кухня
    if employee.role.can_receive_kitchen_orders:
        status_ids = (await session.execute(select(OrderStatus.id).where(OrderStatus.visible_to_chef == True))).scalars().all()
        if status_ids:
            q = select(Order).options(joinedload(Order.table), selectinload(Order.items)).where(Order.status_id.in_(status_ids), Order.kitchen_done == False).order_by(Order.id.asc())
            orders = (await session.execute(q)).scalars().all()
            for o in orders:
                items = [i for i in o.items if i.preparation_area != 'bar'] 
                if items:
                    items_html = "".join([f"<li><b>{html.escape(i.product_name)}</b> x{i.quantity}</li>" for i in items])
                    table_info = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовивіз")
                    content = f"<div class='info-row'><i class='fa-solid fa-utensils'></i> {table_info}</div><ul style='padding-left:20px; margin:5px 0;'>{items_html}</ul>"
                    btn = f"<button class='action-btn' onclick=\"performAction('chef_ready', {o.id}, 'kitchen')\">✅ Кухня готова</button>"
                    orders_data.append({"id": o.id, "html": STAFF_ORDER_CARD.format(
                        id=o.id, 
                        time=o.created_at.strftime('%H:%M'), 
                        badge_class="warning", 
                        status="В роботі", 
                        content=content, 
                        buttons=btn, 
                        color="#f39c12"
                    )})

    # Бар
    if employee.role.can_receive_bar_orders:
        status_ids = (await session.execute(select(OrderStatus.id).where(OrderStatus.visible_to_bartender == True))).scalars().all()
        if status_ids:
            q = select(Order).options(joinedload(Order.table), selectinload(Order.items)).where(Order.status_id.in_(status_ids), Order.bar_done == False).order_by(Order.id.asc())
            orders = (await session.execute(q)).scalars().all()
            for o in orders:
                items = [i for i in o.items if i.preparation_area == 'bar'] 
                if items:
                    items_html = "".join([f"<li><b>{html.escape(i.product_name)}</b> x{i.quantity}</li>" for i in items])
                    table_info = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовивіз")
                    content = f"<div class='info-row'><i class='fa-solid fa-martini-glass'></i> {table_info}</div><ul style='padding-left:20px; margin:5px 0;'>{items_html}</ul>"
                    btn = f"<button class='action-btn' onclick=\"performAction('chef_ready', {o.id}, 'bar')\">✅ Бар готовий</button>"
                    orders_data.append({"id": o.id, "html": STAFF_ORDER_CARD.format(
                        id=o.id, 
                        time=o.created_at.strftime('%H:%M'), 
                        badge_class="info", 
                        status="В роботі", 
                        content=content, 
                        buttons=btn, 
                        color="#3498db"
                    )})
    return orders_data

async def _get_courier_orders(session: AsyncSession, employee: Employee):
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

async def _get_general_orders(session: AsyncSession, employee: Employee):
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    q = select(Order).options(joinedload(Order.status), joinedload(Order.table), joinedload(Order.accepted_by_waiter), joinedload(Order.courier)).where(Order.status_id.not_in(final_ids)).order_by(Order.id.desc())

    orders = (await session.execute(q)).scalars().all()
    res = []
    for o in orders:
        table_name = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовивіз")
        courier_info = f"🚴 {o.courier.full_name}" if o.courier else "🔴 Не призначено"
        
        content = f"""
        <div class="info-row"><i class="fa-solid fa-info-circle"></i> <b>{html.escape(table_name)}</b></div>
        <div class="info-row"><i class="fa-solid fa-money-bill-wave"></i> {o.total_price} грн</div>
        """
        
        if o.is_delivery:
             content += f"<div class='info-row' style='font-size:0.85rem; color:#555;'>{courier_info}</div>"

        btns = ""
        # Если админ/оператор - кнопка управления
        if employee.role.can_manage_orders:
             btns += f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">⚙️ Керувати</button>"
        else:
             btns = f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">Інфо</button>"
        
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
    """Возвращает детали заказа для модального окна, включая список курьеров."""
    order = await session.get(Order, order_id, options=[selectinload(Order.items), joinedload(Order.status), joinedload(Order.courier)])
    if not order: return JSONResponse({"error": "Not found"}, status_code=404)
    
    status_query = select(OrderStatus)
    if employee.role.can_manage_orders:
        status_query = status_query.where(OrderStatus.visible_to_operator == True)
    elif employee.role.can_be_assigned:
        status_query = status_query.where(OrderStatus.visible_to_courier == True)
    elif employee.role.can_serve_tables:
        status_query = status_query.where(OrderStatus.visible_to_waiter == True)
    
    statuses = (await session.execute(status_query.order_by(OrderStatus.id))).scalars().all()
    status_list = [{"id": s.id, "name": s.name, "selected": s.id == order.status_id, "is_completed": s.is_completed_status} for s in statuses]

    items = [{"id": i.product_id, "name": i.product_name, "qty": i.quantity, "price": float(i.price_at_moment)} for i in order.items]
    
    # --- СПИСОК КУРЬЕРОВ (Для операторов) ---
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
        "can_assign_courier": employee.role.can_manage_orders
    })

@router.post("/api/order/assign_courier")
async def assign_courier_api(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
    """Назначение курьера через PWA."""
    if not employee.role.can_manage_orders:
        return JSONResponse({"error": "No permission"}, status_code=403)
        
    data = await request.json()
    order_id = int(data.get("orderId"))
    courier_id = int(data.get("courierId")) # 0 если снять
    
    order = await session.get(Order, order_id)
    if not order: return JSONResponse({"error": "Order not found"}, 404)
    
    if order.status.is_completed_status:
        return JSONResponse({"error": "Order closed"}, 400)

    msg = ""
    if courier_id == 0:
        order.courier_id = None
        msg = "Кур'єра знято"
    else:
        courier = await session.get(Employee, courier_id)
        if not courier: return JSONResponse({"error": "Courier not found"}, 404)
        order.courier_id = courier_id
        msg = f"Призначено: {courier.full_name}"
        
        # --- УВЕДОМЛЕНИЕ КУРЬЕРУ ---
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
    if not order: return JSONResponse({"error": "Not found"}, 404)
    
    old_status = order.status.name
    new_status = await session.get(OrderStatus, new_status_id)
    order.status_id = new_status_id
    
    if payment_method:
        order.payment_method = payment_method

    if new_status.is_completed_status:
        await link_order_to_shift(session, order, employee.id)
        if order.payment_method == 'cash':
            await register_employee_debt(session, order, employee.id)

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
    from sqlalchemy import delete
    data = await request.json()
    order_id = int(data.get("orderId"))
    items = data.get("items")
    
    order = await session.get(Order, order_id)
    if not order: return JSONResponse({"error": "Not found"}, 404)
    if order.status.is_completed_status: return JSONResponse({"error": "Order closed"}, 400)
    
    await session.execute(delete(OrderItem).where(OrderItem.order_id == order_id))
    
    total_price = Decimal(0)
    prod_ids = [int(i['id']) for i in items]
    products = (await session.execute(select(Product).where(Product.id.in_(prod_ids)))).scalars().all()
    prod_map = {p.id: p for p in products}
    
    for item in items:
        pid = int(item['id'])
        qty = int(item['qty'])
        if pid in prod_map and qty > 0:
            p = prod_map[pid]
            total_price += p.price * qty
            session.add(OrderItem(
                order_id=order_id,
                product_id=p.id,
                product_name=p.name,
                quantity=qty,
                price_at_moment=p.price,
                preparation_area=p.preparation_area
            ))
            
    order.total_price = total_price
    await session.commit()
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
        if not order: return JSONResponse({"error": "Not found"}, status_code=404)

        if action == "chef_ready":
            if extra == 'kitchen': order.kitchen_done = True
            elif extra == 'bar': order.bar_done = True
            await notify_station_completion(request.app.state.admin_bot, order, extra, session)
            await session.commit()
            return JSONResponse({"success": True})

        elif action == "accept_order":
            if order.accepted_by_waiter_id: return JSONResponse({"error": "Уже занято"}, status_code=400)
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
    cats = (await session.execute(select(Category).where(Category.show_in_restaurant==True).order_by(Category.sort_order))).scalars().all()
    menu = []
    for c in cats:
        prods = (await session.execute(select(Product).where(Product.category_id==c.id, Product.is_active==True))).scalars().all()
        menu.append({
            "id": c.id, 
            "name": c.name, 
            "products": [{"id": p.id, "name": p.name, "price": float(p.price)} for p in prods]
        })
    return JSONResponse(menu)

@router.post("/api/order/create")
async def create_waiter_order(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
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
        
        for item in cart:
            pid = int(item['id'])
            qty = int(item['qty'])
            if pid in products_map and qty > 0:
                prod = products_map[pid]
                total += prod.price * qty
                items_obj.append(OrderItem(
                    product_id=prod.id, 
                    product_name=prod.name, 
                    quantity=qty, 
                    price_at_moment=prod.price, 
                    preparation_area=prod.preparation_area
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
        
        session.add(OrderStatusHistory(order_id=order.id, status_id=status_id, actor_info=f"{employee.full_name} (PWA)"))
        await session.commit()
        
        await notify_new_order_to_staff(request.app.state.admin_bot, order, session)
        return JSONResponse({"success": True, "orderId": order.id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
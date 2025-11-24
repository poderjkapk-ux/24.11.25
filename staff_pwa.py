# staff_pwa.py

import html
import json
import logging
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response, status, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, and_, delete
from sqlalchemy.orm import joinedload, selectinload

from models import Employee, Settings, Order, OrderStatus, Role, OrderItem, Table, Category, Product, OrderStatusHistory, StaffNotification
from dependencies import get_db_session
from auth_utils import verify_password, create_access_token, get_current_staff
from templates import STAFF_LOGIN_HTML, STAFF_DASHBOARD_HTML
from notification_manager import notify_all_parties_on_status_change, notify_new_order_to_staff, notify_station_completion
from cash_service import link_order_to_shift, register_employee_debt

router = APIRouter(prefix="/staff", tags=["staff_pwa"])
logger = logging.getLogger(__name__)

# --- АВТОРИЗАЦИЯ ---

@router.get("/", include_in_schema=False)
async def staff_root_redirect():
    return RedirectResponse(url="/staff/dashboard")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
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
    clean_phone = ''.join(filter(str.isdigit, phone))
    result = await session.execute(select(Employee).where(Employee.phone_number.ilike(f"%{clean_phone}%")))
    employee = result.scalars().first()

    if not employee:
        return HTMLResponse("Пользователь не найден", status_code=400)
    
    # Проверка пароля (или временный вход admin)
    if not employee.password_hash:
        if password == "admin": 
             pass 
        else:
             return HTMLResponse("Пароль еще не установлен.", status_code=400)
    elif not verify_password(password, employee.password_hash):
        return HTMLResponse("Неверный пароль", status_code=400)

    access_token = create_access_token(data={"sub": str(employee.id)})
    
    response = RedirectResponse(url="/staff/dashboard", status_code=303)
    response.set_cookie(key="staff_access_token", value=access_token, httponly=True, max_age=60*60*12, samesite="lax")
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/staff/login", status_code=303)
    response.delete_cookie("staff_access_token")
    return response

# --- DASHBOARD ---

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_db_session)):
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
    shift_btn_text = "🟢 На смене" if employee.is_on_shift else "🔴 Начать смену"

    # Генерация вкладок на основе прав доступа
    tabs_html = ""
    
    # Официант
    if employee.role.can_serve_tables:
        tabs_html += '<button class="nav-item active" onclick="switchTab(\'tables\')"><i class="fa-solid fa-chair"></i> Столы</button>'
        tabs_html += '<button class="nav-item" onclick="switchTab(\'orders\')"><i class="fa-solid fa-list-ul"></i> Заказы</button>'
    
    # Повар или Бармен
    elif employee.role.can_receive_kitchen_orders or employee.role.can_receive_bar_orders:
        tabs_html += '<button class="nav-item active" onclick="switchTab(\'production\')"><i class="fa-solid fa-fire-burner"></i> Очередь</button>'
    
    # Курьер
    elif employee.role.can_be_assigned:
        tabs_html += '<button class="nav-item active" onclick="switchTab(\'delivery\')"><i class="fa-solid fa-motorcycle"></i> Доставка</button>'
    
    # Админ/Оператор
    else:
        tabs_html += '<button class="nav-item active" onclick="switchTab(\'orders\')"><i class="fa-solid fa-list-check"></i> Все заказы</button>'

    # Вкладка уведомлений (для всех)
    tabs_html += '<button class="nav-item" onclick="switchTab(\'notifications\')" style="position:relative;"><i class="fa-solid fa-bell"></i> Инфо<span id="nav-notify-badge" class="notify-dot" style="display:none;"></span></button>'

    content = f"""
    <div class="dashboard-header">
        <div class="user-info">
            <h3>{html.escape(employee.full_name)}</h3>
            <span class="role-badge">{html.escape(employee.role.name)}</span>
        </div>
        <button onclick="toggleShift()" id="shift-btn" class="shift-btn {shift_btn_class}">{shift_btn_text}</button>
    </div>
    
    <div id="error-message" style="display:none; background:#ffebee; color:#c62828; padding:10px; margin:10px; border-radius:5px; text-align:center;"></div>

    <div id="main-view">
        <div id="loading-indicator"><i class="fa-solid fa-spinner fa-spin"></i></div>
        <div id="content-area"></div>
    </div>

    <div class="bottom-nav" id="bottom-nav">
        {tabs_html}
        <button class="nav-item" onclick="window.location.href='/staff/logout'"><i class="fa-solid fa-right-from-bracket"></i> Выход</button>
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
        "short_name": "StaffApp",
        "start_url": "/staff/dashboard",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": settings.primary_color or "#333333",
        "icons": [
            {"src": "/static/favicons/favicon-32x32.png", "sizes": "32x32", "type": "image/png"},
            {"src": "/static/favicons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/favicons/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    })

# --- API ДЕЙСТВИЙ ---

@router.post("/api/shift/toggle")
async def toggle_shift_api(session: AsyncSession = Depends(get_db_session), employee: Employee = Depends(get_current_staff)):
    employee.is_on_shift = not employee.is_on_shift
    await session.commit()
    return JSONResponse({"status": "ok", "is_on_shift": employee.is_on_shift})

@router.get("/api/notifications")
async def get_notifications_api(session: AsyncSession = Depends(get_db_session), employee: Employee = Depends(get_current_staff)):
    """Получение уведомлений для бейджика и списка."""
    notifs = (await session.execute(
        select(StaffNotification).where(StaffNotification.employee_id == employee.id).order_by(StaffNotification.created_at.desc()).limit(20)
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
        # Отмечаем как прочитанные при запросе списка
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
    try:
        if not employee.is_on_shift:
            return JSONResponse({"html": "<div class='empty-state'>🔴 Вы не на смене. Нажмите кнопку сверху для начала работы.</div>"})

        if view == "tables" and employee.role.can_serve_tables:
            tables = (await session.execute(select(Table).where(Table.assigned_waiters.any(Employee.id == employee.id)).order_by(Table.name))).scalars().all()
            if not tables: return JSONResponse({"html": "<div class='empty-state'>За вами не закреплено столиков.</div>"})
            
            html_content = "<div class='grid-container'>"
            for t in tables:
                final_ids = select(OrderStatus.id).where(or_(OrderStatus.is_completed_status==True, OrderStatus.is_cancelled_status==True))
                active_count = await session.scalar(select(func.count(Order.id)).where(Order.table_id == t.id, Order.status_id.not_in(final_ids)))
                status_class = "alert" if active_count > 0 else "success"
                status_text = f"{active_count} активных" if active_count > 0 else "Свободен"
                html_content += f"""<div class="card table-card" onclick="openTableModal({t.id}, '{html.escape(t.name)}')"><div class="card-title"><i class="fa-solid fa-chair"></i> {html.escape(t.name)}</div><div class="badge {status_class}">{status_text}</div></div>"""
            html_content += "</div>"
            return JSONResponse({"html": html_content})

        elif view == "production":
            orders_data = await _get_production_orders(session, employee)
            return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'>Заказов в очереди нет.</div>"})

        elif view == "delivery" and employee.role.can_be_assigned:
            orders_data = await _get_courier_orders(session, employee)
            return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'>Нет назначенных заказов.</div>"})

        elif view == "orders":
            orders_data = await _get_general_orders(session, employee)
            return JSONResponse({"html": "".join([o["html"] for o in orders_data]) if orders_data else "<div class='empty-state'>Активных заказов нет.</div>"})
        
        elif view == "notifications":
            return JSONResponse({"html": "<div id='notification-list-container'>Загрузка уведомлений...</div>"})

        return JSONResponse({"html": "<div class='empty-state'>Неизвестный режим просмотра.</div>"})
        
    except Exception as e:
        logger.error(f"API Error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КАРТОЧЕК ---

def _build_card(order, content, buttons_html, status_label=None):
    status_html = f"<span class='badge'>{status_label}</span>" if status_label else ""
    return f"""
    <div class="order-card" id="order-{order.id}">
        <div class="card-header">
            <div><b>#{order.id}</b> <span class="time">{order.created_at.strftime('%H:%M')}</span></div>
            {status_html}
        </div>
        <div class="card-body" onclick="openOrderEditModal({order.id})">{content}</div>
        <div class="card-footer">{buttons_html}</div>
    </div>
    """

async def _get_production_orders(session: AsyncSession, employee: Employee):
    orders_data = []
    if employee.role.can_receive_kitchen_orders:
        status_ids = (await session.execute(select(OrderStatus.id).where(OrderStatus.visible_to_chef == True))).scalars().all()
        if status_ids:
            q = select(Order).options(joinedload(Order.table), selectinload(Order.items)).where(Order.status_id.in_(status_ids), Order.kitchen_done == False).order_by(Order.id.asc())
            orders = (await session.execute(q)).scalars().all()
            for o in orders:
                items = [i for i in o.items if i.preparation_area != 'bar'] 
                if items:
                    items_html = "".join([f"<li><b>{html.escape(i.product_name)}</b> x{i.quantity}</li>" for i in items])
                    table_info = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовывоз")
                    content = f"<div class='info-row'><i class='fa-solid fa-utensils'></i> {table_info}</div><ul>{items_html}</ul>"
                    btn = f"<button class='action-btn' onclick=\"performAction('chef_ready', {o.id}, 'kitchen')\">✅ Кухня готова</button>"
                    orders_data.append({"id": o.id, "html": _build_card(o, content, btn, "В работе")})

    if employee.role.can_receive_bar_orders:
        status_ids = (await session.execute(select(OrderStatus.id).where(OrderStatus.visible_to_bartender == True))).scalars().all()
        if status_ids:
            q = select(Order).options(joinedload(Order.table), selectinload(Order.items)).where(Order.status_id.in_(status_ids), Order.bar_done == False).order_by(Order.id.asc())
            orders = (await session.execute(q)).scalars().all()
            for o in orders:
                items = [i for i in o.items if i.preparation_area == 'bar'] 
                if items:
                    items_html = "".join([f"<li><b>{html.escape(i.product_name)}</b> x{i.quantity}</li>" for i in items])
                    table_info = o.table.name if o.table else ("Доставка" if o.is_delivery else "Самовывоз")
                    content = f"<div class='info-row'><i class='fa-solid fa-martini-glass'></i> {table_info}</div><ul>{items_html}</ul>"
                    btn = f"<button class='action-btn' onclick=\"performAction('chef_ready', {o.id}, 'bar')\">✅ Бар готов</button>"
                    orders_data.append({"id": o.id, "html": _build_card(o, content, btn, "В работе")})
    return orders_data

async def _get_courier_orders(session: AsyncSession, employee: Employee):
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    q = select(Order).options(joinedload(Order.status), selectinload(Order.items)).where(Order.courier_id == employee.id, Order.status_id.not_in(final_ids)).order_by(Order.id.desc())
    orders = (await session.execute(q)).scalars().all()
    res = []
    for o in orders:
        content = f"""
        <div class="info-row"><i class="fa-solid fa-map-pin"></i> {html.escape(o.address or 'Не указан')}</div>
        <div class="info-row"><i class="fa-solid fa-phone"></i> <a href="tel:{o.phone_number}">{html.escape(o.phone_number or '')}</a></div>
        <div class="info-row"><i class="fa-solid fa-money-bill"></i> <b>{o.total_price} грн</b> ({o.payment_method})</div>
        <div class="info-row"><small>{html.escape(o.customer_name or '')}</small></div>
        """
        btns = f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">⚙️ Статус/Детали</button>"
        res.append({"id": o.id, "html": _build_card(o, content, btns, o.status.name)})
    return res

async def _get_general_orders(session: AsyncSession, employee: Employee):
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    q = select(Order).options(joinedload(Order.status), joinedload(Order.table), joinedload(Order.accepted_by_waiter)).where(Order.status_id.not_in(final_ids)).order_by(Order.id.desc())

    if employee.role.can_serve_tables:
        tables_sub = select(Table.id).where(Table.assigned_waiters.any(Employee.id == employee.id))
        q = q.where(or_(Order.accepted_by_waiter_id == employee.id, Order.table_id.in_(tables_sub)))
    
    orders = (await session.execute(q)).scalars().all()
    res = []
    for o in orders:
        table_name = o.table.name if o.table else "N/A"
        content = f"""<div class="info-row"><i class="fa-solid fa-chair"></i> <b>{html.escape(table_name)}</b></div><div class="info-row">Сумма: <b>{o.total_price} грн</b></div>"""
        btns = ""
        if employee.role.can_serve_tables:
            if not o.accepted_by_waiter_id: btns += f"<button class='action-btn' onclick=\"performAction('accept_order', {o.id})\">🙋 Принять</button>"
            else: btns += f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">✏️ Ред. / Оплата</button>"
        else:
            btns = f"<button class='action-btn secondary' onclick=\"openOrderEditModal({o.id})\">Инфо</button>"
        res.append({"id": o.id, "html": _build_card(o, content, btns, o.status.name)})
    return res

# --- API ДЕТАЛИ ЗАКАЗА И РЕДАКТИРОВАНИЕ ---

@router.get("/api/order/{order_id}/details")
async def get_order_details(order_id: int, session: AsyncSession = Depends(get_db_session), employee: Employee = Depends(get_current_staff)):
    order = await session.get(Order, order_id, options=[selectinload(Order.items), joinedload(Order.status)])
    if not order: return JSONResponse({"error": "Not found"}, status_code=404)
    
    status_query = select(OrderStatus)
    if employee.role.can_manage_orders:
        status_query = status_query.where(OrderStatus.visible_to_operator == True)
    elif employee.role.can_be_assigned:
        status_query = status_query.where(OrderStatus.visible_to_courier == True)
    elif employee.role.can_serve_tables:
        status_query = status_query.where(OrderStatus.visible_to_waiter == True)
    
    statuses = (await session.execute(status_query.order_by(OrderStatus.id))).scalars().all()
    
    # ВАЖНО: Передаем флаг is_completed для фронтенда
    status_list = [{
        "id": s.id, 
        "name": s.name, 
        "selected": s.id == order.status_id,
        "is_completed": s.is_completed_status
    } for s in statuses]

    items = [{"id": i.product_id, "name": i.product_name, "qty": i.quantity, "price": float(i.price_at_moment)} for i in order.items]
    
    return JSONResponse({
        "id": order.id,
        "total": float(order.total_price),
        "items": items,
        "statuses": status_list,
        "status_id": order.status_id
    })

@router.post("/api/order/update_status")
async def update_order_status_api(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    employee: Employee = Depends(get_current_staff)
):
    data = await request.json()
    order_id = int(data.get("orderId"))
    new_status_id = int(data.get("statusId"))
    payment_method = data.get("paymentMethod") # Получаем метод оплаты
    
    order = await session.get(Order, order_id, options=[joinedload(Order.status)])
    if not order: return JSONResponse({"error": "Not found"}, 404)
    
    old_status = order.status.name
    new_status = await session.get(OrderStatus, new_status_id)
    order.status_id = new_status_id
    
    if payment_method:
        order.payment_method = payment_method

    # Логика закрытия (касса)
    if new_status.is_completed_status:
        await link_order_to_shift(session, order, employee.id)
        if order.payment_method == 'cash':
            await register_employee_debt(session, order, employee.id)

    session.add(OrderStatusHistory(order_id=order.id, status_id=new_status_id, actor_info=f"{employee.full_name} (PWA)"))
    await session.commit()
    
    await notify_all_parties_on_status_change(order, old_status, f"{employee.full_name} (PWA)", request.app.state.admin_bot, request.app.state.client_bot, session)
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

# --- API ACTION HANDLER (Для совместимости) ---
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

        elif action == "pay_order":
            payment_method = extra
            final_status = await session.scalar(select(OrderStatus).where(OrderStatus.is_completed_status == True).limit(1))
            if not final_status: return JSONResponse({"error": "Config error"}, 500)
            order.status_id = final_status.id
            order.payment_method = payment_method
            await link_order_to_shift(session, order, employee.id)
            if payment_method == 'cash': await register_employee_debt(session, order, employee.id)
            session.add(OrderStatusHistory(order_id=order.id, status_id=final_status.id, actor_info=f"{employee.full_name} (Оплата)"))
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
                items_obj.append(OrderItem(product_id=prod.id, product_name=prod.name, quantity=qty, price_at_moment=prod.price, preparation_area=prod.preparation_area))
        
        new_status = await session.scalar(select(OrderStatus).where(OrderStatus.name == "Новий").limit(1))
        status_id = new_status.id if new_status else 1
        
        order = Order(
            table_id=table_id, customer_name=f"Стіл: {table.name}", phone_number=f"table_{table_id}",
            total_price=total, order_type="in_house", is_delivery=False, delivery_time="In House",
            accepted_by_waiter_id=employee.id, status_id=status_id, items=items_obj
        )
        session.add(order)
        await session.flush()
        session.add(OrderStatusHistory(order_id=order.id, status_id=status_id, actor_info=f"{employee.full_name} (PWA)"))
        await session.commit()
        await notify_new_order_to_staff(request.app.state.admin_bot, order, session)
        return JSONResponse({"success": True, "orderId": order.id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/table/{table_id}/orders")
async def get_table_orders_api(table_id: int, session: AsyncSession = Depends(get_db_session)):
    final_ids = (await session.execute(select(OrderStatus.id).where(or_(OrderStatus.is_completed_status == True, OrderStatus.is_cancelled_status == True)))).scalars().all()
    orders = (await session.execute(select(Order).options(joinedload(Order.status), selectinload(Order.items)).where(Order.table_id == table_id, Order.status_id.not_in(final_ids)).order_by(Order.id.desc()))).scalars().all()
    res = []
    for o in orders:
        items_txt = ", ".join([f"{i.product_name} x{i.quantity}" for i in o.items])
        res.append({"id": o.id, "status": o.status.name, "total": float(o.total_price), "items": items_txt})
    return JSONResponse(res)
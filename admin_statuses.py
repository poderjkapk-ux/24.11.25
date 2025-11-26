# admin_statuses.py

import html
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import OrderStatus, Settings
from templates import ADMIN_HTML_TEMPLATE
from dependencies import get_db_session, check_credentials

router = APIRouter()

@router.get("/admin/statuses", response_class=HTMLResponse)
async def admin_statuses(
    error: Optional[str] = None, 
    session: AsyncSession = Depends(get_db_session), 
    username: str = Depends(check_credentials)
):
    """Відображає сторінку управління статусами замовлень."""
    settings = await session.get(Settings, 1) or Settings()
    
    statuses_res = await session.execute(select(OrderStatus).order_by(OrderStatus.id))
    statuses = statuses_res.scalars().all()

    error_html = ""
    if error == "in_use":
        error_html = "<div class='card' style='background:#fee2e2; color:#991b1b; border:1px solid #fecaca; margin-bottom:20px;'>⚠️ Помилка! Неможливо видалити статус, оскільки він використовується в замовленнях.</div>"

    # Функція для генерації кнопки-перемикача
    def toggle_btn(id, field, val, icon_class, title):
        color = "green" if val else "#e5e7eb" # Сірий якщо вимкнено
        opacity = "1" if val else "0.5"
        return f"""
        <form action="/admin/edit_status/{id}" method="post" style="display:inline-block; margin:0 2px;">
            <input type="hidden" name="field" value="{field}">
            <input type="hidden" name="value" value="{'false' if val else 'true'}">
            <button type="submit" class="icon-btn" title="{title} ({'Увімкнено' if val else 'Вимкнено'})" style="color:{color}; opacity:{opacity};">
                <i class="{icon_class}"></i>
            </button>
        </form>
        """

    rows = ""
    for s in statuses:
        # Група: Хто бачить
        visibility_icons = (
            toggle_btn(s.id, "visible_to_operator", s.visible_to_operator, "fa-solid fa-headset", "Оператор") +
            toggle_btn(s.id, "visible_to_courier", s.visible_to_courier, "fa-solid fa-motorcycle", "Кур'єр") +
            toggle_btn(s.id, "visible_to_waiter", s.visible_to_waiter, "fa-solid fa-user-tie", "Офіціант") +
            toggle_btn(s.id, "visible_to_chef", s.visible_to_chef, "fa-solid fa-utensils", "Повар") +
            toggle_btn(s.id, "visible_to_bartender", s.visible_to_bartender, "fa-solid fa-martini-glass", "Бармен")
        )

        # Група: Системні дії
        system_icons = (
            toggle_btn(s.id, "notify_customer", s.notify_customer, "fa-regular fa-bell", "Сповіщати клієнта") +
            toggle_btn(s.id, "requires_kitchen_notify", s.requires_kitchen_notify, "fa-solid fa-bullhorn", "На виробництво (Кухня/Бар)") +
            toggle_btn(s.id, "is_completed_status", s.is_completed_status, "fa-solid fa-flag-checkered", "Фінальний (Успіх/Каса)") +
            toggle_btn(s.id, "is_cancelled_status", s.is_cancelled_status, "fa-solid fa-ban", "Скасування")
        )

        rows += f"""
        <tr>
            <td style="text-align:center; color:#888;">{s.id}</td>
            <td>
                <form action="/admin/edit_status/{s.id}" method="post" class="inline-form">
                    <input type="text" name="name" value="{html.escape(s.name)}" style="width: 100%; min-width:120px; padding: 5px; border:1px solid #eee; border-radius:4px;">
                    <button type="submit" class="button-sm" title="Зберегти назву"><i class="fa-solid fa-floppy-disk"></i></button>
                </form>
            </td>
            <td style="text-align:center; white-space: nowrap;">{visibility_icons}</td>
            <td style="text-align:center; white-space: nowrap; border-left: 1px solid #eee;">{system_icons}</td>
            <td class="actions">
                <a href="/admin/delete_status/{s.id}" onclick="return confirm('Ви впевнені?');" class="button-sm danger" title="Видалити"><i class="fa-solid fa-trash"></i></a>
            </td>
        </tr>"""

    styles = """
    <style>
        .icon-btn { background: none; border: none; cursor: pointer; font-size: 1.1rem; transition: all 0.2s; padding: 2px; }
        .icon-btn:hover { transform: scale(1.2); opacity: 1 !important; }
        .toolbar { display: flex; justify-content: flex-end; margin-bottom: 20px; }
        
        /* Легенда */
        .legend { display: flex; gap: 15px; font-size: 0.85rem; color: #666; margin-bottom: 10px; flex-wrap: wrap; }
        .legend span { display: flex; align-items: center; gap: 5px; }
    </style>
    """

    body = f"""
    {styles}
    {error_html}
    
    <div class="card">
        <div class="toolbar">
            <button class="button" onclick="document.getElementById('add-status-modal').classList.add('active')">
                <i class="fa-solid fa-plus"></i> Додати статус
            </button>
        </div>
        
        <div class="legend">
            <span><i class="fa-solid fa-headset"></i> Оператор</span>
            <span><i class="fa-solid fa-motorcycle"></i> Кур'єр</span>
            <span><i class="fa-solid fa-user-tie"></i> Офіціант</span>
            <span><i class="fa-solid fa-utensils"></i> Повар</span>
            <span><i class="fa-solid fa-martini-glass"></i> Бармен</span>
            <span style="border-left:1px solid #ccc; padding-left:10px;"><i class="fa-solid fa-bullhorn"></i> На кухню</span>
            <span><i class="fa-solid fa-flag-checkered"></i> Фініш</span>
            <span><i class="fa-solid fa-ban"></i> Скасування</span>
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th width="50">ID</th>
                        <th>Назва</th>
                        <th style="text-align:center;">Видимість (Хто бачить)</th>
                        <th style="text-align:center;">Системні налаштування</th>
                        <th width="60">Дії</th>
                    </tr>
                </thead>
                <tbody>
                    {rows or "<tr><td colspan='5' style='text-align:center; padding:20px;'>Статусів немає</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>

    <div class="modal-overlay" id="add-status-modal">
        <div class="modal">
            <div class="modal-header">
                <h4>Новий статус</h4>
                <button type="button" class="close-button" onclick="document.getElementById('add-status-modal').classList.remove('active')">&times;</button>
            </div>
            <div class="modal-body">
                <form action="/admin/add_status" method="post">
                    <label>Назва статусу *</label>
                    <input type="text" name="name" placeholder="Наприклад: Готується" required>
                    
                    <div style="background:#f9fafb; padding:15px; border-radius:8px; border:1px solid #eee; margin-bottom:15px;">
                        <label style="margin-bottom:10px; display:block; font-weight:bold;">Хто бачить цей статус?</label>
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                            <div class="checkbox-group"><input type="checkbox" name="visible_to_operator" value="true" checked><label>Оператор</label></div>
                            <div class="checkbox-group"><input type="checkbox" name="visible_to_courier" value="true"><label>Кур'єр</label></div>
                            <div class="checkbox-group"><input type="checkbox" name="visible_to_waiter" value="true"><label>Офіціант</label></div>
                            <div class="checkbox-group"><input type="checkbox" name="visible_to_chef" value="true"><label>Повар</label></div>
                            <div class="checkbox-group"><input type="checkbox" name="visible_to_bartender" value="true"><label>Бармен</label></div>
                        </div>
                    </div>

                    <div style="background:#fff7ed; padding:15px; border-radius:8px; border:1px solid #ffedd5; margin-bottom:15px;">
                        <label style="margin-bottom:10px; display:block; font-weight:bold;">Системна логіка</label>
                        
                        <div class="checkbox-group">
                            <input type="checkbox" name="notify_customer" value="true" checked>
                            <label>🔔 Сповіщати клієнта про перехід</label>
                        </div>
                        
                        <div class="checkbox-group">
                            <input type="checkbox" name="requires_kitchen_notify" value="true">
                            <label>👨‍🍳 Надсилати на Кухню/Бар (початок готування)</label>
                        </div>
                        
                        <div class="checkbox-group">
                            <input type="checkbox" name="is_completed_status" value="true">
                            <label>🏁 Вважати виконаним (Успіх / В касу)</label>
                        </div>
                        
                        <div class="checkbox-group">
                            <input type="checkbox" name="is_cancelled_status" value="true">
                            <label>🚫 Вважати скасованим</label>
                        </div>
                    </div>

                    <button type="submit" class="button" style="width:100%;">Додати статус</button>
                </form>
            </div>
        </div>
    </div>
    """

    # --- ИСПРАВЛЕНИЕ ---
    active_classes = {key: "" for key in ["main_active", "orders_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]}
    active_classes["statuses_active"] = "active"
    
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(
        title="Статуси замовлень", 
        body=body, 
        site_title=settings.site_title or "Назва", 
        **active_classes
    ))

@router.post("/admin/add_status")
async def add_status(
    name: str = Form(...), 
    notify_customer: bool = Form(False), 
    visible_to_operator: bool = Form(False), 
    visible_to_courier: bool = Form(False), 
    visible_to_waiter: bool = Form(False), 
    visible_to_chef: bool = Form(False), 
    visible_to_bartender: bool = Form(False), 
    requires_kitchen_notify: bool = Form(False), 
    is_completed_status: bool = Form(False), 
    is_cancelled_status: bool = Form(False), 
    session: AsyncSession = Depends(get_db_session), 
    username: str = Depends(check_credentials)
):
    session.add(OrderStatus(
        name=name, 
        notify_customer=notify_customer, 
        visible_to_operator=visible_to_operator, 
        visible_to_courier=visible_to_courier, 
        visible_to_waiter=visible_to_waiter, 
        visible_to_chef=visible_to_chef, 
        visible_to_bartender=visible_to_bartender, 
        requires_kitchen_notify=requires_kitchen_notify, 
        is_completed_status=is_completed_status, 
        is_cancelled_status=is_cancelled_status
    ))
    await session.commit()
    return RedirectResponse(url="/admin/statuses", status_code=303)

@router.post("/admin/edit_status/{status_id}")
async def edit_status(
    status_id: int, 
    name: Optional[str] = Form(None), 
    field: Optional[str] = Form(None), 
    value: Optional[str] = Form(None), 
    session: AsyncSession = Depends(get_db_session), 
    username: str = Depends(check_credentials)
):
    status = await session.get(OrderStatus, status_id)
    if status:
        if name and not field: 
            status.name = name
        elif field: 
            setattr(status, field, value.lower() == 'true')
        await session.commit()
    return RedirectResponse(url="/admin/statuses", status_code=303)

@router.get("/admin/delete_status/{status_id}")
async def delete_status(
    status_id: int, 
    session: AsyncSession = Depends(get_db_session), 
    username: str = Depends(check_credentials)
):
    status = await session.get(OrderStatus, status_id)
    if status:
        try: 
            await session.delete(status)
            await session.commit()
        except IntegrityError: 
            return RedirectResponse(url="/admin/statuses?error=in_use", status_code=303)
            
    return RedirectResponse(url="/admin/statuses", status_code=303)
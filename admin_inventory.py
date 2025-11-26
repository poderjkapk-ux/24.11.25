# admin_inventory.py
import html
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from inventory_models import Ingredient, Unit, Warehouse, TechCard, TechCardItem, Stock, Supplier
from models import Product, Settings
from dependencies import get_db_session, check_credentials
from templates import ADMIN_HTML_TEMPLATE

router = APIRouter(prefix="/admin/inventory", tags=["inventory"])

INVENTORY_TABS = """
<div class="nav-tabs">
    <a href="/admin/inventory/ingredients">🥬 Ингредиенты</a>
    <a href="/admin/inventory/tech_cards">📜 Техкарты</a>
    <a href="/admin/inventory/stock">📦 Остатки</a>
    <a href="/admin/inventory/docs">📄 Документы</a>
</div>
"""

# --- Helper to generate menu active keys ---
def get_active_classes(active_key="inventory_active"):
    keys = ["main_active", "orders_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]
    return {k: "active" if k == active_key else "" for k in keys}

@router.get("/ingredients", response_class=HTMLResponse)
async def ingredients_list(session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    ingredients = (await session.execute(select(Ingredient).options(joinedload(Ingredient.unit)).order_by(Ingredient.name))).scalars().all()
    units = (await session.execute(select(Unit))).scalars().all()
    
    unit_opts = "".join([f"<option value='{u.id}'>{u.name}</option>" for u in units])
    
    rows = ""
    for i in ingredients:
        rows += f"<tr><td>{i.id}</td><td>{i.name}</td><td>{i.unit.name}</td><td>{i.current_cost}</td></tr>"
        
    body = f"""
    {INVENTORY_TABS}
    <div class="card">
        <h3>Добавить ингредиент</h3>
        <form action="/admin/inventory/ingredients/add" method="post" class="inline-form">
            <input type="text" name="name" placeholder="Название (напр. Лук)" required>
            <select name="unit_id">{unit_opts}</select>
            <button type="submit">Добавить</button>
        </form>
    </div>
    <div class="card">
        <table><thead><tr><th>ID</th><th>Название</th><th>Ед. изм.</th><th>Себестоимость</th></tr></thead>
        <tbody>{rows}</tbody></table>
    </div>
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Склад: Ингредиенты", body=body, site_title=settings.site_title, **get_active_classes()))

@router.post("/ingredients/add")
async def add_ingredient(name: str = Form(...), unit_id: int = Form(...), session: AsyncSession = Depends(get_db_session)):
    session.add(Ingredient(name=name, unit_id=unit_id))
    await session.commit()
    return RedirectResponse("/admin/inventory/ingredients", status_code=303)

@router.get("/tech_cards", response_class=HTMLResponse)
async def tech_cards_list(session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    
    # Продукты БЕЗ техкарт (чтобы создать новую)
    prods_without_tc = (await session.execute(
        select(Product).outerjoin(TechCard).where(TechCard.id == None, Product.is_active == True)
    )).scalars().all()
    
    # Существующие техкарты
    tcs = (await session.execute(
        select(TechCard).options(joinedload(TechCard.product)).order_by(TechCard.id)
    )).scalars().all()
    
    prod_opts = "".join([f"<option value='{p.id}'>{p.name}</option>" for p in prods_without_tc])
    
    rows = "".join([f"<tr><td>{tc.id}</td><td><b>{tc.product.name}</b></td><td><a href='/admin/inventory/tech_cards/{tc.id}' class='button-sm'>✏️ Редактировать</a></td></tr>" for tc in tcs])
    
    body = f"""
    {INVENTORY_TABS}
    <div class="card">
        <h3>Создать техкарту</h3>
        <form action="/admin/inventory/tech_cards/create" method="post" class="inline-form">
            <label>Блюдо:</label>
            <select name="product_id">{prod_opts}</select>
            <button type="submit">Создать</button>
        </form>
    </div>
    <div class="card">
        <table><thead><tr><th>ID</th><th>Блюдо</th><th>Действия</th></tr></thead><tbody>{rows}</tbody></table>
    </div>
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Склад: Техкарты", body=body, site_title=settings.site_title, **get_active_classes()))

@router.post("/tech_cards/create")
async def create_tc(product_id: int = Form(...), session: AsyncSession = Depends(get_db_session)):
    tc = TechCard(product_id=product_id)
    session.add(tc)
    await session.commit()
    await session.refresh(tc)
    return RedirectResponse(f"/admin/inventory/tech_cards/{tc.id}", status_code=303)

@router.get("/tech_cards/{tc_id}", response_class=HTMLResponse)
async def edit_tc(tc_id: int, session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    
    # Загружаем техкарту со всеми связями
    tc = await session.get(TechCard, tc_id, options=[
        joinedload(TechCard.product), 
        joinedload(TechCard.components).joinedload(TechCardItem.ingredient).joinedload(Ingredient.unit)
    ])
    
    # --- ИСПРАВЛЕНИЕ: Добавлена загрузка unit для списка ингредиентов ---
    ingredients = (await session.execute(
        select(Ingredient).options(joinedload(Ingredient.unit)).order_by(Ingredient.name)
    )).scalars().all()
    
    ing_opts = "".join([f"<option value='{i.id}'>{i.name} ({i.unit.name})</option>" for i in ingredients])
    
    comp_rows = ""
    total_cost = 0
    if tc and tc.components:
        for c in tc.components:
            cost = float(c.gross_amount) * float(c.ingredient.current_cost)
            total_cost += cost
            comp_rows += f"""
            <tr>
                <td>{c.ingredient.name}</td>
                <td>{c.gross_amount} {c.ingredient.unit.name}</td>
                <td>{c.net_amount} {c.ingredient.unit.name}</td>
                <td>{cost:.2f} грн</td>
                <td><a href='/admin/inventory/tech_cards/comp_del/{c.id}' style='color:red'>X</a></td>
            </tr>
            """
        
    body = f"""
    {INVENTORY_TABS}
    <div class="card">
        <div style="display:flex; justify-content:space-between;">
            <h2>Техкарта: {tc.product.name if tc else 'Не знайдено'}</h2>
            <a href="/admin/inventory/tech_cards" class="button secondary">Назад</a>
        </div>
        <div style="background:#e8f5e9; padding:15px; border-radius:8px; margin-bottom:20px;">
            <strong>Расчетная себестоимость:</strong> {total_cost:.2f} грн
        </div>
        
        <form action="/admin/inventory/tech_cards/{tc_id}/update_method" method="post">
            <label>Технология приготовления (для печати повару):</label>
            <textarea name="cooking_method" style="width:100%;" rows="5">{tc.cooking_method or '' if tc else ''}</textarea>
            <button type="submit" class="button-sm">Сохранить текст</button>
        </form>
        
        <h3>Ингредиенты</h3>
        <table>
            <thead><tr><th>Ингредиент</th><th>Брутто</th><th>Нетто</th><th>Прим. стоимость</th><th>Удалить</th></tr></thead>
            <tbody>{comp_rows}</tbody>
        </table>
        
        <hr>
        <h4>Добавить компонент</h4>
        <form action="/admin/inventory/tech_cards/{tc_id}/add_comp" method="post" class="inline-form">
            <select name="ingredient_id" style="width:200px;">{ing_opts}</select>
            <input type="number" name="gross" step="0.001" placeholder="Брутто" required style="width:100px;">
            <input type="number" name="net" step="0.001" placeholder="Нетто" required style="width:100px;">
            <button type="submit">Добавить</button>
        </form>
    </div>
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title=f"ТК: {tc.product.name if tc else ''}", body=body, site_title=settings.site_title, **get_active_classes()))

@router.post("/tech_cards/{tc_id}/add_comp")
async def add_tc_comp(tc_id: int, ingredient_id: int = Form(...), gross: float = Form(...), net: float = Form(...), session: AsyncSession = Depends(get_db_session)):
    session.add(TechCardItem(tech_card_id=tc_id, ingredient_id=ingredient_id, gross_amount=gross, net_amount=net))
    await session.commit()
    return RedirectResponse(f"/admin/inventory/tech_cards/{tc_id}", status_code=303)

@router.post("/tech_cards/{tc_id}/update_method")
async def update_tc_method(tc_id: int, cooking_method: str = Form(...), session: AsyncSession = Depends(get_db_session)):
    tc = await session.get(TechCard, tc_id)
    if tc:
        tc.cooking_method = cooking_method
        await session.commit()
    return RedirectResponse(f"/admin/inventory/tech_cards/{tc_id}", status_code=303)

@router.get("/tech_cards/comp_del/{item_id}")
async def del_tc_comp(item_id: int, session: AsyncSession = Depends(get_db_session)):
    item = await session.get(TechCardItem, item_id)
    if item:
        tc_id = item.tech_card_id
        await session.delete(item)
        await session.commit()
        return RedirectResponse(f"/admin/inventory/tech_cards/{tc_id}", status_code=303)
    return RedirectResponse("/admin/inventory/tech_cards", status_code=303)

@router.get("/stock", response_class=HTMLResponse)
async def stock_list(session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    stocks = (await session.execute(select(Stock).options(joinedload(Stock.warehouse), joinedload(Stock.ingredient).joinedload(Ingredient.unit)))).scalars().all()
    
    rows = ""
    for s in stocks:
        color = "red" if s.quantity < 0 else "black"
        rows += f"<tr><td>{s.warehouse.name}</td><td>{s.ingredient.name}</td><td style='color:{color}; font-weight:bold;'>{s.quantity:.3f} {s.ingredient.unit.name}</td></tr>"
        
    body = f"""{INVENTORY_TABS}<div class="card"><h3>Текущие остатки</h3><table><thead><tr><th>Склад</th><th>Товар</th><th>Остаток</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Склад: Остатки", body=body, site_title=settings.site_title, **get_active_classes()))

@router.get("/docs", response_class=HTMLResponse)
async def docs_list(session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    # Заглушка для документов
    body = f"""{INVENTORY_TABS}<div class="card"><h3>Документы</h3><p>Функционал в разработке.</p></div>"""
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Склад: Документы", body=body, site_title=settings.site_title, **get_active_classes()))
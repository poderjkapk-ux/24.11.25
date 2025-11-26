# admin_inventory.py
import html
from datetime import datetime
from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload, selectinload

from inventory_models import (
    Ingredient, Unit, Warehouse, TechCard, TechCardItem, Stock, Supplier, 
    InventoryDoc, InventoryDocItem
)
from models import Product, Settings
from dependencies import get_db_session, check_credentials
from templates import ADMIN_HTML_TEMPLATE
from inventory_service import apply_doc_stock_changes

router = APIRouter(prefix="/admin/inventory", tags=["inventory"])

INVENTORY_TABS = """
<div class="nav-tabs">
    <a href="/admin/inventory/ingredients">🥬 Інгредієнти</a>
    <a href="/admin/inventory/tech_cards">📜 Техкарти</a>
    <a href="/admin/inventory/stock">📦 Залишки</a>
    <a href="/admin/inventory/docs">📄 Документи</a>
</div>
"""

def get_active_classes(active_key="inventory_active"):
    keys = ["main_active", "orders_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]
    return {k: "active" if k == active_key else "" for k in keys}

# --- ІНГРЕДІЄНТИ ---
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
        <h3>Додати інгредієнт</h3>
        <form action="/admin/inventory/ingredients/add" method="post" class="inline-form">
            <input type="text" name="name" placeholder="Назва (напр. Цибуля)" required>
            <select name="unit_id">{unit_opts}</select>
            <button type="submit">Додати</button>
        </form>
    </div>
    <div class="card">
        <table><thead><tr><th>ID</th><th>Назва</th><th>Од. вим.</th><th>Собівартість</th></tr></thead>
        <tbody>{rows}</tbody></table>
    </div>
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Склад: Інгредієнти", body=body, site_title=settings.site_title, **get_active_classes()))

@router.post("/ingredients/add")
async def add_ingredient(name: str = Form(...), unit_id: int = Form(...), session: AsyncSession = Depends(get_db_session)):
    session.add(Ingredient(name=name, unit_id=unit_id))
    await session.commit()
    return RedirectResponse("/admin/inventory/ingredients", status_code=303)

# --- ТЕХКАРТИ ---
@router.get("/tech_cards", response_class=HTMLResponse)
async def tech_cards_list(session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    
    prods_without_tc = (await session.execute(
        select(Product).outerjoin(TechCard).where(TechCard.id == None, Product.is_active == True)
    )).scalars().all()
    
    tcs = (await session.execute(
        select(TechCard).options(joinedload(TechCard.product)).order_by(TechCard.id)
    )).scalars().all()
    
    prod_opts = "".join([f"<option value='{p.id}'>{p.name}</option>" for p in prods_without_tc])
    
    rows = "".join([f"<tr><td>{tc.id}</td><td><b>{tc.product.name}</b></td><td><a href='/admin/inventory/tech_cards/{tc.id}' class='button-sm'>✏️ Редагувати</a> <a href='/admin/inventory/tech_cards/{tc.id}/print' target='_blank' class='button-sm secondary' title='Друк'><i class='fa-solid fa-print'></i></a></td></tr>" for tc in tcs])
    
    body = f"""
    {INVENTORY_TABS}
    <div class="card">
        <h3>Створити техкарту</h3>
        <form action="/admin/inventory/tech_cards/create" method="post" class="inline-form">
            <label>Страва:</label>
            <select name="product_id">{prod_opts}</select>
            <button type="submit">Створити</button>
        </form>
    </div>
    <div class="card">
        <table><thead><tr><th>ID</th><th>Страва</th><th>Дії</th></tr></thead><tbody>{rows}</tbody></table>
    </div>
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Склад: Техкарти", body=body, site_title=settings.site_title, **get_active_classes()))

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
    
    tc = await session.get(TechCard, tc_id, options=[
        joinedload(TechCard.product), 
        joinedload(TechCard.components).joinedload(TechCardItem.ingredient).joinedload(Ingredient.unit)
    ])
    
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
            <div style="display:flex; gap:10px;">
                <a href="/admin/inventory/tech_cards/{tc.id}/print" target="_blank" class="button"><i class="fa-solid fa-print"></i> Друк ТК</a>
                <a href="/admin/inventory/tech_cards" class="button secondary">Назад</a>
            </div>
        </div>
        <div style="background:#e8f5e9; padding:15px; border-radius:8px; margin-bottom:20px;">
            <strong>Розрахункова собівартість:</strong> {total_cost:.2f} грн
        </div>
        
        <form action="/admin/inventory/tech_cards/{tc_id}/update_method" method="post">
            <label>Технологія приготування (для кухаря):</label>
            <textarea name="cooking_method" style="width:100%;" rows="5">{tc.cooking_method or '' if tc else ''}</textarea>
            <button type="submit" class="button-sm">Зберегти текст</button>
        </form>
        
        <h3>Інгредієнти</h3>
        <table>
            <thead><tr><th>Інгредієнт</th><th>Брутто</th><th>Нетто</th><th>Прибл. вартість</th><th>Видалити</th></tr></thead>
            <tbody>{comp_rows}</tbody>
        </table>
        
        <hr>
        <h4>Додати компонент</h4>
        <form action="/admin/inventory/tech_cards/{tc_id}/add_comp" method="post" class="inline-form">
            <select name="ingredient_id" style="width:200px;">{ing_opts}</select>
            <input type="number" name="gross" step="0.001" placeholder="Брутто" required style="width:100px;">
            <input type="number" name="net" step="0.001" placeholder="Нетто" required style="width:100px;">
            <button type="submit">Додати</button>
        </form>
    </div>
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title=f"ТК: {tc.product.name if tc else ''}", body=body, site_title=settings.site_title, **get_active_classes()))

@router.get("/tech_cards/{tc_id}/print", response_class=HTMLResponse)
async def print_tech_card(tc_id: int, session: AsyncSession = Depends(get_db_session)):
    """Друк Техкарти (Повноцінний документ)"""
    tc = await session.get(TechCard, tc_id, options=[
        joinedload(TechCard.product), 
        joinedload(TechCard.components).joinedload(TechCardItem.ingredient).joinedload(Ingredient.unit)
    ])
    
    if not tc: return HTMLResponse("Техкарту не знайдено")
    
    rows = ""
    total_gross = 0
    total_net = 0
    for c in tc.components:
        total_gross += float(c.gross_amount)
        total_net += float(c.net_amount)
        rows += f"<tr><td>{c.ingredient.name}</td><td>{c.gross_amount} {c.ingredient.unit.name}</td><td>{c.net_amount} {c.ingredient.unit.name}</td></tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ТК: {tc.product.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ text-align: center; margin-bottom: 5px; }}
            .meta {{ text-align: center; color: #555; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #000; padding: 8px; text-align: left; }}
            th {{ background: #f0f0f0; }}
            .method {{ border: 1px solid #000; padding: 15px; }}
        </style>
    </head>
    <body>
        <h1>Техніко-технологічна карта</h1>
        <div class="meta">Страва: <b>{tc.product.name}</b></div>
        
        <table>
            <thead>
                <tr><th>Найменування сировини</th><th>Брутто</th><th>Нетто</th></tr>
            </thead>
            <tbody>
                {rows}
                <tr>
                    <td><b>ВИХІД:</b></td>
                    <td><b>{total_gross:.3f}</b></td>
                    <td><b>{total_net:.3f}</b></td>
                </tr>
            </tbody>
        </table>
        
        <h3>Технологія приготування:</h3>
        <div class="method">
            {html.escape(tc.cooking_method or 'Не заповнено').replace(chr(10), '<br>')}
        </div>
        
        <script>window.print();</script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

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
        
    body = f"""{INVENTORY_TABS}<div class="card"><h3>Поточні залишки</h3><table><thead><tr><th>Склад</th><th>Товар</th><th>Залишок</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Склад: Залишки", body=body, site_title=settings.site_title, **get_active_classes()))

# --- ДОКУМЕНТООБІГ ---

@router.get("/docs", response_class=HTMLResponse)
async def docs_list(session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    
    docs = (await session.execute(
        select(InventoryDoc)
        .options(
            joinedload(InventoryDoc.source_warehouse), 
            joinedload(InventoryDoc.target_warehouse),
            joinedload(InventoryDoc.supplier)
        )
        .order_by(desc(InventoryDoc.created_at))
    )).scalars().all()
    
    rows = ""
    for d in docs:
        status = "<span class='badge badge-success'>Проведено</span>" if d.is_processed else "<span class='badge warning'>Чернетка</span>"
        
        info = ""
        if d.doc_type == 'supply': info = f"Пост: {d.supplier.name if d.supplier else '-'} -> {d.target_warehouse.name if d.target_warehouse else '-'}"
        elif d.doc_type == 'transfer': info = f"{d.source_warehouse.name if d.source_warehouse else '-'} -> {d.target_warehouse.name if d.target_warehouse else '-'}"
        elif d.doc_type == 'writeoff': info = f"Списання з: {d.source_warehouse.name if d.source_warehouse else '-'}"
        elif d.doc_type == 'deduction': info = f"Продаж (Замовлення #{d.linked_order_id})"
        
        type_map = {'supply': 'Прихід', 'transfer': 'Переміщення', 'writeoff': 'Списання', 'deduction': 'Авто-списання'}
        
        action_btn = f"<a href='/admin/inventory/docs/{d.id}' class='button-sm'>Відкрити</a>"
        if d.doc_type == 'deduction': action_btn = "<span style='color:#999'>Авто</span>"
        
        rows += f"""
        <tr>
            <td>{d.id}</td>
            <td>{d.created_at.strftime('%d.%m %H:%M')}</td>
            <td>{type_map.get(d.doc_type, d.doc_type)}</td>
            <td>{info}</td>
            <td>{status}</td>
            <td>{action_btn}</td>
        </tr>
        """
        
    body = f"""
    {INVENTORY_TABS}
    <div class="card">
        <div style="display:flex; justify-content:space-between;">
            <h3>Журнал документів</h3>
            <a href="/admin/inventory/docs/create" class="button"><i class="fa-solid fa-plus"></i> Новий документ</a>
        </div>
        <table>
            <thead><tr><th>ID</th><th>Дата</th><th>Тип</th><th>Інформація</th><th>Статус</th><th>Дії</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Склад: Документи", body=body, site_title=settings.site_title, **get_active_classes()))

@router.get("/docs/create", response_class=HTMLResponse)
async def create_doc_page(session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    
    warehouses = (await session.execute(select(Warehouse))).scalars().all()
    suppliers = (await session.execute(select(Supplier))).scalars().all()
    
    wh_opts = "".join([f"<option value='{w.id}'>{w.name}</option>" for w in warehouses])
    sup_opts = "".join([f"<option value='{s.id}'>{s.name}</option>" for s in suppliers])
    
    body = f"""
    {INVENTORY_TABS}
    <div class="card" style="max-width:600px; margin:0 auto;">
        <h3>Створення документа</h3>
        <form action="/admin/inventory/docs/create" method="post">
            <label>Тип операції:</label>
            <select name="doc_type" id="doc_type" onchange="toggleFields()">
                <option value="supply">📥 Прихід від постачальника</option>
                <option value="transfer">🔄 Переміщення між складами</option>
                <option value="writeoff">🗑️ Списання (Псування/Інвент)</option>
            </select>
            
            <div id="supplier_div">
                <label>Постачальник:</label>
                <select name="supplier_id"><option value="">Оберіть...</option>{sup_opts}</select>
            </div>
            
            <div id="source_wh_div" style="display:none;">
                <label>Склад ЗВІДКИ:</label>
                <select name="source_warehouse_id"><option value="">Оберіть...</option>{wh_opts}</select>
            </div>
            
            <div id="target_wh_div">
                <label>Склад КУДИ:</label>
                <select name="target_warehouse_id"><option value="">Оберіть...</option>{wh_opts}</select>
            </div>
            
            <label>Коментар:</label>
            <input type="text" name="comment">
            
            <button type="submit" class="button" style="width:100%; margin-top:20px;">Створити та перейти до товарів</button>
        </form>
    </div>
    <script>
        function toggleFields() {{
            const type = document.getElementById('doc_type').value;
            const sup = document.getElementById('supplier_div');
            const src = document.getElementById('source_wh_div');
            const tgt = document.getElementById('target_wh_div');
            
            if(type === 'supply') {{
                sup.style.display = 'block';
                src.style.display = 'none';
                tgt.style.display = 'block';
            }} else if (type === 'transfer') {{
                sup.style.display = 'none';
                src.style.display = 'block';
                tgt.style.display = 'block';
            }} else if (type === 'writeoff') {{
                sup.style.display = 'none';
                src.style.display = 'block';
                tgt.style.display = 'none';
            }}
        }}
        toggleFields();
    </script>
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Новий документ", body=body, site_title=settings.site_title, **get_active_classes()))

@router.post("/docs/create")
async def create_doc_action(
    doc_type: str = Form(...), 
    supplier_id: int = Form(None),
    source_warehouse_id: int = Form(None),
    target_warehouse_id: int = Form(None),
    comment: str = Form(None),
    session: AsyncSession = Depends(get_db_session)
):
    doc = InventoryDoc(
        doc_type=doc_type,
        supplier_id=supplier_id,
        source_warehouse_id=source_warehouse_id,
        target_warehouse_id=target_warehouse_id,
        comment=comment,
        is_processed=False
    )
    session.add(doc)
    await session.commit()
    return RedirectResponse(f"/admin/inventory/docs/{doc.id}", status_code=303)

@router.get("/docs/{doc_id}", response_class=HTMLResponse)
async def view_doc(doc_id: int, session: AsyncSession = Depends(get_db_session), user=Depends(check_credentials)):
    settings = await session.get(Settings, 1) or Settings()
    
    doc = await session.get(InventoryDoc, doc_id, options=[joinedload(InventoryDoc.items).joinedload(InventoryDocItem.ingredient).joinedload(Ingredient.unit)])
    if not doc: return HTMLResponse("Документ не знайдено")
    
    ingredients = (await session.execute(select(Ingredient).options(joinedload(Ingredient.unit)).order_by(Ingredient.name))).scalars().all()
    ing_opts = "".join([f"<option value='{i.id}'>{i.name} ({i.unit.name})</option>" for i in ingredients])
    
    rows = ""
    for item in doc.items:
        rows += f"<tr><td>{item.ingredient.name}</td><td>{item.quantity} {item.ingredient.unit.name}</td><td>{item.price}</td><td><a href='/admin/inventory/docs/{doc.id}/del_item/{item.id}' style='color:red'>X</a></td></tr>"
        
    status_ui = ""
    if not doc.is_processed:
        form_html = f"""
        <div class="card" style="background:#f9f9f9;">
            <h4>Додати позицію</h4>
            <form action="/admin/inventory/docs/{doc.id}/add_item" method="post" class="inline-form">
                <select name="ingredient_id" style="width:250px;" required>{ing_opts}</select>
                <input type="number" name="quantity" step="0.001" placeholder="К-сть" required style="width:100px;">
                <input type="number" name="price" step="0.01" placeholder="Ціна (за од)" style="width:100px;" value="0">
                <button type="submit">Додати</button>
            </form>
        </div>
        <div style="margin-top:20px; text-align:right;">
            <form action="/admin/inventory/docs/{doc.id}/approve" method="post">
                <button type="submit" class="button" onclick="return confirm('Провести документ? Залишки оновляться.')">✅ ПРОВЕСТИ ДОКУМЕНТ</button>
            </form>
        </div>
        """
        status_ui = form_html
    else:
        status_ui = "<div class='card' style='background:#e8f5e9; color:green; text-align:center;'><h3>✅ Документ проведено</h3>Зміни заблоковано.</div>"

    body = f"""
    {INVENTORY_TABS}
    <div class="card">
        <div style="display:flex; justify-content:space-between;">
            <h2>Документ #{doc.id} ({doc.doc_type})</h2>
            <a href="/admin/inventory/docs" class="button secondary">Назад</a>
        </div>
        <p><b>Коментар:</b> {doc.comment or '-'}</p>
        
        <table>
            <thead><tr><th>Товар</th><th>К-сть</th><th>Ціна</th><th>Дія</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    {status_ui}
    """
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title=f"Документ #{doc.id}", body=body, site_title=settings.site_title, **get_active_classes()))

@router.post("/docs/{doc_id}/add_item")
async def add_doc_item(
    doc_id: int, 
    ingredient_id: int = Form(...), 
    quantity: float = Form(...), 
    price: float = Form(0),
    session: AsyncSession = Depends(get_db_session)
):
    doc = await session.get(InventoryDoc, doc_id)
    if not doc or doc.is_processed: raise HTTPException(400, "Не можна змінювати проведений документ")
    
    item = InventoryDocItem(doc_id=doc_id, ingredient_id=ingredient_id, quantity=quantity, price=price)
    session.add(item)
    await session.commit()
    return RedirectResponse(f"/admin/inventory/docs/{doc_id}", status_code=303)

@router.get("/docs/{doc_id}/del_item/{item_id}")
async def del_doc_item(doc_id: int, item_id: int, session: AsyncSession = Depends(get_db_session)):
    doc = await session.get(InventoryDoc, doc_id)
    if not doc or doc.is_processed: raise HTTPException(400, "Заблоковано")
    
    item = await session.get(InventoryDocItem, item_id)
    if item:
        await session.delete(item)
        await session.commit()
    return RedirectResponse(f"/admin/inventory/docs/{doc_id}", status_code=303)

@router.post("/docs/{doc_id}/approve")
async def approve_doc(doc_id: int, session: AsyncSession = Depends(get_db_session)):
    try:
        await apply_doc_stock_changes(session, doc_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse(f"/admin/inventory/docs/{doc_id}", status_code=303)
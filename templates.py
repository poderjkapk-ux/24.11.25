# templates.py

# --- ЧАСТИНА 1: ЗАГАЛЬНИЙ ЛЕЯУТ ТА ТАБЛИЦІ ---

# Головний шаблон адмінки з меню та стилями
ADMIN_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Адмін-панель</title>
    
    <link rel="apple-touch-icon" sizes="180x180" href="/static/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/favicons/favicon-16x16.png">
    <link rel="manifest" href="/static/favicons/site.webmanifest">
    <link rel="shortcut icon" href="/static/favicons/favicon.ico">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --primary-color: #4a4a4a;
            --primary-hover-color: #333333;
            --text-color-light: #111827;
            --text-color-dark: #f9fafb;
            --bg-light: #f9fafb;
            --bg-dark: #111827;
            --sidebar-bg-light: #ffffff;
            --sidebar-bg-dark: #1f2937;
            --card-bg-light: #ffffff;
            --card-bg-dark: #1f2937;
            --border-light: #e5e7eb;
            --border-dark: #374151;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            --font-sans: 'Inter', sans-serif;
            --status-green: #10b981;
            --status-yellow: #f59e0b;
            --status-red: #ef4444;
            --status-blue: #3b82f6;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: var(--font-sans);
            background-color: var(--bg-light);
            color: var(--text-color-light);
            display: flex;
            min-height: 100vh;
            transition: background-color 0.3s, color 0.3s;
        }}
        body.dark-mode {{
            --bg-light: var(--bg-dark);
            --text-color-light: var(--text-color-dark);
            --sidebar-bg-light: var(--sidebar-bg-dark);
            --card-bg-light: var(--card-bg-dark);
            --border-light: var(--border-dark);
        }}
        
        /* --- Sidebar Styles --- */
        .sidebar {{
            width: 260px;
            background-color: var(--sidebar-bg-light);
            border-right: 1px solid var(--border-light);
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100%;
            transition: background-color 0.3s, border-color 0.3s, transform 0.3s ease-in-out;
            z-index: 1000;
        }}
        .sidebar-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 2.5rem;
        }}
        .sidebar-header .logo {{ display: flex; align-items: center; gap: 0.75rem; }}
        .sidebar-header .logo h2 {{ font-size: 1.5rem; font-weight: 700; color: var(--primary-color); }}
        .sidebar nav a {{
            display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem;
            color: #6b7280; text-decoration: none; font-weight: 500;
            border-radius: 0.5rem; transition: all 0.2s ease; margin-bottom: 0.5rem;
        }}
        body.dark-mode .sidebar nav a {{ color: #9ca3af; }}
        .sidebar nav a:hover {{ background-color: #f3f4f6; color: var(--primary-color); }}
        body.dark-mode .sidebar nav a:hover {{ background-color: #374151; }}
        .sidebar nav a.active {{ background-color: var(--primary-color); color: white; box-shadow: var(--shadow); }}
        .sidebar nav a i {{ width: 20px; text-align: center; }}
        .sidebar-footer {{ margin-top: auto; }}
        .sidebar-close {{
            display: none; background: none; border: none; font-size: 2rem;
            color: #6b7280; cursor: pointer;
        }}

        /* --- Main Content & Header --- */
        main {{
            flex-grow: 1;
            padding: 2rem;
            transition: margin-left 0.3s ease-in-out;
            margin-left: 260px;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }}
        .header-left {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        header h1 {{ font-size: 2rem; font-weight: 700; }}
        .menu-toggle {{
            display: none; background: none; border: 1px solid var(--border-light);
            width: 40px; height: 40px; border-radius: 0.5rem;
            align-items: center; justify-content: center;
            font-size: 1.25rem; color: #6b7280; cursor: pointer;
        }}
        .theme-toggle {{ cursor: pointer; font-size: 1.25rem; color: #6b7280; }}

        /* --- Overlay for Mobile Menu --- */
        .content-overlay {{
            display: none; position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 999;
        }}
        .content-overlay.active {{ display: block; }}

        /* --- Responsive Styles (Mobile) --- */
        @media (max-width: 992px) {{
            .sidebar {{
                transform: translateX(-100%);
                box-shadow: var(--shadow);
            }}
            .sidebar.open {{
                transform: translateX(0);
            }}
            .sidebar-close {{
                display: block;
            }}
            main {{
                margin-left: 0;
            }}
            .menu-toggle {{
                display: inline-flex;
            }}
            header h1 {{ font-size: 1.5rem; }}
        }}

        /* --- General Component Styles (Cards, Tables, etc.) --- */
        .card {{
            background-color: var(--card-bg-light); border-radius: 0.75rem;
            padding: 1.5rem; box-shadow: var(--shadow);
            border: 1px solid var(--border-light); margin-bottom: 2rem;
        }}
        .card h2 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 1.5rem; }}
        .card h3 {{
             font-size: 1.1rem; font-weight: 600; margin-top: 1.5rem;
             margin-bottom: 1rem; padding-bottom: 0.5rem;
             border-bottom: 1px solid var(--border-light);
        }}
        .button, button[type="submit"] {{
            padding: 0.6rem 1.2rem; background-color: var(--primary-color);
            color: white !important; border: none; border-radius: 0.5rem;
            cursor: pointer; font-size: 0.9rem; font-weight: 600;
            transition: background-color 0.2s ease; text-decoration: none;
            display: inline-flex; align-items: center; gap: 0.5rem;
        }}
        button:hover, .button:hover {{ background-color: var(--primary-hover-color); }}
        .button.secondary {{ background-color: #6b7280; }}
        .button.secondary:hover {{ background-color: #4b5563; }}
        .button.danger {{ background-color: #ef4444; }}
        .button.danger:hover {{ background-color: #dc2626; }}
        .button.success {{ background-color: var(--status-green); }}
        .button.success:hover {{ filter: brightness(0.9); }}
        
        .button-sm {{
            display: inline-block; padding: 0.4rem 0.6rem; 
            border-radius: 0.3rem; text-decoration: none; color: white !important;
            background-color: #6b7280; font-size: 0.85rem; cursor: pointer; border: none;
        }}
        .button-sm.danger {{ background-color: var(--status-red); }}
        .button-sm.success {{ background-color: var(--status-green); }}
        .button-sm.secondary {{ background-color: #6b7280; }}
        .button-sm:hover {{ opacity: 0.8; }}
        
        .table-wrapper {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 1rem; text-align: left; border-bottom: 1px solid var(--border-light); vertical-align: middle; }}
        th {{ font-weight: 600; font-size: 0.85rem; text-transform: uppercase; color: #6b7280; }}
        body.dark-mode th {{ color: #9ca3af; }}
        td .table-img {{ width: 40px; height: 40px; border-radius: 0.5rem; object-fit: cover; vertical-align: middle; margin-right: 10px; }}
        .status {{
            padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;
            background-color: #e5e7eb; color: #374151;
        }}
        .actions {{ text-align: right; white-space: nowrap; }}
        .actions a, .actions button {{ color: #6b7280; margin-left: 0.5rem; font-size: 1rem; text-decoration: none; display: inline-block; }}
        .actions a:hover, .actions button:hover {{ color: var(--primary-color); }}
        label {{ font-weight: 600; display: block; margin-bottom: 0.5rem; font-size: 0.9rem; }}
        input, textarea, select {{
            width: 100%; padding: 0.75rem 1rem; border: 1px solid var(--border-light);
            border-radius: 0.5rem; font-family: var(--font-sans); font-size: 1rem;
            background-color: var(--bg-light); color: var(--text-color-light);
            margin-bottom: 1rem;
        }}
        input:focus, textarea:focus, select:focus {{
            outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 2px #bfdbfe;
        }}
        input[type="color"] {{
            padding: 0.25rem; height: 40px;
        }}
        .checkbox-group {{ display: flex; align-items: center; gap: 10px; margin-bottom: 1rem;}}
        .checkbox-group input[type="checkbox"] {{ width: auto; margin-bottom: 0; }}
        .checkbox-group label {{ margin-bottom: 0; }}
        .search-form, .inline-form {{ display: flex; gap: 10px; margin-bottom: 1rem; align-items: center; }}
        .inline-form input {{ margin-bottom: 0; }}
        .pagination {{ margin-top: 1rem; display: flex; gap: 5px; }}
        .pagination a {{ padding: 5px 10px; border: 1px solid var(--border-light); text-decoration: none; color: var(--text-color-light); border-radius: 5px; }}
        .pagination a.active {{ background-color: var(--primary-color); color: white; border-color: var(--primary-color);}}
        
        .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-light); padding-bottom: 5px; overflow-x: auto; }}
        .nav-tabs a {{ padding: 8px 15px; border-radius: 5px 5px 0 0; text-decoration: none; color: #6b7280; transition: color 0.2s; white-space: nowrap; }}
        .nav-tabs a:hover {{ color: var(--primary-color); }}
        .nav-tabs a.active {{ background-color: var(--primary-color); color: white !important; }}
        
        /* --- Modal Styles --- */
        .modal-overlay {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6); z-index: 2000;
            display: none; justify-content: center; align-items: center;
        }}
        .modal-overlay.active {{ display: flex; }}
        .modal {{
            background: var(--card-bg-light); border-radius: 0.75rem; padding: 2rem;
            width: 90%; max-width: 700px; max-height: 80vh;
            display: flex; flex-direction: column;
        }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }}
        .modal-header h4 {{ font-size: 1.25rem; }}
        .modal-header .close-button {{ background: none; border: none; font-size: 2rem; cursor: pointer; }}
        .modal-body {{ flex-grow: 1; overflow-y: auto; }}
    </style>
</head>
<body class="">
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <div class="logo">
                <i class="fa-solid fa-utensils"></i>
                <h2>{site_title}</h2>
            </div>
            <button class="sidebar-close" id="sidebar-close">&times;</button>
        </div>
        <nav>
            <a href="/admin" class="{main_active}"><i class="fa-solid fa-chart-line"></i> Головна</a>
            <a href="/admin/orders" class="{orders_active}"><i class="fa-solid fa-box-archive"></i> Замовлення</a>
            <a href="/admin/clients" class="{clients_active}"><i class="fa-solid fa-users-line"></i> Клієнти</a>
            <a href="/admin/tables" class="{tables_active}"><i class="fa-solid fa-chair"></i> Столики</a>
            <a href="/admin/cash" class="{reports_active}"><i class="fa-solid fa-cash-register"></i> 💰 Каса</a>
            
            <hr style="border:0; border-top:1px solid #eee; margin: 10px 0;">
            <a href="/admin/inventory/ingredients" class="{inventory_active}"><i class="fa-solid fa-boxes-stacked"></i> Склад</a>
            <a href="/admin/products" class="{products_active}"><i class="fa-solid fa-burger"></i> Страви</a>
            <a href="/admin/categories" class="{categories_active}"><i class="fa-solid fa-folder-open"></i> Категорії</a>
            <a href="/admin/menu" class="{menu_active}"><i class="fa-solid fa-file-lines"></i> Сторінки меню</a>
            
            <hr style="border:0; border-top:1px solid #eee; margin: 10px 0;">
            <a href="/admin/employees" class="{employees_active}"><i class="fa-solid fa-users"></i> Співробітники</a>
            <a href="/admin/statuses" class="{statuses_active}"><i class="fa-solid fa-clipboard-list"></i> Статуси</a>
            <a href="/admin/reports" class="{reports_active}"><i class="fa-solid fa-chart-pie"></i> Звіти</a>
            <a href="/admin/design_settings" class="{design_active}"><i class="fa-solid fa-palette"></i> Дизайн та SEO</a>
            <a href="/admin/settings" class="{settings_active}"><i class="fa-solid fa-gear"></i> Налаштування</a>
        </nav>
        <div class="sidebar-footer">
            <a href="#"><i class="fa-solid fa-right-from-bracket"></i> Вийти</a>
        </div>
    </div>

    <main>
        <header>
            <div class="header-left">
                <button class="menu-toggle" id="menu-toggle">
                    <i class="fa-solid fa-bars"></i>
                </button>
                <h1>{title}</h1>
            </div>
            <i id="theme-toggle" class="fa-solid fa-sun theme-toggle"></i>
        </header>
        {body}
    </main>

    <div class="content-overlay" id="content-overlay"></div>

    <script>
      // --- Theme Toggler ---
      const themeToggle = document.getElementById('theme-toggle');
      const body = document.body;

      if (localStorage.getItem('theme') === 'light') {{
        body.classList.remove('dark-mode');
        themeToggle.classList.add('fa-moon');
        themeToggle.classList.remove('fa-sun');
      }} else {{
        body.classList.add('dark-mode');
        themeToggle.classList.add('fa-sun');
        themeToggle.classList.remove('fa-moon');
      }}

      themeToggle.addEventListener('click', () => {{
        body.classList.toggle('dark-mode');
        themeToggle.classList.toggle('fa-sun');
        themeToggle.classList.toggle('fa-moon');
        if(body.classList.contains('dark-mode')){{
          localStorage.setItem('theme', 'dark');
        }} else {{
          localStorage.setItem('theme', 'light');
        }}
      }});

      // --- Mobile Sidebar Logic ---
      const sidebar = document.getElementById('sidebar');
      const menuToggle = document.getElementById('menu-toggle');
      const sidebarClose = document.getElementById('sidebar-close');
      const contentOverlay = document.getElementById('content-overlay');

      const openSidebar = () => {{
        sidebar.classList.add('open');
        contentOverlay.classList.add('active');
      }};

      const closeSidebar = () => {{
        sidebar.classList.remove('open');
        contentOverlay.classList.remove('active');
      }};

      menuToggle.addEventListener('click', openSidebar);
      sidebarClose.addEventListener('click', closeSidebar);
      contentOverlay.addEventListener('click', closeSidebar);

    </script>
</body>
</html>
"""

# --- ШАБЛОН ВКЛАДОК СКЛАДА ---
ADMIN_INVENTORY_TABS = """
<div class="nav-tabs">
    <a href="/admin/inventory/ingredients">🥬 Ингредиенты</a>
    <a href="/admin/inventory/tech_cards">📜 Техкарты</a>
    <a href="/admin/inventory/stock">📦 Остатки</a>
    <a href="/admin/inventory/docs">📄 Документы</a>
</div>
"""

ADMIN_TABLES_BODY = """
<style>
    .qr-code-img {{
        width: 100px;
        height: 100px;
        border: 1px solid var(--border-light);
        padding: 5px;
        background: white;
    }}
    /* Стиль для селекта з множинним вибором */
    #waiter_ids_select {{
        height: 250px;
        width: 100%;
    }}
</style>
<div class="card">
    <h2><i class="fa-solid fa-plus"></i> Додати новий столик</h2>
    <form action="/admin/tables/add" method="post" class="search-form">
        <input type="text" id="name" name="name" placeholder="Назва або номер столика" required>
        <button type="submit">Додати столик</button>
    </form>
</div>
<div class="card">
    <h2><i class="fa-solid fa-chair"></i> Список столиків</h2>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Назва</th>
                    <th>QR-код</th>
                    <th>Закріплені офіціанти</th>
                    <th>Дії</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
</div>
<div class="modal-overlay" id="assign-waiter-modal">
    <div class="modal">
        <div class="modal-header">
            <h4 id="modal-title">Призначити офіціантів для столика</h4>
            <button type="button" class="close-button" onclick="closeModal()">&times;</button>
        </div>
        <div class="modal-body">
            <form id="assign-waiter-form" method="post">
                <label for="waiter_ids_select">Виберіть офіціантів (на зміні):</label>
                <p style="font-size: 0.8rem; margin-bottom: 10px;">(Утримуйте Ctrl/Cmd для вибору кількох)</p>
                <select id="waiter_ids_select" name="waiter_ids" multiple>
                    </select>
                <br><br>
                <button type="submit">Призначити</button>
            </form>
        </div>
    </div>
</div>
<script>
function openAssignWaiterModal(tableId, tableName, waiters, assignedWaiterIds) {{
    const modal = document.getElementById('assign-waiter-modal');
    const form = document.getElementById('assign-waiter-form');
    const select = document.getElementById('waiter_ids_select');
    const title = document.getElementById('modal-title');
    
    title.innerText = `Призначити офіціантів для столика "${{tableName}}"`;
    form.action = `/admin/tables/assign_waiter/${{tableId}}`;
    select.innerHTML = ''; // Очищуємо список
    
    waiters.forEach(waiter => {{
        const option = document.createElement('option');
        option.value = waiter.id;
        option.textContent = waiter.full_name;
        // Перевіряємо, чи цей офіціант вже призначений
        if (assignedWaiterIds.includes(waiter.id)) {{
            option.selected = true;
        }}
        select.appendChild(option);
    }});
    
    modal.classList.add('active');
}}

function closeModal() {{
    document.getElementById('assign-waiter-modal').classList.remove('active');
}}

// Закриття модального вікна по кліку поза ним
window.onclick = function(event) {{
    const modal = document.getElementById('assign-waiter-modal');
    if (event.target == modal) {{
        closeModal();
    }}
}}
</script>
"""
# --- ЧАСТИНА 2: АДМІНІСТРАТИВНІ ФОРМИ ТА НАЛАШТУВАННЯ ---

ADMIN_ORDER_FORM_BODY = """
<style>
    .form-grid {{
        display: grid;
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }}
    @media (min-width: 768px) {{
        .form-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    .order-items-table .quantity-input {{
        width: 70px;
        text-align: center;
        padding: 0.5rem;
    }}
    .order-items-table .actions button {{
        background: none; border: none; color: var(--status-red);
        cursor: pointer; font-size: 1.2rem;
    }}
    .totals-summary {{
        text-align: right;
        font-size: 1.1rem;
        font-weight: 600;
    }}
    .totals-summary div {{ margin-bottom: 0.5rem; }}
    .totals-summary .total {{ font-size: 1.4rem; color: var(--primary-color); }}
    
    #product-list {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 1rem;
    }}
    .product-list-item {{
        border: 1px solid var(--border-light);
        border-radius: 0.5rem;
        padding: 1rem;
        cursor: pointer;
        transition: border-color 0.2s, box-shadow 0.2s;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .product-list-item:hover {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px #bfdbfe;
    }}
    .product-list-item h5 {{ font-size: 1rem; font-weight: 600; margin-bottom: 0.25rem;}}
    .product-list-item p {{ font-size: 0.9rem; color: #6b7280; }}
    body.dark-mode .product-list-item p {{ color: #9ca3af; }}
</style>

<div class="card">
    <form id="order-form" method="POST">
        <h3>Інформація про клієнта</h3>
        <div class="form-grid">
            <div class="form-group">
                <label for="phone_number">Номер телефону</label>
                <input type="tel" id="phone_number" placeholder="+380 (XX) XXX-XX-XX" required>
            </div>
            <div class="form-group">
                <label for="customer_name">Ім'я клієнта</label>
                <input type="text" id="customer_name" required>
            </div>
        </div>
        <div class="form-group">
            <label>Тип замовлення</label>
            <select id="delivery_type">
                <option value="delivery">Доставка</option>
                <option value="pickup">Самовивіз</option>
            </select>
        </div>
        <div class="form-group" id="address-group">
            <label for="address">Адреса доставки</label>
            <textarea id="address" rows="2"></textarea>
        </div>

        <h3>Склад замовлення</h3>
        <div class="table-wrapper">
            <table class="order-items-table">
                <thead>
                    <tr>
                        <th>Страва</th>
                        <th>Ціна</th>
                        <th>Кількість</th>
                        <th>Сума</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody id="order-items-body">
                </tbody>
            </table>
        </div>
        <div style="margin-top: 1.5rem; display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 1rem;">
            <button type="button" class="button" id="add-product-btn">
                <i class="fa-solid fa-plus"></i> Додати страву
            </button>
            <div class="totals-summary">
                <div class="total">До сплати: <span id="grand-total">0.00</span> грн</div>
            </div>
        </div>

        <div style="border-top: 1px solid var(--border-light); margin-top: 2rem; padding-top: 1.5rem; display: flex; justify-content: flex-end; gap: 1rem;">
             <a href="/admin/orders" class="button secondary">Скасувати</a>
             <button type="submit" class="button">Зберегти замовлення</button>
        </div>
    </form>
</div>

<div class="modal-overlay" id="product-modal">
    <div class="modal">
        <div class="modal-header">
            <h4>Вибір страви</h4>
            <button type="button" class="close-button" id="close-modal-btn">&times;</button>
        </div>
        <div class="modal-body">
            <div class="form-group">
                <input type="text" id="product-search-input" placeholder="Пошук страви за назвою...">
            </div>
            <div id="product-list">
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    // State
    let orderItems = {};
    let allProducts = [];

    // Element References
    const orderForm = document.getElementById('order-form');
    const orderItemsBody = document.getElementById('order-items-body');
    const grandTotalEl = document.getElementById('grand-total');
    const deliveryTypeSelect = document.getElementById('delivery_type');
    const addressGroup = document.getElementById('address-group');
    const addProductBtn = document.getElementById('add-product-btn');
    const productModal = document.getElementById('product-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const productListContainer = document.getElementById('product-list');
    const productSearchInput = document.getElementById('product-search-input');

    // API Function
    const fetchAllProducts = async () => {
        try {
            const response = await fetch('/api/admin/products');
            if (!response.ok) throw new Error('Failed to fetch products');
            return await response.json();
        } catch (error) {
            console.error("Fetch products error:", error);
            alert('Помилка мережі при завантаженні страв.');
            return [];
        }
    };

    // Core Logic
    const calculateTotals = () => {
        let currentTotal = 0;
        for (const id in orderItems) {
            currentTotal += orderItems[id].price * orderItems[id].quantity;
        }
        grandTotalEl.textContent = currentTotal.toFixed(2);
    };

    const renderOrderItems = () => {
        orderItemsBody.innerHTML = '';
        if (Object.keys(orderItems).length === 0) {
            orderItemsBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Додайте страви до замовлення</td></tr>';
        } else {
            for (const id in orderItems) {
                const item = orderItems[id];
                const row = document.createElement('tr');
                row.dataset.id = id;
                row.innerHTML = `
                    <td>${item.name}</td>
                    <td>${item.price.toFixed(2)} грн</td>
                    <td><input type="number" class="quantity-input" value="${item.quantity}" min="1" data-id="${id}"></td>
                    <td>${(item.price * item.quantity).toFixed(2)} грн</td>
                    <td class="actions"><button type="button" class="remove-item-btn" data-id="${id}">&times;</button></td>
                `;
                orderItemsBody.appendChild(row);
            }
        }
        calculateTotals();
    };

    const addProductToOrder = (product) => {
        if (orderItems[product.id]) {
            orderItems[product.id].quantity++;
        } else {
            orderItems[product.id] = { name: product.name, price: product.price, quantity: 1 };
        }
        renderOrderItems();
    };

    // Modal Logic
    const renderProductsInModal = (products) => {
        productListContainer.innerHTML = '';
        products.forEach(p => {
            const itemEl = document.createElement('div');
            itemEl.className = 'product-list-item';
            itemEl.dataset.id = p.id;
            itemEl.innerHTML = `
                <div><h5>${p.name}</h5><p>${p.category}</p></div>
                <p><strong>${p.price.toFixed(2)} грн</strong></p>`;
            productListContainer.appendChild(itemEl);
        });
    };

    const openProductModal = async () => {
        productListContainer.innerHTML = '<p>Завантаження страв...</p>';
        productModal.classList.add('active');
        if (allProducts.length === 0) {
             allProducts = await fetchAllProducts();
        }
        renderProductsInModal(allProducts);
    };

    const closeProductModal = () => {
        productModal.classList.remove('active');
        productSearchInput.value = '';
    };

    window.initializeForm = (data) => {
        if (!data) {
            console.error("Initial order data is not provided!");
            orderForm.action = '/api/admin/order/new';
            orderForm.querySelector('button[type="submit"]').textContent = 'Створити замовлення';
            orderItems = {};
            renderOrderItems();
            return;
        }

        orderForm.action = data.action;
        orderForm.querySelector('button[type="submit"]').textContent = data.submit_text;

        if (data.form_values) {
            document.getElementById('phone_number').value = data.form_values.phone_number || '';
            document.getElementById('customer_name').value = data.form_values.customer_name || '';
            document.getElementById('delivery_type').value = data.form_values.is_delivery ? "delivery" : "pickup";
            document.getElementById('address').value = data.form_values.address || '';
            deliveryTypeSelect.dispatchEvent(new Event('change'));
        }

        orderItems = data.items || {};
        renderOrderItems();
    };

    // Event Listeners
    deliveryTypeSelect.addEventListener('change', (e) => {
        addressGroup.style.display = e.target.value === 'delivery' ? 'block' : 'none';
    });

    addProductBtn.addEventListener('click', openProductModal);
    closeModalBtn.addEventListener('click', closeProductModal);
    productModal.addEventListener('click', (e) => { if (e.target === productModal) closeProductModal(); });

    productSearchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredProducts = allProducts.filter(p => p.name.toLowerCase().includes(searchTerm));
        renderProductsInModal(filteredProducts);
    });

    productListContainer.addEventListener('click', (e) => {
        const productEl = e.target.closest('.product-list-item');
        if (productEl) {
            const product = allProducts.find(p => p.id == productEl.dataset.id);
            if (product) addProductToOrder(product);
            closeProductModal();
        }
    });

    orderItemsBody.addEventListener('change', (e) => {
        if (e.target.classList.contains('quantity-input')) {
            const id = e.target.dataset.id;
            const newQuantity = parseInt(e.target.value, 10);
            if (newQuantity > 0) {
                if (orderItems[id]) orderItems[id].quantity = newQuantity;
            } else {
                 delete orderItems[id];
            }
            renderOrderItems();
        }
    });

    orderItemsBody.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-item-btn')) {
            delete orderItems[e.target.dataset.id];
            renderOrderItems();
        }
    });

    orderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const saveButton = orderForm.querySelector('button[type="submit"]');
        const originalButtonText = saveButton.textContent;
        saveButton.textContent = 'Збереження...';
        saveButton.disabled = true;

        const payload = {
            customer_name: document.getElementById('customer_name').value,
            phone_number: document.getElementById('phone_number').value,
            delivery_type: document.getElementById('delivery_type').value,
            address: document.getElementById('address').value,
            items: orderItems
        };

        try {
            const response = await fetch(orderForm.action, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                window.location.href = result.redirect_url || '/admin/orders';
            } else {
                alert(`Помилка: ${result.detail || 'Невідома помилка'}`);
                saveButton.textContent = originalButtonText;
                saveButton.disabled = false;
            }
        } catch (error) {
            console.error("Submit error:", error);
            alert('Помилка мережі. Не вдалося зберегти замовлення.');
            saveButton.textContent = originalButtonText;
            saveButton.disabled = false;
        }
    });

    if (typeof window.initializeForm === 'function' && !window.initializeForm.invoked) {
        const newOrderData = {
             items: {},
             action: '/api/admin/order/new',
             submit_text: 'Створити замовлення',
             form_values: null
        };
        window.initializeForm(newOrderData);
        window.initializeForm.invoked = true;
    }
});
</script>
"""

ADMIN_EMPLOYEE_BODY = """
<div class="card">
    <ul class="nav-tabs">
        <li class="nav-item"><a href="/admin/employees" class="active">Співробітники</a></li>
        <li class="nav-item"><a href="/admin/roles">Ролі</a></li>
    </ul>
    <h2>👤 Додати співробітника</h2>
    <form action="/admin/add_employee" method="post">
        <label for="full_name">Повне ім'я:</label><input type="text" id="full_name" name="full_name" required>
        <label for="phone_number">Номер телефону (для авторизації):</label><input type="text" id="phone_number" name="phone_number" placeholder="+380XX XXX XX XX" required>
        <label for="role_id">Роль:</label><select id="role_id" name="role_id" required>{role_options}</select>
        
        <label for="password">Пароль для входу (PWA):</label>
        <input type="text" id="password" name="password" placeholder="Введіть пароль">
        
        <button type="submit">Додати співробітника</button>
    </form>
</div>
<div class="card">
    <h2>👥 Список співробітників</h2>
    <p>🟢 - На зміні (авторизований)</p>
    <table><thead><tr><th>ID</th><th>Ім'я</th><th>Телефон</th><th>Роль</th><th>Статус</th><th>Telegram ID</th><th>Дії</th></tr></thead><tbody>
    {rows}
    </tbody></table>
</div>
"""

ADMIN_ROLES_BODY = """
<div class="card">
    <ul class="nav-tabs">
        <li class="nav-item"><a href="/admin/employees">Співробітники</a></li>
        <li class="nav-item"><a href="/admin/roles" class="active">Ролі</a></li>
    </ul>
    <h2>Додати нову роль</h2>
    <form action="/admin/add_role" method="post">
        <label for="name">Назва ролі:</label><input type="text" id="name" name="name" required>
        <div class="checkbox-group">
            <input type="checkbox" id="can_manage_orders" name="can_manage_orders" value="true">
            <label for="can_manage_orders">Може керувати замовленнями (Оператор)</label>
        </div>
        <div class="checkbox-group">
            <input type="checkbox" id="can_be_assigned" name="can_be_assigned" value="true">
            <label for="can_be_assigned">Може бути призначений на замовлення (Кур'єр)</label>
        </div>
        <div class="checkbox-group">
            <input type="checkbox" id="can_serve_tables" name="can_serve_tables" value="true">
            <label for="can_serve_tables">Може обслуговувати столики (Офіціант)</label>
        </div>
        <div class="checkbox-group">
            <input type="checkbox" id="can_receive_kitchen_orders" name="can_receive_kitchen_orders" value="true">
            <label for="can_receive_kitchen_orders">Отримує замовлення для приготування (Повар)</label>
        </div>
        <div class="checkbox-group">
            <input type="checkbox" id="can_receive_bar_orders" name="can_receive_bar_orders" value="true">
            <label for="can_receive_bar_orders">Отримує замовлення для бару (Бармен)</label> 
        </div>
        <button type="submit">Додати роль</button>
    </form>
</div>
<div class="card">
    <h2>Список ролей</h2>
    <table><thead><tr><th>ID</th><th>Назва</th><th>Керув. замовл.</th><th>Признач. доставку</th><th>Обслуг. столики</th><th>Кухня</th><th>Бар</th><th>Дії</th></tr></thead><tbody>
    {rows}
    </tbody></table>
</div>
"""

ADMIN_REPORTS_BODY = """
<div class="card">
    <h2>📊 Выбор отчета</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <a href="/admin/reports/cash_flow" class="report-link-card" style="display:block; padding:20px; background: #e3f2fd; border-radius:8px; text-decoration:none; color:#333; border:1px solid #90caf9;">
            <i class="fa-solid fa-money-bill-trend-up" style="font-size: 2em; color: #1976d2; margin-bottom:10px;"></i>
            <h3 style="margin:0;">Движение средств</h3>
            <p style="color:#666; font-size:0.9em;">Выручка, расходы, наличные и безнал.</p>
        </a>
        
        <a href="/admin/reports/workers" class="report-link-card" style="display:block; padding:20px; background: #fff3e0; border-radius:8px; text-decoration:none; color:#333; border:1px solid #ffcc80;">
            <i class="fa-solid fa-users-gear" style="font-size: 2em; color: #f57c00; margin-bottom:10px;"></i>
            <h3 style="margin:0;">Эффективность персонала</h3>
            <p style="color:#666; font-size:0.9em;">KPI сотрудников, количество заказов, продажи.</p>
        </a>

        <a href="/admin/reports/analytics" class="report-link-card" style="display:block; padding:20px; background: #e8f5e9; border-radius:8px; text-decoration:none; color:#333; border:1px solid #a5d6a7;">
            <i class="fa-solid fa-chart-column" style="font-size: 2em; color: #388e3c; margin-bottom:10px;"></i>
            <h3 style="margin:0;">Аналитика продаж</h3>
            <p style="color:#666; font-size:0.9em;">Топ блюд, категории.</p>
        </a>
        
        <a href="/admin/reports/couriers" class="report-link-card" style="display:block; padding:20px; background: #f3e5f5; border-radius:8px; text-decoration:none; color:#333; border:1px solid #ce93d8;">
            <i class="fa-solid fa-truck-fast" style="font-size: 2em; color: #8e24aa; margin-bottom:10px;"></i>
            <h3 style="margin:0;">Отчет по курьерам</h3>
            <p style="color:#666; font-size:0.9em;">Старый отчет по доставкам.</p>
        </a>
    </div>
</div>
"""

ADMIN_SETTINGS_BODY = """
<div class="card">
    <form action="/admin/settings" method="post" enctype="multipart/form-data">
        <h2>⚙️ Основні налаштування</h2>
        
        <h3>Зовнішній вигляд</h3>
        <label>Логотип (завантажте новий, щоб замінити):</label>
        <input type="file" name="logo_file" accept="image/*">
        {current_logo_html}

        <h3 style="margin-top: 2rem;">Налаштування Favicon</h3>
        <p>Завантажте необхідні файли favicon. Після завантаження оновіть сторінку (Ctrl+F5), щоб побачити зміни.</p>
        <h4>Поточні іконки</h4>
        <div style="display: flex; gap: 20px; align-items: center; flex-wrap: wrap; margin-bottom: 2rem; background: #f0f0f0; padding: 1rem; border-radius: 8px;">
            <div><img src="/static/favicons/favicon-16x16.png?v={cache_buster}" alt="16x16" style="border: 1px solid #ccc;"><br><small>16x16</small></div>
            <div><img src="/static/favicons/favicon-32x32.png?v={cache_buster}" alt="32x32" style="border: 1px solid #ccc;"><br><small>32x32</small></div>
            <div><img src="/static/favicons/apple-touch-icon.png?v={cache_buster}" alt="Apple Touch Icon" style="width: 60px; height: 60px; border: 1px solid #ccc;"><br><small>Apple Icon</small></div>
        </div>

        <h4>Завантажити нові іконки</h4>
        <div class="form-grid" style="grid-template-columns: 1fr;">
            <div class="form-group"><label for="apple_touch_icon">apple-touch-icon.png (180x180)</label><input type="file" id="apple_touch_icon" name="apple_touch_icon" accept="image/png"></div>
            <div class="form-group"><label for="favicon_32x32">favicon-32x32.png</label><input type="file" id="favicon_32x32" name="favicon_32x32" accept="image/png"></div>
            <div class="form-group"><label for="favicon_16x16">favicon-16x16.png</label><input type="file" id="favicon_16x16" name="favicon_16x16" accept="image/png"></div>
            <div class="form-group"><label for="favicon_ico">favicon.ico (всі розміри)</label><input type="file" id="favicon_ico" name="favicon_ico" accept="image/x-icon"></div>
            <div class="form-group"><label for="site_webmanifest">site.webmanifest</label><input type="file" id="site_webmanifest" name="site_webmanifest" accept="application/manifest+json"></div>
        </div>
        
        <div style="margin-top: 2rem;">
            <button type="submit">Зберегти всі налаштування</button>
        </div>
    </form>
</div>
"""

ADMIN_MENU_BODY = """
<div class="card">
    <h2>{form_title}</h2>
    <form action="{form_action}" method="post">
        <label for="title">Заголовок (текст на кнопці):</label>
        <input type="text" id="title" name="title" value="{item_title}" required>
        
        <label for="content">Зміст сторінки (можна використовувати HTML-теги):</label>
        <textarea id="content" name="content" rows="10" required>{item_content}</textarea>
        
        <label for="sort_order">Порядок сортування (менше = вище):</label>
        <input type="number" id="sort_order" name="sort_order" value="{item_sort_order}" required>
        
        <div class="checkbox-group">
            <input type="checkbox" id="show_on_website" name="show_on_website" value="true" {item_show_on_website_checked}>
            <label for="show_on_website">Показувати на сайті</label>
        </div>
        <div class="checkbox-group">
            <input type="checkbox" id="show_in_telegram" name="show_in_telegram" value="true" {item_show_in_telegram_checked}>
            <label for="show_in_telegram">Показувати в Telegram-боті</label>
        </div>
        
        <button type="submit">{button_text}</button>
        <a href="/admin/menu" class="button secondary">Скасувати</a>
    </form>
</div>
<div class="card">
    <h2>📜 Список сторінок</h2>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Заголовок</th>
                    <th>Сортування</th>
                    <th>На сайті</th>
                    <th>В Telegram</th>
                    <th>Дії</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
</div>
"""

ADMIN_ORDER_MANAGE_BODY = """
<style>
    .manage-grid {{
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 2rem;
    }}
    .order-details-card .detail-item {{
        display: flex;
        justify-content: space-between;
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--border-light);
    }}
    .order-details-card .detail-item:last-child {{
        border-bottom: none;
    }}
    .order-details-card .detail-item strong {{
        color: #6b7280;
    }}
    body.dark-mode .order-details-card .detail-item strong {{
        color: #9ca3af;
    }}
    .status-history {{
        list-style-type: none;
        padding-left: 1rem;
        border-left: 2px solid var(--border-light);
    }}
    .status-history li {{
        margin-bottom: 0.75rem;
        position: relative;
        font-size: 0.9rem;
    }}
    .status-history li::before {{
        content: '✓';
        position: absolute;
        left: -1.1rem;
        top: 2px;
        color: var(--primary-color);
        font-weight: 900;
    }}
    @media (max-width: 992px) {{
        .manage-grid {{
            grid-template-columns: 1fr;
        }}
    }}
</style>
<div class="manage-grid">
    <div class="left-column">
        <div class="card order-details-card">
            <h2>Деталі замовлення #{order_id}</h2>
            <div class="detail-item">
                <strong>Клієнт:</strong>
                <span>{customer_name}</span>
            </div>
            <div class="detail-item">
                <strong>Телефон:</strong>
                <span>{phone_number}</span>
            </div>
            <div class="detail-item">
                <strong>Адреса:</strong>
                <span>{address}</span>
            </div>
             <div class="detail-item">
                <strong>Сума:</strong>
                <span>{total_price} грн</span>
            </div>
            <div class="detail-item">
                <strong>Оплата:</strong>
                <span>{payment_method_text}</span>
            </div>
            <div class="detail-item" style="flex-direction: column; align-items: start;">
                <strong style="margin-bottom: 0.5rem;">Склад замовлення:</strong>
                <div>{products_html}</div>
            </div>
        </div>
        <div class="card">
            <h2>Історія статусів</h2>
            {history_html}
        </div>
    </div>
    <div class="right-column">
        <div class="card">
            <h2>Керування статусом</h2>
            <form action="/admin/order/manage/{order_id}/set_status" method="post">
                <label for="status_id">Новий статус:</label>
                <select name="status_id" id="status_id" required>
                    {status_options}
                </select>
                
                <label for="payment_method" style="margin-top:10px;">Метод оплати (для каси):</label>
                <select name="payment_method" id="payment_method">
                    <option value="cash" {sel_cash}>💵 Готівка</option>
                    <option value="card" {sel_card}>💳 Картка / Термінал</option>
                </select>

                <button type="submit" style="margin-top:15px;">Зберегти зміни</button>
            </form>
        </div>
        <div class="card">
            <h2>Призначення кур'єра</h2>
            <form action="/admin/order/manage/{order_id}/assign_courier" method="post">
                <label for="courier_id">Кур'єр (на зміні):</label>
                <select name="courier_id" id="courier_id" required>
                    {courier_options}
                </select>
                <button type="submit">Призначити кур'єра</button>
            </form>
        </div>
    </div>
</div>
"""

ADMIN_CLIENTS_LIST_BODY = """
<div class="card">
    <h2><i class="fa-solid fa-users-line"></i> Список клієнтів</h2>
    <form action="/admin/clients" method="get" class="search-form">
        <input type="text" name="search" placeholder="Пошук за іменем або телефоном..." value="{search_query}">
        <button type="submit">🔍 Знайти</button>
    </form>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>Ім'я</th>
                    <th>Телефон</th>
                    <th>Всього замовлень</th>
                    <th>Загальна сума</th>
                    <th>Дії</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    {pagination}
</div>
"""

ADMIN_CLIENT_DETAIL_BODY = """
<style>
    .client-info-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }}
    .info-block {{
        background-color: var(--bg-light);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--border-light);
    }}
    .info-block h4 {{
        font-size: 0.9rem;
        color: #6b7280;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}
    .info-block p {{
        font-size: 1.1rem;
        font-weight: 600;
    }}
    .order-summary-row {{
        cursor: pointer;
    }}
    .order-summary-row:hover {{
        background-color: #f3f4f6;
    }}
    body.dark-mode .order-summary-row:hover {{
        background-color: #374151;
    }}
    .order-details-row {{
        display: none;
    }}
    .details-content {{
        padding: 1.5rem;
        background-color: var(--bg-light);
    }}
    .status-history {{
        list-style-type: none;
        padding-left: 1rem;
        border-left: 2px solid var(--border-light);
    }}
    .status-history li {{
        margin-bottom: 0.5rem;
        position: relative;
    }}
    .status-history li::before {{
        content: '✓';
        position: absolute;
        left: -1.1rem;
        top: 2px;
        color: var(--primary-color);
        font-weight: 900;
    }}
</style>
<div class="card">
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <i class="fa-solid fa-user-circle" style="font-size: 3rem;"></i>
        <div>
            <h2 style="margin-bottom: 0;">{client_name}</h2>
            <a href="tel:{phone_number}">{phone_number}</a>
        </div>
    </div>
    <div class="client-info-grid">
        <div class="info-block">
            <h4>Остання адреса</h4>
            <p>{address}</p>
        </div>
        <div class="info-block">
            <h4>Всього замовлень</h4>
            <p>{total_orders}</p>
        </div>
        <div class="info-block">
            <h4>Загальна сума</h4>
            <p>{total_spent} грн</p>
        </div>
    </div>
</div>
<div class="card">
    <h3>Історія замовлень</h3>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Дата</th>
                    <th>Статус</th>
                    <th>Сума</th>
                    <th>Доставив</th>
                    <th>Деталі</th>
                </tr>
            </thead>
            <tbody>
                {order_rows}
            </tbody>
        </table>
    </div>
</div>
<script>
    function toggleDetails(row) {{
        const detailsRow = row.nextElementSibling;
        const icon = row.querySelector('i');
        if (detailsRow.style.display === 'table-row') {{
            detailsRow.style.display = 'none';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }} else {{
            detailsRow.style.display = 'table-row';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        }}
    }}
</script>
"""

ADMIN_DESIGN_SETTINGS_BODY = """
<div class="card">
    <form action="/admin/design_settings" method="post" enctype="multipart/form-data">
        <h2><i class="fa-solid fa-file-signature"></i> Назви та SEO</h2>
        
        <label for="site_title">Назва сайту/закладу:</label>
        <input type="text" id="site_title" name="site_title" value="{site_title}" placeholder="Назва, що відображається на сайті та в адмін-панелі">
        
        <label for="seo_description">SEO Опис (Description):</label>
        <textarea id="seo_description" name="seo_description" rows="3" placeholder="Короткий опис для пошукових систем (до 160 символів)">{seo_description}</textarea>
        
        <label for="seo_keywords">SEO Ключові слова (Keywords):</label>
        <input type="text" id="seo_keywords" name="seo_keywords" value="{seo_keywords}" placeholder="Наприклад: доставка їжі, ресторан, назва">

        <h2 style="margin-top: 2rem;"><i class="fa-solid fa-palette"></i> Дизайн та Кольори</h2>
        
        <div class="form-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">
            <div>
                <label for="primary_color">Основний колір (Акцент):</label>
                <input type="color" id="primary_color" name="primary_color" value="{primary_color}" style="width: 100%; height: 40px;">
            </div>
            <div>
                <label for="secondary_color">Додатковий колір:</label>
                <input type="color" id="secondary_color" name="secondary_color" value="{secondary_color}" style="width: 100%; height: 40px;">
            </div>
            <div>
                <label for="background_color">Колір фону сторінки:</label>
                <input type="color" id="background_color" name="background_color" value="{background_color}" style="width: 100%; height: 40px;">
            </div>
            <div>
                <label for="text_color">Колір основного тексту:</label>
                <input type="color" id="text_color" name="text_color" value="{text_color}" style="width: 100%; height: 40px;">
            </div>
            <div>
                <label for="footer_bg_color">Фон підвалу (Footer):</label>
                <input type="color" id="footer_bg_color" name="footer_bg_color" value="{footer_bg_color}" style="width: 100%; height: 40px;">
            </div>
            <div>
                <label for="footer_text_color">Текст підвалу:</label>
                <input type="color" id="footer_text_color" name="footer_text_color" value="{footer_text_color}" style="width: 100%; height: 40px;">
            </div>
        </div>
        
        <h3 style="margin-top: 1rem;">Навігація по категоріям</h3>
        <div class="form-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">
            <div>
                <label for="category_nav_bg_color">Колір фону (можна прозорий):</label>
                <input type="color" id="category_nav_bg_color" name="category_nav_bg_color" value="{category_nav_bg_color}" style="width: 100%; height: 40px;">
            </div>
            <div>
                <label for="category_nav_text_color">Колір тексту посилань:</label>
                <input type="color" id="category_nav_text_color" name="category_nav_text_color" value="{category_nav_text_color}" style="width: 100%; height: 40px;">
            </div>
        </div>
        
        <h3 style="margin-top: 2rem;">Зображення Шапки (Header)</h3>
        <label>Завантажте фонове зображення для шапки (Overlay буде додано автоматично):</label>
        <input type="file" name="header_image_file" accept="image/*">
        
        <div style="margin-top: 1rem;">
            <label for="font_family_sans">Основний шрифт (Без засічок):</label>
            <select id="font_family_sans" name="font_family_sans">
                {font_options_sans}
            </select>
            
            <label for="font_family_serif">Шрифт заголовків (Із засічками):</label>
            <select id="font_family_serif" name="font_family_serif">
                {font_options_serif}
            </select>
        </div>

        <h2 style="margin-top: 2rem;"><i class="fa-solid fa-circle-info"></i> Підвал сайту (Контакти)</h2>
        <div class="form-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <label for="footer_address"><i class="fa-solid fa-location-dot"></i> Адреса:</label>
                <input type="text" id="footer_address" name="footer_address" value="{footer_address}" placeholder="вул. Прикладна, 10">
            </div>
            <div>
                <label for="footer_phone"><i class="fa-solid fa-phone"></i> Телефон:</label>
                <input type="text" id="footer_phone" name="footer_phone" value="{footer_phone}" placeholder="+380 XX XXX XX XX">
            </div>
            <div>
                <label for="working_hours"><i class="fa-solid fa-clock"></i> Час роботи:</label>
                <input type="text" id="working_hours" name="working_hours" value="{working_hours}" placeholder="Пн-Нд: 10:00 - 22:00">
            </div>
        </div>
        
        <h4 style="margin-top: 1rem;">Налаштування Wi-Fi (для QR меню)</h4>
        <div class="form-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <label for="wifi_ssid"><i class="fa-solid fa-wifi"></i> Назва мережі (SSID):</label>
                <input type="text" id="wifi_ssid" name="wifi_ssid" value="{wifi_ssid}" placeholder="Restaurant_WiFi">
            </div>
            <div>
                <label for="wifi_password"><i class="fa-solid fa-lock"></i> Пароль:</label>
                <input type="text" id="wifi_password" name="wifi_password" value="{wifi_password}" placeholder="securepass123">
            </div>
        </div>

        <div class="form-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px;">
            <div>
                <label for="instagram_url"><i class="fa-brands fa-instagram"></i> Instagram (посилання):</label>
                <input type="text" id="instagram_url" name="instagram_url" value="{instagram_url}" placeholder="https://instagram.com/...">
            </div>
            <div>
                <label for="facebook_url"><i class="fa-brands fa-facebook"></i> Facebook (посилання):</label>
                <input type="text" id="facebook_url" name="facebook_url" value="{facebook_url}" placeholder="https://facebook.com/...">
            </div>
        </div>
        
        <h2 style="margin-top: 2rem;"><i class="fa-brands fa-telegram"></i> Тексти Telegram-бота</h2>
        
        <label for="telegram_welcome_message">Привітальне повідомлення (Клієнт-бот):</label>
        <textarea id="telegram_welcome_message" name="telegram_welcome_message" rows="5" placeholder="Текст, який бачить користувач при старті бота.">{telegram_welcome_message}</textarea>
        <p style="font-size: 0.8rem; margin-top: -0.5rem; margin-bottom: 1rem;">Використовуйте <code>{{user_name}}</code>, щоб вставити ім'я користувача.</p>

        <div style="margin-top: 2rem;">
            <button type="submit">Зберегти налаштування</button>
        </div>
    </form>
</div>
"""
ADMIN_REPORT_CASH_FLOW_BODY = """
<div class="card">
    <h2>💰 Отчет о движении денежных средств</h2>
    <form action="/admin/reports/cash_flow" method="get" class="search-form" style="background: #f9f9f9; padding: 15px; border-radius: 8px;">
        <label>Период:</label>
        <input type="date" name="date_from" value="{date_from}" required>
        <span>—</span>
        <input type="date" name="date_to" value="{date_to}" required>
        <button type="submit">Показать</button>
    </form>
</div>

<div class="card">
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">
        <div style="background:#e8f5e9; padding:15px; border-radius:5px;">
            <small>Общая выручка</small>
            <div style="font-size:1.4em; font-weight:bold; color:#2e7d32;">{total_revenue} грн</div>
        </div>
        <div style="background:#fff3e0; padding:15px; border-radius:5px;">
            <small>Наличные</small>
            <div style="font-size:1.4em; font-weight:bold; color:#ef6c00;">{cash_revenue} грн</div>
        </div>
        <div style="background:#e3f2fd; padding:15px; border-radius:5px;">
            <small>Карта / Терминал</small>
            <div style="font-size:1.4em; font-weight:bold; color:#1565c0;">{card_revenue} грн</div>
        </div>
        <div style="background:#ffebee; padding:15px; border-radius:5px;">
            <small>Расходы (Изъятия)</small>
            <div style="font-size:1.4em; font-weight:bold; color:#c62828;">{total_expenses} грн</div>
        </div>
    </div>

    <h3>Детализация транзакций (Служебные)</h3>
    <table>
        <thead><tr><th>Дата</th><th>Тип</th><th>Сумма</th><th>Кассир</th><th>Комментарий</th></tr></thead>
        <tbody>{transaction_rows}</tbody>
    </table>
</div>
"""

ADMIN_REPORT_WORKERS_BODY = """
<div class="card">
    <h2>👥 Отчет по сотрудникам</h2>
    <form action="/admin/reports/workers" method="get" class="search-form" style="background: #f9f9f9; padding: 15px; border-radius: 8px;">
        <label>Период:</label>
        <input type="date" name="date_from" value="{date_from}" required>
        <span>—</span>
        <input type="date" name="date_to" value="{date_to}" required>
        <button type="submit">Показать</button>
    </form>
</div>

<div class="card">
    <table>
        <thead>
            <tr>
                <th>Сотрудник</th>
                <th>Роль</th>
                <th>Кол-во заказов</th>
                <th>Общая сумма продаж</th>
                <th>Средний чек</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</div>
"""

ADMIN_REPORT_ANALYTICS_BODY = """
<div class="card">
    <h2>📈 Аналитика продаж (Топ блюд)</h2>
    <form action="/admin/reports/analytics" method="get" class="search-form" style="background: #f9f9f9; padding: 15px; border-radius: 8px;">
        <label>Период:</label>
        <input type="date" name="date_from" value="{date_from}" required>
        <span>—</span>
        <input type="date" name="date_to" value="{date_to}" required>
        <button type="submit">Показать</button>
    </form>
</div>

<div class="card">
    <h3>Топ популярных позиций</h3>
    <table>
        <thead>
            <tr>
                <th>№</th>
                <th>Название блюда</th>
                <th>Продано (шт)</th>
                <th>Выручка (грн)</th>
                <th>Доля выручки</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</div>
"""
# --- ЧАСТИНА 3: КЛІЄНТСЬКЕ QR-МЕНЮ (IN-HOUSE) ---

IN_HOUSE_MENU_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_title} - {table_name}</title>
    <meta name="description" content="{seo_description}">
    <meta name="keywords" content="{seo_keywords}">
    <meta name="robots" content="noindex, nofollow">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family={font_family_serif_encoded}:wght@400;700&family={font_family_sans_encoded}:wght@400;600&display=swap" rel="stylesheet">
    
    <style>
      :root {{
        --primary-color: {primary_color_val};
        --secondary-color: {secondary_color_val};
        --background-color: {background_color_val};
        --text-color: {text_color_val};
        --footer-bg-color: {footer_bg_color_val};
        --footer-text-color: {footer_text_color_val};
        --nav-bg-color: {category_nav_bg_color};
        --nav-text-color: {category_nav_text_color};
        --header-bg-image: url('/{header_image_url}');
        --primary-hover-color: color-mix(in srgb, {primary_color_val}, black 10%);
        --primary-glow-color: {primary_color_val}26;
      }}
      
      body, .category-nav a, .add-to-cart-btn, .action-btn, #checkout-form, .radio-group label {{
        font-family: '{font_family_sans_val}', sans-serif;
      }}
      header h1, .category-title, .product-name, .product-price, .cart-header h2, .modal-content h2 {{
        font-family: '{font_family_serif_val}', serif;
      }}
      
      /* Основні стилі */
      body {{ margin: 0; background-color: var(--background-color); color: var(--text-color); display: flex; flex-direction: column; min-height: 100vh; }}
      .container {{ width: 100%; margin: 0 auto; padding: 0; }}
      
      /* HEADER */
      header {{ 
          text-align: center; padding: 60px 20px 40px; position: relative;
          background-image: var(--header-bg-image); background-size: cover; background-position: center;
          color: white;
      }}
      header::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 0; }}
      .header-logo-container, header h1, header h2, header p {{ position: relative; z-index: 1; }}
      .header-logo {{ height: 100px; width: auto; margin-bottom: 25px; }}
      header h1 {{ font-size: clamp(2.5em, 5vw, 3.5em); margin: 0; font-weight: 700; }}
      .table-name-header {{ font-size: 1.2em; margin-top: 10px; opacity: 0.9; }}

      /* MENU GRID */
      .category-nav {{ display: flex; position: sticky; top: -1px; background: var(--nav-bg-color); backdrop-filter: blur(12px); z-index: 100; overflow-x: auto; padding: 15px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
      .category-nav a {{ color: var(--nav-text-color); text-decoration: none; padding: 8px 20px; border-radius: 20px; margin: 0 5px; white-space: nowrap; transition: all 0.2s; background: rgba(0,0,0,0.05); }}
      .category-nav a.active {{ background: var(--primary-color); color: white; }}
      .category-nav a:first-child {{ margin-left: 20px; }}
      
      #menu {{ padding: 20px; display: grid; gap: 40px; }}
      .category-title {{ text-align: center; color: var(--primary-color); margin-bottom: 20px; font-size: 2em; border-bottom: 1px solid var(--secondary-color); padding-bottom: 10px; }}
      .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; }}
      @media(min-width: 768px) {{ .products-grid {{ grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 25px; }} }}

      .product-card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: flex; flex-direction: column; }}
      .product-image-wrapper {{ width: 100%; aspect-ratio: 4/3; overflow: hidden; }}
      .product-image {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }}
      .product-info {{ padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }}
      .product-name {{ font-size: 1.1em; font-weight: 700; margin: 0 0 5px; color: #333; }}
      .product-desc {{ font-size: 0.85em; color: #666; margin-bottom: 15px; flex-grow: 1; line-height: 1.4; }}
      .product-footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: auto; }}
      .product-price {{ font-weight: 700; color: var(--primary-color); font-size: 1.1em; }}
      .add-to-cart-btn {{ background: var(--primary-color); color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s; }}
      .add-to-cart-btn:hover {{ background: var(--primary-hover-color); }}

      /* MODALS */
      .modal-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 3000; display: none; justify-content: center; align-items: flex-end; backdrop-filter: blur(3px); }}
      .modal-overlay.active {{ display: flex; animation: fadeIn 0.2s; }}
      @media(min-width: 768px) {{ .modal-overlay {{ align-items: center; }} }}
      
      .modal {{ background: white; width: 100%; max-width: 500px; border-radius: 20px 20px 0 0; padding: 20px; max-height: 85vh; display: flex; flex-direction: column; position: relative; box-shadow: 0 -5px 30px rgba(0,0,0,0.2); animation: slideUp 0.3s; }}
      @media(min-width: 768px) {{ .modal {{ border-radius: 20px; max-height: 80vh; animation: zoomIn 0.2s; }} }}
      
      @keyframes slideUp {{ from {{ transform: translateY(100%); }} to {{ transform: translateY(0); }} }}
      @keyframes zoomIn {{ from {{ transform: scale(0.9); opacity: 0; }} to {{ transform: scale(1); opacity: 1; }} }}
      @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

      .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
      .modal-header h3 {{ margin: 0; font-size: 1.3em; color: #333; }}
      .close-button {{ background: none; border: none; font-size: 1.5em; cursor: pointer; color: #999; }}
      
      .modifier-group {{ margin-bottom: 20px; overflow-y: auto; padding-right: 5px; }}
      .modifier-item {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee; cursor: pointer; }}
      .modifier-item:last-child {{ border-bottom: none; }}
      .modifier-info {{ display: flex; align-items: center; gap: 10px; }}
      .checkbox-custom {{ width: 20px; height: 20px; border: 2px solid #ddd; border-radius: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }}
      .modifier-input:checked + .modifier-label .checkbox-custom {{ background: var(--primary-color); border-color: var(--primary-color); }}
      .checkbox-custom::after {{ content: '✓'; color: white; font-size: 14px; display: none; }}
      .modifier-input:checked + .modifier-label .checkbox-custom::after {{ display: block; }}
      
      .modal-footer {{ margin-top: auto; padding-top: 15px; border-top: 1px solid #eee; }}
      .modal-add-btn {{ width: 100%; background: var(--primary-color); color: white; border: none; padding: 15px; border-radius: 12px; font-size: 1.1em; font-weight: bold; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 10px; }}
      
      /* SIDEBARS (CART & HISTORY) */
      .sidebar-panel {{ position: fixed; top: 0; right: -100%; width: 100%; max-width: 400px; height: 100%; background: white; z-index: 2000; transition: right 0.3s; display: flex; flex-direction: column; box-shadow: -5px 0 30px rgba(0,0,0,0.1); }}
      .sidebar-panel.open {{ right: 0; }}
      
      /* HISTORY SIDEBAR SPECIFIC (LEFT SIDE) */
      #history-sidebar {{ right: auto; left: -100%; border-right: 1px solid #eee; transition: left 0.3s; }}
      #history-sidebar.open {{ left: 0; }}

      .sidebar-header {{ padding: 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; background: var(--background-color); }}
      .sidebar-content {{ flex-grow: 1; overflow-y: auto; padding: 20px; }}
      
      .cart-item {{ display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee; }}
      .cart-item-details {{ flex-grow: 1; }}
      .cart-item-title {{ font-weight: bold; display: block; margin-bottom: 4px; color: #333; }}
      .cart-item-mods {{ font-size: 0.85em; color: #666; display: block; margin-bottom: 5px; }}
      .cart-item-price {{ color: var(--primary-color); font-weight: 600; }}
      .cart-controls {{ display: flex; align-items: center; gap: 10px; }}
      .qty-btn {{ width: 28px; height: 28px; border-radius: 50%; border: 1px solid #ddd; background: white; cursor: pointer; display: flex; align-items: center; justify-content: center; }}

      /* HISTORY ITEMS */
      .history-item {{ padding: 15px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 15px; background-color: #f9f9f9; }}
      .history-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.9em; color: #777; }}
      .history-products {{ font-weight: 500; margin-bottom: 10px; line-height: 1.4; color: #333; }}
      .history-footer {{ display: flex; justify-content: space-between; font-weight: 700; color: var(--primary-color); }}
      
      .sidebar-footer {{ padding: 20px; background: white; border-top: 1px solid #eee; }}
      .total-row {{ display: flex; justify-content: space-between; font-size: 1.1em; font-weight: 700; margin-bottom: 10px; color: #333; }}
      .total-row.final {{ font-size: 1.3em; color: var(--primary-color); margin-top: 10px; padding-top: 10px; border-top: 1px dashed #ddd; }}

      /* FAB BUTTONS */
      .fab {{ position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; border-radius: 50%; background: var(--primary-color); color: white; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); cursor: pointer; z-index: 1000; transition: transform 0.2s; }}
      .fab:active {{ transform: scale(0.95); }}
      .fab-badge {{ position: absolute; top: -5px; right: -5px; background: #e74c3c; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 0.8em; font-weight: bold; border: 2px solid white; }}
      
      .history-btn {{ left: 20px; right: auto; background: white; color: var(--primary-color); }}
      
      /* TOAST & SPINNERS */
      .toast {{ position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%) translateY(20px); background: #333; color: white; padding: 12px 24px; border-radius: 50px; opacity: 0; transition: all 0.3s; pointer-events: none; z-index: 5000; }}
      .toast.show {{ transform: translateX(-50%) translateY(0); opacity: 1; }}
      
      .btn-spinner {{ display: none; border: 2px solid rgba(255,255,255,0.3); border-top: 2px solid white; border-radius: 50%; width: 16px; height: 16px; animation: spin 0.8s linear infinite; margin-right: 8px; }}
      @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
      .working .btn-spinner {{ display: inline-block; }}
      
      /* PAYMENT MODAL OPTIONS */
      .payment-options {{ display: grid; gap: 15px; margin-top: 10px; }}
      .payment-option-btn {{ width: 100%; padding: 18px; border: none; border-radius: 12px; font-size: 1.1rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 12px; color: white; background: var(--primary-color); transition: opacity 0.2s; }}
      .payment-option-btn:hover {{ opacity: 0.9; }}
    </style>
</head>
<body>
    <header>
        <div class="header-logo-container">{logo_html}</div>
        <h1>{site_title}</h1>
        <div class="table-name-header">{table_name}</div>
    </header>

    <div class="container">
        <nav class="category-nav" id="category-nav"></nav>
        <div id="menu"></div>
    </div>
    
    <div style="height: 100px;"></div>

    <div class="fab history-btn" id="history-toggle" title="Історія та Рахунок">
        <i class="fa-solid fa-clock-rotate-left" style="font-size: 1.4em;"></i>
    </div>
    
    <div class="fab" id="cart-toggle" title="Кошик">
        <i class="fa-solid fa-basket-shopping" style="font-size: 1.4em;"></i>
        <div class="fab-badge" id="cart-count" style="display:none;">0</div>
    </div>

    <div class="modal-overlay" id="modifier-modal">
        <div class="modal">
            <div class="modal-header">
                <h3 id="modal-product-name">Назва товару</h3>
                <button class="close-button" id="close-mod-modal">&times;</button>
            </div>
            <div class="modifier-group" id="modal-modifiers-list">
                </div>
            <div class="modal-footer">
                <button class="modal-add-btn" id="modal-add-btn">
                    <span>Додати в кошик</span>
                    <span id="modal-total-price">0 грн</span>
                </button>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="payment-modal">
        <div class="modal" style="height: auto;">
            <div class="modal-header">
                <h3>💳 Спосіб оплати</h3>
                <button class="close-button" id="close-pay-modal">&times;</button>
            </div>
            <div class="modal-body">
                <p style="margin-bottom: 20px; color: #666; text-align: center;">Як ви бажаєте розрахуватись?</p>
                <div class="payment-options">
                    <button class="payment-option-btn confirm-payment-btn" data-method="cash">
                        <i class="fa-solid fa-money-bill-wave"></i> Готівка
                    </button>
                    <button class="payment-option-btn confirm-payment-btn" data-method="card">
                        <i class="fa-regular fa-credit-card"></i> Картка / Термінал
                    </button>
                </div>
            </div>
        </div>
    </div>

    <div id="cart-sidebar" class="sidebar-panel">
        <div class="sidebar-header">
            <h2>Ваше замовлення</h2>
            <button class="close-button" id="close-cart">&times;</button>
        </div>
        <div class="sidebar-content" id="cart-items">
            </div>
        <div class="sidebar-footer">
            <div class="total-row">
                <span>Разом:</span>
                <span id="cart-total">0.00 грн</span>
            </div>
            <button class="modal-add-btn" id="place-order-btn">
                <div class="btn-spinner"></div>
                <span>Замовити</span>
            </button>
            <div style="margin-top: 15px;">
                 <button class="action-btn" id="call-waiter-btn" style="width:100%; padding: 12px; background: #f5f5f5; border: none; border-radius: 12px; color: #555; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-bell"></i> Викликати офіціанта
                </button>
            </div>
        </div>
    </div>
    
    <div id="history-sidebar" class="sidebar-panel">
        <div class="sidebar-header">
            <h2>Історія та Рахунок</h2>
            <button class="close-button" id="close-history">&times;</button>
        </div>
        <div class="sidebar-content">
            <div id="history-list"></div>
        </div>
        <div class="sidebar-footer">
            <div class="total-row">
                <span>Замовлені страви:</span>
                <span id="history-total">0.00 грн</span>
            </div>
            <div class="total-row" style="color: #777; font-size: 0.9em;">
                <span>Поточний кошик:</span>
                <span id="cart-pending-total">0 грн</span>
            </div>
            <div class="total-row final">
                <span>До сплати:</span>
                <span id="grand-total-display">0.00 грн</span>
            </div>
            <button class="modal-add-btn" id="request-bill-btn" style="background: #333;">
                <i class="fa-solid fa-receipt"></i> Попросити рахунок
            </button>
        </div>
    </div>

    <div id="toast" class="toast">Повідомлення</div>

    <script>
        const TABLE_ID = {table_id};
        const MENU_DATA = {menu_data}; 
        
        // Initial state from backend
        let HISTORY_DATA = {history_data}; 
        let SERVER_GRAND_TOTAL = {grand_total};

        let CART = []; 
        let currentProduct = null;
        let selectedModifiers = new Set();

        // Elements
        const menuContainer = document.getElementById('menu');
        const navContainer = document.getElementById('category-nav');
        
        // Modals
        const modModal = document.getElementById('modifier-modal');
        const payModal = document.getElementById('payment-modal');
        
        // Sidebars
        const cartSidebar = document.getElementById('cart-sidebar');
        const historySidebar = document.getElementById('history-sidebar');
        
        // Toast
        const toast = document.getElementById('toast');
        
        // History Elements
        const historyListEl = document.getElementById('history-list');
        const historyTotalEl = document.getElementById('history-total');
        const cartPendingTotalEl = document.getElementById('cart-pending-total');
        const grandTotalDisplayEl = document.getElementById('grand-total-display');

        function init() {{
            renderMenu();
            renderHistory();
            updateCartUI();
            updateTotals();
            
            // Event Listeners
            document.getElementById('cart-toggle').onclick = () => {{
                cartSidebar.classList.add('open');
                historySidebar.classList.remove('open');
            }};
            document.getElementById('close-cart').onclick = () => cartSidebar.classList.remove('open');
            
            document.getElementById('history-toggle').onclick = () => {{
                historySidebar.classList.add('open');
                cartSidebar.classList.remove('open');
                fetchUpdates(); // Refresh on open
            }};
            document.getElementById('close-history').onclick = () => historySidebar.classList.remove('open');

            // Modifiers
            document.getElementById('close-mod-modal').onclick = closeModModal;
            document.getElementById('modal-add-btn').onclick = addToCartFromModal;
            
            // Payment
            document.getElementById('request-bill-btn').onclick = () => payModal.classList.add('active');
            document.getElementById('close-pay-modal').onclick = () => payModal.classList.remove('active');
            
            document.querySelectorAll('.confirm-payment-btn').forEach(btn => {{
                btn.onclick = (e) => handlePaymentRequest(e.currentTarget);
            }});

            // Actions
            document.getElementById('place-order-btn').onclick = placeOrder;
            document.getElementById('call-waiter-btn').onclick = callWaiter;
            
            // Polling and ScrollSpy
            window.addEventListener('scroll', onScroll);
            setInterval(fetchUpdates, 5000); // Poll every 5 seconds
        }}

        // --- RENDER MENU (NEW LOGIC) ---
        function renderMenu() {{
            const categories = MENU_DATA.categories;
            const products = MENU_DATA.products;
            
            categories.forEach((cat, idx) => {{
                const link = document.createElement('a');
                link.href = `#cat-${{cat.id}}`;
                link.textContent = cat.name;
                link.className = idx === 0 ? 'active' : '';
                navContainer.appendChild(link);
                
                const section = document.createElement('div');
                section.id = `cat-${{cat.id}}`;
                section.className = 'category-section';
                section.innerHTML = `<h2 class="category-title">${{cat.name}}</h2>`;
                
                const grid = document.createElement('div');
                grid.className = 'products-grid';
                
                products.filter(p => p.category_id === cat.id).forEach(prod => {{
                    const card = document.createElement('div');
                    card.className = 'product-card';
                    const imgUrl = prod.image_url ? `/${{prod.image_url}}` : '/static/images/placeholder.jpg';
                    const prodData = JSON.stringify(prod).replace(/"/g, '&quot;');
                    
                    card.innerHTML = `
                        <div class="product-image-wrapper">
                            <img src="${{imgUrl}}" class="product-image" loading="lazy">
                        </div>
                        <div class="product-info">
                            <div class="product-name">${{prod.name}}</div>
                            <div class="product-desc">${{prod.description || ''}}</div>
                            <div class="product-footer">
                                <div class="product-price">${{prod.price}} грн</div>
                                <button class="add-to-cart-btn" onclick="handleProductClick(this)" data-product="${{prodData}}">
                                    Додати
                                </button>
                            </div>
                        </div>
                    `;
                    grid.appendChild(card);
                }});
                
                section.appendChild(grid);
                menuContainer.appendChild(section);
            }});
        }}

        // --- CART & MODIFIER LOGIC (NEW LOGIC) ---
        window.handleProductClick = (btn) => {{
            const product = JSON.parse(btn.dataset.product);
            if (product.modifiers && product.modifiers.length > 0) {{
                openModifierModal(product);
            }} else {{
                addToCart(product, []);
            }}
        }};

        function openModifierModal(product) {{
            currentProduct = product;
            selectedModifiers.clear();
            document.getElementById('modal-product-name').textContent = product.name;
            const list = document.getElementById('modal-modifiers-list');
            list.innerHTML = '';
            
            product.modifiers.forEach(mod => {{
                const item = document.createElement('div');
                item.className = 'modifier-item';
                item.innerHTML = `
                    <div class="modifier-info">
                        <input type="checkbox" id="mod-${{mod.id}}" class="modifier-input" hidden onchange="toggleModifier(${{mod.id}})">
                        <label for="mod-${{mod.id}}" class="modifier-label" style="display:flex; align-items:center; gap:10px; width:100%; cursor:pointer;">
                            <div class="checkbox-custom"></div>
                            <span style="font-size:1.1em;">${{mod.name}}</span>
                        </label>
                    </div>
                    <div style="font-weight:600; color:#555;">+${{mod.price}} грн</div>
                `;
                list.appendChild(item);
            }});
            updateModalPrice();
            modModal.classList.add('active');
        }}

        window.toggleModifier = (modId) => {{
            if (selectedModifiers.has(modId)) selectedModifiers.delete(modId);
            else selectedModifiers.add(modId);
            updateModalPrice();
        }};

        function updateModalPrice() {{
            let total = currentProduct.price;
            currentProduct.modifiers.forEach(mod => {{
                if (selectedModifiers.has(mod.id)) total += mod.price;
            }});
            document.getElementById('modal-total-price').textContent = `${{total.toFixed(2)}} грн`;
        }}

        function closeModModal() {{
            modModal.classList.remove('active');
            currentProduct = null;
        }}

        function addToCartFromModal() {{
            const mods = [];
            currentProduct.modifiers.forEach(m => {{
                if (selectedModifiers.has(m.id)) mods.push(m);
            }});
            addToCart(currentProduct, mods);
            closeModModal();
        }}

        function addToCart(product, modifiers) {{
            const modIds = modifiers.map(m => m.id).sort().join('-');
            const uniqueKey = `${{product.id}}-${{modIds}}`;
            
            const existing = CART.find(i => i.key === uniqueKey);
            if (existing) {{
                existing.quantity++;
            }} else {{
                let unitPrice = product.price;
                modifiers.forEach(m => unitPrice += m.price);
                CART.push({{
                    key: uniqueKey, id: product.id, name: product.name,
                    price: unitPrice, quantity: 1, modifiers: modifiers
                }});
            }}
            updateCartUI();
            showToast(`"${{product.name}}" додано!`);
            
            const fab = document.getElementById('cart-toggle');
            fab.style.transform = 'scale(1.2)';
            setTimeout(() => fab.style.transform = 'scale(1)', 200);
        }}

        function updateCartUI() {{
            const container = document.getElementById('cart-items');
            container.innerHTML = '';
            let total = 0;
            let count = 0;
            
            CART.forEach((item, idx) => {{
                total += item.price * item.quantity;
                count += item.quantity;
                const modNames = item.modifiers.map(m => m.name).join(', ');
                
                const div = document.createElement('div');
                div.className = 'cart-item';
                div.innerHTML = `
                    <div class="cart-item-details">
                        <span class="cart-item-title">${{item.name}}</span>
                        ${{modNames ? `<span class="cart-item-mods">+ ${{modNames}}</span>` : ''}}
                        <span class="cart-item-price">${{(item.price * item.quantity).toFixed(2)}} грн</span>
                    </div>
                    <div class="cart-controls">
                        <button class="qty-btn" onclick="updateQty(${{idx}}, -1)">-</button>
                        <span>${{item.quantity}}</span>
                        <button class="qty-btn" onclick="updateQty(${{idx}}, 1)">+</button>
                    </div>
                `;
                container.appendChild(div);
            }});
            
            document.getElementById('cart-total').textContent = `${{total.toFixed(2)}} грн`;
            const badge = document.getElementById('cart-count');
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
            
            const placeBtn = document.getElementById('place-order-btn');
            placeBtn.disabled = count === 0;
            placeBtn.style.opacity = count === 0 ? 0.5 : 1;
            
            updateTotals(); // Update Grand Total on History Sidebar
        }}

        window.updateQty = (index, delta) => {{
            CART[index].quantity += delta;
            if (CART[index].quantity <= 0) CART.splice(index, 1);
            updateCartUI();
        }};

        // --- HISTORY & POLLING (OLD LOGIC) ---
        function renderHistory() {{
            historyListEl.innerHTML = '';
            if (!HISTORY_DATA || HISTORY_DATA.length === 0) {{
                historyListEl.innerHTML = '<p style="text-align:center; color:#888;">Історія замовлень порожня.</p>';
                return;
            }}
            
            HISTORY_DATA.forEach(order => {{
                const item = document.createElement('div');
                item.className = 'history-item';
                const productsHtml = order.products.replace(/, /g, '<br>');
                
                item.innerHTML = `
                    <div class="history-header">
                        <span>#${{order.id}} • ${{order.time}}</span>
                        <span style="color:var(--primary-color); font-weight:600;">${{order.status}}</span>
                    </div>
                    <div class="history-products">${{productsHtml}}</div>
                    <div class="history-footer">
                        <span>Сума:</span>
                        <span>${{order.total_price}} грн</span>
                    </div>
                `;
                historyListEl.appendChild(item);
            }});
        }}

        function updateTotals() {{
            let cartTotal = 0;
            CART.forEach(item => cartTotal += item.price * item.quantity);
            
            historyTotalEl.textContent = `${{SERVER_GRAND_TOTAL.toFixed(2)}} грн`;
            cartPendingTotalEl.textContent = `${{cartTotal.toFixed(2)}} грн`;
            grandTotalDisplayEl.textContent = `${{(SERVER_GRAND_TOTAL + cartTotal).toFixed(2)}} грн`;
        }}

        async function fetchUpdates() {{
            try {{
                const response = await fetch(`/api/menu/table/${{TABLE_ID}}/updates`);
                if (!response.ok) return;
                
                const data = await response.json();
                HISTORY_DATA = data.history_data;
                SERVER_GRAND_TOTAL = data.grand_total;
                
                renderHistory();
                updateTotals();
            }} catch (error) {{
                console.error("Polling error:", error);
            }}
        }}

        // --- SERVER ACTIONS ---
        async function placeOrder() {{
            if (CART.length === 0) return;
            const btn = document.getElementById('place-order-btn');
            btn.classList.add('working');
            btn.disabled = true;
            
            try {{
                const response = await fetch(`/api/menu/table/${{TABLE_ID}}/place_order`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(CART)
                }});
                const result = await response.json();
                
                if (response.ok) {{
                    CART = [];
                    updateCartUI();
                    cartSidebar.classList.remove('open');
                    historySidebar.classList.add('open'); // Switch to history
                    fetchUpdates(); // Get new data immediately
                    showToast("✅ Замовлення прийнято!");
                }} else {{
                    showToast(`❌ Помилка: ${{result.message || 'Невідома'}}`);
                }}
            }} catch (e) {{
                showToast("❌ Помилка з'єднання");
            }} finally {{
                btn.classList.remove('working');
                btn.disabled = false;
            }}
        }}

        async function callWaiter() {{
            const btn = document.getElementById('call-waiter-btn');
            btn.innerHTML = '<div class="btn-spinner" style="border-color:#555; border-top-color:#000;"></div> Виклик...';
            try {{
                const response = await fetch(`/api/menu/table/${{TABLE_ID}}/call_waiter`, {{ method: 'POST' }});
                const result = await response.json();
                showToast(result.message);
            }} catch(e) {{ showToast('Помилка з`єднання'); }}
            finally {{ 
                btn.innerHTML = '<i class="fa-solid fa-bell"></i> Викликати офіціанта'; 
            }}
        }}

        async function handlePaymentRequest(btn) {{
            const method = btn.dataset.method;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<div class="btn-spinner"></div> Обробка...';
            btn.disabled = true;
            
            try {{
                const response = await fetch(`/api/menu/table/${{TABLE_ID}}/request_bill?method=${{method}}`, {{ method: 'POST' }});
                const result = await response.json();
                payModal.classList.remove('active');
                showToast(result.message);
            }} catch (error) {{
                showToast('Помилка з`єднання');
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = originalText;
            }}
        }}

        function showToast(msg) {{
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }}

        function onScroll() {{
            const sections = document.querySelectorAll('.category-section');
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                if (scrollY >= sectionTop - 150) current = section.getAttribute('id');
            }});
            document.querySelectorAll('.category-nav a').forEach(a => {{
                a.classList.remove('active');
                if (a.getAttribute('href').includes(current)) {{
                    a.classList.add('active');
                    a.scrollIntoView({{ behavior: 'smooth', inline: 'center', block: 'nearest' }});
                }}
            }});
        }}

        init();
    </script>
</body>
</html>
"""
# --- ЧАСТИНА 4: ВЕБ-САЙТ (ДОСТАВКА ТА САМОВИВІЗ) ---

WEB_ORDER_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_title}</title>
    <meta name="description" content="{seo_description}">
    <meta name="keywords" content="{seo_keywords}">
    
    <link rel="apple-touch-icon" sizes="180x180" href="/static/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/favicons/favicon-16x16.png">
    <link rel="manifest" href="/static/favicons/site.webmanifest">
    <link rel="shortcut icon" href="/static/favicons/favicon.ico">
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family={font_family_serif_encoded}:wght@400;700&family={font_family_sans_encoded}:wght@400;600&display=swap" rel="stylesheet">
    
    <style>
      :root {{
        --primary-color: {primary_color_val};
        --secondary-color: {secondary_color_val};
        --background-color: {background_color_val};
        --text-color: {text_color_val};
        --footer-bg-color: {footer_bg_color_val};
        --footer-text-color: {footer_text_color_val};
        
        /* Navigation settings */
        --nav-bg-color: {category_nav_bg_color};
        --nav-text-color: {category_nav_text_color};
        
        --header-bg-image: url('/{header_image_url}');
        
        --primary-hover-color: color-mix(in srgb, {primary_color_val}, black 10%);
        --primary-glow-color: {primary_color_val}26;
        --success-color: #28a745;
        --dark-text-for-accent: #ffffff;
        --side-padding: 20px;
        
        /* Common fonts */
        --font-sans: '{font_family_sans_val}', sans-serif;
        --font-serif: '{font_family_serif_val}', serif;
      }}
      
      body, .category-nav a, .add-to-cart-btn, .action-btn, #checkout-form, .radio-group label {{
        font-family: var(--font-sans);
      }}
      header h1, .category-title, .product-name, .product-price, .cart-header h2, .modal-content h2, #page-modal-title {{
        font-family: var(--font-serif);
      }}

      /* --- GLOBAL LAYOUT --- */
      @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
      @keyframes popIn {{ from {{ opacity: 0; transform: scale(0.95); }} to {{ opacity: 1; transform: scale(1); }} }}
      @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}

      html {{ scroll-behavior: smooth; }}
      body {{
        margin: 0;
        background-color: var(--background-color);
        color: var(--text-color);
        display: flex; flex-direction: column; min-height: 100vh;
      }}
      .container {{ width: 100%; margin: 0 auto; padding: 0; }}
      
      /* --- HEADER --- */
      header {{ 
          text-align: center; padding: 60px var(--side-padding) 40px; position: relative;
          background-image: var(--header-bg-image); background-size: cover; background-position: center;
          color: white;
      }}
      header::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 0; }}
      .header-logo-container, header h1, .main-nav {{ position: relative; z-index: 1; }}
      .header-logo {{ height: 100px; width: auto; margin-bottom: 25px; }}
      header h1 {{ font-size: clamp(3em, 6vw, 4em); margin: 0; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }}

      /* --- TOP NAV (PAGES) --- */
      .main-nav {{ text-align: center; padding: 10px var(--side-padding); margin-bottom: 20px; position: relative; }}
      .main-nav a {{ color: var(--text-color); text-decoration: none; margin: 0 15px; font-size: 1.1em; font-weight: 500; transition: color 0.3s; cursor: pointer; }}
      .main-nav a:hover {{ color: var(--primary-color); }}

      /* --- CATEGORY NAV --- */
      .category-nav {{
        display: flex; position: sticky; top: -1px; background: var(--nav-bg-color); backdrop-filter: blur(12px);
        z-index: 100; overflow-x: auto; padding: 15px 0; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-top: 1px solid var(--secondary-color); border-bottom: 1px solid var(--secondary-color);
      }}
      .category-nav::-webkit-scrollbar {{ display: none; }}
      .category-nav a {{
        color: var(--nav-text-color); text-decoration: none; padding: 10px 25px; border-radius: 20px;
        margin: 0 10px; background: rgba(255,255,255,0.1); transition: all 0.3s ease; font-weight: 500; white-space: nowrap;
      }}
      .category-nav a:first-child {{ margin-left: var(--side-padding); }}
      .category-nav a:hover, .category-nav a.active {{
        background: var(--primary-color); color: var(--dark-text-for-accent); transform: scale(1.05); font-weight: 600;
      }}

      /* --- MENU GRID --- */
      #menu {{ display: grid; grid-template-columns: 1fr; gap: 40px; padding: 0 var(--side-padding); margin-bottom: 40px; }}
      .category-section {{ margin-bottom: 30px; padding-top: 90px; margin-top: -90px; }}
      .category-title {{
        text-align: center; font-size: 2.5em; color: var(--primary-color); margin-bottom: 40px;
        padding-bottom: 15px; border-bottom: 1px solid var(--secondary-color);
      }}
      .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 30px; }}
      
      .product-card {{
        background: var(--card-bg, #fff); border-radius: 8px; overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: transform 0.3s, box-shadow 0.3s;
        display: flex; flex-direction: column; animation: fadeIn 0.5s ease-out;
      }}
      .product-card:hover {{ transform: translateY(-10px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); border: 1px solid var(--primary-color); }}
      
      .product-image-wrapper {{ width: 100%; height: 220px; overflow: hidden; position: relative; }}
      .product-image {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s; }}
      .product-card:hover .product-image {{ transform: scale(1.1); }}
      
      .product-info {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
      .product-name {{ font-size: 1.5em; margin: 0 0 10px; font-weight: 700; }}
      .product-desc {{ font-size: 0.9em; color: #777; margin-bottom: 20px; flex-grow: 1; }}
      .product-footer {{ display: flex; justify-content: space-between; align-items: center; }}
      .product-price {{ font-size: 1.5em; font-weight: 700; color: var(--primary-color); }}
      
      .add-to-cart-btn {{
        background: var(--primary-color); color: var(--dark-text-for-accent); border: none;
        padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: 600;
        transition: all 0.3s;
      }}
      .add-to-cart-btn:hover {{ background: var(--primary-hover-color); transform: scale(1.05); }}
      .add-to-cart-btn.added {{ background: var(--success-color); }}

      /* --- CART SIDEBAR --- */
      #cart-sidebar {{
        position: fixed; top: 0; right: -100%; width: 100%; max-width: 400px; height: 100%;
        background: rgba(255,255,255,0.95); backdrop-filter: blur(15px);
        box-shadow: -5px 0 25px rgba(0,0,0,0.1); transition: right 0.4s ease-in-out;
        z-index: 1000; display: flex; flex-direction: column; color: #333;
      }}
      #cart-sidebar.open {{ right: 0; }}
      .cart-header {{ padding: 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
      .cart-items {{ flex-grow: 1; overflow-y: auto; padding: 20px; }}
      .cart-item {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee; animation: popIn 0.3s; }}
      .cart-item-info {{ flex-grow: 1; }}
      .cart-item-name {{ font-weight: 600; display: block; }}
      .cart-item-mods {{ font-size: 0.8em; color: #666; display: block; }}
      .cart-item-controls button {{ width: 25px; height: 25px; border-radius: 50%; border: 1px solid #ddd; background: #fff; cursor: pointer; }}
      .cart-footer {{ padding: 20px; background: rgba(255,255,255,0.8); border-top: 1px solid #eee; }}
      #checkout-btn {{ width: 100%; padding: 15px; background: var(--primary-color); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }}
      #checkout-btn:disabled {{ background: #ccc; cursor: not-allowed; }}

      /* --- FLOATING BUTTONS --- */
      #cart-toggle {{
        position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px;
        background: var(--primary-color); color: white; border-radius: 50%; border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2); cursor: pointer; z-index: 1001;
        display: flex; justify-content: center; align-items: center; transition: transform 0.3s;
      }}
      #cart-toggle:hover {{ transform: scale(1.1); }}
      #cart-count {{ position: absolute; top: -5px; right: -5px; background: #e74c3c; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8em; font-weight: bold; border: 2px solid white; }}
      
      #scroll-to-top {{
        position: fixed; bottom: 90px; right: 20px; width: 50px; height: 50px;
        background: var(--primary-color); color: white; border-radius: 50%; border: none;
        cursor: pointer; z-index: 999; display: none; justify-content: center; align-items: center; font-size: 1.2em;
        transition: opacity 0.3s;
      }}
      #scroll-to-top.visible {{ display: flex; }}

      /* --- MODALS (Checkout & Modifiers) --- */
      .modal-overlay {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.7); z-index: 2000; display: none; justify-content: center; align-items: center;
        backdrop-filter: blur(5px); opacity: 0; transition: opacity 0.3s;
      }}
      .modal-overlay.visible {{ display: flex; opacity: 1; }}
      .modal-content {{
        background: #fff; padding: 30px; border-radius: 12px; width: 90%; max-width: 500px;
        max-height: 90vh; overflow-y: auto; position: relative; transform: scale(0.95); transition: transform 0.3s; color: #333;
      }}
      .modal-overlay.visible .modal-content {{ transform: scale(1); }}
      
      .form-group {{ margin-bottom: 15px; }}
      .form-group label {{ display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9em; }}
      .form-group input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; }}
      
      .radio-group {{ display: flex; gap: 10px; }}
      .radio-group input {{ display: none; }}
      .radio-group label {{
        flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; text-align: center; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;
      }}
      .radio-group input:checked + label {{ background: var(--primary-color); color: white; border-color: var(--primary-color); }}
      
      .close-modal {{ position: absolute; top: 15px; right: 20px; font-size: 1.5em; cursor: pointer; color: #999; }}

      /* --- FOOTER --- */
      footer {{ background: var(--footer-bg-color); color: var(--footer-text-color); padding: 50px var(--side-padding) 30px; margin-top: auto; border-top: 1px solid var(--secondary-color); }}
      .footer-content {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 40px; max-width: 1200px; margin: 0 auto; }}
      .footer-section h4 {{ font-size: 1.3em; margin-bottom: 20px; font-weight: 700; border-bottom: 2px solid var(--primary-color); display: inline-block; padding-bottom: 5px; color: var(--footer-text-color); }}
      .footer-contact-item {{ margin-bottom: 10px; display: flex; gap: 10px; }}
      .footer-contact-item i {{ color: var(--primary-color); }}
      .footer-contact-item a {{ color: inherit; text-decoration: none; }}
      .footer-social a {{ display: inline-flex; width: 40px; height: 40px; background: rgba(255,255,255,0.1); border-radius: 50%; align-items: center; justify-content: center; margin-right: 10px; color: inherit; text-decoration: none; transition: background 0.3s; }}
      .footer-social a:hover {{ background: var(--primary-color); color: white; }}
      
      /* --- PAGE MODAL --- */
      #page-modal-content h2 {{ color: var(--primary-color); border-bottom: 1px solid #eee; padding-bottom: 10px; }}
      #page-loader {{ display: flex; justify-content: center; padding: 20px; }}
      .spinner {{ border: 4px solid #f3f3f3; border-top: 4px solid var(--primary-color); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }}
    </style>
</head>
<body>
    <header>
        <div class="header-logo-container">{logo_html}</div>
        <h1>{site_title}</h1>
    </header>
    
    <nav class="main-nav">{menu_links_html}</nav>
    
    <div class="container">
        <nav class="category-nav" id="category-nav"></nav>
        <main id="menu">
            <div style="text-align:center; padding: 50px;"><div class="spinner"></div></div>
        </main>
    </div>

    <button id="cart-toggle">
        <i class="fa-solid fa-basket-shopping" style="font-size: 1.2em;"></i>
        <span id="cart-count">0</span>
    </button>
    <button id="scroll-to-top"><i class="fa-solid fa-arrow-up"></i></button>

    <aside id="cart-sidebar">
        <div class="cart-header">
            <h2>Ваше замовлення</h2>
            <button id="close-cart-btn" style="background:none; border:none; font-size:1.5em; cursor:pointer;">&times;</button>
        </div>
        <div id="cart-items-container" class="cart-items"></div>
        <div class="cart-footer">
            <div class="cart-total" style="display:flex; justify-content:space-between; font-weight:bold; font-size:1.2em; margin-bottom:15px;">
                <span>Всього:</span>
                <span id="cart-total-price">0.00 грн</span>
            </div>
            <button id="checkout-btn" disabled>Оформити замовлення</button>
        </div>
    </aside>

    <div id="modifier-modal" class="modal-overlay">
        <div class="modal-content">
            <span class="close-modal" id="close-mod-modal">&times;</span>
            <h3 id="mod-product-name" style="margin-top:0;"></h3>
            <div id="mod-list" style="margin: 20px 0;"></div>
            <button id="mod-add-btn" class="add-to-cart-btn" style="width:100%; display:flex; justify-content:center; gap:10px;">
                <span>Додати</span>
                <span id="mod-total-price"></span>
            </button>
        </div>
    </div>

    <div id="checkout-modal" class="modal-overlay">
        <div class="modal-content">
            <span class="close-modal" id="close-checkout-modal">&times;</span>
            <h2 style="text-align:center;">Оформлення</h2>
            <form id="checkout-form">
                <div class="form-group">
                    <label>Отримання:</label>
                    <div class="radio-group">
                        <input type="radio" id="delivery" name="delivery_type" value="delivery" checked>
                        <label for="delivery"><i class="fa-solid fa-truck"></i> Доставка</label>
                        <input type="radio" id="pickup" name="delivery_type" value="pickup">
                        <label for="pickup"><i class="fa-solid fa-bag-shopping"></i> Самовивіз</label>
                    </div>
                </div>
                
                <div class="form-group"><input type="text" id="customer_name" placeholder="Ваше ім'я" required></div>
                <div class="form-group"><input type="tel" id="phone_number" placeholder="Телефон" required></div>
                
                <div id="address-group" class="form-group">
                    <input type="text" id="address" placeholder="Адреса доставки" required>
                </div>

                <div class="form-group">
                    <label>Час:</label>
                    <div class="radio-group">
                        <input type="radio" id="asap" name="delivery_time" value="asap" checked>
                        <label for="asap">Якнайшвидше</label>
                        <input type="radio" id="specific" name="delivery_time" value="specific">
                        <label for="specific">На час</label>
                    </div>
                </div>
                <div id="specific-time-group" class="form-group" style="display:none;">
                    <input type="text" id="specific_time_input" placeholder="Наприклад: 18:30">
                </div>

                <div class="form-group">
                    <label>Оплата:</label>
                    <div class="radio-group">
                        <input type="radio" id="pay_cash" name="payment_method" value="cash" checked>
                        <label for="pay_cash">💵 Готівка</label>
                        <input type="radio" id="pay_card" name="payment_method" value="card">
                        <label for="pay_card">💳 Картка</label>
                    </div>
                </div>

                <button type="submit" id="place-order-submit" class="add-to-cart-btn" style="width:100%;">Підтвердити</button>
            </form>
        </div>
    </div>

    <div id="page-modal" class="modal-overlay">
        <div class="modal-content" id="page-modal-content">
            <span class="close-modal" id="close-page-modal">&times;</span>
            <h2 id="page-modal-title"></h2>
            <div id="page-modal-body"></div>
        </div>
    </div>

    <footer>
        <div class="footer-content">
            <div class="footer-section">
                <h4>Контакти</h4>
                <div class="footer-contact-item"><i class="fa-solid fa-location-dot"></i> <span>{footer_address}</span></div>
                <div class="footer-contact-item"><i class="fa-solid fa-phone"></i> <a href="tel:{footer_phone}">{footer_phone}</a></div>
                <div class="footer-contact-item"><i class="fa-solid fa-clock"></i> <span>{working_hours}</span></div>
            </div>
            <div class="footer-section">
                <h4>Соцмережі</h4>
                <div class="footer-social">{social_links_html}</div>
            </div>
        </div>
        <div style="text-align:center; margin-top:30px; opacity:0.7; font-size:0.9em;">
            &copy; 2024 {site_title}
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            let cart = JSON.parse(localStorage.getItem('webCart') || '{{}}');
            let menuData = null;
            let currentProd = null;
            let selectedMods = new Set();

            // DOM Elements
            const menuContainer = document.getElementById('menu');
            const cartSidebar = document.getElementById('cart-sidebar');
            const cartItemsContainer = document.getElementById('cart-items-container');
            const cartTotalEl = document.getElementById('cart-total-price');
            const cartCountEl = document.getElementById('cart-count');
            const checkoutBtn = document.getElementById('checkout-btn');
            
            // Fetch Menu
            async function fetchMenu() {{
                try {{
                    const res = await fetch('/api/menu');
                    menuData = await res.json();
                    renderMenu();
                    updateCartView();
                }} catch (e) {{
                    menuContainer.innerHTML = '<p style="text-align:center">Помилка завантаження меню.</p>';
                }}
            }}

            function renderMenu() {{
                menuContainer.innerHTML = '';
                const nav = document.getElementById('category-nav');
                nav.innerHTML = '';

                menuData.categories.forEach((cat, idx) => {{
                    // Nav Link
                    const link = document.createElement('a');
                    link.href = `#cat-${{cat.id}}`;
                    link.textContent = cat.name;
                    if(idx===0) link.classList.add('active');
                    nav.appendChild(link);

                    // Section
                    const section = document.createElement('div');
                    section.id = `cat-${{cat.id}}`;
                    section.className = 'category-section';
                    section.innerHTML = `<h2 class="category-title">${{cat.name}}</h2>`;

                    const grid = document.createElement('div');
                    grid.className = 'products-grid';

                    menuData.products.filter(p => p.category_id === cat.id).forEach(prod => {{
                        const card = document.createElement('div');
                        card.className = 'product-card';
                        const img = prod.image_url ? `/${{prod.image_url}}` : '/static/images/placeholder.jpg';
                        const prodJson = JSON.stringify(prod).replace(/"/g, '&quot;');
                        
                        card.innerHTML = `
                            <div class="product-image-wrapper"><img src="${{img}}" class="product-image"></div>
                            <div class="product-info">
                                <div class="product-name">${{prod.name}}</div>
                                <div class="product-desc">${{prod.description || ''}}</div>
                                <div class="product-footer">
                                    <div class="product-price">${{prod.price}} грн</div>
                                    <button class="add-to-cart-btn" data-product="${{prodJson}}" onclick="handleClick(this)">Додати</button>
                                </div>
                            </div>
                        `;
                        grid.appendChild(card);
                    }});
                    section.appendChild(grid);
                    menuContainer.appendChild(section);
                }});
                setupScrollSpy();
            }}

            // --- Cart Logic ---
            window.handleClick = (btn) => {{
                const prod = JSON.parse(btn.dataset.product);
                if (prod.modifiers && prod.modifiers.length > 0) openModModal(prod);
                else addToCart(prod, []);
                
                // Animation
                btn.classList.add('added');
                btn.textContent = '✓';
                setTimeout(() => {{ btn.classList.remove('added'); btn.textContent = 'Додати'; }}, 1000);
            }};

            function addToCart(prod, mods) {{
                const modIds = mods.map(m => m.id).sort().join('-');
                const key = `${{prod.id}}-${{modIds}}`;
                
                if (cart[key]) {{
                    cart[key].quantity++;
                }} else {{
                    let price = prod.price;
                    mods.forEach(m => price += m.price);
                    cart[key] = {{
                        id: prod.id, name: prod.name, price: price, quantity: 1, modifiers: mods, key: key
                    }};
                }}
                saveCart();
                updateCartView();
                
                // Pop animation on cart icon
                const toggle = document.getElementById('cart-toggle');
                toggle.style.transform = 'scale(1.2)';
                setTimeout(() => toggle.style.transform = 'scale(1)', 200);
            }}

            function updateCartView() {{
                cartItemsContainer.innerHTML = '';
                let total = 0;
                let count = 0;
                const items = Object.values(cart);
                
                if (items.length === 0) {{
                    cartItemsContainer.innerHTML = '<p style="text-align:center;color:#999;margin-top:50px;">Кошик порожній</p>';
                }}

                items.forEach(item => {{
                    total += item.price * item.quantity;
                    count += item.quantity;
                    
                    const div = document.createElement('div');
                    div.className = 'cart-item';
                    const modStr = (item.modifiers || []).map(m => m.name).join(', ');
                    
                    div.innerHTML = `
                        <div class="cart-item-info">
                            <span class="cart-item-name">${{item.name}}</span>
                            ${{modStr ? `<span class="cart-item-mods">+ ${{modStr}}</span>` : ''}}
                            <span style="color:var(--primary-color)">${{item.price}} грн</span>
                        </div>
                        <div class="cart-item-controls">
                            <button onclick="updateQty('${{item.key}}', -1)">-</button>
                            <span>${{item.quantity}}</span>
                            <button onclick="updateQty('${{item.key}}', 1)">+</button>
                        </div>
                    `;
                    cartItemsContainer.appendChild(div);
                }});
                
                cartTotalEl.textContent = total.toFixed(2) + ' грн';
                cartCountEl.textContent = count;
                cartCountEl.style.display = count > 0 ? 'flex' : 'none';
                checkoutBtn.disabled = count === 0;
            }}

            window.updateQty = (key, delta) => {{
                if (cart[key]) {{
                    cart[key].quantity += delta;
                    if (cart[key].quantity <= 0) delete cart[key];
                    saveCart();
                    updateCartView();
                }}
            }};

            function saveCart() {{ localStorage.setItem('webCart', JSON.stringify(cart)); }}

            // --- Modals Logic ---
            const modModal = document.getElementById('modifier-modal');
            const modList = document.getElementById('mod-list');
            
            function openModModal(prod) {{
                currentProd = prod;
                selectedMods.clear();
                document.getElementById('mod-product-name').textContent = prod.name;
                modList.innerHTML = '';
                
                prod.modifiers.forEach(mod => {{
                    const div = document.createElement('div');
                    div.style.padding = '10px';
                    div.style.borderBottom = '1px solid #eee';
                    div.style.display = 'flex';
                    div.style.justifyContent = 'space-between';
                    div.style.cursor = 'pointer';
                    div.innerHTML = `
                        <label style="cursor:pointer; display:flex; align-items:center; width:100%">
                            <input type="checkbox" onchange="toggleMod(${{mod.id}})" style="margin-right:10px;"> ${{mod.name}}
                        </label>
                        <b>+${{mod.price}}</b>
                    `;
                    modList.appendChild(div);
                }});
                updateModPrice();
                modModal.classList.add('visible');
            }}
            
            window.toggleMod = (id) => {{
                if (selectedMods.has(id)) selectedMods.delete(id);
                else selectedMods.add(id);
                updateModPrice();
            }};
            
            function updateModPrice() {{
                let p = currentProd.price;
                currentProd.modifiers.forEach(m => {{ if(selectedMods.has(m.id)) p += m.price; }});
                document.getElementById('mod-total-price').textContent = p.toFixed(2) + ' грн';
            }}
            
            document.getElementById('mod-add-btn').onclick = () => {{
                const mods = currentProd.modifiers.filter(m => selectedMods.has(m.id));
                addToCart(currentProd, mods);
                modModal.classList.remove('visible');
            }};

            // --- Checkout Logic ---
            const checkoutModal = document.getElementById('checkout-modal');
            const addressGroup = document.getElementById('address-group');
            const timeGroup = document.getElementById('specific-time-group');
            
            checkoutBtn.onclick = () => checkoutModal.classList.add('visible');
            
            // Radio Toggles
            document.querySelectorAll('input[name="delivery_type"]').forEach(el => {{
                el.onchange = (e) => {{
                    const isDelivery = e.target.value === 'delivery';
                    addressGroup.style.display = isDelivery ? 'block' : 'none';
                    document.getElementById('address').required = isDelivery;
                }};
            }});
            
            document.querySelectorAll('input[name="delivery_time"]').forEach(el => {{
                el.onchange = (e) => {{
                    timeGroup.style.display = e.target.value === 'specific' ? 'block' : 'none';
                }};
            }});
            
            // Auto-fill customer info
            document.getElementById('phone_number').onblur = async (e) => {{
                if(e.target.value.length >= 10) {{
                    try {{
                        const res = await fetch('/api/customer_info/' + encodeURIComponent(e.target.value));
                        if(res.ok) {{
                            const data = await res.json();
                            if(data.customer_name) document.getElementById('customer_name').value = data.customer_name;
                            if(data.address) document.getElementById('address').value = data.address;
                        }}
                    }} catch(err) {{}}
                }}
            }};

            document.getElementById('checkout-form').onsubmit = async (e) => {{
                e.preventDefault();
                const btn = document.getElementById('place-order-submit');
                btn.disabled = true; btn.textContent = 'Обробка...';
                
                const dType = document.querySelector('input[name="delivery_type"]:checked').value;
                const tType = document.querySelector('input[name="delivery_time"]:checked').value;
                const payMethod = document.querySelector('input[name="payment_method"]:checked').value;
                
                let timeVal = "Якнайшвидше";
                if(tType === 'specific') timeVal = document.getElementById('specific_time_input').value || "Не вказано";

                const data = {{
                    customer_name: document.getElementById('customer_name').value,
                    phone_number: document.getElementById('phone_number').value,
                    is_delivery: dType === 'delivery',
                    address: dType === 'delivery' ? document.getElementById('address').value : null,
                    delivery_time: timeVal,
                    payment_method: payMethod,
                    items: Object.values(cart)
                }};

                try {{
                    const res = await fetch('/api/place_order', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }});
                    
                    if(res.ok) {{
                        alert('Дякуємо! Замовлення прийнято.');
                        cart = {{}};
                        saveCart();
                        updateCartView();
                        checkoutModal.classList.remove('visible');
                        cartSidebar.classList.remove('open');
                    }} else {{
                        alert('Помилка при замовленні');
                    }}
                }} catch(err) {{
                    alert('Помилка з`єднання');
                }} finally {{
                    btn.disabled = false; btn.textContent = 'Підтвердити';
                }}
            }};

            // --- Page Modal ---
            const pageModal = document.getElementById('page-modal');
            const pageContent = document.getElementById('page-modal-body');
            const pageTitle = document.getElementById('page-modal-title');
            
            document.querySelectorAll('.menu-popup-trigger').forEach(link => {{
                link.onclick = async (e) => {{
                    e.preventDefault();
                    pageModal.classList.add('visible');
                    pageContent.innerHTML = '<div class="spinner"></div>';
                    pageTitle.textContent = '';
                    
                    try {{
                        const res = await fetch('/api/page/' + link.dataset.itemId);
                        if(res.ok) {{
                            const d = await res.json();
                            pageTitle.textContent = d.title;
                            pageContent.innerHTML = d.content;
                        }} else {{
                            pageContent.textContent = 'Помилка';
                        }}
                    }} catch(err) {{ pageContent.textContent = 'Помилка'; }}
                }};
            }});

            // --- General UI ---
            document.getElementById('cart-toggle').onclick = () => cartSidebar.classList.add('open');
            document.getElementById('close-cart-btn').onclick = () => cartSidebar.classList.remove('open');
            
            document.querySelectorAll('.close-modal').forEach(btn => {{
                btn.onclick = (e) => e.target.closest('.modal-overlay').classList.remove('visible');
            }});

            const scrollBtn = document.getElementById('scroll-to-top');
            window.onscroll = () => {{
                if(window.scrollY > 300) scrollBtn.classList.add('visible');
                else scrollBtn.classList.remove('visible');
            }};
            scrollBtn.onclick = () => window.scrollTo({{top:0, behavior:'smooth'}});

            function setupScrollSpy() {{
                const navLinks = document.querySelectorAll('.category-nav a');
                const observer = new IntersectionObserver(entries => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) {{
                            navLinks.forEach(l => l.classList.remove('active'));
                            const active = document.querySelector(`.category-nav a[href="#${{entry.target.id}}"]`);
                            if(active) {{
                                active.classList.add('active');
                                active.scrollIntoView({{behavior:'smooth', inline:'center'}});
                            }}
                        }}
                    }});
                }}, {{rootMargin: '-40% 0px -60% 0px'}});
                document.querySelectorAll('.category-section').forEach(s => observer.observe(s));
            }}

            fetchMenu();
        }});
    </script>
</body>
</html>
"""
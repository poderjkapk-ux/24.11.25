# tpl_client_qr.py

IN_HOUSE_MENU_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{site_title} - {table_name}</title>
    <meta name="robots" content="noindex, nofollow">
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family={font_family_serif_encoded}:wght@400;600;700&family={font_family_sans_encoded}:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
      :root {{
        /* --- Dynamic Variables --- */
        --primary: {primary_color_val};
        --secondary: {secondary_color_val};
        --bg-color: {background_color_val};
        --text-main: {text_color_val};
        --footer-bg: {footer_bg_color_val};
        --footer-text: {footer_text_color_val};
        --nav-bg: {category_nav_bg_color};
        --nav-text: {category_nav_text_color};
        --header-img: url('/{header_image_url}');
        
        /* --- System Colors & Shadows --- */
        --surface: #ffffff;
        --surface-glass: rgba(255, 255, 255, 0.98);
        --border-light: rgba(0, 0, 0, 0.08);
        
        --shadow-sm: 0 4px 12px rgba(0,0,0,0.03);
        --shadow-lg: 0 20px 50px rgba(0,0,0,0.12);
        
        --radius: 16px;
        --ease: cubic-bezier(0.22, 1, 0.36, 1);
        
        --font-sans: '{font_family_sans_val}', sans-serif;
        --font-serif: '{font_family_serif_val}', serif;
      }}
      
      * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; outline: none; }}
      body {{
        margin: 0; font-family: var(--font-sans); background: var(--bg-color); color: var(--text-main);
        display: flex; flex-direction: column; min-height: 100vh;
      }}
      
      /* HEADER */
      header {{
          position: relative; height: 35vh; min-height: 280px;
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          text-align: center; color: white; border-radius: 0 0 40px 40px; overflow: hidden;
          box-shadow: 0 10px 40px rgba(0,0,0,0.1); margin-bottom: 20px;
      }}
      .header-bg {{
          position: absolute; inset: 0; background-image: var(--header-img);
          background-size: cover; background-position: center; z-index: 0;
      }}
      header::after {{
          content: ''; position: absolute; inset: 0;
          background: linear-gradient(to bottom, rgba(0,0,0,0.2), rgba(0,0,0,0.6)); z-index: 1;
      }}
      .header-content {{ position: relative; z-index: 2; width: 90%; animation: fadeUp 0.8s var(--ease); display:flex; flex-direction:column; align-items:center; }}
      .header-logo {{ height: 90px; width: auto; margin-bottom: 15px; filter: drop-shadow(0 5px 15px rgba(0,0,0,0.2)); }}
      header h1 {{ font-family: var(--font-serif); font-size: 2.2rem; margin: 0; font-weight: 700; }}
      .table-badge {{
          display: inline-block; background: rgba(255,255,255,0.2); backdrop-filter: blur(10px);
          padding: 6px 14px; border-radius: 30px; font-size: 0.9rem; margin-top: 10px;
          border: 1px solid rgba(255,255,255,0.3);
      }}

      /* NAV */
      .category-nav-wrapper {{ position: sticky; top: 10px; z-index: 90; padding: 0 10px; margin-bottom: 30px; display: flex; justify-content: center; }}
      .category-nav {{
          display: flex; gap: 5px; overflow-x: auto; padding: 6px; border-radius: 50px;
          background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(20px);
          box-shadow: var(--shadow-sm); border: 1px solid var(--border-light); max-width: 100%;
      }}
      .category-nav a {{
          padding: 10px 20px; border-radius: 40px; font-weight: 600; font-size: 0.9rem;
          color: var(--nav-text); text-decoration: none; white-space: nowrap; transition: all 0.3s;
      }}
      .category-nav a.active {{ background: var(--primary); color: white; box-shadow: 0 4px 15px color-mix(in srgb, var(--primary), transparent 60%); }}

      /* MENU */
      .container {{ max-width: 1280px; margin: 0 auto; padding: 0 15px; }}
      .category-title {{ font-family: var(--font-serif); font-size: 1.8rem; margin: 40px 0 20px; display: flex; align-items: center; gap: 15px; }}
      .category-title::after {{ content: ''; height: 1px; background: var(--border-light); flex-grow: 1; }}
      
      .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(165px, 1fr)); gap: 15px; }}
      @media (min-width: 768px) {{ .products-grid {{ grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 25px; }} }}

      .product-card {{
          background: var(--surface); border-radius: var(--radius); overflow: hidden;
          box-shadow: var(--shadow-sm); border: 1px solid var(--border-light);
          display: flex; flex-direction: column; height: 100%; cursor: pointer;
          transition: transform 0.2s;
      }}
      .product-card:active {{ transform: scale(0.98); }}
      
      .product-img {{ width: 100%; aspect-ratio: 4/3; object-fit: cover; background: #f5f5f5; }}
      .product-info {{ padding: 12px; flex-grow: 1; display: flex; flex-direction: column; }}
      .product-name {{ font-weight: 700; font-size: 1rem; margin-bottom: 5px; line-height: 1.2; }}
      .product-desc {{ font-size: 0.8rem; color: #666; margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
      .product-footer {{ margin-top: auto; display: flex; justify-content: space-between; align-items: center; }}
      .product-price {{ font-weight: 800; font-size: 1.1rem; color: var(--text-main); }}
      
      .add-btn {{
          width: 32px; height: 32px; border-radius: 50%; background: var(--primary); color: white;
          border: none; display: flex; align-items: center; justify-content: center; font-size: 1rem;
          box-shadow: 0 4px 10px color-mix(in srgb, var(--primary), transparent 70%);
      }}

      /* UNIFIED SIDEBAR (CART + HISTORY) */
      .sidebar {{
          position: fixed; top: 0; right: 0; width: 100%; max-width: 480px; height: 100%;
          background: #fff; z-index: 1000; display: flex; flex-direction: column;
          transform: translateX(100%); transition: transform 0.4s var(--ease);
          box-shadow: -10px 0 40px rgba(0,0,0,0.1);
      }}
      .sidebar.open {{ transform: translateX(0); }}
      
      .sidebar-header {{
          padding: 15px 20px; background: white; border-bottom: 1px solid var(--border-light);
          display: flex; flex-direction: column; gap: 15px;
      }}
      
      .header-top {{ display: flex; justify-content: space-between; align-items: center; }}
      .header-title {{ font-family: var(--font-serif); font-size: 1.4rem; font-weight: 700; }}
      .close-btn {{ background: none; border: none; font-size: 1.5rem; color: #999; cursor: pointer; padding: 5px; }}

      /* SEGMENTED CONTROL (TABS) */
      .tabs-container {{
          background: #f1f5f9; padding: 4px; border-radius: 12px; display: flex; position: relative;
      }}
      .tab-btn {{
          flex: 1; border: none; background: transparent; padding: 10px; border-radius: 10px;
          font-weight: 600; font-size: 0.95rem; color: #64748b; cursor: pointer; z-index: 2;
          transition: color 0.2s; text-align: center;
      }}
      .tab-btn.active {{ color: var(--primary); }}
      
      .tab-indicator {{
          position: absolute; top: 4px; left: 4px; width: calc(50% - 4px); height: calc(100% - 8px);
          background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
          transition: transform 0.3s var(--ease); z-index: 1;
      }}
      /* Logic for indicator slide */
      .tabs-container[data-active="history"] .tab-indicator {{ transform: translateX(100%); }}

      /* SIDEBAR CONTENT */
      .sidebar-body {{ flex-grow: 1; overflow-y: auto; padding: 20px; background: #f8fafc; position: relative; }}
      
      .tab-view {{ display: none; animation: fadeIn 0.3s ease; }}
      .tab-view.active {{ display: block; }}

      /* CART ITEMS */
      .cart-item {{
          background: white; padding: 15px; border-radius: 16px; margin-bottom: 15px;
          display: flex; justify-content: space-between; align-items: center;
          box-shadow: var(--shadow-sm); border: 1px solid var(--border-light);
      }}
      .item-info {{ flex-grow: 1; }}
      .item-name {{ font-weight: 700; display: block; margin-bottom: 4px; }}
      .item-mods {{ font-size: 0.8rem; color: #888; display: block; }}
      .item-price {{ color: var(--primary); font-weight: 700; font-size: 0.95rem; }}
      
      .qty-control {{ display: flex; align-items: center; gap: 10px; background: #f1f5f9; padding: 4px; border-radius: 8px; }}
      .qty-btn {{ width: 28px; height: 28px; background: white; border-radius: 6px; border: none; font-weight: 700; box-shadow: var(--shadow-sm); cursor: pointer; }}
      .qty-val {{ min-width: 20px; text-align: center; font-weight:600; }}

      /* HISTORY ITEMS */
      .history-card {{
          background: white; border-radius: 16px; padding: 20px; margin-bottom: 15px;
          border-left: 5px solid #cbd5e1; box-shadow: var(--shadow-sm); position: relative;
      }}
      .history-card.completed {{ border-left-color: #10b981; }} /* Готово */
      .history-card.processing {{ border-left-color: #f59e0b; }} /* В работе */
      
      .h-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.85rem; color: #64748b; }}
      .h-body {{ font-weight: 500; line-height: 1.5; margin-bottom: 10px; color: #333; }}
      .h-footer {{ display: flex; justify-content: space-between; font-weight: 700; font-size: 1rem; color: var(--primary); border-top: 1px dashed #eee; padding-top: 10px; }}

      /* SIDEBAR FOOTER */
      .sidebar-footer {{
          padding: 20px; background: white; border-top: 1px solid var(--border-light);
          box-shadow: 0 -5px 20px rgba(0,0,0,0.03);
      }}
      .total-row {{ display: flex; justify-content: space-between; font-size: 1.3rem; font-weight: 800; margin-bottom: 20px; color: var(--text-main); }}
      
      .main-btn {{
          width: 100%; padding: 16px; border-radius: 14px; border: none;
          font-size: 1.1rem; font-weight: 700; cursor: pointer; color: white;
          display: flex; justify-content: center; align-items: center; gap: 10px;
          background: var(--primary); transition: transform 0.1s;
      }}
      .main-btn:active {{ transform: scale(0.98); }}
      .main-btn.secondary {{ background: #f1f5f9; color: #333; margin-top: 10px; }}

      /* UNIFIED FAB (Main Button) */
      #main-fab {{
          position: fixed; bottom: 30px; right: 30px; width: 65px; height: 65px;
          background: var(--primary); color: white; border-radius: 50%;
          box-shadow: 0 10px 30px color-mix(in srgb, var(--primary), transparent 60%);
          display: flex; justify-content: center; align-items: center; cursor: pointer;
          z-index: 900; transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      }}
      #main-fab:hover {{ transform: scale(1.1); }}
      #main-fab i {{ font-size: 1.6rem; }}
      #fab-badge {{
          position: absolute; top: 0; right: 0; background: #ef4444; color: white;
          width: 24px; height: 24px; border-radius: 50%; font-size: 0.8rem; font-weight: 800;
          display: flex; align-items: center; justify-content: center; border: 2px solid white;
      }}

      /* MODALS */
      .modal-overlay {{
          position: fixed; top: 0; left: 0; width: 100%; height: 100%;
          background: rgba(0,0,0,0.5); backdrop-filter: blur(5px);
          z-index: 2000; display: none; justify-content: center; align-items: center; opacity: 0; transition: opacity 0.3s;
      }}
      .modal-overlay.visible {{ display: flex; opacity: 1; }}
      .modal-content {{
          background: white; width: 90%; max-width: 450px; padding: 30px;
          border-radius: 24px; transform: translateY(20px); transition: transform 0.3s;
          max-height: 85vh; overflow-y: auto;
      }}
      .modal-overlay.visible .modal-content {{ transform: translateY(0); }}
      
      /* Product Detail Modal */
      .detail-img {{ width: 100%; border-radius: 16px; margin-bottom: 20px; }}
      .detail-title {{ font-size: 1.6rem; font-weight: 800; margin-bottom: 10px; line-height: 1.2; }}
      .detail-desc {{ color: #666; margin-bottom: 20px; line-height: 1.5; }}
      .detail-price {{ font-size: 1.4rem; font-weight: 800; color: var(--primary); margin-bottom: 25px; }}

      /* --- MODIFIERS IN MODAL (NEW) --- */
      #detail-modifiers {{
          margin-bottom: 20px; border-top: 1px solid #f1f5f9; padding-top: 15px;
      }}
      .mod-detail-item {{
          display: flex; justify-content: space-between; align-items: center;
          padding: 10px 0; border-bottom: 1px solid #f1f5f9; cursor: pointer;
      }}
      .mod-detail-item label {{ display: flex; align-items: center; width: 100%; cursor: pointer; }}
      .mod-detail-checkbox {{ width: 20px; height: 20px; margin-right: 12px; accent-color: var(--primary); cursor: pointer; }}
      .mod-detail-name {{ font-weight: 600; font-size: 0.95rem; color: var(--text-main); flex-grow: 1; }}
      .mod-detail-price {{ font-weight: 700; color: var(--primary); font-size: 0.9rem; }}

      /* FOOTER */
      footer {{ padding: 60px 20px 40px; background: var(--footer-bg); color: var(--footer-text); margin-top: auto; }}
      .footer-grid {{ display: grid; gap: 30px; max-width: 1000px; margin: 0 auto; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }}
      .footer-col h4 {{ text-transform: uppercase; font-size: 0.9rem; margin-bottom: 20px; opacity: 0.7; letter-spacing: 1px; }}
      .footer-link {{ display: flex; align-items: center; gap: 10px; margin-bottom: 12px; color: inherit; text-decoration: none; opacity: 0.8; }}
      .socials a {{ display: inline-flex; width: 40px; height: 40px; background: rgba(255,255,255,0.1); border-radius: 10px; justify-content: center; align-items: center; color: white; text-decoration: none; margin-right: 10px; font-size: 1.2rem; }}

      @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
      @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
      
      /* Payment Options */
      .pay-option {{ padding: 15px; border: 2px solid #e2e8f0; border-radius: 12px; margin-bottom: 10px; cursor: pointer; display: flex; align-items: center; gap: 15px; font-weight: 600; transition: all 0.2s; }}
      .pay-option:hover {{ border-color: var(--primary); background: #f8faff; }}
      
      /* Spinner */
      .spinner {{ width: 24px; height: 24px; border: 3px solid rgba(0,0,0,0.1); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; }}
      @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <header>
        <div class="header-bg"></div>
        <div class="header-content">
            <div class="header-logo-container">{logo_html}</div>
            <h1>{site_title}</h1>
            <div class="table-badge"><i class="fa-solid fa-chair"></i> {table_name}</div>
        </div>
    </header>
    
    <div class="category-nav-wrapper">
        <nav class="category-nav" id="category-nav"></nav>
    </div>
    
    <div class="container">
        <main id="menu"></main>
    </div>
    
    <div style="height: 100px;"></div> <div id="main-fab">
        <i class="fa-solid fa-utensils" id="fab-icon"></i>
        <span id="fab-badge" style="display:none;">0</span>
    </div>

    <aside id="unified-sidebar" class="sidebar">
        <div class="sidebar-header">
            <div class="header-top">
                <div class="header-title">Замовлення</div>
                <button id="close-sidebar" class="close-btn">&times;</button>
            </div>
            
            <div class="tabs-container" id="tabs-ctrl">
                <div class="tab-indicator"></div>
                <button class="tab-btn active" onclick="switchTab('cart')">Кошик</button>
                <button class="tab-btn" onclick="switchTab('history')">Історія</button>
            </div>
        </div>
        
        <div class="sidebar-body">
            <div id="view-cart" class="tab-view active">
                <div id="cart-list"></div>
                <div id="empty-cart-msg" style="text-align:center; padding:40px; color:#999; display:none;">
                    <i class="fa-solid fa-basket-shopping" style="font-size:3rem; opacity:0.3; margin-bottom:15px;"></i>
                    <p>Кошик порожній</p>
                </div>
            </div>
            
            <div id="view-history" class="tab-view">
                <div id="history-list"></div>
            </div>
        </div>
        
        <div class="sidebar-footer">
            <div class="total-row">
                <span id="footer-label">До сплати:</span>
                <span id="footer-total">0.00 грн</span>
            </div>
            
            <div id="cart-actions">
                <button id="place-order-btn" class="main-btn">Замовити <i class="fa-solid fa-arrow-right"></i></button>
                <button id="call-waiter-btn" class="main-btn secondary"><i class="fa-solid fa-bell"></i> Викликати офіціанта</button>
            </div>
            
            <div id="history-actions" style="display:none;">
                <button id="request-bill-btn" class="main-btn" style="background:#1e293b;">
                    <i class="fa-solid fa-receipt"></i> Попросити рахунок
                </button>
                <button onclick="switchTab('cart')" class="main-btn secondary">Додати ще страв</button>
            </div>
        </div>
    </aside>

    <div id="product-modal" class="modal-overlay">
        <div class="modal-content">
            <div style="position:relative;">
                <button class="close-modal close-btn" style="position:absolute; top:-10px; right:-10px; background:white; border-radius:50%; width:35px; height:35px; display:flex; align-items:center; justify-content:center; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">&times;</button>
                <img src="" id="det-img" class="product-detail-img">
                <h2 id="det-name" class="detail-title"></h2>
                <div id="det-desc" class="detail-desc"></div>
                <div id="det-price" class="detail-price"></div>
                
                <div id="detail-modifiers"></div>
                
                <button id="det-add-btn" class="main-btn">Додати в кошик</button>
            </div>
        </div>
    </div>

    <div id="pay-modal" class="modal-overlay">
        <div class="modal-content">
            <h3 style="margin-top:0;">Спосіб оплати</h3>
            <p style="color:#666; margin-bottom:20px;">Як бажаєте розрахуватись?</p>
            <div class="pay-option" onclick="sendBillRequest('cash')">
                <i class="fa-solid fa-money-bill-wave" style="color:#2e7d32; font-size:1.5rem;"></i> Готівка
            </div>
            <div class="pay-option" onclick="sendBillRequest('card')">
                <i class="fa-regular fa-credit-card" style="color:#1565c0; font-size:1.5rem;"></i> Картка / Термінал
            </div>
        </div>
    </div>

    <div id="success-modal" class="modal-overlay">
        <div class="modal-content" style="text-align:center;">
            <div style="width:70px; height:70px; background:#dcfce7; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px;">
                <i class="fa-solid fa-check" style="color:#16a34a; font-size:35px;"></i>
            </div>
            <h3 id="success-title" style="margin-bottom:10px; font-size:1.5rem;">Успішно!</h3>
            <p id="success-msg" style="color:#64748b; margin-bottom:25px; font-size:1rem;"></p>
            <button class="main-btn" onclick="document.getElementById('success-modal').classList.remove('visible')">Гаразд</button>
        </div>
    </div>

    <div id="page-modal" class="modal-overlay">
        <div class="modal-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; padding-bottom:10px; border-bottom:1px solid #eee;">
                <h3 id="page-title" style="margin:0;"></h3>
                <button class="close-modal close-btn">&times;</button>
            </div>
            <div id="page-body" class="page-content-body" style="line-height:1.6; color:#333;"></div>
        </div>
    </div>

    <footer>
        <div class="footer-grid">
            <div class="footer-col">
                <h4>Контакти</h4>
                <div class="footer-link"><i class="fa-solid fa-location-dot"></i> {footer_address}</div>
                <a href="tel:{footer_phone}" class="footer-link"><i class="fa-solid fa-phone"></i> {footer_phone}</a>
                <div class="footer-link"><i class="fa-regular fa-clock"></i> {working_hours}</div>
            </div>
            <div class="footer-col">
                <h4>Інформація</h4>
                {menu_links_html}
            </div>
            <div class="footer-col">
                <h4>Wi-Fi</h4>
                <div class="footer-link"><i class="fa-solid fa-wifi"></i> {wifi_ssid}</div>
                <div class="footer-link"><i class="fa-solid fa-lock"></i> {wifi_password}</div>
            </div>
            <div class="footer-col">
                <h4>Соцмережі</h4>
                <div class="socials">{social_links_html}</div>
            </div>
        </div>
        <div style="text-align:center; margin-top:40px; font-size:0.8rem; opacity:0.5;">
            &copy; 2024 {site_title}
        </div>
    </footer>

    <script>
        const TABLE_ID = {table_id};
        const MENU = {menu_data};
        let HISTORY = {history_data};
        let GRAND_TOTAL = {grand_total};
        let cart = {{}}; // Глобальный объект корзины
        
        let curProd = null;

        document.addEventListener('DOMContentLoaded', () => {{
            // Очистка и восстановление корзины
            try {{
                const saved = localStorage.getItem('qrCart');
                if (saved) {{
                    const parsed = JSON.parse(saved);
                    // Проверка на валидность (старый формат был массивом, новый - объектом)
                    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {{
                        cart = parsed;
                    }} else {{
                        cart = {{}}; // Сброс, если формат неверный
                    }}
                }}
            }} catch (e) {{
                console.error("Cart load error", e);
                cart = {{}};
                localStorage.removeItem('qrCart');
            }}

            renderMenu();
            initUI();
            
            // Poll for updates
            setInterval(fetchUpdates, 5000);
        }});

        function initUI() {{
            // Sidebar Toggles
            const sidebar = document.getElementById('unified-sidebar');
            document.getElementById('main-fab').onclick = () => sidebar.classList.add('open');
            document.getElementById('close-sidebar').onclick = () => sidebar.classList.remove('open');
            
            // Modals close
            document.querySelectorAll('.close-modal').forEach(b => {{
                b.onclick = (e) => e.target.closest('.modal-overlay').classList.remove('visible');
            }});

            // Buttons
            document.getElementById('place-order-btn').onclick = placeOrder;
            document.getElementById('call-waiter-btn').onclick = callWaiter;
            document.getElementById('request-bill-btn').onclick = () => document.getElementById('pay-modal').classList.add('visible');
            
            // "Add to cart" in modal
            document.getElementById('det-add-btn').onclick = () => {{
                const selectedMods = [];
                const container = document.getElementById('detail-modifiers');
                container.querySelectorAll('.mod-detail-checkbox:checked').forEach(cb => {{
                    selectedMods.push({{
                        id: parseInt(cb.value),
                        name: cb.dataset.name,
                        price: parseFloat(cb.dataset.price)
                    }});
                }});
                
                addToCart(curProd, selectedMods);
                document.getElementById('product-modal').classList.remove('visible');
            }};

            // Page links
            document.body.addEventListener('click', (e) => {{
                const link = e.target.closest('.menu-popup-trigger');
                if(link) {{
                    e.preventDefault();
                    openPageModal(link.dataset.itemId, link.innerText);
                }}
            }});

            updateUI();
        }}

        // --- TABS LOGIC ---
        window.switchTab = (tab) => {{
            document.getElementById('tabs-ctrl').dataset.active = tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelector(`.tab-btn[onclick="switchTab('${{tab}}')"]`).classList.add('active');
            
            document.querySelectorAll('.tab-view').forEach(v => v.classList.remove('active'));
            document.getElementById(`view-${{tab}}`).classList.add('active');
            
            const cartActs = document.getElementById('cart-actions');
            const histActs = document.getElementById('history-actions');
            const label = document.getElementById('footer-label');
            const total = document.getElementById('footer-total');
            
            if (tab === 'cart') {{
                cartActs.style.display = 'block';
                histActs.style.display = 'none';
                label.innerText = 'Разом (Кошик):';
                const items = Object.values(cart);
                const cartSum = items.reduce((sum, i) => sum + (i.price * i.quantity), 0);
                total.innerText = cartSum.toFixed(2) + ' грн';
            }} else {{
                cartActs.style.display = 'none';
                histActs.style.display = 'block';
                label.innerText = 'Всього до сплати:';
                const items = Object.values(cart);
                const cartSum = items.reduce((sum, i) => sum + (i.price * i.quantity), 0);
                total.innerText = (GRAND_TOTAL + cartSum).toFixed(2) + ' грн';
            }}
        }};

        // --- MENU RENDER ---
        function renderMenu() {{
            const nav = document.getElementById('category-nav');
            const main = document.getElementById('menu');
            
            // Очистка и защита от ошибок
            try {{
                nav.innerHTML = '';
                main.innerHTML = '';

                MENU.categories.forEach((cat, i) => {{
                    const link = document.createElement('a');
                    link.href = `#c-${{cat.id}}`;
                    link.textContent = cat.name;
                    if(i===0) link.classList.add('active');
                    nav.appendChild(link);

                    const section = document.createElement('div');
                    section.id = `c-${{cat.id}}`;
                    section.className = 'category-section';
                    section.innerHTML = `<h2 class="category-title">${{cat.name}}</h2>`;

                    const grid = document.createElement('div');
                    grid.className = 'products-grid';

                    const products = MENU.products.filter(p => p.category_id === cat.id);
                    if (products.length > 0) {{
                        products.forEach(prod => {{
                            const card = document.createElement('div');
                            card.className = 'product-card';
                            const img = prod.image_url ? `/${{prod.image_url}}` : '/static/images/placeholder.jpg';
                            const prodJson = JSON.stringify(prod).replace(/"/g, '&quot;');
                            
                            // Клик по карточке открывает детали
                            card.onclick = (e) => {{
                                if(!e.target.closest('.add-btn')) openDetail(prod);
                            }};

                            card.innerHTML = `
                                <div class="product-image-wrapper"><img src="${{img}}" class="product-image" loading="lazy"></div>
                                <div class="product-info">
                                    <div class="product-header">
                                        <div class="product-name">${{prod.name}}</div>
                                        <div class="product-desc">${{prod.description||''}}</div>
                                    </div>
                                    <div class="product-footer">
                                        <div class="product-price">${{prod.price}} грн</div>
                                        <button class="add-btn" onclick="event.stopPropagation(); handleAdd(JSON.parse(this.dataset.product), this)" data-product="${{prodJson}}">
                                            <i class="fa-solid fa-plus"></i>
                                        </button>
                                    </div>
                                </div>
                            `;
                            grid.appendChild(card);
                        }});
                        section.appendChild(grid);
                        main.appendChild(section);
                    }}
                }});
                
                setupScrollSpy();
            }} catch (e) {{
                console.error("Render error", e);
                main.innerHTML = '<div style="text-align:center; padding:40px;">Помилка відображення меню. Спробуйте оновити сторінку.</div>';
            }}
        }}

        // --- ACTIONS ---
        window.handleAdd = (prod, btn) => {{
            if(prod.modifiers && prod.modifiers.length > 0) {{
                // Open modal if modifiers exist
                openDetail(prod);
            }} else {{
                // Direct add
                addToCart(prod, []);
                if(btn) animateBtn(btn);
            }}
        }};

        function openDetail(prod) {{
            curProd = prod;
            const img = curProd.image_url ? `/${{curProd.image_url}}` : '/static/images/placeholder.jpg';
            document.getElementById('det-img').src = img;
            document.getElementById('det-name').innerText = curProd.name;
            document.getElementById('det-desc').innerText = curProd.description || '';
            
            // Generate modifiers
            const modContainer = document.getElementById('detail-modifiers');
            modContainer.innerHTML = '';
            
            if(prod.modifiers && prod.modifiers.length > 0) {{
                const title = document.createElement('p');
                title.style.cssText = "font-weight:600; color:#64748b; margin-bottom:10px;";
                title.textContent = "Добавки:";
                modContainer.appendChild(title);
                
                prod.modifiers.forEach(m => {{
                    modContainer.innerHTML += `
                    <div class="mod-detail-item">
                        <label>
                            <input type="checkbox" class="mod-detail-checkbox" value="${{m.id}}" data-price="${{m.price}}" data-name="${{m.name}}" onchange="updateDetailPrice()">
                            <span class="mod-detail-name">${{m.name}}</span>
                            <span class="mod-detail-price">+${{m.price}} грн</span>
                        </label>
                    </div>`;
                }});
            }}
            
            updateDetailPrice();
            document.getElementById('product-modal').classList.add('visible');
        }}
        
        window.updateDetailPrice = () => {{
            if(!curProd) return;
            let price = curProd.price;
            const modContainer = document.getElementById('detail-modifiers');
            modContainer.querySelectorAll('.mod-detail-checkbox:checked').forEach(cb => {{
                price += parseFloat(cb.dataset.price);
            }});
            
            document.getElementById('det-price').innerText = price.toFixed(2) + ' грн';
            document.getElementById('det-add-btn').innerText = `В кошик за ${{price.toFixed(2)}} грн`;
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
                    key: key, 
                    id: prod.id, 
                    name: prod.name, 
                    price: price, 
                    qty: 1, 
                    mods: mods 
                }};
            }}
            saveCart();
            updateUI();
            
            const fab = document.getElementById('main-fab');
            fab.style.transform = 'scale(1.2)';
            setTimeout(() => fab.style.transform = 'scale(1)', 200);
        }}

        function updateUI() {{
            const list = document.getElementById('cart-list');
            list.innerHTML = '';
            let cartTotal = 0;
            let count = 0;
            
            const items = Object.values(cart);
            
            items.forEach((item) => {{
                cartTotal += item.price * item.qty;
                count += item.qty;
                const modStr = item.mods.map(m => m.name).join(', ');
                list.innerHTML += `
                <div class="cart-item">
                    <div class="item-info">
                        <span class="item-name">${{item.name}}</span>
                        <span class="item-mods">${{modStr}}</span>
                        <span class="item-price">${{(item.price * item.qty).toFixed(2)}}</span>
                    </div>
                    <div class="qty-control">
                        <button class="qty-btn" onclick="changeQty('${{item.key}}', -1)">-</button>
                        <div class="qty-val">${{item.qty}}</div>
                        <button class="qty-btn" onclick="changeQty('${{item.key}}', 1)">+</button>
                    </div>
                </div>`;
            }});
            
            document.getElementById('empty-cart-msg').style.display = count === 0 ? 'block' : 'none';
            document.getElementById('place-order-btn').disabled = count === 0;
            document.getElementById('place-order-btn').style.opacity = count === 0 ? '0.5' : '1';
            
            // History Render
            const hList = document.getElementById('history-list');
            hList.innerHTML = '';
            HISTORY.forEach(o => {{
                const cls = o.status === 'Готовий до видачі' ? 'completed' : 'processing';
                hList.innerHTML += `
                <div class="history-card ${{cls}}">
                    <div class="h-header"><span>#${{o.id}}</span> <span>${{o.time}}</span></div>
                    <div class="h-body">${{o.products.replace(/, /g, '<br>')}}</div>
                    <div class="h-footer">
                        <span>${{o.status}}</span> <span>${{o.total_price}} грн</span>
                    </div>
                </div>`;
            }});
            if(HISTORY.length === 0) hList.innerHTML = '<div style="text-align:center; color:#999; padding:20px;">Історія порожня</div>';

            const fabBadge = document.getElementById('fab-badge');
            fabBadge.innerText = count || '!';
            fabBadge.style.display = (count > 0 || HISTORY.length > 0) ? 'flex' : 'none';
            fabBadge.style.backgroundColor = count > 0 ? '#ef4444' : '#22c55e';
            
            document.getElementById('fab-icon').className = count > 0 ? 'fa-solid fa-basket-shopping' : 'fa-solid fa-clock-rotate-left';
            
            const activeTab = document.querySelector('.tab-btn.active').getAttribute('onclick').includes('cart') ? 'cart' : 'history';
            switchTab(activeTab);
        }}

        window.changeQty = (key, delta) => {{
            if (cart[key]) {{
                cart[key].qty += delta;
                if (cart[key].qty <= 0) delete cart[key];
                saveCart();
                updateUI();
            }}
        }};
        
        function saveCart() {{ localStorage.setItem('qrCart', JSON.stringify(cart)); }}

        async function placeOrder() {{
            const btn = document.getElementById('place-order-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<div class="spinner"></div>';
            
            try {{
                const items = Object.values(cart).map(i => ({{
                    id: i.id, quantity: i.qty, modifiers: i.mods
                }}));
                
                const res = await fetch(`/api/menu/table/${{TABLE_ID}}/place_order`, {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}, 
                    body: JSON.stringify(items)
                }});
                if(res.ok) {{
                    cart = {{}}; 
                    saveCart();
                    fetchUpdates();
                    switchTab('history');
                    showSuccess('Замовлення прийнято!', 'Офіціант незабаром підтвердить його.');
                }} else {{
                    throw new Error('Server error');
                }}
            }} catch(e) {{ 
                alert('Помилка при створенні замовлення.'); 
            }} finally {{ 
                btn.innerHTML = 'Замовити <i class="fa-solid fa-arrow-right"></i>';
            }}
        }}

        async function fetchUpdates() {{
            try {{
                const res = await fetch(`/api/menu/table/${{TABLE_ID}}/updates`);
                if(res.ok) {{
                    const data = await res.json();
                    HISTORY = data.history_data;
                    GRAND_TOTAL = data.grand_total;
                    updateUI();
                }}
            }} catch(e) {{}}
        }}

        async function callWaiter() {{
            try {{ 
                await fetch(`/api/menu/table/${{TABLE_ID}}/call_waiter`, {{method:'POST'}}); 
                showSuccess('Викликано!', 'Офіціант вже прямує до вас.');
            }} catch(e) {{}}
        }}

        async function sendBillRequest(method) {{
            try {{ 
                await fetch(`/api/menu/table/${{TABLE_ID}}/request_bill?method=${{method}}`, {{method:'POST'}}); 
                document.getElementById('pay-modal').classList.remove('visible');
                showSuccess('Запит надіслано', 'Офіціант принесе рахунок.');
            }} catch(e) {{}}
        }}
        
        function showSuccess(title, msg) {{
            document.getElementById('success-title').innerText = title;
            document.getElementById('success-msg').innerText = msg;
            document.getElementById('success-modal').classList.add('visible');
        }}

        async function openPageModal(id, title) {{
            document.getElementById('page-modal').classList.add('visible');
            document.getElementById('page-title').innerText = title;
            document.getElementById('page-body').innerHTML = '<div style="text-align:center; padding:20px;"><div class="spinner" style="border-top-color:#333; margin:0 auto;"></div></div>';
            try {{
                const res = await fetch('/api/page/'+id);
                const data = await res.json();
                document.getElementById('page-body').innerHTML = data.content;
            }} catch(e) {{ document.getElementById('page-body').innerText = 'Помилка'; }}
        }}

        function animateBtn(btn) {{
            const icon = btn.querySelector('i');
            if(icon) {{
                const oldClass = icon.className;
                icon.className = 'fa-solid fa-check';
                btn.style.background = '#22c55e';
                setTimeout(() => {{ icon.className = oldClass; btn.style.background = ''; }}, 1000);
            }}
        }}
        
        function setupScrollSpy() {{
            const observer = new IntersectionObserver(entries => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        document.querySelectorAll('.category-nav a').forEach(l => l.classList.remove('active'));
                        const active = document.querySelector(`.category-nav a[href="#${{entry.target.id}}"]`);
                        if(active) {{
                            active.classList.add('active');
                            active.scrollIntoView({{behavior:'smooth', inline:'center', block: 'nearest'}});
                        }}
                    }}
                }});
            }}, {{rootMargin: '-20% 0px -70% 0px'}});
            document.querySelectorAll('.category-section').forEach(s => observer.observe(s));
        }}
    </script>
</body>
</html>
"""
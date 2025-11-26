# tpl_client_web.py

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
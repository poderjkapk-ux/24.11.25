# tpl_client_qr.py

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
# templates.py

# ... (ADMIN_HTML_TEMPLATE и другие переменные остаются без изменений, приводим только измененный WEB_ORDER_HTML) ...

# --- ЧАСТИНА 4: ВЕБ-САЙТ (ДОСТАВКА ТА САМОВИВІЗ) - MODERN REDESIGN ---

WEB_ORDER_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{site_title}</title>
    <meta name="description" content="{seo_description}">
    <meta name="keywords" content="{seo_keywords}">
    <meta name="theme-color" content="{primary_color_val}">
    
    <link rel="apple-touch-icon" sizes="180x180" href="/static/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/favicons/favicon-16x16.png">
    <link rel="manifest" href="/static/favicons/site.webmanifest">
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family={font_family_serif_encoded}:wght@400;600;700&family={font_family_sans_encoded}:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
      :root {{
        /* Colors from Admin */
        --primary: {primary_color_val};
        --secondary: {secondary_color_val};
        --bg-color: {background_color_val};
        --text-main: {text_color_val};
        --footer-bg: {footer_bg_color_val};
        --footer-text: {footer_text_color_val};
        --nav-bg: {category_nav_bg_color};
        --nav-text: {category_nav_text_color};
        
        /* Derived Colors (Modern CSS) */
        --primary-light: color-mix(in srgb, var(--primary), white 85%);
        --primary-dark: color-mix(in srgb, var(--primary), black 20%);
        --primary-shadow: color-mix(in srgb, var(--primary), transparent 70%);
        --text-muted: color-mix(in srgb, var(--text-main), transparent 40%);
        
        /* UI Constants */
        --radius-lg: 24px;
        --radius-md: 16px;
        --radius-sm: 12px;
        --shadow-soft: 0 10px 40px -10px rgba(0,0,0,0.08);
        --shadow-hover: 0 20px 50px -12px rgba(0,0,0,0.15);
        --glass-bg: rgba(255, 255, 255, 0.8);
        --glass-border: 1px solid rgba(255, 255, 255, 0.3);
        --blur-amt: 20px;
        
        /* Fonts */
        --font-sans: '{font_family_sans_val}', system-ui, sans-serif;
        --font-serif: '{font_family_serif_val}', Georgia, serif;
        
        --header-img: url('/{header_image_url}');
      }}

      /* RESET & BASE */
      *, *::before, *::after {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
      html {{ scroll-behavior: smooth; font-size: 16px; }}
      
      body {{
        margin: 0;
        background-color: var(--bg-color);
        color: var(--text-main);
        font-family: var(--font-sans);
        line-height: 1.6;
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        overflow-x: hidden;
      }}

      h1, h2, h3, h4 {{ font-family: var(--font-serif); line-height: 1.2; margin: 0; }}
      button, input, textarea {{ font-family: var(--font-sans); }}
      img {{ max-width: 100%; display: block; }}
      a {{ text-decoration: none; color: inherit; transition: 0.3s; }}

      /* --- HERO HEADER (Parallax & Glass) --- */
      header {{ 
          position: relative; 
          min-height: 60vh; 
          display: flex; 
          flex-direction: column;
          align-items: center; 
          justify-content: center;
          text-align: center; 
          color: white;
          padding: 20px;
          overflow: hidden;
      }}
      
      .header-bg {{
          position: absolute; top: 0; left: 0; width: 100%; height: 100%;
          background-image: var(--header-img); 
          background-size: cover; 
          background-position: center;
          z-index: -2;
          transform: scale(1.1); /* Prevent white edges on scroll */
      }}
      
      .header-overlay {{
          position: absolute; top: 0; left: 0; width: 100%; height: 100%;
          background: linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(0,0,0,0.7));
          z-index: -1;
          backdrop-filter: blur(2px);
      }}

      .header-content {{ 
          z-index: 1; 
          animation: fadeInUp 1s ease-out; 
          max-width: 800px;
      }}
      
      .header-logo {{ 
          height: 120px; 
          width: auto; 
          margin: 0 auto 20px; 
          filter: drop-shadow(0 5px 15px rgba(0,0,0,0.3)); 
      }}
      
      header h1 {{ 
          font-size: clamp(2.5rem, 6vw, 4.5rem); 
          font-weight: 700; 
          margin-bottom: 10px;
          text-shadow: 0 4px 20px rgba(0,0,0,0.5);
          letter-spacing: -0.02em;
      }}

      /* --- TOP NAVIGATION (Pages) --- */
      .main-nav {{
          position: absolute; top: 20px; right: 20px; z-index: 10;
          display: flex; gap: 15px;
      }}
      .main-nav a {{
          color: white; font-weight: 500; font-size: 0.95rem;
          padding: 8px 16px; border-radius: 50px;
          background: rgba(255,255,255,0.15);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255,255,255,0.2);
          transition: all 0.3s;
      }}
      .main-nav a:hover {{ background: white; color: black; transform: translateY(-2px); }}

      /* --- CATEGORY STICKY NAV (Glassmorphism) --- */
      .category-nav-wrapper {{
          position: sticky; top: 10px; z-index: 900;
          margin: -30px auto 30px; max-width: 95%;
      }}
      
      .category-nav {{
          display: flex; 
          gap: 10px; 
          overflow-x: auto; 
          padding: 10px 10px;
          background: var(--glass-bg);
          backdrop-filter: blur(var(--blur-amt));
          -webkit-backdrop-filter: blur(var(--blur-amt));
          border-radius: 50px;
          border: var(--glass-border);
          box-shadow: var(--shadow-soft);
          scrollbar-width: none; /* Firefox */
      }}
      .category-nav::-webkit-scrollbar {{ display: none; }}
      
      .category-nav a {{
          padding: 10px 24px;
          border-radius: 40px;
          color: var(--nav-text);
          font-weight: 600;
          font-size: 0.95rem;
          white-space: nowrap;
          transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
          border: 1px solid transparent;
      }}
      
      .category-nav a:hover {{ background: rgba(0,0,0,0.05); }}
      
      .category-nav a.active {{
          background: var(--primary);
          color: white;
          box-shadow: 0 4px 15px var(--primary-shadow);
          transform: scale(1.05);
      }}

      /* --- MENU GRID --- */
      .container {{ width: 92%; max-width: 1200px; margin: 0 auto; padding-bottom: 80px; }}
      
      .category-section {{ padding-top: 80px; margin-top: -40px; /* Anchor offset */ }}
      
      .category-title {{
          font-size: 2.5rem; 
          margin-bottom: 30px; 
          color: var(--text-main);
          position: relative;
          display: inline-block;
      }}
      .category-title::after {{
          content: ''; display: block; width: 60%; height: 4px; 
          background: var(--primary); margin-top: 5px; border-radius: 2px;
      }}

      .products-grid {{
          display: grid; 
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
          gap: 30px;
      }}

      /* --- PRODUCT CARD (Modern) --- */
      .product-card {{
          background: white;
          border-radius: var(--radius-lg);
          overflow: hidden;
          position: relative;
          transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          border: 1px solid rgba(0,0,0,0.03);
          box-shadow: var(--shadow-soft);
          display: flex; flex-direction: column;
          height: 100%;
      }}
      
      .product-card:hover {{
          transform: translateY(-8px);
          box-shadow: var(--shadow-hover);
      }}

      .product-image-wrapper {{
          position: relative;
          padding-top: 70%; /* Aspect Ratio */
          overflow: hidden;
      }}
      
      .product-image {{
          position: absolute; top: 0; left: 0; width: 100%; height: 100%;
          object-fit: cover;
          transition: transform 0.6s ease;
      }}
      .product-card:hover .product-image {{ transform: scale(1.08); }}

      .product-info {{
          padding: 20px;
          display: flex; flex-direction: column; flex-grow: 1;
      }}
      
      .product-name {{
          font-size: 1.25rem;
          font-weight: 700;
          margin-bottom: 8px;
          color: var(--text-main);
      }}
      
      .product-desc {{
          font-size: 0.9rem;
          color: var(--text-muted);
          margin-bottom: 20px;
          flex-grow: 1;
          line-height: 1.5;
          display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
      }}
      
      .product-footer {{
          display: flex; justify-content: space-between; align-items: center;
          margin-top: auto;
      }}
      
      .product-price {{
          font-size: 1.4rem;
          font-weight: 700;
          color: var(--text-main);
      }}
      
      .add-btn {{
          background: var(--primary);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: var(--radius-sm);
          font-weight: 600;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.3s;
          box-shadow: 0 4px 10px var(--primary-shadow);
          display: flex; align-items: center; gap: 8px;
      }}
      .add-btn:hover {{
          background: var(--primary-dark);
          transform: translateY(-2px);
          box-shadow: 0 6px 15px var(--primary-shadow);
      }}
      .add-btn:active {{ transform: translateY(0); }}
      
      /* --- FLOATING UI --- */
      .fab-container {{
          position: fixed; bottom: 30px; right: 30px; 
          display: flex; flex-direction: column; gap: 15px; z-index: 950;
      }}
      
      .fab {{
          width: 60px; height: 60px;
          border-radius: 50%;
          border: none;
          cursor: pointer;
          box-shadow: 0 8px 25px rgba(0,0,0,0.2);
          display: flex; align-items: center; justify-content: center;
          transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
          position: relative;
      }}
      
      #cart-toggle {{ background: var(--primary); color: white; font-size: 1.4rem; }}
      #cart-toggle:hover {{ transform: scale(1.1); }}
      
      #scroll-to-top {{ 
          background: white; color: var(--text-main); font-size: 1.2rem;
          opacity: 0; pointer-events: none; transform: translateY(20px);
      }}
      #scroll-to-top.visible {{ opacity: 1; pointer-events: auto; transform: translateY(0); }}

      #cart-count {{
          position: absolute; top: -5px; right: -5px;
          background: #ff3b30; color: white;
          font-size: 0.75rem; font-weight: bold;
          min-width: 24px; height: 24px;
          border-radius: 12px;
          display: flex; align-items: center; justify-content: center;
          border: 2px solid white;
          animation: popIn 0.3s;
      }}

      /* --- CART SIDEBAR (Glass) --- */
      .cart-sidebar {{
          position: fixed; top: 0; right: 0; bottom: 0;
          width: 100%; max-width: 420px;
          background: rgba(255, 255, 255, 0.85);
          backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
          z-index: 1000;
          transform: translateX(100%);
          transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          display: flex; flex-direction: column;
          box-shadow: -10px 0 40px rgba(0,0,0,0.1);
          border-left: 1px solid rgba(255,255,255,0.5);
      }}
      .cart-sidebar.open {{ transform: translateX(0); }}
      
      .cart-header {{
          padding: 25px;
          display: flex; justify-content: space-between; align-items: center;
          border-bottom: 1px solid rgba(0,0,0,0.05);
      }}
      .cart-header h2 {{ font-size: 1.5rem; font-weight: 700; color: var(--text-main); }}
      .close-btn {{
          background: rgba(0,0,0,0.05); border: none;
          width: 36px; height: 36px; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          cursor: pointer; font-size: 1.2rem; transition: 0.2s;
      }}
      .close-btn:hover {{ background: rgba(0,0,0,0.1); }}

      .cart-items {{ flex-grow: 1; overflow-y: auto; padding: 25px; scroll-behavior: smooth; }}
      
      .cart-item {{
          display: flex; gap: 15px; margin-bottom: 20px;
          animation: slideInRight 0.3s ease-out;
      }}
      .cart-item-details {{ flex-grow: 1; }}
      .cart-item-name {{ font-weight: 600; font-size: 1rem; display: block; margin-bottom: 4px; }}
      .cart-item-mods {{ font-size: 0.8rem; color: var(--text-muted); display: block; margin-bottom: 8px; }}
      .cart-item-price {{ font-weight: 700; color: var(--primary); }}
      
      .qty-controls {{
          display: flex; align-items: center; gap: 10px;
          background: white; border-radius: 8px; padding: 4px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.05);
          height: fit-content;
      }}
      .qty-btn {{
          width: 28px; height: 28px; border: none; background: transparent;
          border-radius: 6px; cursor: pointer; font-weight: bold; color: var(--text-main);
          transition: background 0.2s;
      }}
      .qty-btn:hover {{ background: #f0f0f0; }}
      
      .cart-footer {{
          padding: 30px;
          background: white;
          border-top: 1px solid rgba(0,0,0,0.05);
          box-shadow: 0 -5px 20px rgba(0,0,0,0.03);
      }}
      .total-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; font-size: 1.3rem; font-weight: 700; }}
      
      .checkout-btn {{
          width: 100%; padding: 16px; border: none; border-radius: var(--radius-md);
          background: var(--primary); color: white; font-size: 1.1rem; font-weight: 600;
          cursor: pointer; transition: 0.3s;
          display: flex; justify-content: center; align-items: center; gap: 10px;
          box-shadow: 0 5px 20px var(--primary-shadow);
      }}
      .checkout-btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px var(--primary-shadow); }}
      .checkout-btn:disabled {{ background: #ccc; cursor: not-allowed; box-shadow: none; transform: none; }}

      /* --- MODALS --- */
      .modal-overlay {{
          position: fixed; top: 0; left: 0; width: 100%; height: 100%;
          background: rgba(0,0,0,0.6); backdrop-filter: blur(8px);
          z-index: 2000; opacity: 0; pointer-events: none;
          transition: opacity 0.3s ease;
          display: flex; align-items: center; justify-content: center;
      }}
      .modal-overlay.visible {{ opacity: 1; pointer-events: auto; }}
      
      .modal-content {{
          background: white; width: 90%; max-width: 550px;
          border-radius: var(--radius-lg); padding: 30px;
          max-height: 85vh; overflow-y: auto;
          box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
          transform: scale(0.95) translateY(20px);
          transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      }}
      .modal-overlay.visible .modal-content {{ transform: scale(1) translateY(0); }}

      /* Form Styles in Modal */
      .form-group {{ margin-bottom: 20px; }}
      .form-group label {{ display: block; font-weight: 600; margin-bottom: 8px; font-size: 0.9rem; color: var(--text-main); }}
      
      .input-field {{
          width: 100%; padding: 14px 16px; border: 2px solid #eee; border-radius: var(--radius-sm);
          font-size: 1rem; transition: all 0.2s; outline: none; background: #f9f9f9;
      }}
      .input-field:focus {{ border-color: var(--primary); background: white; box-shadow: 0 0 0 4px var(--primary-light); }}
      
      .radio-group {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
      .radio-card input {{ display: none; }}
      .radio-card label {{
          display: flex; flex-direction: column; align-items: center; gap: 8px;
          padding: 15px; border: 2px solid #eee; border-radius: var(--radius-sm);
          cursor: pointer; transition: all 0.2s; font-weight: 500;
      }}
      .radio-card label i {{ font-size: 1.5rem; color: #ccc; transition: 0.2s; }}
      
      .radio-card input:checked + label {{
          border-color: var(--primary); background: var(--primary-light); color: var(--primary-dark);
      }}
      .radio-card input:checked + label i {{ color: var(--primary); }}

      /* Modifiers List */
      .mod-item {{
          display: flex; justify-content: space-between; align-items: center;
          padding: 12px 0; border-bottom: 1px solid #eee; cursor: pointer;
      }}
      .checkbox {{
          width: 22px; height: 22px; border: 2px solid #ddd; border-radius: 6px;
          margin-right: 12px; display: flex; align-items: center; justify-content: center;
          transition: 0.2s;
      }}
      .mod-item input:checked + span .checkbox {{
          background: var(--primary); border-color: var(--primary);
      }}
      .checkbox::after {{ content: '✓'; color: white; font-size: 14px; opacity: 0; }}
      .mod-item input:checked + span .checkbox::after {{ opacity: 1; }}

      /* --- FOOTER --- */
      footer {{
          background: var(--footer-bg); color: var(--footer-text);
          padding: 60px 0 30px; margin-top: auto;
      }}
      .footer-grid {{
          display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 40px;
          margin-bottom: 40px;
      }}
      .footer-col h4 {{
          font-size: 1.2rem; margin-bottom: 20px; opacity: 0.9;
      }}
      .contact-row {{ display: flex; gap: 12px; margin-bottom: 12px; align-items: center; opacity: 0.8; }}
      .social-links {{ display: flex; gap: 15px; }}
      .social-btn {{
          width: 44px; height: 44px; border-radius: 50%;
          background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center;
          transition: 0.3s; font-size: 1.2rem;
      }}
      .social-btn:hover {{ background: var(--primary); color: white; transform: translateY(-3px); }}

      /* Animations */
      @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(30px); }} to {{ opacity: 1; transform: translateY(0); }} }}
      @keyframes popIn {{ 0% {{ transform: scale(0); }} 80% {{ transform: scale(1.2); }} 100% {{ transform: scale(1); }} }}
      @keyframes slideInRight {{ from {{ opacity: 0; transform: translateX(20px); }} to {{ opacity: 1; transform: translateX(0); }} }}

      /* Mobile Tweaks */
      @media (max-width: 768px) {{
          header {{ min-height: 50vh; }}
          .category-nav-wrapper {{ margin-top: -20px; }}
          .products-grid {{ grid-template-columns: 1fr 1fr; gap: 15px; }}
          .product-card {{ display: flex; flex-direction: column; }}
          .product-image-wrapper {{ padding-top: 80%; }}
          .product-info {{ padding: 12px; }}
          .product-name {{ font-size: 1rem; }}
          .product-price {{ font-size: 1.1rem; }}
          .add-btn {{ padding: 8px 12px; font-size: 0.85rem; }}
          .cart-sidebar {{ max-width: 100%; }}
      }}
    </style>
</head>
<body>

    <header>
        <div class="header-bg"></div>
        <div class="header-overlay"></div>
        
        <nav class="main-nav">
            {menu_links_html}
        </nav>

        <div class="header-content">
            <div class="header-logo-container">{logo_html}</div>
            <h1>{site_title}</h1>
            <p style="font-size: 1.1rem; opacity: 0.9; max-width: 600px; margin: 0 auto;">
                {seo_description}
            </p>
        </div>
    </header>

    <div class="category-nav-wrapper">
        <nav class="category-nav" id="category-nav">
            </nav>
    </div>

    <div class="container">
        <main id="menu">
            <div style="padding: 100px; text-align: center; color: var(--text-muted);">
                <i class="fa-solid fa-spinner fa-spin" style="font-size: 2rem;"></i><br>Завантаження меню...
            </div>
        </main>
    </div>

    <div class="fab-container">
        <button id="scroll-to-top" class="fab" title="Вгору">
            <i class="fa-solid fa-arrow-up"></i>
        </button>
        <button id="cart-toggle" class="fab" title="Кошик">
            <i class="fa-solid fa-basket-shopping"></i>
            <span id="cart-count">0</span>
        </button>
    </div>

    <aside id="cart-sidebar" class="cart-sidebar">
        <div class="cart-header">
            <h2>Ваше замовлення</h2>
            <button class="close-btn" id="close-cart-btn">&times;</button>
        </div>
        
        <div id="cart-items-container" class="cart-items">
            </div>
        
        <div class="cart-footer">
            <div class="total-row">
                <span>Разом:</span>
                <span id="cart-total-price">0.00 грн</span>
            </div>
            <button id="checkout-btn" class="checkout-btn" disabled>
                Оформити замовлення <i class="fa-solid fa-arrow-right"></i>
            </button>
        </div>
    </aside>

    <div id="modifier-modal" class="modal-overlay">
        <div class="modal-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h3 id="mod-product-name" style="margin:0; font-size:1.4rem;">Назва товару</h3>
                <button class="close-btn close-modal">&times;</button>
            </div>
            
            <div style="background:#f9f9f9; padding:15px; border-radius:12px; margin-bottom:20px;">
                <p style="margin:0; color:var(--text-muted); font-size:0.9rem;">Оберіть добавки:</p>
                <div id="mod-list" style="margin-top:10px;"></div>
            </div>
            
            <button id="mod-add-btn" class="checkout-btn">
                <span>Додати в кошик</span>
                <span style="background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:4px;" id="mod-total-price">0 грн</span>
            </button>
        </div>
    </div>

    <div id="checkout-modal" class="modal-overlay">
        <div class="modal-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h2 style="margin:0;">Оформлення</h2>
                <button class="close-btn close-modal">&times;</button>
            </div>
            
            <form id="checkout-form">
                <div class="form-group">
                    <label>Спосіб отримання</label>
                    <div class="radio-group">
                        <div class="radio-card">
                            <input type="radio" id="delivery" name="delivery_type" value="delivery" checked>
                            <label for="delivery"><i class="fa-solid fa-truck-fast"></i> Доставка</label>
                        </div>
                        <div class="radio-card">
                            <input type="radio" id="pickup" name="delivery_type" value="pickup">
                            <label for="pickup"><i class="fa-solid fa-store"></i> Самовивіз</label>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label>Ваші дані</label>
                    <input type="text" id="customer_name" class="input-field" placeholder="Ім'я" required style="margin-bottom:10px;">
                    <input type="tel" id="phone_number" class="input-field" placeholder="Телефон" required>
                </div>

                <div id="address-group" class="form-group">
                    <label>Адреса доставки</label>
                    <input type="text" id="address" class="input-field" placeholder="Вулиця, будинок, квартира" required>
                </div>

                <div class="form-group">
                    <label>Час доставки</label>
                    <div class="radio-group">
                        <div class="radio-card">
                            <input type="radio" id="asap" name="delivery_time" value="asap" checked>
                            <label for="asap"><i class="fa-regular fa-clock"></i> Якнайшвидше</label>
                        </div>
                        <div class="radio-card">
                            <input type="radio" id="specific" name="delivery_time" value="specific">
                            <label for="specific"><i class="fa-solid fa-calendar-day"></i> На час</label>
                        </div>
                    </div>
                    <div id="specific-time-group" style="margin-top:10px; display:none;">
                        <input type="text" id="specific_time_input" class="input-field" placeholder="Вкажіть час (напр. 19:00)">
                    </div>
                </div>

                <div class="form-group">
                    <label>Оплата</label>
                    <div class="radio-group">
                        <div class="radio-card">
                            <input type="radio" id="pay_cash" name="payment_method" value="cash" checked>
                            <label for="pay_cash"><i class="fa-solid fa-money-bill-wave"></i> Готівка</label>
                        </div>
                        <div class="radio-card">
                            <input type="radio" id="pay_card" name="payment_method" value="card">
                            <label for="pay_card"><i class="fa-regular fa-credit-card"></i> Картка</label>
                        </div>
                    </div>
                </div>

                <button type="submit" id="place-order-submit" class="checkout-btn" style="margin-top:20px;">
                    Підтвердити замовлення
                </button>
            </form>
        </div>
    </div>

    <div id="page-modal" class="modal-overlay">
        <div class="modal-content" style="max-width:700px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border-bottom:1px solid #eee; padding-bottom:15px;">
                <h2 id="page-modal-title" style="margin:0; color:var(--primary);"></h2>
                <button class="close-btn close-modal">&times;</button>
            </div>
            <div id="page-modal-body" style="line-height:1.8; color:var(--text-main);"></div>
        </div>
    </div>

    <footer>
        <div class="container">
            <div class="footer-grid">
                <div class="footer-col">
                    <h4>Контакти</h4>
                    <div class="contact-row"><i class="fa-solid fa-location-dot"></i> {footer_address}</div>
                    <div class="contact-row"><i class="fa-solid fa-phone"></i> <a href="tel:{footer_phone}">{footer_phone}</a></div>
                    <div class="contact-row"><i class="fa-regular fa-clock"></i> {working_hours}</div>
                </div>
                <div class="footer-col">
                    <h4>Ми в соцмережах</h4>
                    <div class="social-links">
                        {social_links_html}
                    </div>
                </div>
                <div class="footer-col">
                    <h4>Про нас</h4>
                    <p style="opacity:0.8; font-size:0.9rem;">Найсмачніші страви з доставкою додому. Ми використовуємо тільки свіжі інгредієнти та авторські рецепти.</p>
                </div>
            </div>
            <div style="text-align:center; padding-top:30px; border-top:1px solid rgba(255,255,255,0.1); opacity:0.6; font-size:0.9rem;">
                &copy; 2024 {site_title}. Всі права захищені.
            </div>
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            // === STATE ===
            let cart = JSON.parse(localStorage.getItem('webCart') || '{{}}');
            let menuData = null;
            let currentProd = null; // For modifier modal
            let selectedMods = new Set();

            // === ELEMENTS ===
            const menuContainer = document.getElementById('menu');
            const navContainer = document.getElementById('category-nav');
            const cartSidebar = document.getElementById('cart-sidebar');
            const overlay = document.querySelector('.modal-overlay'); // Generic background
            
            // === INIT ===
            async function init() {{
                await fetchMenu();
                updateCartUI();
                setupEventListeners();
            }}

            async function fetchMenu() {{
                try {{
                    const res = await fetch('/api/menu');
                    if(!res.ok) throw new Error("Network response was not ok");
                    menuData = await res.json();
                    renderMenu();
                }} catch (e) {{
                    console.error(e);
                    menuContainer.innerHTML = '<div style="text-align:center; padding:50px;">Сталася помилка завантаження меню. Спробуйте оновити сторінку.</div>';
                }}
            }}

            function renderMenu() {{
                menuContainer.innerHTML = '';
                navContainer.innerHTML = '';

                menuData.categories.forEach((cat, idx) => {{
                    // Nav
                    const link = document.createElement('a');
                    link.href = `#cat-${{cat.id}}`;
                    link.textContent = cat.name;
                    if (idx === 0) link.classList.add('active');
                    link.onclick = (e) => {{
                        e.preventDefault();
                        document.getElementById(`cat-${{cat.id}}`).scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                        // Manual active set
                        document.querySelectorAll('.category-nav a').forEach(a => a.classList.remove('active'));
                        link.classList.add('active');
                    }};
                    navContainer.appendChild(link);

                    // Section
                    const section = document.createElement('div');
                    section.id = `cat-${{cat.id}}`;
                    section.className = 'category-section';
                    
                    const title = document.createElement('h2');
                    title.className = 'category-title';
                    title.textContent = cat.name;
                    section.appendChild(title);

                    const grid = document.createElement('div');
                    grid.className = 'products-grid';

                    const products = menuData.products.filter(p => p.category_id === cat.id);
                    
                    if (products.length === 0) {{
                        grid.innerHTML = '<p>В цій категорії поки немає товарів.</p>';
                    }} else {{
                        products.forEach(prod => {{
                            const card = createProductCard(prod);
                            grid.appendChild(card);
                        }});
                    }}

                    section.appendChild(grid);
                    menuContainer.appendChild(section);
                }});

                setupScrollSpy();
            }}

            function createProductCard(prod) {{
                const div = document.createElement('div');
                div.className = 'product-card';
                
                const imgUrl = prod.image_url ? `/${{prod.image_url}}` : '/static/images/placeholder.jpg';
                // Escape JSON for attribute
                const prodJson = JSON.stringify(prod).replace(/"/g, '&quot;');

                div.innerHTML = `
                    <div class="product-image-wrapper">
                        <img src="${{imgUrl}}" class="product-image" alt="${{prod.name}}" loading="lazy">
                    </div>
                    <div class="product-info">
                        <h3 class="product-name">${{prod.name}}</h3>
                        <div class="product-desc">${{prod.description || ''}}</div>
                        <div class="product-footer">
                            <div class="product-price">${{prod.price}} грн</div>
                            <button class="add-btn" onclick="handleAddToCart(this)" data-product="${{prodJson}}">
                                <i class="fa-solid fa-plus"></i> Додати
                            </button>
                        </div>
                    </div>
                `;
                return div;
            }}

            // === CART & MODIFIERS ===
            
            window.handleAddToCart = (btn) => {{
                const prod = JSON.parse(btn.dataset.product);
                if (prod.modifiers && prod.modifiers.length > 0) {{
                    openModModal(prod);
                }} else {{
                    addToCart(prod, []);
                    animateBtn(btn);
                }}
            }};

            function animateBtn(btn) {{
                const originalHTML = btn.innerHTML;
                btn.innerHTML = '<i class="fa-solid fa-check"></i>';
                btn.style.background = 'var(--success-color)';
                setTimeout(() => {{
                    btn.innerHTML = originalHTML;
                    btn.style.background = '';
                }}, 1000);
            }}

            function addToCart(prod, mods) {{
                const modIds = mods.map(m => m.id).sort().join('-');
                const key = `${{prod.id}}-${{modIds}}`;
                
                if (cart[key]) {{
                    cart[key].quantity++;
                }} else {{
                    let price = prod.price;
                    mods.forEach(m => price += m.price);
                    cart[key] = {{
                        id: prod.id,
                        name: prod.name,
                        price: price,
                        quantity: 1,
                        modifiers: mods,
                        key: key
                    }};
                }}
                saveCart();
                updateCartUI();
                // Open cart sidebar feedback
                document.getElementById('cart-toggle').classList.add('bump');
                setTimeout(() => document.getElementById('cart-toggle').classList.remove('bump'), 200);
            }}

            function updateCartUI() {{
                const container = document.getElementById('cart-items-container');
                container.innerHTML = '';
                
                const items = Object.values(cart);
                let total = 0;
                let count = 0;

                if (items.length === 0) {{
                    container.innerHTML = `
                        <div style="text-align:center; margin-top:50px; color:var(--text-muted);">
                            <i class="fa-solid fa-basket-shopping" style="font-size:3rem; opacity:0.5; margin-bottom:15px;"></i>
                            <p>Ваш кошик порожній</p>
                            <button onclick="document.getElementById('cart-sidebar').classList.remove('open')" 
                                    style="margin-top:10px; padding:8px 16px; border:1px solid #ddd; background:white; border-radius:20px; cursor:pointer;">
                                Перейти до меню
                            </button>
                        </div>`;
                }} else {{
                    items.forEach(item => {{
                        total += item.price * item.quantity;
                        count += item.quantity;
                        
                        const modText = item.modifiers.map(m => m.name).join(', ');
                        
                        const row = document.createElement('div');
                        row.className = 'cart-item';
                        row.innerHTML = `
                            <div class="cart-item-details">
                                <span class="cart-item-name">${{item.name}}</span>
                                ${{modText ? `<span class="cart-item-mods">+ ${{modText}}</span>` : ''}}
                                <div class="cart-item-price">${{item.price.toFixed(2)}} грн</div>
                            </div>
                            <div class="qty-controls">
                                <button class="qty-btn" onclick="changeQty('${{item.key}}', -1)">-</button>
                                <span style="font-weight:600; min-width:20px; text-align:center;">${{item.quantity}}</span>
                                <button class="qty-btn" onclick="changeQty('${{item.key}}', 1)">+</button>
                            </div>
                        `;
                        container.appendChild(row);
                    }});
                }}

                document.getElementById('cart-total-price').textContent = total.toFixed(2) + ' грн';
                document.getElementById('cart-count').textContent = count;
                document.getElementById('cart-count').style.display = count > 0 ? 'flex' : 'none';
                document.getElementById('checkout-btn').disabled = count === 0;
            }}

            window.changeQty = (key, delta) => {{
                if (cart[key]) {{
                    cart[key].quantity += delta;
                    if (cart[key].quantity <= 0) delete cart[key];
                    saveCart();
                    updateCartUI();
                }}
            }};

            function saveCart() {{ localStorage.setItem('webCart', JSON.stringify(cart)); }}

            // === MODIFIERS MODAL ===
            const modModal = document.getElementById('modifier-modal');
            
            function openModModal(prod) {{
                currentProd = prod;
                selectedMods.clear();
                document.getElementById('mod-product-name').textContent = prod.name;
                
                const list = document.getElementById('mod-list');
                list.innerHTML = '';
                
                prod.modifiers.forEach(mod => {{
                    const row = document.createElement('label');
                    row.className = 'mod-item';
                    row.innerHTML = `
                        <span style="display:flex; align-items:center;">
                            <input type="checkbox" hidden onchange="toggleMod(${{mod.id}})">
                            <span>
                                <div class="checkbox"></div>
                            </span>
                            ${{mod.name}}
                        </span>
                        <span style="font-weight:600;">+${{mod.price}}</span>
                    `;
                    list.appendChild(row);
                }});
                updateModTotal();
                modModal.classList.add('visible');
            }}

            window.toggleMod = (id) => {{
                if (selectedMods.has(id)) selectedMods.delete(id);
                else selectedMods.add(id);
                updateModTotal();
            }};

            function updateModTotal() {{
                let p = currentProd.price;
                currentProd.modifiers.forEach(m => {{
                    if(selectedMods.has(m.id)) p += m.price;
                }});
                document.getElementById('mod-total-price').textContent = p.toFixed(2) + ' грн';
            }}

            document.getElementById('mod-add-btn').onclick = () => {{
                const mods = currentProd.modifiers.filter(m => selectedMods.has(m.id));
                addToCart(currentProd, mods);
                modModal.classList.remove('visible');
            }};

            // === CHECKOUT ===
            const checkoutModal = document.getElementById('checkout-modal');
            
            document.getElementById('checkout-btn').onclick = () => {{
                // Hide cart, show checkout
                cartSidebar.classList.remove('open');
                checkoutModal.classList.add('visible');
            }};

            // Logic for toggling fields
            const addrGroup = document.getElementById('address-group');
            const timeGroup = document.getElementById('specific-time-group');
            const addrInput = document.getElementById('address');

            document.querySelectorAll('input[name="delivery_type"]').forEach(el => {{
                el.addEventListener('change', (e) => {{
                    const isDel = e.target.value === 'delivery';
                    addrGroup.style.display = isDel ? 'block' : 'none';
                    addrInput.required = isDel;
                }});
            }});

            document.querySelectorAll('input[name="delivery_time"]').forEach(el => {{
                el.addEventListener('change', (e) => {{
                    timeGroup.style.display = e.target.value === 'specific' ? 'block' : 'none';
                }});
            }});

            // Checkout Submit
            document.getElementById('checkout-form').onsubmit = async (e) => {{
                e.preventDefault();
                const btn = document.getElementById('place-order-submit');
                const originalText = btn.textContent;
                btn.disabled = true; 
                btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Обробка...';

                // Gather Data
                const formData = new FormData(e.target);
                const data = {{
                    items: Object.values(cart),
                    customer_name: document.getElementById('customer_name').value,
                    phone_number: document.getElementById('phone_number').value,
                    delivery_type: formData.get('delivery_type'), // delivery / pickup
                    is_delivery: formData.get('delivery_type') === 'delivery',
                    address: document.getElementById('address').value,
                    delivery_time: formData.get('delivery_time') === 'asap' ? "Якнайшвидше" : document.getElementById('specific_time_input').value,
                    payment_method: formData.get('payment_method')
                }};

                try {{
                    const res = await fetch('/api/place_order', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await res.json();
                    
                    if (res.ok) {{
                        // Success
                        checkoutModal.classList.remove('visible');
                        cart = {{}};
                        saveCart();
                        updateCartUI();
                        alert(`✅ Дякуємо! Ваше замовлення #${{result.order_id}} прийнято.`);
                    }} else {{
                        alert(`❌ Помилка: ${{result.detail}}`);
                    }}
                }} catch (err) {{
                    alert("❌ Помилка з'єднання з сервером.");
                }} finally {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                }}
            }};

            // === PAGE MODAL ===
            const pageModal = document.getElementById('page-modal');
            const pageTitle = document.getElementById('page-modal-title');
            const pageBody = document.getElementById('page-modal-body');

            document.querySelectorAll('.menu-popup-trigger').forEach(link => {{
                link.onclick = async (ev) => {{
                    ev.preventDefault();
                    const id = link.dataset.itemId;
                    pageModal.classList.add('visible');
                    pageTitle.textContent = 'Завантаження...';
                    pageBody.innerHTML = '';
                    
                    try {{
                        const res = await fetch('/api/page/' + id);
                        if(res.ok) {{
                            const data = await res.json();
                            pageTitle.textContent = data.title;
                            pageBody.innerHTML = data.content;
                        }}
                    }} catch(e) {{ pageTitle.textContent = 'Помилка'; }}
                }};
            }});

            // === UI HELPERS ===
            function setupEventListeners() {{
                // Sidebars
                document.getElementById('cart-toggle').onclick = () => cartSidebar.classList.add('open');
                document.getElementById('close-cart-btn').onclick = () => cartSidebar.classList.remove('open');
                
                // Close Modals
                document.querySelectorAll('.close-modal').forEach(btn => {{
                    btn.onclick = function() {{
                        this.closest('.modal-overlay').classList.remove('visible');
                    }};
                }});
                
                // Close on overlay click
                document.querySelectorAll('.modal-overlay').forEach(overlay => {{
                    overlay.onclick = (e) => {{
                        if(e.target === overlay) overlay.classList.remove('visible');
                    }};
                }});

                // Scroll Spy
                setupScrollSpy();
                
                // Scroll Top
                const scrollBtn = document.getElementById('scroll-to-top');
                window.onscroll = () => {{
                    if (window.scrollY > 300) scrollBtn.classList.add('visible');
                    else scrollBtn.classList.remove('visible');
                }};
                scrollBtn.onclick = () => window.scrollTo({{top:0, behavior:'smooth'}});
                
                // Phone Autocomplete (Simple)
                const phoneInput = document.getElementById('phone_number');
                phoneInput.onblur = async () => {{
                    if(phoneInput.value.length > 9) {{
                        try {{
                            const r = await fetch('/api/customer_info/'+encodeURIComponent(phoneInput.value));
                            if(r.ok) {{
                                const d = await r.json();
                                if(d.customer_name) document.getElementById('customer_name').value = d.customer_name;
                                if(d.address) document.getElementById('address').value = d.address;
                            }}
                        }} catch(e){{}}
                    }}
                }};
            }}

            function setupScrollSpy() {{
                const links = document.querySelectorAll('.category-nav a');
                const observer = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) {{
                            links.forEach(l => l.classList.remove('active'));
                            const activeLink = document.querySelector(`.category-nav a[href="#${{entry.target.id}}"]`);
                            if(activeLink) {{
                                activeLink.classList.add('active');
                                activeLink.scrollIntoView({{ behavior: 'smooth', inline: 'center', block: 'nearest' }});
                            }}
                        }}
                    }});
                }}, {{ rootMargin: "-100px 0px -70% 0px" }});

                document.querySelectorAll('.category-section').forEach(section => {{
                    observer.observe(section);
                }});
            }}

            init();
        }});
    </script>
</body>
</html>
"""
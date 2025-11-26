# tpl_client_web.py

WEB_ORDER_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{site_title}</title>
    <meta name="description" content="{seo_description}">
    <meta name="keywords" content="{seo_keywords}">
    
    <link rel="apple-touch-icon" sizes="180x180" href="/static/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/favicons/favicon-16x16.png">
    <link rel="manifest" href="/static/favicons/site.webmanifest">
    <link rel="shortcut icon" href="/static/favicons/favicon.ico">
    
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
        --surface-glass: rgba(255, 255, 255, 0.85);
        --border-light: rgba(0, 0, 0, 0.06);
        
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.04);
        --shadow-md: 0 8px 24px rgba(0,0,0,0.08);
        --shadow-lg: 0 15px 40px rgba(0,0,0,0.12);
        
        /* --- Geometry --- */
        --radius-lg: 20px;
        --radius-md: 14px;
        --radius-sm: 8px;
        
        /* --- Animation --- */
        --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
        
        /* --- Fonts --- */
        --font-sans: '{font_family_sans_val}', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        --font-serif: '{font_family_serif_val}', serif;
      }}
      
      html {{ scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }}
      * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; outline: none; }}
      
      body {{
        margin: 0;
        background-color: var(--bg-color);
        /* Subtle Mesh Gradient */
        background-image: 
            radial-gradient(at 0% 0%, color-mix(in srgb, var(--primary), transparent 96%), transparent 50%),
            radial-gradient(at 100% 100%, color-mix(in srgb, var(--secondary), transparent 96%), transparent 50%);
        background-attachment: fixed;
        color: var(--text-main);
        font-family: var(--font-sans);
        display: flex; flex-direction: column; min-height: 100vh;
        -webkit-font-smoothing: antialiased;
        font-size: 15px;
      }}

      h1, h2, h3, .serif {{ font-family: var(--font-serif); margin: 0; }}
      button, input {{ font-family: var(--font-sans); }}

      /* --- PREMIUM HEADER --- */
      header {{
          position: relative;
          height: 40vh; min-height: 300px; max-height: 450px;
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          text-align: center; color: white;
          border-radius: 0 0 40px 40px;
          overflow: hidden;
          box-shadow: 0 10px 40px rgba(0,0,0,0.15);
          margin-bottom: 20px;
      }}
      .header-bg {{
          position: absolute; inset: 0;
          background-image: var(--header-img);
          background-size: cover; background-position: center;
          z-index: 0; transition: transform 10s ease;
      }}
      header:hover .header-bg {{ transform: scale(1.05); }}
      header::after {{
          content: ''; position: absolute; inset: 0;
          background: linear-gradient(to bottom, rgba(0,0,0,0.2), rgba(0,0,0,0.6));
          z-index: 1;
      }}
      
      .header-content {{ position: relative; z-index: 2; width: 90%; max-width: 800px; animation: fadeUp 0.8s var(--ease-out); }}
      .header-logo {{ 
          height: 100px; width: auto; margin-bottom: 15px; 
          filter: drop-shadow(0 8px 20px rgba(0,0,0,0.25)); 
      }}
      header h1 {{ 
          font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 700; 
          text-shadow: 0 4px 20px rgba(0,0,0,0.3); line-height: 1.1;
      }}

      /* --- NAVIGATION --- */
      .category-nav-wrapper {{
          position: sticky; top: 15px; z-index: 90;
          display: flex; justify-content: center;
          padding: 0 15px; margin-bottom: 30px;
      }}
      .category-nav {{
          display: flex; gap: 6px; overflow-x: auto; 
          padding: 6px; border-radius: 100px;
          background: rgba(255, 255, 255, 0.8); 
          backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px);
          border: 1px solid rgba(255,255,255,0.5);
          box-shadow: var(--shadow-md);
          scrollbar-width: none; max-width: 100%;
      }}
      .category-nav::-webkit-scrollbar {{ display: none; }}
      
      .category-nav a {{
          color: var(--nav-text); text-decoration: none; padding: 8px 20px; 
          border-radius: 50px; font-weight: 600; white-space: nowrap; font-size: 0.9rem;
          transition: all 0.3s var(--ease-out);
      }}
      .category-nav a:hover {{ background: rgba(0,0,0,0.05); }}
      .category-nav a.active {{ 
          background: var(--primary); color: white; 
          box-shadow: 0 4px 15px color-mix(in srgb, var(--primary), transparent 60%);
      }}

      /* --- MAIN CONTENT --- */
      .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
      
      .category-section {{ margin-bottom: 50px; scroll-margin-top: 100px; }}
      .category-title {{ 
          font-size: 1.8rem; color: var(--text-main); margin-bottom: 20px; 
          font-weight: 700; display: flex; align-items: center; gap: 15px;
      }}
      .category-title::after {{ 
          content: ''; height: 1px; background: var(--secondary); flex-grow: 1; opacity: 0.6; 
      }}

      /* --- PRODUCT GRID (Adaptive) --- */
      .products-grid {{ 
          display: grid; 
          /* PC: 3-4 items, Mobile: 2 items (min 160px) */
          grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); 
          gap: 24px; 
      }}

      /* --- PRODUCT CARD --- */
      .product-card {{
          background: var(--surface); border-radius: var(--radius-md);
          overflow: hidden; display: flex; flex-direction: column;
          box-shadow: var(--shadow-sm); border: 1px solid var(--border-light);
          transition: transform 0.3s var(--ease-out), box-shadow 0.3s var(--ease-out);
          height: 100%; position: relative;
      }}
      .product-card:hover {{ 
          transform: translateY(-5px); box-shadow: var(--shadow-md); z-index: 2;
      }}

      .product-image-wrapper {{ 
          width: 100%; aspect-ratio: 4/3; overflow: hidden; 
          background: #f5f5f7; position: relative;
      }}
      .product-image {{ 
          width: 100%; height: 100%; object-fit: cover; 
          transition: transform 0.5s var(--ease-out); 
      }}
      .product-card:hover .product-image {{ transform: scale(1.08); }}

      .product-info {{ 
          padding: 16px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; 
      }}
      .product-name {{ 
          font-size: 1.1rem; font-weight: 700; margin: 0 0 6px; 
          line-height: 1.25; color: var(--text-main);
      }}
      .product-desc {{ 
          font-size: 0.85rem; color: #64748b; line-height: 1.5; margin-bottom: 12px; 
          display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
      }}

      .product-footer {{ 
          display: flex; justify-content: space-between; align-items: center; 
          margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border-light);
      }}
      .product-price {{ font-size: 1.15rem; font-weight: 800; color: var(--text-main); }}
      
      .add-btn {{
          background: var(--primary); color: white; border: none;
          padding: 8px 16px; border-radius: var(--radius-sm);
          font-weight: 600; cursor: pointer; font-size: 0.9rem;
          display: flex; align-items: center; gap: 6px;
          transition: all 0.2s var(--ease-out);
      }}
      .add-btn:hover {{ background: color-mix(in srgb, var(--primary), black 10%); transform: translateY(-1px); }}
      .add-btn:active {{ transform: scale(0.95); }}
      .add-btn i {{ font-size: 0.9rem; }}

      /* --- MOBILE SPECIFIC OVERRIDES (Compact) --- */
      @media (max-width: 768px) {{
          header {{ height: 30vh; min-height: 220px; border-radius: 0 0 25px 25px; margin-bottom: 15px; }}
          header h1 {{ font-size: 2rem; }}
          .header-logo {{ height: 60px; margin-bottom: 10px; }}
          
          .category-nav-wrapper {{ padding: 0 10px; top: 10px; margin-bottom: 20px; }}
          .category-nav a {{ padding: 8px 16px; font-size: 0.85rem; }}
          .category-title {{ font-size: 1.5rem; margin-bottom: 15px; }}
          
          /* Two columns on mobile */
          .products-grid {{ 
              grid-template-columns: repeat(2, 1fr); 
              gap: 12px; padding: 0 5px;
          }}
          
          .product-info {{ padding: 12px; }}
          .product-name {{ font-size: 0.95rem; margin-bottom: 4px; }}
          .product-desc {{ font-size: 0.75rem; margin-bottom: 10px; -webkit-line-clamp: 2; }}
          .product-price {{ font-size: 1rem; }}
          
          /* Icon only button on mobile to save space */
          .add-btn {{ padding: 0; width: 32px; height: 32px; border-radius: 50%; justify-content: center; }}
          .add-btn span {{ display: none; }}
          .add-btn i {{ font-size: 1rem; }}
          
          .container {{ padding: 0 10px; }}
          .category-section {{ margin-bottom: 40px; }}
      }}

      /* --- FLOATING CART --- */
      #cart-toggle {{
          position: fixed; bottom: 30px; right: 30px; width: 64px; height: 64px;
          background: var(--primary); color: white; border-radius: 50%; border: none;
          box-shadow: 0 12px 30px rgba(0,0,0,0.25); cursor: pointer; z-index: 99;
          display: flex; justify-content: center; align-items: center; 
          transition: transform 0.3s var(--ease-out);
      }}
      #cart-toggle:hover {{ transform: scale(1.1); }}
      #cart-toggle i {{ font-size: 1.6rem; }}
      #cart-count {{ 
          position: absolute; top: 0; right: 0; background: white; color: var(--primary);
          width: 24px; height: 24px; border-radius: 50%; font-size: 0.8rem; font-weight: 800; 
          display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
      }}
      
      @media (max-width: 768px) {{
          #cart-toggle {{ width: 56px; height: 56px; bottom: 20px; right: 20px; }}
          #cart-toggle i {{ font-size: 1.4rem; }}
      }}

      /* --- SIDEBAR (Cart) --- */
      #cart-sidebar {{
          position: fixed; top: 0; right: -100%; width: 100%; max-width: 420px; height: 100%;
          z-index: 1000; display: flex; flex-direction: column;
          transition: right 0.4s var(--ease-out);
          box-shadow: -10px 0 40px rgba(0,0,0,0.15);
      }}
      #cart-sidebar.open {{ right: 0; }}
      @media (max-width: 768px) {{ #cart-sidebar {{ max-width: 100%; }} }}
      
      .cart-content-wrapper {{
          height: 100%; display: flex; flex-direction: column;
          background: rgba(255, 255, 255, 0.95); 
          backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
      }}
      
      .cart-header {{ 
          padding: 20px 25px; display: flex; justify-content: space-between; align-items: center; 
          background: rgba(255,255,255,0.6); border-bottom: 1px solid var(--border-light);
      }}
      .cart-header h3 {{ font-size: 1.3rem; font-weight: 700; }}
      
      .cart-items {{ flex-grow: 1; overflow-y: auto; padding: 20px; }}
      
      .cart-item {{ 
          display: flex; justify-content: space-between; align-items: center; 
          margin-bottom: 15px; padding: 15px; background: white; 
          border-radius: 12px; box-shadow: var(--shadow-sm);
          animation: fadeUp 0.3s ease;
      }}
      
      .cart-item-info {{ flex-grow: 1; padding-right: 10px; }}
      .cart-item-name {{ font-weight: 600; font-size: 0.95rem; display: block; margin-bottom: 4px; }}
      .cart-item-mods {{ font-size: 0.8rem; color: #888; }}
      .cart-item-price {{ color: var(--primary); font-weight: 700; font-size: 0.95rem; margin-top: 4px; display: block; }}
      
      .qty-control {{ display: flex; align-items: center; gap: 8px; background: #f8fafc; padding: 4px; border-radius: 8px; }}
      .qty-btn {{ 
          width: 28px; height: 28px; background: white; border-radius: 6px; border: 1px solid #eee; 
          cursor: pointer; display: flex; align-items: center; justify-content: center; font-weight: 700;
      }}
      
      .cart-footer {{ padding: 25px; background: white; box-shadow: 0 -5px 20px rgba(0,0,0,0.03); }}
      .cart-total-row {{ display: flex; justify-content: space-between; font-size: 1.3rem; font-weight: 800; margin-bottom: 20px; }}
      
      .main-btn {{ 
          width: 100%; padding: 16px; background: var(--primary); color: white; 
          border: none; border-radius: var(--radius-md); font-size: 1.1rem; font-weight: 600; 
          cursor: pointer; transition: all 0.2s; display: flex; justify-content: center; align-items: center; gap: 10px;
      }}
      .main-btn:active {{ transform: scale(0.98); }}
      .main-btn:disabled {{ background: #e2e8f0; color: #94a3b8; cursor: not-allowed; }}

      /* --- MODALS (Desktop Center / Mobile Bottom Sheet) --- */
      .modal-overlay {{
          position: fixed; top: 0; left: 0; width: 100%; height: 100%;
          background: rgba(0,0,0,0.5); backdrop-filter: blur(5px);
          z-index: 2000; display: none; justify-content: center; align-items: center;
          opacity: 0; transition: opacity 0.3s ease;
      }}
      .modal-overlay.visible {{ display: flex; opacity: 1; }}
      
      .modal-content {{
          background: #fff; padding: 30px; border-radius: 24px; 
          width: 90%; max-width: 480px; max-height: 85vh; overflow-y: auto; 
          transform: scale(0.95); opacity: 0; transition: all 0.3s var(--ease-out);
          box-shadow: var(--shadow-lg);
      }}
      .modal-overlay.visible .modal-content {{ transform: scale(1); opacity: 1; }}
      
      @media (max-width: 768px) {{
          .modal-overlay {{ align-items: flex-end; }}
          .modal-content {{ 
              width: 100%; max-width: 100%; border-radius: 24px 24px 0 0; 
              padding: 25px; max-height: 85vh; transform: translateY(100%);
          }}
          .modal-overlay.visible .modal-content {{ transform: translateY(0); }}
      }}
      
      /* Inputs & Forms */
      .form-group {{ margin-bottom: 20px; }}
      .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
      
      .form-control {{ 
          width: 100%; padding: 14px; border: 1px solid #e2e8f0; border-radius: 12px; 
          font-size: 1rem; font-family: var(--font-sans); background: #f8fafc;
      }}
      .form-control:focus {{ outline: none; background: white; border-color: var(--primary); }}
      
      .radio-group {{ display: flex; gap: 10px; }}
      .radio-group label {{ 
          flex: 1; padding: 12px; text-align: center; cursor: pointer; 
          border-radius: 12px; border: 1px solid #f1f5f9; background: white;
          color: #64748b; font-weight: 500; transition: all 0.2s;
          display: flex; flex-direction: column; gap: 5px; font-size: 0.9rem;
      }}
      .radio-group input {{ display: none; }}
      .radio-group input:checked + label {{ 
          background: color-mix(in srgb, var(--primary), white 95%); 
          border-color: var(--primary); color: var(--primary); font-weight: 700;
      }}

      .modifier-item {{
          display: flex; justify-content: space-between; align-items: center;
          padding: 12px 0; border-bottom: 1px solid #f1f5f9; cursor: pointer;
      }}
      .checkbox-circle {{
          width: 22px; height: 22px; border: 2px solid #cbd5e1; border-radius: 6px;
          display: flex; align-items: center; justify-content: center; margin-right: 12px;
          transition: all 0.2s;
      }}
      .modifier-item.selected .checkbox-circle {{ border-color: var(--primary); background: var(--primary); }}
      .modifier-item.selected .checkbox-circle::after {{ content: '✓'; color: white; font-size: 12px; font-weight: 900; }}

      /* --- FOOTER --- */
      footer {{ 
          background: var(--footer-bg); color: var(--footer-text); 
          padding: 60px 20px 30px; margin-top: auto; 
      }}
      .footer-content {{ 
          display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
          gap: 40px; max-width: var(--container-width); margin: 0 auto; 
      }}
      .footer-section h4 {{ 
          font-size: 0.9rem; margin-bottom: 20px; opacity: 0.6; 
          text-transform: uppercase; font-weight: 700; letter-spacing: 1px;
      }}
      .footer-link {{ 
          display: flex; align-items: center; gap: 10px; margin-bottom: 12px; 
          color: inherit; text-decoration: none; opacity: 0.8; transition: opacity 0.2s;
      }}
      .footer-link:hover {{ opacity: 1; }}
      
      .social-links {{ display: flex; gap: 10px; }}
      .social-links a {{ 
          display: flex; width: 40px; height: 40px; border-radius: 10px; 
          background: rgba(255,255,255,0.1); align-items: center; justify-content: center; 
          color: inherit; text-decoration: none; transition: all 0.3s;
      }}
      .social-links a:hover {{ background: var(--primary); color: white; }}

      /* --- ANIMATIONS & UTILS --- */
      @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}
      @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
      .spinner {{ 
          border: 2px solid rgba(0,0,0,0.1); border-top: 2px solid var(--primary); 
          border-radius: 50%; width: 24px; height: 24px; animation: spin 0.8s linear infinite; 
      }}
    </style>
</head>
<body>
    <header>
        <div class="header-bg"></div>
        <div class="header-content">
            <div class="header-logo-container">{logo_html}</div>
            <h1>{site_title}</h1>
        </div>
    </header>
    
    <div class="category-nav-wrapper">
        <nav class="category-nav" id="category-nav"></nav>
    </div>
    
    <div class="container">
        <main id="menu">
            <div style="text-align:center; padding: 80px;"><div class="spinner"></div></div>
        </main>
    </div>

    <button id="cart-toggle">
        <i class="fa-solid fa-bag-shopping"></i>
        <span id="cart-count">0</span>
    </button>

    <aside id="cart-sidebar">
        <div class="cart-content-wrapper">
            <div class="cart-header">
                <h3 style="margin:0;">Кошик</h3>
                <button id="close-cart-btn" style="background:none; border:none; font-size:1.5rem; cursor:pointer; color: #94a3b8;">&times;</button>
            </div>
            <div id="cart-items-container" class="cart-items"></div>
            <div class="cart-footer">
                <div class="cart-total-row">
                    <span>Всього:</span>
                    <span id="cart-total-price">0.00 грн</span>
                </div>
                <button id="checkout-btn" class="main-btn" disabled>Оформити замовлення</button>
            </div>
        </div>
    </aside>

    <div id="modifier-modal" class="modal-overlay">
        <div class="modal-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h3 id="mod-product-name" style="font-size:1.2rem; margin:0;">Назва</h3>
                <span class="close-modal" style="font-size:1.5rem; cursor:pointer; color:#cbd5e1;">&times;</span>
            </div>
            <p style="color:#64748b; margin-bottom:15px; font-size:0.9rem;">Додайте інгредієнти:</p>
            <div id="mod-list" style="margin-bottom: 25px;"></div>
            <button id="mod-add-btn" class="main-btn" style="width:100%;">
                <span>Додати</span>
                <span id="mod-total-price" style="background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:6px; font-size:0.9rem; margin-left:auto;"></span>
            </button>
        </div>
    </div>

    <div id="checkout-modal" class="modal-overlay">
        <div class="modal-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:25px;">
                <h3 style="font-size:1.4rem; margin:0;">Оформлення</h3>
                <span class="close-modal" style="font-size:1.5rem; cursor:pointer; color:#cbd5e1;">&times;</span>
            </div>
            
            <form id="checkout-form">
                <div class="form-group">
                    <label>Отримання</label>
                    <div class="radio-group">
                        <input type="radio" id="delivery" name="delivery_type" value="delivery" checked>
                        <label for="delivery"><i class="fa-solid fa-motorcycle"></i> Доставка</label>
                        <input type="radio" id="pickup" name="delivery_type" value="pickup">
                        <label for="pickup"><i class="fa-solid fa-shop"></i> Самовивіз</label>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Контакти</label>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <input type="text" id="customer_name" class="form-control" placeholder="Ваше ім'я" required>
                        <input type="tel" id="phone_number" class="form-control" placeholder="Телефон" required>
                    </div>
                </div>
                
                <div id="address-group" class="form-group">
                    <label>Адреса</label>
                    <input type="text" id="address" class="form-control" placeholder="Вулиця, будинок, під'їзд..." required>
                </div>

                <div class="form-group">
                    <label>Час</label>
                    <div class="radio-group">
                        <input type="radio" id="asap" name="delivery_time" value="asap" checked>
                        <label for="asap"><i class="fa-solid fa-fire"></i> Зараз</label>
                        <input type="radio" id="specific" name="delivery_time" value="specific">
                        <label for="specific"><i class="fa-regular fa-clock"></i> На час</label>
                    </div>
                </div>
                <div id="specific-time-group" class="form-group" style="display:none;">
                    <input type="text" id="specific_time_input" class="form-control" placeholder="Наприклад: 19:00">
                </div>

                <div class="form-group">
                    <label>Оплата</label>
                    <div class="radio-group">
                        <input type="radio" id="pay_cash" name="payment_method" value="cash" checked>
                        <label for="pay_cash"><i class="fa-solid fa-money-bill-wave"></i> Готівка</label>
                        <input type="radio" id="pay_card" name="payment_method" value="card">
                        <label for="pay_card"><i class="fa-regular fa-credit-card"></i> Картка</label>
                    </div>
                </div>

                <button type="submit" id="place-order-submit" class="main-btn" style="margin-top:10px;">
                    Підтвердити
                </button>
            </form>
        </div>
    </div>

    <div id="page-modal" class="modal-overlay">
        <div class="modal-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; padding-bottom:10px; border-bottom:1px solid #f1f5f9;">
                <h3 id="page-modal-title" style="margin:0; font-size:1.3rem;"></h3>
                <span class="close-modal" style="font-size:1.5rem; cursor:pointer; color:#cbd5e1;">&times;</span>
            </div>
            <div id="page-modal-body" class="page-content-body" style="line-height:1.6; color:#475569;"></div>
        </div>
    </div>

    <footer>
        <div class="footer-content">
            <div class="footer-section">
                <h4>Контакти</h4>
                <a href="#" class="footer-link"><i class="fa-solid fa-location-dot"></i> <span>{footer_address}</span></a>
                <a href="tel:{footer_phone}" class="footer-link"><i class="fa-solid fa-phone"></i> <span>{footer_phone}</span></a>
                <div class="footer-link"><i class="fa-regular fa-clock"></i> <span>{working_hours}</span></div>
            </div>
            <div class="footer-section">
                <h4>Соціальні мережі</h4>
                <div class="social-links">{social_links_html}</div>
            </div>
        </div>
        <div style="text-align:center; margin-top:50px; opacity:0.5; font-size:0.8rem;">
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
            
            fetchMenu();

            async function fetchMenu() {{
                try {{
                    const res = await fetch('/api/menu');
                    if (!res.ok) throw new Error("Failed");
                    menuData = await res.json();
                    renderMenu();
                    updateCartView();
                }} catch (e) {{
                    menuContainer.innerHTML = '<div style="text-align:center; padding:60px; color:#94a3b8;">Не вдалося завантажити меню.</div>';
                }}
            }}

            function renderMenu() {{
                menuContainer.innerHTML = '';
                const nav = document.getElementById('category-nav');
                nav.innerHTML = '';

                menuData.categories.forEach((cat, idx) => {{
                    const link = document.createElement('a');
                    link.href = `#cat-${{cat.id}}`;
                    link.textContent = cat.name;
                    if(idx===0) link.classList.add('active');
                    nav.appendChild(link);

                    const section = document.createElement('div');
                    section.id = `cat-${{cat.id}}`;
                    section.className = 'category-section';
                    section.innerHTML = `<h2 class="category-title">${{cat.name}}</h2>`;

                    const grid = document.createElement('div');
                    grid.className = 'products-grid';

                    const products = menuData.products.filter(p => p.category_id === cat.id);
                    if (products.length > 0) {{
                        products.forEach(prod => {{
                            const card = document.createElement('div');
                            card.className = 'product-card';
                            const img = prod.image_url ? `/${{prod.image_url}}` : '/static/images/placeholder.jpg';
                            const prodJson = JSON.stringify(prod).replace(/"/g, '&quot;');
                            
                            card.innerHTML = `
                                <div class="product-image-wrapper"><img src="${{img}}" class="product-image" loading="lazy"></div>
                                <div class="product-info">
                                    <div class="product-header">
                                        <div class="product-name">${{prod.name}}</div>
                                        <div class="product-desc">${{prod.description || ''}}</div>
                                    </div>
                                    <div class="product-footer">
                                        <div class="product-price">${{prod.price}} грн</div>
                                        <button class="add-btn" data-product="${{prodJson}}" onclick="handleClick(this)">
                                            <span>Додати</span> <i class="fa-solid fa-plus"></i>
                                        </button>
                                    </div>
                                </div>
                            `;
                            grid.appendChild(card);
                        }});
                        section.appendChild(grid);
                        menuContainer.appendChild(section);
                    }}
                }});
                setupScrollSpy();
            }}

            window.handleClick = (btn) => {{
                const prod = JSON.parse(btn.dataset.product);
                
                const originalHTML = btn.innerHTML;
                btn.classList.add('added');
                btn.innerHTML = '<i class="fa-solid fa-check"></i>';
                
                setTimeout(() => {{ 
                    btn.classList.remove('added'); 
                    btn.innerHTML = originalHTML;
                }}, 1200);

                if (prod.modifiers && prod.modifiers.length > 0) openModModal(prod);
                else addToCart(prod, []);
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
                
                const toggle = document.getElementById('cart-toggle');
                toggle.style.transform = 'scale(1.15)';
                setTimeout(() => toggle.style.transform = 'scale(1)', 200);
            }}

            function updateCartView() {{
                cartItemsContainer.innerHTML = '';
                let total = 0;
                let count = 0;
                const items = Object.values(cart);
                
                if (items.length === 0) {{
                    cartItemsContainer.innerHTML = '<div style="text-align:center;color:#94a3b8;margin-top:60px;"><i class="fa-solid fa-basket-shopping" style="font-size:2.5rem; opacity:0.2; margin-bottom:10px;"></i><p>Кошик порожній</p></div>';
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
                            <span class="cart-item-price">${{item.price}} грн</span>
                        </div>
                        <div class="qty-control">
                            <button class="qty-btn" onclick="updateQty('${{item.key}}', -1)">-</button>
                            <div class="qty-val">${{item.quantity}}</div>
                            <button class="qty-btn" onclick="updateQty('${{item.key}}', 1)">+</button>
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

            // Modals
            const modModal = document.getElementById('modifier-modal');
            const modList = document.getElementById('mod-list');
            
            function openModModal(prod) {{
                currentProd = prod;
                selectedMods.clear();
                document.getElementById('mod-product-name').textContent = prod.name;
                modList.innerHTML = '';
                
                prod.modifiers.forEach(mod => {{
                    const div = document.createElement('div');
                    div.className = 'modifier-item';
                    div.onclick = () => {{
                        toggleMod(mod.id); 
                        div.classList.toggle('selected', selectedMods.has(mod.id));
                    }};
                    div.innerHTML = `
                        <div style="display:flex; align-items:center;">
                            <div class="checkbox-circle"></div>
                            <span style="font-weight:500; font-size:0.95rem; color:#334155;">${{mod.name}}</span>
                        </div>
                        <b style="color:var(--primary); font-size:0.9rem;">+${{mod.price}}</b>
                    `;
                    modList.appendChild(div);
                }});
                updateModPrice();
                modModal.classList.add('visible');
            }}
            
            function toggleMod(id) {{
                if (selectedMods.has(id)) selectedMods.delete(id);
                else selectedMods.add(id);
                updateModPrice();
            }}
            
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

            // Checkout
            const checkoutModal = document.getElementById('checkout-modal');
            const addressGroup = document.getElementById('address-group');
            const timeGroup = document.getElementById('specific-time-group');
            
            checkoutBtn.onclick = () => {{
                cartSidebar.classList.remove('open');
                checkoutModal.classList.add('visible');
            }};
            
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
                const originalText = btn.innerText;
                btn.disabled = true; 
                btn.innerHTML = '<div class="spinner" style="border-color:white; border-top-color:transparent;"></div>';
                
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
                        method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(data)
                    }});
                    if(res.ok) {{
                        alert('Дякуємо! Замовлення успішно прийнято.');
                        cart = {{}}; saveCart(); updateCartView();
                        checkoutModal.classList.remove('visible');
                    }} else {{ alert('Помилка. Спробуйте ще раз.'); }}
                }} catch(err) {{ alert('Помилка з`єднання'); }} 
                finally {{ btn.disabled = false; btn.innerText = originalText; }}
            }};

            // Utils
            document.getElementById('cart-toggle').onclick = () => cartSidebar.classList.add('open');
            document.getElementById('close-cart-btn').onclick = () => cartSidebar.classList.remove('open');
            
            document.querySelectorAll('.close-modal').forEach(btn => {{
                btn.onclick = (e) => e.target.closest('.modal-overlay').classList.remove('visible');
            }});

            const pageModal = document.getElementById('page-modal');
            document.querySelectorAll('.menu-popup-trigger').forEach(link => {{
                link.onclick = async (e) => {{
                    e.preventDefault();
                    pageModal.classList.add('visible');
                    document.getElementById('page-modal-body').innerHTML = '<div style="text-align:center; padding:40px;"><div class="spinner"></div></div>';
                    document.getElementById('page-modal-title').innerText = link.innerText;
                    try {{
                        const res = await fetch('/api/page/' + link.dataset.itemId);
                        if(res.ok) {{
                            const d = await res.json();
                            document.getElementById('page-modal-title').innerText = d.title;
                            document.getElementById('page-modal-body').innerHTML = d.content;
                        }}
                    }} catch(err) {{ document.getElementById('page-modal-body').innerText = 'Помилка.'; }}
                }};
            }});

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
                }}, {{rootMargin: '-30% 0px -70% 0px'}});
                document.querySelectorAll('.category-section').forEach(s => observer.observe(s));
            }}
        }});
    </script>
</body>
</html>
"""
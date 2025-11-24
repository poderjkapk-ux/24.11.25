# staff_templates.py

# --- СТРАНИЦА ВХОДА ---
STAFF_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Вхід для персоналу</title>
    
    <link rel="manifest" href="/staff/manifest.json">
    <meta name="theme-color" content="#333333">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-icon" href="/static/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" href="/static/favicons/favicon-32x32.png">

    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            background: #f0f2f5; 
        }
        .login-card { 
            background: white; 
            padding: 2rem; 
            border-radius: 15px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
            width: 90%; 
            max-width: 350px; 
            text-align: center; 
        }
        h2 { margin-top: 0; color: #333; margin-bottom: 1.5rem; }
        input { 
            width: 100%; 
            padding: 14px; 
            margin: 8px 0; 
            border: 1px solid #ddd; 
            border-radius: 12px; 
            box-sizing: border-box; 
            font-size: 16px; 
            background: #fafafa; 
            -webkit-appearance: none; 
        }
        input:focus { border-color: #333; outline: none; background: #fff; }
        button { 
            width: 100%; 
            padding: 14px; 
            background: #333; 
            color: white; 
            border: none; 
            border-radius: 12px; 
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer; 
            margin-top: 15px; 
            transition: background 0.2s; 
            -webkit-appearance: none; 
        }
        button:hover { background: #000; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔐 Вхід для персоналу</h2>
        <form action="/staff/login" method="post">
            <input type="tel" name="phone" placeholder="Номер телефону" required autocomplete="username">
            <input type="password" name="password" placeholder="Пароль" required autocomplete="current-password">
            <button type="submit">Увійти</button>
        </form>
    </div>
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('SW зареєстровано:', reg.scope))
            .catch(err => console.log('SW помилка:', err));
        });
      }
    </script>
</body>
</html>
"""

# --- ГЛАВНАЯ ПАНЕЛЬ (DASHBOARD) ---
STAFF_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{site_title} - Персонал</title>
    
    <link rel="manifest" href="/staff/manifest.json">
    <meta name="theme-color" content="#333333">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-icon" href="/static/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" href="/static/favicons/favicon-32x32.png">
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <style>
        :root {{ --primary: #333; --bg: #f4f4f4; --white: #fff; --green: #27ae60; --red: #e74c3c; --blue: #3498db; --orange: #f39c12; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: var(--bg); padding-bottom: 80px; -webkit-tap-highlight-color: transparent; user-select: none; }}
        
        /* HEADER */
        .dashboard-header {{ background: var(--white); padding: 15px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); position: sticky; top: 0; z-index: 100; }}
        .user-info h3 {{ margin: 0; font-size: 1.1rem; color: var(--primary); }}
        .role-badge {{ font-size: 0.75rem; background: #eee; padding: 3px 8px; border-radius: 6px; color: #555; display: inline-block; margin-top: 4px; }}
        .shift-btn {{ border: none; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .shift-btn.on {{ background: #e8f5e9; color: var(--green); border: 1px solid var(--green); }}
        .shift-btn.off {{ background: #ffebee; color: var(--red); border: 1px solid var(--red); }}

        /* CONTENT */
        #main-view {{ padding: 15px; max-width: 800px; margin: 0 auto; min-height: 70vh; }}
        .empty-state {{ text-align: center; color: #999; margin-top: 50px; font-size: 0.9rem; display: flex; flex-direction: column; align-items: center; gap: 10px; }}
        .empty-state i {{ font-size: 2rem; opacity: 0.3; }}
        
        /* CARDS */
        .grid-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }}
        .card {{ background: var(--white); border-radius: 12px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); cursor: pointer; transition: transform 0.1s; border: 1px solid transparent; }}
        .card:active {{ transform: scale(0.96); background: #f9f9f9; }}
        
        .table-card {{ text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100px; }}
        .table-card .card-title {{ font-weight: 700; margin-bottom: 8px; font-size: 1.1rem; }}
        
        /* GROUP HEADERS */
        .table-group-header {{
            background: #eee;
            padding: 8px 15px;
            border-radius: 8px;
            font-weight: bold;
            color: #555;
            margin: 15px 0 10px;
            position: sticky;
            top: 70px;
            z-index: 90;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex; align-items: center; gap: 10px;
        }}
        
        /* FINANCE CARDS */
        .finance-card {{
            background: var(--white);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }}
        .finance-header {{ font-size: 0.9rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }}
        .finance-amount {{ font-size: 2.5rem; font-weight: 800; }}
        .finance-amount.red-text {{ color: var(--red); }}
        .finance-amount.green-text {{ color: var(--green); }}
        
        .debt-list {{ background: var(--white); border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }}
        .debt-item {{ display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #eee; }}
        .debt-item:last-child {{ border-bottom: none; }}
        
        .order-card {{ margin-bottom: 15px; border-left: 5px solid var(--primary); position: relative; background: var(--white); padding: 15px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .order-card .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; font-size: 0.9rem; color: #666; }}
        .order-card .order-id {{ font-size: 1.1rem; font-weight: 800; color: #333; }}
        .order-card .card-body {{ font-size: 0.95rem; line-height: 1.5; padding-bottom: 12px; border-bottom: 1px solid #eee; margin-bottom: 12px; }}
        .order-card .card-footer {{ display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }}
        .info-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
        .info-row i {{ width: 20px; text-align: center; color: #777; }}
        
        /* STATUS BADGES */
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        .badge.success {{ background: #e8f5e9; color: var(--green); }}
        .badge.alert {{ background: #ffebee; color: var(--red); }}
        .badge.warning {{ background: #fff3e0; color: var(--orange); }}
        .badge.info {{ background: #e3f2fd; color: var(--blue); }}

        /* BUTTONS */
        .action-btn {{ background: var(--primary); color: var(--white); border: none; padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 6px; }}
        .action-btn.secondary {{ background: #f0f0f0; color: #333; }}
        .action-btn:active {{ opacity: 0.8; transform: translateY(1px); }}
        
        /* NOTIFICATIONS */
        .notify-item {{ background: var(--white); padding: 15px; margin-bottom: 10px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 4px solid var(--blue); position: relative; }}
        .notify-item.read {{ border-left-color: #ddd; opacity: 0.7; box-shadow: none; background: #fcfcfc; }}
        .notify-time {{ font-size: 0.75rem; color: #999; position: absolute; top: 15px; right: 15px; }}
        .notify-msg {{ padding-right: 30px; }}
        .notify-dot {{ position: absolute; top: 2px; right: 50%; transform: translateX(50%); width: 10px; height: 10px; background: var(--red); border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 5px rgba(0,0,0,0.2); }}

        /* TOAST NOTIFICATION (SYSTEM) */
        #toast-container {{ position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 2000; width: 90%; max-width: 400px; pointer-events: none; }}
        .toast {{ background: #333; color: #fff; padding: 15px 20px; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); opacity: 0; transform: translateY(-20px); transition: all 0.3s ease; display: flex; align-items: center; gap: 10px; pointer-events: auto; }}
        .toast.show {{ opacity: 1; transform: translateY(0); }}
        .toast i {{ color: var(--orange); font-size: 1.2rem; }}

        /* BOTTOM NAV */
        .bottom-nav {{ position: fixed; bottom: 0; left: 0; width: 100%; background: var(--white); border-top: 1px solid #eee; display: flex; justify-content: space-around; padding: 8px 0; z-index: 500; padding-bottom: max(8px, env(safe-area-inset-bottom)); box-shadow: 0 -2px 10px rgba(0,0,0,0.03); }}
        .nav-item {{ background: none; border: none; color: #aaa; display: flex; flex-direction: column; align-items: center; font-size: 0.7rem; width: 100%; cursor: pointer; position: relative; transition: color 0.2s; gap: 4px; }}
        .nav-item.active {{ color: var(--primary); font-weight: 600; }}
        .nav-item i {{ font-size: 1.4rem; }}

        /* MODAL */
        .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; justify-content: center; align-items: flex-end; backdrop-filter: blur(2px); }}
        .modal.active {{ display: flex; animation: slideUp 0.25s ease-out; }}
        .modal-content {{ background: var(--white); width: 100%; max-width: 600px; max-height: 85vh; border-radius: 20px 20px 0 0; padding: 25px; overflow-y: auto; box-sizing: border-box; display: flex; flex-direction: column; box-shadow: 0 -10px 40px rgba(0,0,0,0.2); }}
        .close {{ position: absolute; top: 20px; right: 20px; font-size: 24px; color: #999; cursor: pointer; z-index: 10; }}
        @keyframes slideUp {{ from {{ transform: translateY(100%); }} to {{ transform: translateY(0); }} }}
        
        /* EDIT LIST */
        .edit-list {{ max-height: 40vh; overflow-y: auto; margin: 15px 0; border: 1px solid #eee; border-radius: 8px; }}
        .edit-item {{ display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid #eee; }}
        .edit-item:last-child {{ border-bottom: none; }}
        .qty-ctrl-sm {{ display: flex; gap: 10px; align-items: center; background: #f5f5f5; padding: 4px; border-radius: 8px; }}
        .qty-btn-sm {{ width: 28px; height: 28px; border-radius: 6px; border: none; background: #fff; cursor: pointer; font-weight: bold; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}
        
        .big-btn {{ width: 100%; padding: 16px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 1rem; font-weight: bold; margin-top: 15px; cursor: pointer; }}
        
        #loading-indicator {{ text-align: center; padding: 20px; color: #999; display: none; }}
    </style>
</head>
<body>
    {content}
    
    <div id="toast-container"></div>

    <div id="staff-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        let currentView = 'orders'; 
        let currentTableId = null;
        let menuData = [];
        let cart = {{}}; 
        let editingOrderId = null;
        let currentStatusChangeId = null;
        let lastNotificationCount = 0;
        let wakeLock = null;

        document.addEventListener('DOMContentLoaded', () => {{
            const activeBtn = document.querySelector('.nav-item.active');
            if (activeBtn) {{
                const onclick = activeBtn.getAttribute('onclick');
                const match = onclick.match(/switchTab\('(\w+)'\)/);
                if (match) currentView = match[1];
            }}
            
            fetchData();
            updateNotifications();
            
            setInterval(fetchData, 7000); 
            setInterval(updateNotifications, 4000); 
            
            document.addEventListener("visibilitychange", async () => {{
                if (document.visibilityState === 'visible') {{
                    requestWakeLock();
                    updateNotifications();
                }}
            }});
            
            document.body.addEventListener('click', initNotifications, {{ once: true }});
        }});

        function initNotifications() {{
            if (!("Notification" in window)) return;
            if (Notification.permission === "default") {{
                Notification.requestPermission().then(permission => {{
                    if (permission === "granted") {{
                        new Notification("Staff App", {{ body: "Сповіщення увімкнено ✅" }});
                    }}
                }});
            }}
            requestWakeLock();
        }}

        function sendSystemNotification(text) {{
            if (!("Notification" in window)) return;
            
            if (Notification.permission === "granted") {{
                if (navigator.serviceWorker && navigator.serviceWorker.controller) {{
                    navigator.serviceWorker.ready.then(registration => {{
                        registration.showNotification("Staff Panel", {{
                            body: text,
                            icon: '/static/favicons/icon-192.png',
                            vibrate: [200, 100, 200],
                            tag: 'staff-notification',
                            renotify: true
                        }});
                    }});
                }} else {{
                    try {{
                        const notification = new Notification("Нове сповіщення", {{
                            body: text,
                            icon: '/static/favicons/icon-192.png',
                            vibrate: [200, 100, 200]
                        }});
                        notification.onclick = function() {{ window.focus(); }};
                    }} catch (e) {{ console.log(e); }}
                }}
            }}
        }}

        async function requestWakeLock() {{
            try {{
                if ('wakeLock' in navigator) {{
                    wakeLock = await navigator.wakeLock.request('screen');
                    console.log('Wake Lock active');
                }}
            }} catch (err) {{
                console.log('Wake Lock error:', err);
            }}
        }}

        function showToast(message) {{
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.innerHTML = `<i class="fa-solid fa-bell"></i> <span>${{message}}</span>`;
            container.appendChild(toast);
            
            setTimeout(() => toast.classList.add('show'), 10);
            if (navigator.vibrate) navigator.vibrate(200);
            
            setTimeout(() => {{
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }}, 5000);
        }}

        function switchTab(view) {{
            currentView = view;
            document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
            event.currentTarget.classList.add('active');
            
            if (view === 'notifications') {{
                renderNotifications();
            }} else {{
                document.getElementById('content-area').innerHTML = '';
                document.getElementById('loading-indicator').style.display = 'block';
                fetchData();
            }}
        }}

        async function fetchData() {{
            if (currentView === 'notifications') return;
            try {{
                const response = await fetch(`/staff/api/data?view=${{currentView}}`);
                if (!response.ok) throw new Error("Server error");
                const data = await response.json();
                
                document.getElementById('loading-indicator').style.display = 'none';
                document.getElementById('content-area').innerHTML = data.html;
            }} catch (e) {{ console.error("Fetch error:", e); }}
        }}

        async function updateNotifications() {{
            try {{
                const res = await fetch('/staff/api/notifications');
                const data = await res.json();
                const badge = document.getElementById('nav-notify-badge');
                
                window.notificationsList = data.list;

                if (data.unread_count > 0) {{
                    badge.style.display = 'block';
                    if (data.unread_count > lastNotificationCount) {{
                        const newest = data.list[0];
                        if (newest) {{
                            showToast(newest.message);
                            sendSystemNotification(newest.message);
                        }}
                    }}
                }} else {{
                    badge.style.display = 'none';
                }}
                
                lastNotificationCount = data.unread_count;
                if (currentView === 'notifications') renderNotifications();
            }} catch(e) {{}}
        }}

        function renderNotifications() {{
            const container = document.getElementById('content-area');
            document.getElementById('loading-indicator').style.display = 'none';
            
            if (!window.notificationsList || window.notificationsList.length === 0) {{
                container.innerHTML = "<div class='empty-state'><i class='fa-regular fa-bell-slash'></i>Сповіщень немає</div>";
                return;
            }}
            
            let html = "";
            window.notificationsList.forEach(n => {{
                const cls = n.is_read ? 'read' : '';
                html += `<div class="notify-item ${{cls}}"><div class="notify-msg">${{n.message}}</div><span class="notify-time">${{n.time}}</span></div>`;
            }});
            container.innerHTML = html;
            document.getElementById('nav-notify-badge').style.display = 'none';
        }}

        async function toggleShift() {{
            if(!confirm("Змінити статус зміни?")) return;
            const res = await fetch('/staff/api/shift/toggle', {{ method: 'POST' }});
            const data = await res.json();
            if (data.status === 'ok') location.reload();
        }}

        async function openOrderEditModal(orderId) {{
            editingOrderId = orderId;
            const modal = document.getElementById('staff-modal');
            const body = document.getElementById('modal-body');
            body.innerHTML = '<div style="text-align:center; padding:20px;"><i class="fa-solid fa-spinner fa-spin"></i> Завантаження...</div>';
            modal.classList.add('active');
            try {{
                const res = await fetch(`/staff/api/order/${{orderId}}/details`);
                const data = await res.json();
                let itemsHtml = `<div class="edit-list">`;
                data.items.forEach(item => {{
                    itemsHtml += `
                    <div class="edit-item">
                        <div><b>${{item.name}}</b><br><small>${{item.price}} грн</small></div>
                        <div class="qty-ctrl-sm">
                            <button class="qty-btn-sm" onclick="updateEditQty(${{item.id}}, -1)">-</button>
                            <span id="qty-${{item.id}}" style="min-width:20px; text-align:center;">${{item.qty}}</span>
                            <button class="qty-btn-sm" onclick="updateEditQty(${{item.id}}, 1)">+</button>
                        </div>
                    </div>`;
                }});
                itemsHtml += `</div>`;
                itemsHtml += `<button class="action-btn secondary" style="width:100%; justify-content:center;" onclick="openAddProductModal()"><i class="fa-solid fa-plus"></i> Додати страву</button>`;
                let statusOptions = "";
                data.statuses.forEach(s => {{
                    statusOptions += `<option value="${{s.id}}" ${{s.selected ? 'selected' : ''}} data-completed="${{s.is_completed}}">${{s.name}}</option>`;
                }});
                body.innerHTML = `
                    <h3 style="margin-top:0;">Замовлення #${{orderId}}</h3>
                    <div style="margin-bottom:20px; background:#f9f9f9; padding:10px; border-radius:8px;">
                        <label style="font-size:0.85rem; color:#666; margin-bottom:5px; display:block;">Змінити статус:</label>
                        <select id="status-select" style="width:100%; padding:10px; border-radius:6px; border:1px solid #ddd; background:#fff; font-size:1rem;" onchange="changeOrderStatus(this)">
                            ${{statusOptions}}
                        </select>
                    </div>
                    <h4 style="margin-bottom:10px;">Склад:</h4>
                    ${{itemsHtml}}
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px; font-size:1.2rem; font-weight:bold;">
                        <span>Разом:</span>
                        <span>${{data.total}} грн</span>
                    </div>
                    <button class="big-btn" onclick="saveOrderChanges()">Зберегти зміни</button>
                `;
                cart = {{}};
                data.items.forEach(i => cart[i.id] = {{ qty: i.qty, id: i.id }});
            }} catch (e) {{
                body.innerHTML = "Помилка: " + e.message;
            }}
        }}

        function updateEditQty(prodId, delta) {{
            if (cart[prodId]) {{
                cart[prodId].qty += delta;
                if (cart[prodId].qty <= 0) delete cart[prodId];
                const qtySpan = document.getElementById(`qty-${{prodId}}`);
                if (qtySpan) qtySpan.innerText = cart[prodId] ? cart[prodId].qty : 0;
            }}
        }}

        async function changeOrderStatus(selectElem) {{
            const newStatusId = selectElem.value;
            const option = selectElem.options[selectElem.selectedIndex];
            const isCompleted = option.getAttribute('data-completed') === 'true';
            if (isCompleted) {{
                currentStatusChangeId = newStatusId;
                const body = document.getElementById('modal-body');
                body.innerHTML = `
                    <h3 style="text-align:center;">💰 Оплата замовлення</h3>
                    <p style="text-align:center; color:#666; margin-bottom:20px;">Оберіть метод оплати:</p>
                    <button class="big-btn" style="background:#27ae60;" onclick="finishStatusChange('cash')"><i class="fa-solid fa-money-bill-wave"></i> Готівка</button>
                    <button class="big-btn" style="background:#2980b9;" onclick="finishStatusChange('card')"><i class="fa-regular fa-credit-card"></i> Картка / Термінал</button>
                    <br>
                    <button class="action-btn secondary" style="width:100%; margin-top:10px; justify-content:center;" onclick="openOrderEditModal(editingOrderId)">Скасувати</button>
                `;
                return;
            }}
            await updateStatusAPI(newStatusId, null);
        }}

        async function finishStatusChange(method) {{
            await updateStatusAPI(currentStatusChangeId, method);
            closeModal();
            fetchData();
        }}

        async function updateStatusAPI(statusId, paymentMethod) {{
            await fetch('/staff/api/order/update_status', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ 
                    orderId: editingOrderId, 
                    statusId: statusId,
                    paymentMethod: paymentMethod 
                }})
            }});
        }}

        async function saveOrderChanges() {{
            const items = Object.values(cart);
            await fetch('/staff/api/order/update_items', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ orderId: editingOrderId, items: items }})
            }});
            closeModal();
            fetchData();
        }}

        async function openAddProductModal() {{
            const body = document.getElementById('modal-body');
            body.innerHTML = '<div style="text-align:center; padding:20px;">Завантаження меню...</div>';
            if (menuData.length === 0) {{
                const res = await fetch('/staff/api/menu/full');
                menuData = await res.json();
            }}
            let html = `
                <div style="display:flex;justify-content:space-between;align-items:center; margin-bottom:15px;">
                    <h3 style="margin:0;">Меню</h3>
                    <button onclick="openOrderEditModal(editingOrderId)" class="action-btn secondary" style="padding:5px 10px;">Назад</button>
                </div>
                <div class="edit-list" style="max-height:60vh;">`;
            menuData.forEach(cat => {{
                html += `<div style="background:#eee; padding:8px 12px; font-weight:bold; font-size:0.9rem; position:sticky; top:0;">${{cat.name}}</div>`;
                cat.products.forEach(p => {{
                    html += `
                    <div class="edit-item">
                        <div style="flex-grow:1;">${{p.name}}</div>
                        <button class="action-btn" style="padding:6px 12px;" onclick="addToEditCart(${{p.id}})">+</button>
                    </div>`;
                }});
            }});
            html += `</div>`;
            body.innerHTML = html;
        }}

        function addToEditCart(prodId) {{
            if (!cart[prodId]) cart[prodId] = {{ id: prodId, qty: 0 }};
            cart[prodId].qty++;
            const btn = event.currentTarget;
            const originalText = btn.innerText;
            btn.innerText = "✓";
            setTimeout(() => btn.innerText = originalText, 500);
        }}

        function performAction(action, orderId, extra=null) {{
            if(action === 'chef_ready' && !confirm("Підтвердити готовність?")) return;
            fetch('/staff/api/action', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ action, orderId, extra }})
            }}).then(res => res.json()).then(data => {{
                if(data.success) fetchData();
                else alert("Помилка: " + (data.error || "Unknown"));
            }});
        }}
        
        function openTableModal(tableId, tableName) {{
            currentTableId = tableId;
            cart = {{}};
            const modal = document.getElementById('staff-modal');
            document.getElementById('modal-body').innerHTML = `
                <h3 style="text-align:center;">${{tableName}}</h3>
                <div style="display:flex; flex-direction:column; gap:10px; margin-top:30px;">
                    <button class="big-btn" onclick="createNewOrderMenu()">📝 Нове замовлення</button>
                    <button class="action-btn secondary" style="justify-content:center; padding:15px;" onclick="closeModal()">Закрити</button>
                </div>
            `;
            modal.classList.add('active');
        }}
        
        async function createNewOrderMenu() {{
             const body = document.getElementById('modal-body');
             body.innerHTML = '<div style="text-align:center; padding:20px;">Завантаження...</div>';
             if (menuData.length === 0) {{
                const res = await fetch('/staff/api/menu/full');
                menuData = await res.json();
            }}
            let html = `<h3 style="margin-top:0;">Створення замовлення</h3><div class="edit-list" style="max-height:55vh;">`;
            menuData.forEach(cat => {{
                html += `<div style="background:#eee; padding:8px 12px; font-weight:bold; font-size:0.9rem; position:sticky; top:0;">${{cat.name}}</div>`;
                cat.products.forEach(p => {{
                    html += `
                    <div class="edit-item">
                        <div style="font-size:0.95rem;">${{p.name}}</div>
                        <div class="qty-ctrl-sm">
                            <button class="qty-btn-sm" onclick="updateNewOrderCart(${{p.id}}, -1)">-</button>
                            <span id="new-qty-${{p.id}}" style="width:20px; text-align:center;">0</span>
                            <button class="qty-btn-sm" onclick="updateNewOrderCart(${{p.id}}, 1)">+</button>
                        </div>
                    </div>`;
                }});
            }});
            html += `</div><button class="big-btn" onclick="submitNewOrder()">✅ Підтвердити замовлення</button>`;
            body.innerHTML = html;
        }}
        
        function updateNewOrderCart(id, delta) {{
            if (!cart[id]) cart[id] = {{ id: id, qty: 0 }};
            cart[id].qty += delta;
            if(cart[id].qty < 0) cart[id].qty = 0;
            const el = document.getElementById(`new-qty-${{id}}`);
            if (el) el.innerText = cart[id].qty;
        }}
        
        async function submitNewOrder() {{
            const items = Object.values(cart).filter(i => i.qty > 0);
            if(items.length === 0) return alert("Кошик порожній");
            const btn = event.currentTarget;
            btn.disabled = true;
            btn.innerText = "Створення...";
            try {{
                await fetch('/staff/api/order/create', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ tableId: currentTableId, cart: items }})
                }});
                closeModal();
                fetchData();
            }} catch (e) {{
                alert("Помилка створення");
                btn.disabled = false;
            }}
        }}

        function closeModal() {{
            document.getElementById('staff-modal').classList.remove('active');
        }}
    </script>
</body>
</html>
"""

# --- ШАБЛОН КАРТОЧКИ СТОЛИКА ---
STAFF_TABLE_CARD = """
<div class="card table-card" onclick="openTableModal({id}, '{name_esc}')" style="border: 2px solid {border_color}; background: {bg_color};">
    <div class="card-title"><i class="fa-solid fa-chair"></i> {name_esc}</div>
    <div class="badge {badge_class}">{status_text}</div>
</div>
"""

# --- ШАБЛОН КАРТОЧКИ ЗАКАЗА ---
STAFF_ORDER_CARD = """
<div class="order-card" id="order-{id}" style="border-left-color: {color}">
    <div class="card-header">
        <div class="order-id">#{id} <span style="font-weight:normal; font-size:0.8rem; color:#999; margin-left:5px;">{time}</span></div>
        <span class="badge {badge_class}">{status}</span>
    </div>
    <div class="card-body" onclick="openOrderEditModal({id})">
        {content}
    </div>
    <div class="card-footer">
        {buttons}
    </div>
</div>
"""
# main.py

import asyncio
import logging
import sys
import os
import secrets
import re
import aiofiles
import json
import html
from contextlib import asynccontextmanager
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import quote_plus as url_quote_plus

# --- FastAPI & Uvicorn ---
from fastapi import FastAPI, Form, Request, Depends, HTTPException, File, UploadFile, Body, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# --- Aiogram ---
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- SQLAlchemy ---
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError
import sqlalchemy as sa
from sqlalchemy import func, desc, or_

# --- Локальні імпорти ---
from templates import (
    ADMIN_HTML_TEMPLATE, WEB_ORDER_HTML, 
    ADMIN_ORDER_FORM_BODY, ADMIN_SETTINGS_BODY, 
    ADMIN_REPORTS_BODY
)
from models import *
# Импортируем модели склада, чтобы они зарегистрировались в Base.metadata
import inventory_models 
from inventory_models import Unit, Warehouse

from admin_handlers import register_admin_handlers
from courier_handlers import register_courier_handlers
from notification_manager import notify_new_order_to_staff
from admin_clients import router as clients_router
from dependencies import get_db_session, check_credentials
from auth_utils import get_password_hash 

# --- ІМПОРТИ РОУТЕРІВ ---
from admin_order_management import router as admin_order_router
from admin_tables import router as admin_tables_router
from in_house_menu import router as in_house_menu_router
from admin_design_settings import router as admin_design_router
from admin_cash import router as admin_cash_router
from admin_reports import router as admin_reports_router
from staff_pwa import router as staff_router
from admin_products import router as admin_products_router
from admin_menu_pages import router as admin_menu_pages_router
from admin_employees import router as admin_employees_router
from admin_statuses import router as admin_statuses_router
from admin_inventory import router as admin_inventory_router
# -----------------------------------------------

# --- КОНФІГУРАЦІЯ ---
from dotenv import load_dotenv
load_dotenv()

PRODUCTS_PER_PAGE = 5

class CheckoutStates(StatesGroup):
    waiting_for_delivery_type = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    confirm_data = State()
    waiting_for_order_time = State()
    waiting_for_specific_time = State()

# --- TELEGRAM БОТИ ---
dp = Dispatcher()
dp_admin = Dispatcher()

async def get_main_reply_keyboard(session: AsyncSession):
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🍽️ Меню"), KeyboardButton(text="🛒 Кошик"))
    builder.row(KeyboardButton(text="📋 Мої замовлення"), KeyboardButton(text="❓ Допомога"))

    menu_items_res = await session.execute(
        sa.select(MenuItem).where(MenuItem.show_in_telegram == True).order_by(MenuItem.sort_order)
    )
    menu_items = menu_items_res.scalars().all()
    if menu_items:
        dynamic_buttons = [KeyboardButton(text=item.title.strip()) for item in menu_items]
        for i in range(0, len(dynamic_buttons), 2):
            builder.row(*dynamic_buttons[i:i+2])

    return builder.as_markup(resize_keyboard=True)

async def handle_dynamic_menu_item(message: Message, session: AsyncSession):
    menu_item_res = await session.execute(
        sa.select(MenuItem.content).where(func.trim(MenuItem.title) == message.text, MenuItem.show_in_telegram == True)
    )
    content = menu_item_res.scalar_one_or_none()

    if content is not None:
        if not content.strip():
            await message.answer("Ця сторінка наразі порожня.")
            return

        try:
            await message.answer(content, parse_mode=ParseMode.HTML)
        except TelegramBadRequest:
            try:
                await message.answer(content, parse_mode=None)
            except Exception as e:
                logging.error(f"Не вдалося надіслати вміст пункту меню '{message.text}': {e}")
                await message.answer("Вибачте, сталася помилка під час відображення цієї сторінки.")
    else:
        await message.answer("Вибачте, я не зрозумів цю команду.")


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    
    settings = await session.get(Settings, 1) or Settings()
    
    default_welcome = f"Шановний {{user_name}}, ласкаво просимо! 👋\n\nМи раді вас бачити. Оберіть опцію:"
    welcome_template = settings.telegram_welcome_message or default_welcome
    
    try:
        caption = welcome_template.format(user_name=html.escape(message.from_user.full_name))
    except (KeyError, ValueError):
        caption = default_welcome.format(user_name=html.escape(message.from_user.full_name))

    keyboard = await get_main_reply_keyboard(session)
    await message.answer(caption, reply_markup=keyboard)


@dp.message(F.text == "🍽️ Меню")
async def handle_menu_message(message: Message, session: AsyncSession):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await show_menu(message, session)

@dp.message(F.text == "🛒 Кошик")
async def handle_cart_message(message: Message, session: AsyncSession):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await show_cart(message, session)

@dp.message(F.text == "📋 Мої замовлення")
async def handle_my_orders_message(message: Message, session: AsyncSession):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await show_my_orders(message, session)

@dp.message(F.text == "❓ Допомога")
async def handle_help_message(message: Message):
    text = "Шановний клієнте, ось інструкція:\n- /start: Розпочати роботу з ботом\n- Додайте страви до кошика\n- Оформлюйте замовлення з доставкою\n- Переглядайте свої замовлення\nМи завжди раді допомогти!"
    await message.answer(text)

@dp.message(Command("cancel"))
async def cancel_checkout(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Шановний клієнте, оформлення замовлення скасовано. Будь ласка, звертайтеся, якщо потрібна допомога.")

@dp.callback_query(F.data == "start_menu")
async def back_to_start_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logging.warning(f"Не вдалося видалити повідомлення в back_to_start_menu: {e}")

    settings = await session.get(Settings, 1) or Settings()
    default_welcome = f"Шановний {{user_name}}, ласкаво просимо! 👋\n\nМи раді вас бачити. Оберіть опцію:"
    welcome_template = settings.telegram_welcome_message or default_welcome
    try:
        caption = welcome_template.format(user_name=html.escape(callback.from_user.full_name))
    except (KeyError, ValueError):
        caption = default_welcome.format(user_name=html.escape(callback.from_user.full_name))

    keyboard = await get_main_reply_keyboard(session)
    await callback.message.answer(caption, reply_markup=keyboard)
    await callback.answer()

async def show_my_orders(message_or_callback: Message | CallbackQuery, session: AsyncSession):
    is_callback = isinstance(message_or_callback, CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback
    user_id = message_or_callback.from_user.id

    orders_result = await session.execute(
        sa.select(Order).options(joinedload(Order.status), selectinload(Order.items)).where(Order.user_id == user_id).order_by(Order.id.desc())
    )
    orders = orders_result.scalars().all()

    if not orders:
        text = "Шановний клієнте, у вас поки що немає замовлень. Чекаємо на ваше перше!"
        if is_callback:
            await message_or_callback.answer(text, show_alert=True)
        else:
            await message.answer(text)
        return

    text = "📋 <b>Ваші замовлення:</b>\n\n"
    for order in orders:
        status_name = order.status.name if order.status else 'Невідомий'
        products_str = ", ".join([f"{item.product_name} x {item.quantity}" for item in order.items])
        text += f"<b>Замовлення #{order.id} ({status_name})</b>\nСтрави: {html.escape(products_str)}\nСума: {order.total_price} грн\n\n"

    kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text="⬅️ Головне меню", callback_data="start_menu")).as_markup()

    if is_callback:
        try:
            await message.edit_text(text, reply_markup=kb)
        except TelegramBadRequest:
            await message.delete()
            await message.answer(text, reply_markup=kb)
        await message_or_callback.answer()
    else:
        await message.answer(text, reply_markup=kb)

async def show_menu(message_or_callback: Message | CallbackQuery, session: AsyncSession):
    is_callback = isinstance(message_or_callback, CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback

    keyboard = InlineKeyboardBuilder()
    categories_result = await session.execute(
        sa.select(Category)
        .where(Category.show_on_delivery_site == True)
        .order_by(Category.sort_order, Category.name)
    )
    categories = categories_result.scalars().all()

    if not categories:
        text = "Шановний клієнте, меню поки що порожнє. Зачекайте на оновлення!"
        if is_callback: await message_or_callback.answer(text, show_alert=True)
        else: await message.answer(text)
        return

    for category in categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f"show_category_{category.id}_1"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Головне меню", callback_data="start_menu"))
    keyboard.adjust(1)

    text = "Шановний клієнте, ось категорії страв:"

    if is_callback:
        try:
            await message.edit_text(text, reply_markup=keyboard.as_markup())
        except TelegramBadRequest:
            await message.delete()
            await message.answer(text, reply_markup=keyboard.as_markup())
        await message_or_callback.answer()
    else:
        await message.answer(text, reply_markup=keyboard.as_markup())

@dp.callback_query(F.data == "menu")
async def show_menu_callback(callback: CallbackQuery, session: AsyncSession):
    await show_menu(callback, session)

@dp.callback_query(F.data.startswith("show_category_"))
async def show_category_paginated(callback: CallbackQuery, session: AsyncSession):
    await callback.answer("⏳ Завантаження...")
    parts = callback.data.split("_")
    category_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 1

    category = await session.get(Category, category_id)
    if not category:
        await callback.answer("Категорію не знайдено!", show_alert=True)
        return

    offset = (page - 1) * PRODUCTS_PER_PAGE
    query_total = sa.select(sa.func.count(Product.id)).where(Product.category_id == category_id, Product.is_active == True)
    query_products = sa.select(Product).where(Product.category_id == category_id, Product.is_active == True).order_by(Product.name).offset(offset).limit(PRODUCTS_PER_PAGE)

    total_products_res = await session.execute(query_total)
    total_products = total_products_res.scalar_one_or_none() or 0

    total_pages = (total_products + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE

    products_result = await session.execute(query_products)
    products_on_page = products_result.scalars().all()

    keyboard = InlineKeyboardBuilder()
    for product in products_on_page:
        keyboard.add(InlineKeyboardButton(text=f"{product.name} - {product.price} грн", callback_data=f"show_product_{product.id}"))

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"show_category_{category_id}_{page-1}"))
    if total_pages > 1:
        nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"show_category_{category_id}_{page+1}"))
    if nav_buttons:
        keyboard.row(*nav_buttons)

    keyboard.row(InlineKeyboardButton(text="Меню категорій", callback_data="menu"))
    keyboard.adjust(1)

    text = f"<b>{html.escape(category.name)}</b> (Сторінка {page}):"

    try:
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    except TelegramBadRequest as e:
        if "there is no text in the message to edit" in str(e):
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=keyboard.as_markup())
        else:
            logging.error(f"Неочікувана помилка TelegramBadRequest у show_category_paginated: {e}")

async def get_photo_input(image_url: str):
    if image_url and os.path.exists(image_url) and os.path.getsize(image_url) > 0:
        return FSInputFile(image_url)
    return None

@dp.callback_query(F.data.startswith("show_product_"))
async def show_product(callback: CallbackQuery, session: AsyncSession):
    await callback.answer("⏳ Завантаження...")
    product_id = int(callback.data.split("_")[2])
    product = await session.get(Product, product_id)

    if not product or not product.is_active:
        await callback.answer("Страву не знайдено або вона тимчасово недоступна!", show_alert=True)
        return

    text = (f"<b>{html.escape(product.name)}</b>\n\n"
            f"<i>{html.escape(product.description or 'Опис відсутній.')}</i>\n\n"
            f"<b>Ціна: {product.price} грн</b>")

    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="➕ Додати в кошик", callback_data=f"add_to_cart_{product.id}"))
    kb.add(InlineKeyboardButton(text="⬅️ Назад до страв", callback_data=f"show_category_{product.category_id}_1"))
    kb.adjust(1)

    photo_input = await get_photo_input(product.image_url)
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logging.warning(f"Не вдалося видалити повідомлення в show_product: {e}")

    if photo_input:
        await callback.message.answer_photo(photo=photo_input, caption=text, reply_markup=kb.as_markup())
    else:
        await callback.message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery, session: AsyncSession):
    try:
        product_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError):
        await callback.answer("Помилка! Не вдалося обробити запит.", show_alert=True)
        logging.error(f"Не вдалося розпарсити product_id з даних колбеку: {callback.data}")
        return

    user_id = callback.from_user.id

    product = await session.get(Product, product_id)
    if not product or not product.is_active:
        await callback.answer("Ця страва тимчасово недоступна.", show_alert=True)
        return

    result = await session.execute(sa.select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
    cart_item = result.scalars().first()

    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
        session.add(cart_item)

    await session.commit()
    await callback.answer(f"✅ {html.escape(product.name)} додано до кошика!", show_alert=False)

async def show_cart(message_or_callback: Message | CallbackQuery, session: AsyncSession):
    is_callback = isinstance(message_or_callback, CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback
    user_id = message_or_callback.from_user.id

    cart_items_result = await session.execute(sa.select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id == user_id).order_by(CartItem.id))
    cart_items = cart_items_result.scalars().all()

    if not cart_items:
        text = "Шановний клієнте, ваш кошик порожній. Оберіть щось смачненьке з меню!"
        if is_callback:
            await message_or_callback.answer(text, show_alert=True)
            await show_menu(message_or_callback, session)
        else:
            await message.answer(text)
        return

    text = "🛒 <b>Ваш кошик:</b>\n\n"
    total_price = 0
    kb = InlineKeyboardBuilder()

    for item in cart_items:
        if item.product:
            item_total = item.product.price * item.quantity
            total_price += item_total
            text += f"<b>{html.escape(item.product.name)}</b>\n"
            text += f"<i>{item.quantity} шт. x {item.product.price} грн</i> = <code>{item_total} грн</code>\n\n"
            kb.row(
                InlineKeyboardButton(text="➖", callback_data=f"change_qnt_{item.product.id}_-1"),
                InlineKeyboardButton(text=f"{item.quantity}", callback_data="noop"),
                InlineKeyboardButton(text="➕", callback_data=f"change_qnt_{item.product.id}_1"),
                InlineKeyboardButton(text="❌", callback_data=f"delete_item_{item.product.id}")
            )

    text += f"\n<b>Разом до сплати: {total_price} грн</b>"

    kb.row(InlineKeyboardButton(text="✅ Оформити замовлення", callback_data="checkout"))
    kb.row(InlineKeyboardButton(text="🗑️ Очистити кошик", callback_data="clear_cart"))
    kb.row(InlineKeyboardButton(text="⬅️ Продовжити покупки", callback_data="menu"))

    if is_callback:
        try:
            await message.edit_text(text, reply_markup=kb.as_markup())
        except TelegramBadRequest:
            await message.delete()
            await message.answer(text, reply_markup=kb.as_markup())
        await message_or_callback.answer()
    else:
        await message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "cart")
async def show_cart_callback(callback: CallbackQuery, session: AsyncSession):
    await show_cart(callback, session)

@dp.callback_query(F.data.startswith("change_qnt_"))
async def change_quantity(callback: CallbackQuery, session: AsyncSession):
    await callback.answer("⏳ Оновлюю...")
    product_id, change = map(int, callback.data.split("_")[2:])
    cart_item_res = await session.execute(sa.select(CartItem).where(CartItem.user_id == callback.from_user.id, CartItem.product_id == product_id))
    cart_item = cart_item_res.scalars().first()


    if not cart_item: return

    cart_item.quantity += change
    if cart_item.quantity < 1:
        await session.delete(cart_item)
    await session.commit()
    await show_cart(callback, session)

@dp.callback_query(F.data.startswith("delete_item_"))
async def delete_from_cart(callback: CallbackQuery, session: AsyncSession):
    await callback.answer("⏳ Видаляю...")
    product_id = int(callback.data.split("_")[2])
    await session.execute(sa.delete(CartItem).where(CartItem.user_id == callback.from_user.id, CartItem.product_id == product_id))
    await session.commit()
    await show_cart(callback, session)

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, session: AsyncSession):
    await session.execute(sa.delete(CartItem).where(CartItem.user_id == callback.from_user.id))
    await session.commit()
    await callback.answer("Кошик очищено!", show_alert=True)
    await show_menu(callback, session)

@dp.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback.from_user.id
    cart_items_result = await session.execute(
        sa.select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id == user_id)
    )
    cart_items = cart_items_result.scalars().all()

    if not cart_items:
        await callback.answer("Шановний клієнте, кошик порожній! Оберіть щось з меню.", show_alert=True)
        return

    total_price = sum(item.product.price * item.quantity for item in cart_items if item.product)
    
    await state.update_data(
        total_price=total_price,
        user_id=user_id,
        username=callback.from_user.username,
        order_type='delivery' 
    )
    await state.set_state(CheckoutStates.waiting_for_delivery_type)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🚚 Доставка", callback_data="delivery_type_delivery"))
    kb.add(InlineKeyboardButton(text="🏠 Самовивіз", callback_data="delivery_type_pickup"))
    kb.adjust(1)

    try:
        await callback.message.edit_text("Шановний клієнте, оберіть тип отримання замовлення:", reply_markup=kb.as_markup())
    except TelegramBadRequest:
        await callback.message.delete()
        await callback.message.answer("Шановний клієнте, оберіть тип отримання замовлення:", reply_markup=kb.as_markup())

    await callback.answer()

@dp.callback_query(F.data.startswith("delivery_type_"))
async def process_delivery_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    delivery_type = callback.data.split("_")[2]
    is_delivery = delivery_type == "delivery"
    await state.update_data(is_delivery=is_delivery, order_type=delivery_type)
    customer = await session.get(Customer, callback.from_user.id)
    if customer and customer.name and customer.phone_number and (not is_delivery or customer.address):
        text = f"Шановний клієнте, ми маємо ваші дані:\nІм'я: {customer.name}\nТелефон: {customer.phone_number}"
        if is_delivery:
            text += f"\nАдреса: {customer.address}"
        text += "\nБажаєте використати ці дані?"
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="✅ Так", callback_data="confirm_data_yes"))
        kb.add(InlineKeyboardButton(text="✏️ Змінити", callback_data="confirm_data_no"))
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
        await state.set_state(CheckoutStates.confirm_data)
    else:
        await state.set_state(CheckoutStates.waiting_for_name)
        await callback.message.edit_text("Шановний клієнте, будь ласка, введіть ваше ім'я (наприклад, Іван):")
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_data_"))
async def process_confirm_data(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    confirm = callback.data.split("_")[2]
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logging.warning(f"Не вдалося видалити повідомлення в process_confirm_data: {e}")

    message = callback.message

    if confirm == "yes":
        customer = await session.get(Customer, callback.from_user.id)
        data_to_update = {"customer_name": customer.name, "phone_number": customer.phone_number}
        if (await state.get_data()).get("is_delivery"):
            data_to_update["address"] = customer.address
        await state.update_data(**data_to_update)

        await ask_for_order_time(message, state, session)
    else:
        await state.set_state(CheckoutStates.waiting_for_name)
        await message.answer("Шановний клієнте, будь ласка, введіть ваше ім'я (наприклад, Іван Іванов):")
    await callback.answer()

@dp.message(CheckoutStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or len(name) < 3:
        await message.answer("Шановний клієнте, ім'я повинно бути не менше 3 символів! Спробуйте ще раз.")
        return
    await state.update_data(customer_name=name)
    await state.set_state(CheckoutStates.waiting_for_phone)
    await message.answer("Будь ласка, введіть номер телефону (наприклад, +380XXXXXXXXX):")

@dp.message(CheckoutStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext, session: AsyncSession):
    phone = message.text.strip()
    if not re.match(r'^\+?\d{10,15}$', phone):
        await message.answer("Шановний клієнте, некоректний номер телефону! Він повинен бути у форматі +380XXXXXXXXX. Спробуйте ще раз.")
        return
    await state.update_data(phone_number=phone)
    data = await state.get_data()
    if data.get('is_delivery'):
        await state.set_state(CheckoutStates.waiting_for_address)
        await message.answer("Будь ласка, введіть вулицю та номер будинку для доставки (наприклад, вул. Головна, 1):")
    else:
        await ask_for_order_time(message, state, session)

@dp.message(CheckoutStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext, session: AsyncSession):
    address = message.text.strip()
    if not address or len(address) < 5:
        await message.answer("Шановний клієнте, адреса повинна бути не менше 5 символів! Спробуйте ще раз.")
        return
    await state.update_data(address=address)
    await ask_for_order_time(message, state, session)

async def ask_for_order_time(message_or_callback: Message | CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(CheckoutStates.waiting_for_order_time)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🚀 Якнайшвидше", callback_data="order_time_asap"))
    kb.add(InlineKeyboardButton(text="🕒 На конкретний час", callback_data="order_time_specific"))
    text = "Чудово! Останній крок: коли доставити замовлення?"

    current_message = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
    await current_message.answer(text, reply_markup=kb.as_markup())
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.answer()

@dp.callback_query(CheckoutStates.waiting_for_order_time, F.data.startswith("order_time_"))
async def process_order_time(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    time_choice = callback.data.split("_")[2]

    if time_choice == "asap":
        await state.update_data(delivery_time="Якнайшвидше")
        try:
            await callback.message.delete()
        except TelegramBadRequest as e:
            logging.warning(f"Не вдалося видалити повідомлення в process_order_time: {e}")
        await finalize_order(callback.message, state, session)
    else: # "specific"
        await state.set_state(CheckoutStates.waiting_for_specific_time)
        await callback.message.edit_text("Будь ласка, введіть бажаний час доставки (наприклад, '18:30' або 'на 14:00'):")
    await callback.answer()

@dp.message(CheckoutStates.waiting_for_specific_time)
async def process_specific_time(message: Message, state: FSMContext, session: AsyncSession):
    specific_time = message.text.strip()
    if not specific_time:
        await message.answer("Час не може бути порожнім. Спробуйте ще раз.")
        return
    await state.update_data(delivery_time=specific_time)
    await finalize_order(message, state, session)

async def finalize_order(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    user_id = data.get('user_id')
    
    # Получаем бота из state
    admin_bot = message.bot 
    
    cart_items_res = await session.execute(
        sa.select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id == user_id)
    )
    cart_items = cart_items_res.scalars().all()
    
    if not cart_items:
        await message.answer("Помилка: кошик порожній.")
        return

    total_price = sum(item.product.price * item.quantity for item in cart_items if item.product)

    order = Order(
        user_id=data['user_id'], username=data.get('username'),
        total_price=total_price, customer_name=data['customer_name'],
        phone_number=data['phone_number'], address=data.get('address'),
        is_delivery=data.get('is_delivery', True),
        delivery_time=data.get('delivery_time', 'Якнайшвидше'),
        order_type=data.get('order_type', 'delivery')
    )
    session.add(order)
    await session.flush()

    for cart_item in cart_items:
        if cart_item.product:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=cart_item.product.name,
                quantity=cart_item.quantity,
                price_at_moment=cart_item.product.price,
                preparation_area=cart_item.product.preparation_area
            )
            session.add(order_item)

    if user_id:
        customer = await session.get(Customer, user_id)
        if not customer:
            customer = Customer(user_id=user_id)
            session.add(customer)
        customer.name, customer.phone_number = data['customer_name'], data['phone_number']
        if 'address' in data and data['address'] is not None:
            customer.address = data.get('address')
        await session.execute(sa.delete(CartItem).where(CartItem.user_id == user_id))

    await session.commit()
    await session.refresh(order)

    # Используем instance бота для уведомлений, если он был сохранен в app.state или берем текущего
    app_admin_bot = message.bot # В aiogram хендлере message.bot это и есть бот
    if app_admin_bot:
        await notify_new_order_to_staff(app_admin_bot, order, session)

    await message.answer("Шановний клієнте, ваше замовлення оформлено! Дякуємо за вибір. Смачного!")

    await state.clear()
    await command_start_handler(message, state, session)

# --- Функция start_bot ---
async def start_bot(client_dp: Dispatcher, admin_dp: Dispatcher, client_bot: Bot, admin_bot: Bot):
    try:
        admin_dp["client_bot"] = client_bot
        admin_dp["bot_instance"] = admin_bot
        client_dp["admin_bot_instance"] = admin_bot
        
        client_dp["session_factory"] = async_session_maker
        admin_dp["session_factory"] = async_session_maker

        client_dp.message.register(handle_dynamic_menu_item, F.text)

        register_admin_handlers(admin_dp)
        register_courier_handlers(admin_dp)

        client_dp.callback_query.middleware(DbSessionMiddleware(session_pool=async_session_maker))
        client_dp.message.middleware(DbSessionMiddleware(session_pool=async_session_maker))
        admin_dp.callback_query.middleware(DbSessionMiddleware(session_pool=async_session_maker))
        admin_dp.message.middleware(DbSessionMiddleware(session_pool=async_session_maker))

        await client_bot.delete_webhook(drop_pending_updates=True)
        await admin_bot.delete_webhook(drop_pending_updates=True)

        logging.info("Запускаємо поллінг ботів...")
        await asyncio.gather(
            client_dp.start_polling(client_bot),
            admin_dp.start_polling(admin_bot)
        )
    except Exception as e:
        logging.critical(f"Не вдалося запустити ботів: {e}", exc_info=True)

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Запуск додатка...")
    os.makedirs("static/images", exist_ok=True)
    os.makedirs("static/favicons", exist_ok=True)
    
    # --- Инициализация БД ---
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # --- Инициализация данных (Статусы, Роли, Склад) ---
    async with async_session_maker() as session:
        # Статусы
        result_status = await session.execute(sa.select(OrderStatus).limit(1))
        if not result_status.scalars().first():
            default_statuses = {
                "Новий": {"visible_to_operator": True, "visible_to_courier": False, "visible_to_waiter": True, "visible_to_chef": True, "visible_to_bartender": True, "requires_kitchen_notify": False},
                "В обробці": {"visible_to_operator": True, "visible_to_courier": False, "visible_to_waiter": True, "visible_to_chef": True, "visible_to_bartender": True, "requires_kitchen_notify": True},
                "Готовий до видачі": {"visible_to_operator": True, "visible_to_courier": True, "visible_to_waiter": True, "visible_to_chef": False, "visible_to_bartender": False, "notify_customer": True, "requires_kitchen_notify": False},
                "Доставлений": {"visible_to_operator": True, "visible_to_courier": True, "is_completed_status": True},
                "Скасований": {"visible_to_operator": True, "visible_to_courier": False, "is_cancelled_status": True, "visible_to_waiter": True, "visible_to_chef": False, "visible_to_bartender": False},
                "Оплачено": {"visible_to_operator": True, "is_completed_status": True, "visible_to_waiter": True, "visible_to_chef": False, "visible_to_bartender": False, "notify_customer": False}
            }
            for name, props in default_statuses.items():
                session.add(OrderStatus(name=name, **props))

        # Роли
        result_roles = await session.execute(sa.select(Role).limit(1))
        if not result_roles.scalars().first():
            session.add(Role(name="Адміністратор", can_manage_orders=True, can_be_assigned=True, can_serve_tables=True, can_receive_kitchen_orders=True, can_receive_bar_orders=True))
            session.add(Role(name="Оператор", can_manage_orders=True, can_be_assigned=False, can_serve_tables=True, can_receive_kitchen_orders=True, can_receive_bar_orders=True))
            session.add(Role(name="Кур'єр", can_manage_orders=False, can_be_assigned=True, can_serve_tables=False, can_receive_kitchen_orders=False, can_receive_bar_orders=False))
            session.add(Role(name="Офіціант", can_manage_orders=False, can_be_assigned=False, can_serve_tables=True, can_receive_kitchen_orders=False, can_receive_bar_orders=False))
            session.add(Role(name="Повар", can_manage_orders=False, can_be_assigned=False, can_serve_tables=False, can_receive_kitchen_orders=True, can_receive_bar_orders=False))
            session.add(Role(name="Бармен", can_manage_orders=False, can_be_assigned=False, can_serve_tables=False, can_receive_kitchen_orders=False, can_receive_bar_orders=True))

        # --- Инициализация Склада (Единицы измерения и Склады) ---
        result_units = await session.execute(sa.select(Unit).limit(1))
        if not result_units.scalars().first():
            session.add_all([
                Unit(name='кг', is_weighable=True),
                Unit(name='л', is_weighable=True),
                Unit(name='шт', is_weighable=False),
                Unit(name='порц', is_weighable=False)
            ])
            
        result_warehouses = await session.execute(sa.select(Warehouse).limit(1))
        if not result_warehouses.scalars().first():
            session.add_all([
                Warehouse(name='Основной склад'),
                Warehouse(name='Кухня'),
                Warehouse(name='Бар')
            ])

        await session.commit()
    
    # --- Запуск ботов ---
    client_token = os.environ.get('CLIENT_BOT_TOKEN')
    admin_token = os.environ.get('ADMIN_BOT_TOKEN')
    
    client_bot = None
    admin_bot = None
    bot_task = None

    if not all([client_token, admin_token]):
        logging.warning("Токени ботів не встановлені! Боти не будуть запущені.")
    else:
        try:
            client_bot = Bot(token=client_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            admin_bot = Bot(token=admin_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            bot_task = asyncio.create_task(start_bot(dp, dp_admin, client_bot, admin_bot))
        except Exception as e:
             logging.error(f"Помилка при створенні ботів: {e}")

    app.state.client_bot = client_bot
    app.state.admin_bot = admin_bot
    
    yield
    
    logging.info("Зупинка додатка...")
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
    
    if client_bot: await client_bot.session.close()
    if admin_bot: await admin_bot.session.close()


app = FastAPI(lifespan=lifespan)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- ПОДКЛЮЧЕНИЕ РОУТЕРОВ ---
app.include_router(in_house_menu_router)
app.include_router(clients_router)
app.include_router(admin_order_router)
app.include_router(admin_tables_router)
app.include_router(admin_design_router)
app.include_router(admin_cash_router)
app.include_router(admin_reports_router)
app.include_router(staff_router) 
app.include_router(admin_products_router)
app.include_router(admin_menu_pages_router)
app.include_router(admin_employees_router) 
app.include_router(admin_statuses_router) 
app.include_router(admin_inventory_router)

# --- Спеціальний роут для Service Worker ---
@app.get("/sw.js", response_class=FileResponse)
async def get_service_worker():
    return FileResponse("sw.js", media_type="application/javascript")

class DbSessionMiddleware:
    def __init__(self, session_pool): self.session_pool = session_pool
    async def __call__(self, handler, event, data: Dict[str, Any]):
        async with self.session_pool() as session:
            data['session'] = session
            return await handler(event, data)

async def get_settings(session: AsyncSession) -> Settings:
    settings = await session.get(Settings, 1)
    if not settings:
        settings = Settings(id=1)
        session.add(settings)
        try: await session.commit(); await session.refresh(settings)
        except Exception: await session.rollback(); return Settings(id=1)
    if not settings.telegram_welcome_message: settings.telegram_welcome_message = f"Шановний {{user_name}}, ласкаво просимо!"
    return settings

# --- FastAPI ендпоінти для КЛІЄНТА (WEB) ---

@app.get("/", response_class=HTMLResponse)
async def get_web_ordering_page(session: AsyncSession = Depends(get_db_session)):
    settings = await get_settings(session)
    logo_html = f'<img src="/{settings.logo_url}" alt="Логотип" class="header-logo">' if settings.logo_url else ''

    menu_items_res = await session.execute(
        sa.select(MenuItem).where(MenuItem.show_on_website == True).order_by(MenuItem.sort_order)
    )
    menu_items = menu_items_res.scalars().all()
    menu_links_html = "".join(
        [f'<a href="#" class="menu-popup-trigger" data-item-id="{item.id}">{html.escape(item.title)}</a>' for item in menu_items]
    )

    template_params = {
        "logo_html": logo_html,
        "menu_links_html": menu_links_html,
        "site_title": html.escape(settings.site_title or "Назва"),
        "seo_description": html.escape(settings.seo_description or ""),
        "seo_keywords": html.escape(settings.seo_keywords or ""),
        "primary_color_val": settings.primary_color or "#5a5a5a",
        "secondary_color_val": settings.secondary_color or "#eeeeee",
        "background_color_val": settings.background_color or "#f4f4f4",
        "text_color_val": settings.text_color or "#333333",
        "footer_bg_color_val": settings.footer_bg_color or "#333333",
        "footer_text_color_val": settings.footer_text_color or "#ffffff",
        "font_family_sans_val": settings.font_family_sans or "Golos Text",
        "font_family_serif_val": settings.font_family_serif or "Playfair Display",
        "font_family_sans_encoded": url_quote_plus(settings.font_family_sans or "Golos Text"),
        "font_family_serif_encoded": url_quote_plus(settings.font_family_serif or "Playfair Display"),
        "footer_address": html.escape(settings.footer_address or "Адреса не вказана"),
        "footer_phone": html.escape(settings.footer_phone or ""),
        "working_hours": html.escape(settings.working_hours or ""),
        "social_links_html": "", 
        "category_nav_bg_color": settings.category_nav_bg_color or "#ffffff",
        "category_nav_text_color": settings.category_nav_text_color or "#333333",
        "header_image_url": settings.header_image_url or "",
        "wifi_ssid": html.escape(settings.wifi_ssid or ""),
        "wifi_password": html.escape(settings.wifi_password or "")
    }

    return HTMLResponse(content=WEB_ORDER_HTML.format(**template_params))

@app.get("/api/page/{item_id}", response_class=JSONResponse)
async def get_menu_page_content(item_id: int, session: AsyncSession = Depends(get_db_session)):
    menu_item = await session.get(MenuItem, item_id)
    if not menu_item or not menu_item.show_on_website:
        raise HTTPException(status_code=404, detail="Сторінку не знайдено")
    return {"title": menu_item.title, "content": menu_item.content}

@app.get("/api/menu")
async def get_menu_data(session: AsyncSession = Depends(get_db_session)):
    categories_res = await session.execute(
        sa.select(Category)
        .where(Category.show_on_delivery_site == True)
        .order_by(Category.sort_order, Category.name)
    )
    products_res = await session.execute(
        sa.select(Product)
        .join(Category, Product.category_id == Category.id)
        .where(Product.is_active == True, Category.show_on_delivery_site == True)
    )

    categories = [{"id": c.id, "name": c.name} for c in categories_res.scalars().all()]
    products = [{"id": p.id, "name": p.name, "description": p.description, "price": float(p.price), "image_url": p.image_url, "category_id": p.category_id} for p in products_res.scalars().all()]

    return {"categories": categories, "products": products}

@app.get("/api/customer_info/{phone_number}")
async def get_customer_info(phone_number: str, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        sa.select(Order).where(Order.phone_number == phone_number).order_by(Order.id.desc()).limit(1)
    )
    last_order = result.scalars().first()
    if last_order:
        return {"customer_name": last_order.customer_name, "phone_number": last_order.phone_number, "address": last_order.address}
    raise HTTPException(status_code=404, detail="Клієнта не знайдено")

@app.post("/api/place_order")
async def place_web_order(request: Request, order_data: dict = Body(...), session: AsyncSession = Depends(get_db_session)):
    items = order_data.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="Кошик порожній")

    try:
        product_ids = [int(item['id']) for item in items]
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Невірний формат ID товару (має бути число).")

    products_res = await session.execute(sa.select(Product).where(Product.id.in_(product_ids)))
    db_products = {str(p.id): p for p in products_res.scalars().all()}

    total_price = Decimal('0.00')
    order_items_objects = []

    for item in items:
        pid = str(item['id'])
        if pid in db_products:
            product = db_products[pid]
            qty = int(item.get('quantity', 1))
            total_price += product.price * qty
            
            order_items_objects.append(OrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=qty,
                price_at_moment=product.price,
                preparation_area=product.preparation_area
            ))

    is_delivery = order_data.get('is_delivery', True)
    address = order_data.get('address') if is_delivery else None
    order_type = 'delivery' if is_delivery else 'pickup'
    payment_method = order_data.get('payment_method', 'cash')

    order = Order(
        customer_name=order_data.get('customer_name'), phone_number=order_data.get('phone_number'),
        address=address, 
        total_price=total_price,
        is_delivery=is_delivery, delivery_time=order_data.get('delivery_time', "Якнайшвидше"),
        order_type=order_type,
        payment_method=payment_method,
        items=order_items_objects
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)

    if request.app.state.admin_bot:
        await notify_new_order_to_staff(request.app.state.admin_bot, order, session)

    return JSONResponse(content={"message": "Замовлення успішно розміщено", "order_id": order.id})

# --- АДМИН ПАНЕЛЬ (DASHBOARD) ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    settings = await get_settings(session)
    orders_res = await session.execute(sa.select(Order).order_by(Order.id.desc()).limit(5))
    orders_count_res = await session.execute(sa.select(sa.func.count(Order.id)))
    products_count_res = await session.execute(sa.select(sa.func.count(Product.id)))
    orders_count = orders_count_res.scalar_one_or_none() or 0
    products_count = products_count_res.scalar_one_or_none() or 0

    body = f"""
    <div class="card"><strong>Ласкаво просимо, {username}!</strong></div>
    <div class="card"><h2>📈 Швидка статистика</h2><p><strong>Всього страв:</strong> {products_count}</p><p><strong>Всього замовлень:</strong> {orders_count}</p></div>
    <div class="card"><h2>📦 5 останніх замовлень</h2>
        <table><thead><tr><th>ID</th><th>Клієнт</th><th>Телефон</th><th>Сума</th></tr></thead><tbody>
        {''.join([f"<tr><td><a href='/admin/order/manage/{o.id}'>#{o.id}</a></td><td>{html.escape(o.customer_name or '')}</td><td>{html.escape(o.phone_number or '')}</td><td>{o.total_price} грн</td></tr>" for o in orders_res.scalars().all()]) or "<tr><td colspan='4'>Немає замовлень</td></tr>"}
        </tbody></table></div>"""

    active_classes = {key: "" for key in ["orders_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]}
    active_classes["main_active"] = "active"

    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(
        title="Головна панель", body=body, site_title=settings.site_title or "Назва", **active_classes
    ))

# --- МАРШРУТЫ КАТЕГОРИЙ ---

@app.get("/admin/categories", response_class=HTMLResponse)
async def admin_categories(session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    settings = await get_settings(session)
    categories_res = await session.execute(sa.select(Category).order_by(Category.sort_order, Category.name))
    categories = categories_res.scalars().all()

    def bool_to_icon(val): return '✅' if val else '❌'
    rows = "".join([f"""<tr><td>{c.id}</td><td><form action="/admin/edit_category/{c.id}" method="post" class="inline-form"><input type="hidden" name="field" value="name_sort"><input type="text" name="name" value="{html.escape(c.name)}" style="width: 150px;"><input type="number" name="sort_order" value="{c.sort_order}" style="width: 80px;"><button type="submit">💾</button></form></td><td style="text-align: center;"><form action="/admin/edit_category/{c.id}" method="post" class="inline-form"><input type="hidden" name="field" value="show_on_delivery_site"><input type="hidden" name="value" value="{'false' if c.show_on_delivery_site else 'true'}"><button type="submit" class="button-sm" style="background: none; color: inherit; padding: 0; font-size: 1.2rem;">{bool_to_icon(c.show_on_delivery_site)}</button></form></td><td style="text-align: center;"><form action="/admin/edit_category/{c.id}" method="post" class="inline-form"><input type="hidden" name="field" value="show_in_restaurant"><input type="hidden" name="value" value="{'false' if c.show_in_restaurant else 'true'}"><button type="submit" class="button-sm" style="background: none; color: inherit; padding: 0; font-size: 1.2rem;">{bool_to_icon(c.show_in_restaurant)}</button></form></td><td class='actions'><a href='/admin/delete_category/{c.id}' onclick="return confirm('Ви впевнені?');" class='button-sm danger'>🗑️</a></td></tr>""" for c in categories])

    body = f"""<div class="card"><h2>Додати нову категорію</h2><form action="/admin/add_category" method="post"><label for="name">Назва категорії:</label><input type="text" id="name" name="name" required><label for="sort_order">Порядок сортування:</label><input type="number" id="sort_order" name="sort_order" value="100"><div class="checkbox-group"><input type="checkbox" id="show_on_delivery_site" name="show_on_delivery_site" value="true" checked><label for="show_on_delivery_site">Показувати на сайті та в боті (доставка)</label></div><div class="checkbox-group"><input type="checkbox" id="show_in_restaurant" name="show_in_restaurant" value="true" checked><label for="show_in_restaurant">Показувати в закладі (QR-меню)</label></div><button type="submit">Додати</button></form></div><div class="card"><h2>Список категорій</h2><table><thead><tr><th>ID</th><th>Назва та сортування</th><th>Сайт/Бот</th><th>В закладі</th><th>Дії</th></tr></thead><tbody>{rows or "<tr><td colspan='5'>Немає категорій</td></tr>"}</tbody></table></div>"""
    active_classes = {key: "" for key in ["main_active", "orders_active", "clients_active", "tables_active", "products_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]}
    active_classes["categories_active"] = "active"
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Категорії", body=body, site_title=settings.site_title or "Назва", **active_classes))

@app.post("/admin/add_category")
async def add_category(name: str = Form(...), sort_order: int = Form(100), show_on_delivery_site: bool = Form(False), show_in_restaurant: bool = Form(False), session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    session.add(Category(name=name, sort_order=sort_order, show_on_delivery_site=show_on_delivery_site, show_in_restaurant=show_in_restaurant))
    await session.commit()
    return RedirectResponse(url="/admin/categories", status_code=303)

@app.post("/admin/edit_category/{cat_id}")
async def edit_category(cat_id: int, name: Optional[str] = Form(None), sort_order: Optional[int] = Form(None), field: Optional[str] = Form(None), value: Optional[str] = Form(None), session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    category = await session.get(Category, cat_id)
    if category:
        if field == "name_sort" and name is not None and sort_order is not None:
            category.name = name
            category.sort_order = sort_order
        elif field in ["show_on_delivery_site", "show_in_restaurant"]:
            setattr(category, field, value.lower() == 'true')
        await session.commit()
    return RedirectResponse(url="/admin/categories", status_code=303)

@app.get("/admin/delete_category/{cat_id}")
async def delete_category(cat_id: int, session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    category = await session.get(Category, cat_id)
    if category:
        products_exist_res = await session.execute(sa.select(sa.func.count(Product.id)).where(Product.category_id == cat_id))
        if products_exist_res.scalar_one_or_none() > 0:
             return RedirectResponse(url="/admin/categories?error=category_in_use", status_code=303)
        await session.delete(category)
        await session.commit()
    return RedirectResponse(url="/admin/categories", status_code=303)

# --- МАРШРУТЫ СПИСКА ЗАКАЗОВ И СОЗДАНИЯ ---

@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(page: int = Query(1, ge=1), q: str = Query(None, alias="search"), session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    settings = await get_settings(session)
    per_page = 15
    offset = (page - 1) * per_page
    
    query = sa.select(Order).options(joinedload(Order.status), selectinload(Order.items)).order_by(Order.id.desc())
    
    filters = []
    if q:
        search_term = q.replace('#', '')
        if search_term.isdigit():
             filters.append(sa.or_(Order.id == int(search_term), Order.customer_name.ilike(f"%{q}%"), Order.phone_number.ilike(f"%{q}%")))
        else:
             filters.append(sa.or_(Order.customer_name.ilike(f"%{q}%"), Order.phone_number.ilike(f"%{q}%")))
    if filters:
        query = query.where(*filters)

    count_query = sa.select(sa.func.count(Order.id))
    if filters:
        count_query = count_query.where(*filters)
        
    total_res = await session.execute(count_query)
    total = total_res.scalar_one_or_none() or 0
    
    orders_res = await session.execute(query.limit(per_page).offset(offset))
    orders = orders_res.scalars().all()
    pages = (total // per_page) + (1 if total % per_page > 0 else 0)

    rows = ""
    for o in orders:
        items_str = ", ".join([f"{i.product_name} x {i.quantity}" for i in o.items])
        if len(items_str) > 50:
            items_str = items_str[:50] + "..."
            
        rows += f"""
        <tr>
            <td><a href="/admin/order/manage/{o.id}" title="Керувати замовленням">#{o.id}</a></td>
            <td>{html.escape(o.customer_name or '')}</td>
            <td>{html.escape(o.phone_number or '')}</td>
            <td>{o.total_price} грн</td>
            <td><span class='status'>{o.status.name if o.status else '-'}</span></td>
            <td>{html.escape(items_str)}</td>
            <td class='actions'>
                <a href='/admin/order/manage/{o.id}' class='button-sm' title="Керувати статусом та кур'єром">⚙️ Керувати</a>
                <a href='/admin/order/edit/{o.id}' class='button-sm' title="Редагувати склад замовлення">✏️ Редагувати</a>
            </td>
        </tr>"""

    links_orders = []
    for i in range(1, pages + 1):
        search_part = f'&search={q}' if q else ''
        class_part = 'active' if i == page else ''
        links_orders.append(f'<a href="/admin/orders?page={i}{search_part}" class="{class_part}">{i}</a>')
    
    pagination = f"<div class='pagination'>{' '.join(links_orders)}</div>"

    body = f"""
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h2>📋 Список замовлень</h2>
            <a href="/admin/order/new" class="button"><i class="fa-solid fa-plus"></i> Створити замовлення</a>
        </div>
        <form action="/admin/orders" method="get" class="search-form">
            <input type="text" name="search" placeholder="Пошук за ID, іменем, телефоном..." value="{q or ''}">
            <button type="submit">🔍 Знайти</button>
        </form>
        <table><thead><tr><th>ID</th><th>Клієнт</th><th>Телефон</th><th>Сума</th><th>Статус</th><th>Склад</th><th>Дії</th></tr></thead><tbody>
        {rows or "<tr><td colspan='7'>Немає замовлень</td></tr>"}
        </tbody></table>{pagination if pages > 1 else ''}
    </div>"""
    active_classes = {key: "" for key in ["main_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]}
    active_classes["orders_active"] = "active"
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Замовлення", body=body, site_title=settings.site_title or "Назва", **active_classes))

@app.get("/admin/order/new", response_class=HTMLResponse)
async def get_add_order_form(session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    settings = await get_settings(session)
    initial_data = {"items": {}, "action": "/api/admin/order/new", "submit_text": "Створити замовлення", "form_values": None}
    script = f"<script>document.addEventListener('DOMContentLoaded',()=>{{if(typeof window.initializeForm==='function'&&!window.orderFormInitialized){{window.initializeForm({json.dumps(initial_data)});window.orderFormInitialized=true;}}else if(!window.initializeForm){{document.addEventListener('formScriptLoaded',()=>{{if(!window.orderFormInitialized){{window.initializeForm({json.dumps(initial_data)});window.orderFormInitialized=true;}}}});}}}});</script>"
    body = ADMIN_ORDER_FORM_BODY + script
    active_classes = {key: "" for key in ["main_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]}
    active_classes["orders_active"] = "active"
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title="Нове замовлення", body=body, site_title=settings.site_title or "Назва", **active_classes))

@app.get("/admin/order/edit/{order_id}", response_class=HTMLResponse)
async def get_edit_order_form(order_id: int, session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    settings = await get_settings(session)
    order = await session.get(Order, order_id, options=[joinedload(Order.status), selectinload(Order.items)])
    if not order: raise HTTPException(404, "Замовлення не знайдено")

    if order.status.is_completed_status or order.status.is_cancelled_status:
        return HTMLResponse(f"""<div style="padding: 20px; font-family: sans-serif; max-width: 600px; margin: 20px auto; border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9;"><h2 style="color: #d32f2f;">⛔️ Замовлення #{order.id} закрите</h2><p>Редагування заборонено.</p><div style="margin-top: 20px;"><a href="/admin/orders" style="display: inline-block; padding: 10px 20px; background: #5a5a5a; color: white; text-decoration: none; border-radius: 5px;">⬅️ Назад</a><a href="/admin/order/manage/{order.id}" style="display: inline-block; padding: 10px 20px; background: #0d6efd; color: white; text-decoration: none; border-radius: 5px; margin-left: 10px;">⚙️ Керувати</a></div></div>""")

    initial_items = {}
    for item in order.items:
        initial_items[item.product_id] = {"name": item.product_name, "price": float(item.price_at_moment), "quantity": item.quantity}

    initial_data = {
        "items": initial_items,
        "action": f"/api/admin/order/edit/{order_id}",
        "submit_text": "Зберегти зміни",
        "form_values": {"phone_number": order.phone_number or "", "customer_name": order.customer_name or "", "is_delivery": order.is_delivery, "address": order.address or ""}
    }
    script = f"<script>document.addEventListener('DOMContentLoaded',()=>{{if(typeof window.initializeForm==='function'&&!window.orderFormInitialized){{window.initializeForm({json.dumps(initial_data)});window.orderFormInitialized=true;}}else if(!window.initializeForm){{document.addEventListener('formScriptLoaded',()=>{{if(!window.orderFormInitialized){{window.initializeForm({json.dumps(initial_data)});window.orderFormInitialized=true;}}}});}}}});</script>"
    body = ADMIN_ORDER_FORM_BODY + script
    active_classes = {key: "" for key in ["main_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]}
    active_classes["orders_active"] = "active"
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(title=f"Редагування замовлення #{order.id}", body=body, site_title=settings.site_title or "Назва", **active_classes))

async def _process_and_save_order(order: Order, data: dict, session: AsyncSession, request: Request):
    is_new_order = order.id is None
    order.customer_name = data.get("customer_name")
    order.phone_number = data.get("phone_number")
    order.is_delivery = data.get("delivery_type") == "delivery"
    order.address = data.get("address") if order.is_delivery else None
    order.order_type = "delivery" if order.is_delivery else "pickup"

    items_from_js = data.get("items", {})
    
    if order.id:
        await session.execute(sa.delete(OrderItem).where(OrderItem.order_id == order.id))
    
    total_price = Decimal('0.00') 
    new_items = []
    
    if items_from_js:
        valid_product_ids = [int(pid) for pid in items_from_js.keys() if pid.isdigit()]
        if valid_product_ids:
            products_res = await session.execute(sa.select(Product).where(Product.id.in_(valid_product_ids)))
            db_products_map = {p.id: p for p in products_res.scalars().all()}

            for pid_str, item_data in items_from_js.items():
                if not pid_str.isdigit(): continue
                pid = int(pid_str)
                product = db_products_map.get(pid)
                if product:
                    qty = int(item_data.get('quantity', 0))
                    if qty > 0:
                        total_price += product.price * qty
                        new_items.append(OrderItem(
                            product_id=pid,
                            product_name=product.name,
                            quantity=qty,
                            price_at_moment=product.price, 
                            preparation_area=product.preparation_area
                        ))

    order.total_price = total_price
    
    if is_new_order:
        session.add(order)
        if not order.status_id:
            new_status_res = await session.execute(sa.select(OrderStatus.id).where(OrderStatus.name == "Новий").limit(1))
            order.status_id = new_status_res.scalar_one_or_none() or 1
        
        await session.flush()
        
        for item in new_items:
            item.order_id = order.id
            session.add(item)
    else:
        for item in new_items:
            item.order_id = order.id
            session.add(item)

    await session.commit()
    await session.refresh(order)

    if is_new_order:
        try:
             session.add(OrderStatusHistory(order_id=order.id, status_id=order.status_id, actor_info="Адміністративна панель"))
             await session.commit()
        except Exception as e: logging.error(f"History error: {e}")

        admin_bot = request.app.state.admin_bot
        if admin_bot:
            await notify_new_order_to_staff(admin_bot, order, session)

@app.post("/api/admin/order/new", response_class=JSONResponse)
async def api_create_order(request: Request, session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    try: data = await request.json()
    except json.JSONDecodeError: raise HTTPException(400, "Invalid JSON")
    try:
        await _process_and_save_order(Order(), data, session, request)
        return JSONResponse(content={"message": "Замовлення створено успішно", "redirect_url": "/admin/orders"})
    except Exception as e:
        logging.error(f"Create order error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to create order")

@app.post("/api/admin/order/edit/{order_id}", response_class=JSONResponse)
async def api_update_order(order_id: int, request: Request, session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    try: data = await request.json()
    except json.JSONDecodeError: raise HTTPException(400, "Invalid JSON")
    
    order = await session.get(Order, order_id, options=[joinedload(Order.status)])
    if not order: raise HTTPException(404, "Order not found")
    if order.status.is_completed_status or order.status.is_cancelled_status: raise HTTPException(400, "Order closed")

    try:
        await _process_and_save_order(order, data, session, request)
        return JSONResponse(content={"message": "Замовлення оновлено успішно", "redirect_url": "/admin/orders"})
    except Exception as e:
        logging.error(f"Update order error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to update order")

# --- ВОССТАНОВЛЕННЫЕ РАЗДЕЛЫ: ЗВІТИ ТА НАЛАШТУВАННЯ ---

@app.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports_menu(session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    settings = await get_settings(session)
    
    body = ADMIN_REPORTS_BODY
    
    active_classes = {key: "" for key in ["main_active", "orders_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]}
    active_classes["reports_active"] = "active"
    
    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(
        title="Звіти", 
        body=body, 
        site_title=settings.site_title, 
        **active_classes
    ))

@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings_page(saved: bool = False, session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials)):
    settings = await get_settings(session)
    
    current_logo_html = f'<img src="/{settings.logo_url}" alt="Лого" style="height: 50px;">' if settings.logo_url else "Логотип не завантажено"
    cache_buster = secrets.token_hex(4)
    
    body = ADMIN_SETTINGS_BODY.format(
        current_logo_html=current_logo_html,
        cache_buster=cache_buster
    )
    
    if saved:
        body = "<div class='card' style='background:#d4edda; color:#155724; padding:10px; margin-bottom:20px;'>✅ Налаштування збережено!</div>" + body

    active_classes = {key: "" for key in ["main_active", "orders_active", "clients_active", "tables_active", "products_active", "categories_active", "menu_active", "employees_active", "statuses_active", "reports_active", "settings_active", "design_active", "inventory_active"]}
    active_classes["settings_active"] = "active"

    return HTMLResponse(ADMIN_HTML_TEMPLATE.format(
        title="Налаштування", body=body, site_title=settings.site_title or "Назва", **active_classes
    ))

@app.post("/admin/settings")
async def save_admin_settings(session: AsyncSession = Depends(get_db_session), username: str = Depends(check_credentials), logo_file: UploadFile = File(None), apple_touch_icon: UploadFile = File(None), favicon_32x32: UploadFile = File(None), favicon_16x16: UploadFile = File(None), favicon_ico: UploadFile = File(None), site_webmanifest: UploadFile = File(None)):
    settings = await get_settings(session)
    if logo_file and logo_file.filename:
        if settings.logo_url and os.path.exists(settings.logo_url):
            try: os.remove(settings.logo_url)
            except OSError: pass
        ext = os.path.splitext(logo_file.filename)[1]
        path = os.path.join("static/images", secrets.token_hex(8) + ext)
        try:
            async with aiofiles.open(path, 'wb') as f: await f.write(await logo_file.read())
            settings.logo_url = path
        except Exception as e: logging.error(f"Save logo error: {e}")

    favicon_dir = "static/favicons"
    os.makedirs(favicon_dir, exist_ok=True)
    for name, file in {"apple-touch-icon.png": apple_touch_icon, "favicon-32x32.png": favicon_32x32, "favicon-16x16.png": favicon_16x16, "favicon.ico": favicon_ico, "site.webmanifest": site_webmanifest}.items():
        if file and file.filename:
            try:
                async with aiofiles.open(os.path.join(favicon_dir, name), 'wb') as f: await f.write(await file.read())
            except Exception as e: logging.error(f"Save favicon error: {e}")

    await session.commit()
    return RedirectResponse(url="/admin/settings?saved=true", status_code=303)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
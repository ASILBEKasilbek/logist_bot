from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import get_statistics, get_all_users, get_all_orders

admin_router = Router()

# Konstantalar
CMD_ADMIN = "/admin"
CMD_STATS = "/stats"
CMD_USERS = "/users"
CMD_ORDERS = "/orders"
MSG_NO_ACCESS = "❌ Siz admin emassiz!"
MSG_NO_USERS = "❌ Foydalanuvchilar topilmadi."
MSG_NO_ORDERS = "❌ Buyurtmalar topilmadi."

# Admin tekshiruvi dekoratori
def admin_only(func):
    """Faqat admin uchun ruxsat beruvchi dekorator."""
    async def wrapper(message: types.Message, *args, **kwargs):
        if message.from_user.id != ADMIN_ID:
            await message.answer(MSG_NO_ACCESS)
            return
        return await func(message, *args, **kwargs)
    return wrapper

# Admin panel klaviaturasi
def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Admin paneli uchun klaviatura yaratadi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CMD_STATS), KeyboardButton(text=CMD_USERS)],
            [KeyboardButton(text=CMD_ORDERS)],
        ],
        resize_keyboard=True
    )

# Admin panel
@admin_router.message(Command("admin"))
@admin_only
async def admin_panel(message: types.Message):
    """Admin panelini ko'rsatadi."""
    await message.answer("📊 Admin paneli:", reply_markup=get_admin_keyboard())

# Statistika
@admin_router.message(Command("stats"))
@admin_only
async def stats(message: types.Message):
    """Bot statistikasini ko'rsatadi."""
    stats = get_statistics()
    if not stats:
        return await message.answer("❌ Statistika ma'lumotlari topilmadi.")
    
    text = (
        f"📊 Statistika:\n\n"
        f"👥 Foydalanuvchilar: {stats['total_users']}\n"
        f"📦 Buyurtmalar: {stats['total_orders']}\n"
        f"⏳ Kutilayotgan: {stats['pending_orders']}\n"
    )
    await message.answer(text)

# Foydalanuvchilar ro'yxati
@admin_router.message(Command("users"))
@admin_only
async def list_users(message: types.Message):
    """Barcha foydalanuvchilar ro'yxatini ko'rsatadi."""
    users = get_all_users()
    if not users:
        return await message.answer(MSG_NO_USERS)
    
    text = "📋 Foydalanuvchilar ro'yxati:\n\n"
    for user in users:
        username = f"@{user[1]}" if user[1] else "yo'q"
        text += (
            f"🆔 ID: {user[0]}\n"
            f"👤 Username: {username}\n"
            f"📛 Ism: {user[2]}\n"
            f"📞 Telefon: {user[3]}\n\n"
        )
    
    # Agar xabar juda uzun bo'lsa, qismlarga bo'lib yuborish
    if len(text) > 4000:  # Telegram xabar uzunligi cheklovi ~4096
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i+4000])
    else:
        await message.answer(text)

# Buyurtmalar ro'yxati
@admin_router.message(Command("orders"))
@admin_only
async def list_orders(message: types.Message):
    """Barcha buyurtmalar ro'yxatini ko'rsatadi."""
    orders = get_all_orders()
    if not orders:
        return await message.answer(MSG_NO_ORDERS)
    
    text = "📦 Buyurtmalar ro'yxati:\n\n"
    for order in orders:
        from_location = f"{order[2]}, {order[3]}"
        to_location = f"{order[4]}, {order[5]}"
        location = f"Lat {order[9]}, Long {order[10]}" if order[9] and order[10] else "Yo'q"
        text += (
            f"🆔 ID: {order[0]}\n"
            f"👥 Foydalanuvchi ID: {order[1]}\n"
            f"🚚 Olib ketish: {from_location}\n"
            f"🏁 Yetkazish: {to_location}\n"
            f"⚖️ Og'irlik: {order[6]} kg\n"
            f"📍 Manzil: {order[7]}\n"
            f"📞 Telefon: {order[8]}\n"
            f"🌍 Lokatsiya: {location}\n"
            f"📊 Status: {order[11]}\n"
            f"🕒 Yaratilgan: {order[12]}\n\n"
        )
    
    # Agar xabar juda uzun bo'lsa, qismlarga bo'lib yuborish
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i+4000])
    else:
        await message.answer(text)

def register_admin_handlers(dp):
    """Admin handlerlarini ro'yxatga oladi."""
    dp.include_router(admin_router)
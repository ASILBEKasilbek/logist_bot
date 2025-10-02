from aiogram import Router, types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from states import RegistrationState, DriverRegistrationState
from config import ADMIN_ID
from database import (
    is_user_registered, register_user, register_driver, is_driver, get_driver_by_id, update_driver_status
)
import logging

router = Router()

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konstantalar
BUTTON_CANCEL = "❌ Bekor qilish"
BUTTON_INFO = "ℹ️ Ma'lumot"
BUTTON_SHARE_PHONE = "📞 Telefon raqamni yuborish"
BUTTON_CONFIRM_YES = "✅ Ha"
BUTTON_CONFIRM_NO = "❌ Yo‘q"
BUTTON_CUSTOMER = "👤 Mijoz"
BUTTON_DRIVER = "🚗 Haydovchi"
BUTTON_REGISTER_DRIVER = "🚗 Haydovchi sifatida ro'yxatdan o'tish"
BUTTON_APPROVE = "✅ Tasdiqlash"
BUTTON_REJECT = "❌ Rad etish"

# Avtomobil turlari ro'yxati
VEHICLE_TYPES = [
    "Tent", "Ref", "Kichkina Isuzu", "Katta Isuzu", "Chakman", "Kamaz",
    "Mega", "Ploshadka", "Paravoztral", "Labo", "Dagruz", "Boshqa"
]

# Umumiy klaviatura yaratish funksiyasi
def create_keyboard(items: list, columns: int = 2, add_cancel: bool = True) -> ReplyKeyboardMarkup:
    """Dinamik klaviatura yaratadi."""
    kb_buttons = [
        [KeyboardButton(text=items[j]) for j in range(i, min(i + columns, len(items)))]
        for i in range(0, len(items), columns)
    ]
    if add_cancel:
        kb_buttons.append([KeyboardButton(text=BUTTON_CANCEL)])
    return ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)

# Asosiy menyu klaviaturasi
def get_main_menu(is_driver_user: bool = False, driver_status: str = None) -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasini qaytaradi."""
    keyboard = [
        [KeyboardButton(text="🚚 Buyurtma berish")],
        [KeyboardButton(text=BUTTON_INFO)],
    ]
    # if not is_driver_user:
    #     keyboard.append([KeyboardButton(text=BUTTON_REGISTER_DRIVER)])
    if driver_status == "pending":
        keyboard = [[KeyboardButton(text=BUTTON_INFO)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# State tozalash komandasi
@router.message(Command("clearstate"))
async def clear_state(message: types.Message, state: FSMContext):
    """Foydalanuvchi state'ni tozalaydi."""
    await state.clear()
    await message.answer("✅ State tozalandi! Iltimos, qaytadan boshlang: /start")

# Start komandasi
@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    """Botni ishga tushiradi va ro'yxatdan o'tishni so'raydi."""
    user_id = message.from_user.id
    if not is_user_registered(user_id):
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=BUTTON_CUSTOMER), KeyboardButton(text=BUTTON_DRIVER)]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "🚚 Assalomu alaykum! Logistika botiga xush kelibsiz.\n"
            "Siz mijozmisiz yoki haydovchi?",
            reply_markup=kb
        )
        await state.set_state(RegistrationState.user_type)
    else:
        driver = get_driver_by_id(user_id)

        if driver:  # agar topilgan bo‘lsa
            driver_status = driver[4]   # indeks yoki ustun nomi bo‘yicha oling
        else:
            driver_status = None

        await show_main_menu(message, user_id, driver_status)

async def show_main_menu(message: types.Message, user_id: int, driver_status: str = None):
    """Asosiy menyuni ko'rsatadi."""
    is_driver_user = is_driver(user_id)
    if is_driver_user and driver_status == "pending":
        await message.answer(
            "⏳ Sizning haydovchi sifatidagi ro'yxatdan o'tish so'rovingiz admin tasdiqini kutmoqda.",
            reply_markup=get_main_menu(is_driver_user, driver_status)
        )
    elif is_driver_user and driver_status == "approved":
        await message.answer(
            "✅ <b>Tabriklaymiz!</b>\n\n"
            "Siz <b>haydovchi</b> sifatida muvaffaqiyatli tasdiqlandingiz. 🚛\n\n"
            "📌 Endi buyurtmalarni qabul qilishingiz mumkin. Buning uchun quyidagi havolaga o‘ting 👇\n"
            "<a href='https://t.me/ShopirlarYuk'>🔗 Buyurtmalar kanali</a>\n\n"
            "⏳ Iltimos, biroz kuting — tez orada buyurtmalar paydo bo‘ladi."
            , parse_mode="HTML"
        )

    else:
        await message.answer(
            "Quyidagi variantlardan birini tanlang:",
            reply_markup=get_main_menu(is_driver_user, driver_status)
        )

# Foydalanuvchi turi tanlash
@router.message(RegistrationState.user_type)
async def set_user_type(message: types.Message, state: FSMContext):
    """Foydalanuvchi turini qayta ishlaydi."""
    user_type = message.text
    if user_type not in [BUTTON_CUSTOMER, BUTTON_DRIVER]:
        return await message.answer("❌ Iltimos, variantlardan birini tanlang!")

    await state.update_data(user_type=user_type)
    logger.info(f"User {message.from_user.id} selected user_type: {user_type}")
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BUTTON_SHARE_PHONE, request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer(
        "📞 Telefon raqamingizni yuboring.",
        reply_markup=kb
    )
    await state.set_state(RegistrationState.phone)

# Ro'yxatdan o'tish (telefon)
@router.message(RegistrationState.phone)
async def register_phone(message: types.Message, state: FSMContext):
    """Foydalanuvchi telefon raqamini qayta ishlaydi."""
    phone = message.contact.phone_number if message.contact else message.text
    if not phone:
        return await message.answer("❌ Iltimos, telefon raqamini yuboring!")

    data = await state.get_data()
    logger.info(f"State data in register_phone: {data}")
    user_type = data.get('user_type')
    if not user_type:
        await state.clear()
        return await message.answer(
            "⚠️ Xatolik: Foydalanuvchi turi topilmadi. Iltimos, qaytadan boshlang: /start",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.update_data(phone=phone)
    register_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        phone,
        user_type == BUTTON_DRIVER
    )
    
    if user_type == BUTTON_DRIVER:
        kb = create_keyboard(VEHICLE_TYPES, columns=2)
        await message.answer("🚗 Avtomobil turini tanlang:", reply_markup=kb)
        await state.set_state(DriverRegistrationState.vehicle_type)
    else:
        await state.clear()
        await message.answer("✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=types.ReplyKeyboardRemove())
        await show_main_menu(message, message.from_user.id)

# Avtomobil turi tanlash
@router.message(DriverRegistrationState.vehicle_type)
async def set_vehicle_type(message: types.Message, state: FSMContext):
    """Avtomobil turini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    vehicle_type = message.text.strip()
    if vehicle_type == "Boshqa":
        await message.answer("Iltimos, avtomobil turini kiriting:")
        await state.set_state(DriverRegistrationState.custom_vehicle_type)
        return

    if vehicle_type not in VEHICLE_TYPES[:-1]:  # Exclude "Boshqa" from validation
        return await message.answer("❌ Iltimos, ro'yxatdan avtomobil turini tanlang yoki 'Boshqa' ni tanlab kiriting!")

    await state.update_data(vehicle_type=vehicle_type)
    await message.answer("📄 Haydovchi guvohnomasi raqamini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(DriverRegistrationState.license_number)

# Maxsus avtomobil turi (Boshqa)
@router.message(DriverRegistrationState.custom_vehicle_type)
async def set_custom_vehicle_type(message: types.Message, state: FSMContext):
    """Maxsus avtomobil turini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    await state.update_data(vehicle_type=message.text.strip())
    await message.answer("📄 Haydovchi guvohnomasi raqamini kiriting:")
    await state.set_state(DriverRegistrationState.license_number)

# Haydovchi ro'yxati (guvohnoma raqami)
@router.message(DriverRegistrationState.license_number)
async def set_license_number(message: types.Message, state: FSMContext):
    """Haydovchi guvohnomasi raqamini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    await state.update_data(license_number=message.text)
    await message.answer_photo( photo="AgACAgIAAxkBAAIIe2jd8m9-aNm-ZIpis-ZvBffom29KAAL59jEb3KvwShWAgb-QASgbAQADAgADeAADNgQ",caption="🔎 Namuna kabi haydovchilik guvohnomangiz bilan rasmga tushib yuboring.")
    await state.set_state(DriverRegistrationState.license_photo)

# Haydovchi ro'yxati (guvohnoma rasmi)
@router.message(DriverRegistrationState.license_photo)
async def set_license_photo(message: types.Message, state: FSMContext):
    """Haydovchi guvohnomasi rasmini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    if not message.photo:
        return await message.answer("❌ Iltimos, guvohnoma rasmini yuboring!")

    await state.update_data(license_photo=message.photo[-1].file_id)
    data = await state.get_data()
    logger.info(f"State data in set_license_photo: {data}")

    # Telefonni tekshirish
    phone = data.get('phone')
    if not phone:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=BUTTON_SHARE_PHONE, request_contact=True)]],
            resize_keyboard=True
        )
        await message.answer(
            "⚠️ Telefon raqami topilmadi. Iltimos, telefon raqamingizni qayta yuboring:",
            reply_markup=kb
        )
        await state.set_state(RegistrationState.phone)
        return

    # Ma'lumotlarni tasdiqlash
    driver_text = (
        f"🚗 Haydovchi ro'yxatdan o'tish ma'lumotlari:\n\n"
        f"👤 Ism: {message.from_user.full_name}\n"
        f"📞 Telefon: {phone}\n"
        f"🚗 Avtomobil turi: {data['vehicle_type']}\n"
        f"📄 Guvohnoma raqami: {data['license_number']}\n"
        f"📸 Guvohnoma rasmi: Yuborildi\n\n"
        f"Ma'lumotlarni tasdiqlaysizmi?"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_CONFIRM_YES, callback_data="driver_confirm_yes")],
        [InlineKeyboardButton(text=BUTTON_CONFIRM_NO, callback_data="driver_confirm_no")]
    ])

    await message.answer(driver_text, reply_markup=kb)
    await state.set_state(DriverRegistrationState.confirm)

# Haydovchi ro'yxatdan o'tish tasdiqlash
@router.callback_query(DriverRegistrationState.confirm)
async def confirm_driver_registration(callback: types.CallbackQuery, state: FSMContext):
    """Haydovchi ro'yxatdan o'tishni tasdiqlaydi yoki bekor qiladi."""
    if callback.data == "driver_confirm_yes":
        data = await state.get_data()
        logger.info(f"State data in confirm_driver_registration: {data}")
        phone = data.get('phone', 'Telefon raqami kiritilmagan')

        register_driver(
            user_id=callback.from_user.id,
            vehicle_type=data['vehicle_type'],
            license_number=data['license_number'],
            license_photo=data['license_photo'],
            status="pending"
        )

        driver_text = (
            f"🚗 <b>Yangi haydovchi so'rovi!</b>\n\n"
            f"👤 Ism: {callback.from_user.full_name}\n"
            f"📞 Telefon: {phone}\n"
            f"🚗 Avtomobil turi: {data['vehicle_type']}\n"
            f"📄 Guvohnoma raqami: {data['license_number']}\n"
            f"📸 Guvohnoma rasmi: Yuborildi\n"
            f"🆔 Telegram ID: {callback.from_user.id}\n"
        )

        # Adminga yuborish
        try:
            for admin_id in ADMIN_ID:
                await callback.bot.send_message(admin_id, driver_text, parse_mode="HTML")
                await callback.bot.send_photo(admin_id, data['license_photo'])
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=BUTTON_APPROVE, callback_data=f"approve_driver_{callback.from_user.id}")],
                    [InlineKeyboardButton(text=BUTTON_REJECT, callback_data=f"reject_driver_{callback.from_user.id}")]
                ])
                await callback.bot.send_message(admin_id, "Haydovchini tasdiqlash yoki rad etish:", reply_markup=kb)
        except Exception as e:
            logger.error(f"Error sending to admin: {str(e)}")
            await callback.message.answer(f"⚠️ Xatolik: Admin bilan bog‘lanishda muammo: {str(e)}")

        await callback.message.edit_text(
            "✅ Ro'yxatdan o'tish so'rovingiz qabul qilindi! Admin tasdiqini kuting.",
            reply_markup=None
        )
        await state.clear()
    else:
        await callback.message.edit_text("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=None)
        await state.clear()

# Admin haydovchini tasdiqlash yoki rad etish
@router.callback_query(lambda c: c.data.startswith("approve_driver_") or c.data.startswith("reject_driver_"))
async def handle_driver_approval(callback: types.CallbackQuery):
    """Admin haydovchini tasdiqlaydi yoki rad etadi."""
    action, _, user_id = callback.data.partition("_driver_")
    user_id = int(user_id)
    status = "approved" if action == "approve" else "rejected"
    
    update_driver_status(user_id, status)
    driver = get_driver_by_id(user_id)
    
    if driver:
        try:
            await callback.bot.send_message(
                user_id,
                f"✅ Haydovchi sifatidagi ro'yxatdan o'tishingiz {'tasdiqlandi' if status == 'approved' else 'rad etildi'}!"
            )
            if status == "approved":
                await callback.bot.send_message(
                    user_id,
                    "Siz endi buyurtmalarni qabul qilishingiz mumkin!"
                )
            await callback.message.edit_text(f"Haydovchi {status} qilindi.", reply_markup=None)
        except Exception as e:
            logger.error(f"Error notifying user: {str(e)}")
            await callback.message.answer(f"⚠️ Xatolik: Foydalanuvchi bilan bog‘lanishda muammo: {str(e)}")
    else:
        await callback.message.edit_text("❌ Haydovchi topilmadi.", reply_markup=None)

# Haydovchi ro'yxatdan o'tish (qo'shimcha)
@router.message(lambda m: m.text == BUTTON_REGISTER_DRIVER)
async def start_driver_registration(message: types.Message, state: FSMContext):
    """Haydovchi ro'yxatdan o'tishni boshlaydi."""
    user_id = message.from_user.id
    if is_driver(user_id):
        driver_status = get_driver_by_id(user_id)[4]
        if driver_status == "pending":
            return await message.answer("⏳ Sizning ro'yxatdan o'tish so'rovingiz admin tasdiqini kutmoqda!")
        elif driver_status == "approved":
            return await message.answer("Siz allaqachon haydovchi sifatida tasdiqlangansiz!")
        else:
            return await message.answer("Sizning oldingi so'rovingiz rad etilgan. Qayta urinib ko'ring.")

    kb = create_keyboard(VEHICLE_TYPES, columns=2)
    await message.answer("🚗 Avtomobil turini tanlang:")
    await state.set_state(DriverRegistrationState.vehicle_type)

# Ma'lumot
@router.message(lambda m: m.text == BUTTON_INFO)
async def info(message: types.Message):
    """Bot haqida ma'lumot beradi."""
    await message.answer(
        "🚚 Bu logistika boti. Yuk jo'natish uchun 'Buyurtma berish' tugmasini bosing.\n"
        "Haydovchilar buyurtmalarni guruhda ko'rishlari mumkin."
    )

def register_user_handlers(dp: Dispatcher):
    """Handlerlarni ro'yxatga oladi."""
    dp.include_router(router)
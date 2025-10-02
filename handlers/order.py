from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from states import OrderState
from config import ADMIN_ID, GROUP_ID
from database import is_user_registered, get_user_phone, save_order, is_driver, get_driver_by_id
from regions import regions, viloyatlar
from aiogram import Dispatcher
import logging

router = Router()

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konstantalar
BUTTON_CANCEL = "❌ Bekor qilish"
BUTTON_SKIP = "O'tkazib yuborish"
BUTTON_ORDER = "🚚 Buyurtma berish"
BUTTON_SHARE_PHONE = "📞 Telefon raqamni yuborish"
BUTTON_SHARE_LOCATION = "📍 Lokatsiyani yuborish"
BUTTON_CONFIRM_YES = "✅ Ha"
BUTTON_CONFIRM_NO = "❌ Yo‘q"

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

# Buyurtma boshlash
@router.message(lambda m: m.text in [BUTTON_ORDER, "/buyurtma"])
async def order_start(message: types.Message, state: FSMContext):
    """Buyurtma berish jarayonini boshlaydi."""
    user_id = message.from_user.id
    if not is_user_registered(user_id):
        return await message.answer("Iltimos, avval ro'yxatdan o'ting! /start")
    
    if is_driver(user_id) and get_driver_by_id(user_id)[4] != "approved":
        return await message.answer("⏳ Buyurtma berish uchun admin tasdiqini kuting.")

    kb = create_keyboard(viloyatlar, columns=2)
    await message.answer("🏙️ Yuk qaysi viloyatdan jo'natiladi?", reply_markup=kb)
    await state.set_state(OrderState.from_viloyat)

# Viloyat tanlash (yuborish)
@router.message(OrderState.from_viloyat)
async def set_from_viloyat(message: types.Message, state: FSMContext):
    """Yuborish viloyatini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    viloyat = message.text.strip()
    if viloyat not in regions:
        return await message.answer("❌ Noto'g'ri viloyat! Iltimos, ro'yxatdan tanlang.")

    await state.update_data(from_viloyat=viloyat)
    tumanlar = regions[viloyat]
    kb = create_keyboard(tumanlar, columns=2)
    await message.answer(f"🏘️ {viloyat}ning qaysi tumani/shahridan?", reply_markup=kb)
    await state.set_state(OrderState.from_tuman)

# Tuman tanlash (yuborish)
@router.message(OrderState.from_tuman)
async def set_from_tuman(message: types.Message, state: FSMContext):
    """Yuborish tumanini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    await state.update_data(from_tuman=message.text.strip())
    kb = create_keyboard(viloyatlar, columns=2)
    await message.answer("🏙️ Yuk qaysi viloyatga yetkaziladi?", reply_markup=kb)
    await state.set_state(OrderState.to_viloyat)

# Viloyat tanlash (yetkazish)
@router.message(OrderState.to_viloyat)
async def set_to_viloyat(message: types.Message, state: FSMContext):
    """Yetkazish viloyatini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    viloyat = message.text.strip()
    if viloyat not in regions:
        return await message.answer("❌ Noto'g'ri viloyat! Iltimos, ro'yxatdan tanlang.")

    await state.update_data(to_viloyat=viloyat)
    tumanlar = regions[viloyat]
    kb = create_keyboard(tumanlar, columns=2)
    await message.answer(f"🏘️ {viloyat}ning qaysi tumani/shahriga?", reply_markup=kb)
    await state.set_state(OrderState.to_tuman)

# Tuman tanlash (yetkazish)
@router.message(OrderState.to_tuman)
async def set_to_tuman(message: types.Message, state: FSMContext):
    """Yetkazish tumanini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    await state.update_data(to_tuman=message.text.strip())
    await message.answer("📝 Buyurtma nomini (yuk tavsifini) kiriting:")
    await state.set_state(OrderState.order_name)

# Buyurtma nomi
@router.message(OrderState.order_name)
async def set_order_name(message: types.Message, state: FSMContext):
    """Buyurtma nomini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    await state.update_data(order_name=message.text.strip())
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="5 kg"), KeyboardButton(text="10 kg"), KeyboardButton(text="20 kg")],
            [KeyboardButton(text="50 kg"), KeyboardButton(text="100 kg"), KeyboardButton(text="Boshqa")],
            [KeyboardButton(text=BUTTON_CANCEL)],
        ],
        resize_keyboard=True
    )
    await message.answer("⚖️ Yukning og‘irligini tanlang yoki kiriting (kg):", reply_markup=kb)
    await state.set_state(OrderState.weight)

# Yuk og'irligi
@router.message(OrderState.weight)
async def set_weight(message: types.Message, state: FSMContext):
    """Yuk og'irligini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    text = message.text.strip().replace(" kg", "")
    try:
        weight = float(text)
    except ValueError:
        return await message.answer("❌ Iltimos, faqat son kiriting (masalan: 20)!")

    await state.update_data(weight=weight)
    kb = create_keyboard(VEHICLE_TYPES, columns=2)
    await message.answer("🚛 Qanday transport turi kerak?", reply_markup=kb)
    await state.set_state(OrderState.vehicle_type)

# Transport turi
@router.message(OrderState.vehicle_type)
async def set_vehicle_type(message: types.Message, state: FSMContext):
    """Transport turini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    vehicle_type = message.text.strip()
    if vehicle_type == "Boshqa":
        await message.answer("Iltimos, transport turini kiriting:")
        await state.set_state(OrderState.custom_vehicle_type)
        return

    if vehicle_type not in VEHICLE_TYPES[:-1]:  # Exclude "Boshqa" from validation
        return await message.answer("❌ Iltimos, ro'yxatdan transport turini tanlang yoki 'Boshqa' ni tanlab kiriting!")

    await state.update_data(vehicle_type=vehicle_type)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_SKIP)],
            [KeyboardButton(text=BUTTON_CANCEL)],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "📸 Yuk rasmini yuboring (ixtiyoriy). Yoki 'O'tkazib yuborish' ni tanlang.",
        reply_markup=kb
    )
    await state.set_state(OrderState.photo)

# Maxsus transport turi (Boshqa)
@router.message(OrderState.custom_vehicle_type)
async def set_custom_vehicle_type(message: types.Message, state: FSMContext):
    """Maxsus transport turini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    await state.update_data(vehicle_type=message.text.strip())
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_SKIP)],
            [KeyboardButton(text=BUTTON_CANCEL)],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "📸 Yuk rasmini yuboring (ixtiyoriy). Yoki 'O'tkazib yuborish' ni tanlang.",
        reply_markup=kb
    )
    await state.set_state(OrderState.photo)

# Yuk rasmi
@router.message(OrderState.photo)
async def set_photo(message: types.Message, state: FSMContext):
    """Yuk rasmini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text.lower() != BUTTON_SKIP.lower():
        return await message.answer("❌ Iltimos, rasm yuboring yoki o'tkazib yuboring!")

    await state.update_data(photo_id=photo_id)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_SKIP)],
            [KeyboardButton(text=BUTTON_CANCEL)],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "📍 Yukni olib ketish manzilini kiriting (ixtiyoriy). Yoki 'O'tkazib yuborish' ni tanlang.",
        reply_markup=kb
    )
    await state.set_state(OrderState.pickup_address)

# Manzil kiritish
@router.message(OrderState.pickup_address)
async def set_pickup_address(message: types.Message, state: FSMContext):
    """Yukni olib ketish manzilini qayta ishlaydi."""
    if message.text == BUTTON_CANCEL:
        await state.clear()
        return await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())

    address = "Yo'q" if message.text.lower() == BUTTON_SKIP.lower() else message.text
    await state.update_data(pickup_address=address)

    phone = get_user_phone(message.from_user.id)
    if phone:
        await state.update_data(phone=phone)
        await ask_for_location(message, state)
    else:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=BUTTON_SHARE_PHONE, request_contact=True)]],
            resize_keyboard=True
        )
        await message.answer("📞 Telefon raqamingizni yuboring:", reply_markup=kb)
        await state.set_state(OrderState.phone)

# Telefon raqami (agar ro'yxatdan o'tmagan bo'lsa)
@router.message(OrderState.phone)
async def set_phone(message: types.Message, state: FSMContext):
    """Telefon raqamini qayta ishlaydi."""
    phone = message.contact.phone_number if message.contact else message.text
    if not phone:
        return await message.answer("❌ Iltimos, telefon raqamini yuboring!")

    await state.update_data(phone=phone)
    register_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        phone=phone
    )
    await ask_for_location(message, state)

async def ask_for_location(message: types.Message, state: FSMContext):
    """Lokatsiya so'raydi."""
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BUTTON_SHARE_LOCATION, request_location=True)]],
        resize_keyboard=True
    )
    await message.answer("📍 Yukni olib ketish lokatsiyasini yuboring (joylashuvni yoqishni esdan chiqarmang!):", reply_markup=kb)
    await state.set_state(OrderState.location)

# Lokatsiya
@router.message(OrderState.location)
async def set_location(message: types.Message, state: FSMContext):
    """Yuborilgan lokatsiyani qayta ishlaydi."""
    if not message.location:
        return await message.answer("❌ Iltimos, lokatsiya yuboring!")

    await state.update_data(latitude=message.location.latitude, longitude=message.location.longitude)
    data = await state.get_data()
    logger.info(f"State data in set_location: {data}")

    from_location = f"{data['from_viloyat']}, {data['from_tuman']}"
    to_location = f"{data['to_viloyat']}, {data['to_tuman']}"
    photo_text = "Yuborildi" if data.get('photo_id') else "Yo'q"
    text = (
        f"📦 Buyurtma ma'lumotlari:\n\n"
        f"📝 Nom: {data['order_name']}\n"
        f"🚚 Olinadigan joy: {from_location}\n"
        f"🏁 Yetkaziladigan joy: {to_location}\n"
        f"⚖️ Og‘irligi: {data['weight']} kg\n"
        f"🚛 Transport turi: {data['vehicle_type']}\n"
        f"📸 Rasm: {photo_text}\n"
        f"📍 Manzil: {data['pickup_address']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"🌍 Lokatsiya: Yuborildi\n\n"
        f"Ma'lumotlarni tasdiqlaysizmi?"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_CONFIRM_YES, callback_data="confirm_yes")],
        [InlineKeyboardButton(text=BUTTON_CONFIRM_NO, callback_data="confirm_no")]
    ])

    await message.answer(text, reply_markup=kb)
    await state.set_state(OrderState.confirm)

# Buyurtmani tasdiqlash
@router.callback_query(OrderState.confirm)
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    """Buyurtmani tasdiqlaydi yoki bekor qiladi."""
    if callback.data == "confirm_yes":
        data = await state.get_data()
        logger.info(f"State data in confirm_order: {data}")
        from_location = f"{data['from_viloyat']}, {data['from_tuman']}"
        to_location = f"{data['to_viloyat']}, {data['to_tuman']}"
        order_text = (
            f"📦 <b>Yangi buyurtma!</b>\n\n"
            f"👤 Foydalanuvchi: {callback.from_user.full_name} "
            f"(@{callback.from_user.username or 'username yo‘q'})\n"
            f"📝 Nom: {data['order_name']}\n"
            f"🚚 Olinadigan joy: {from_location}\n"
            f"🏁 Yetkaziladigan joy: {to_location}\n"
            f"⚖️ Og‘irligi: {data['weight']} kg\n"
            f"🚛 Transport turi: {data['vehicle_type']}\n"
            f"📍 Manzil: {data['pickup_address']}\n"
            f"📞 Telefon: {data['phone']}\n"
            f"🌍 Lokatsiya: Lat: {data['latitude']}, Long: {data['longitude']}"
        )

        # Ma'lumotlar bazasiga saqlash
        save_order(
            user_id=callback.from_user.id,
            order_name=data['order_name'],
            from_viloyat=data['from_viloyat'],
            from_tuman=data['from_tuman'],
            to_viloyat=data['to_viloyat'],
            to_tuman=data['to_tuman'],
            weight=data['weight'],
            vehicle_type=data['vehicle_type'],
            photo_id=data.get('photo_id'),
            pickup_address=data['pickup_address'],
            phone=data['phone'],
            latitude=data['latitude'],
            longitude=data['longitude']
        )

        # Foydalanuvchiga javob
        await callback.message.edit_text("✅ Buyurtmangiz qabul qilindi!", reply_markup=None)
        await callback.message.answer(
            "🔜 Tez orada operator yoki haydovchi siz bilan bog‘lanadi.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Admin va guruhga yuborish
        try:
            for admin_id in ADMIN_ID:
                if data.get('photo_id'):
                    await callback.bot.send_photo(
                        chat_id=admin_id,
                        photo=data['photo_id'],
                        caption=order_text,
                        parse_mode="HTML"
                    )
                else:
                    await callback.bot.send_message(admin_id, order_text, parse_mode="HTML")
                await callback.bot.send_location(chat_id=admin_id, latitude=data['latitude'], longitude=data['longitude'])
            
            # # Guruhga (haydovchilar uchun)
            # await callback.bot.send_message(GROUP_ID, order_text, parse_mode="HTML")
            # await callback.bot.send_location(GROUP_ID, data['latitude'], data['longitude'])
            # if data.get('photo_id'):
            #     await callback.bot.send_photo(GROUP_ID, data['photo_id'])

        except Exception as e:
            logger.error(f"Error sending order to admin/group: {str(e)}")
            await callback.message.answer(f"⚠️ Xatolik: {str(e)}")

        await state.clear()
    else:
        await callback.message.edit_text("❌ Buyurtma bekor qilindi.", reply_markup=None)
        await state.clear()

def register_order_handlers(dp: Dispatcher):
    """Handlerlarni ro'yxatga oladi."""
    dp.include_router(router)
from aiogram.fsm.state import State, StatesGroup

class OrderState(StatesGroup):
    from_viloyat = State()
    from_tuman = State()
    to_viloyat = State()
    to_tuman = State()
    order_name = State()
    weight = State()
    vehicle_type = State()
    custom_vehicle_type = State()
    photo = State()
    pickup_address = State()
    phone = State()
    location = State()
    confirm = State()

class RegistrationState(StatesGroup):
    user_type = State()
    phone = State()

class DriverRegistrationState(StatesGroup):
    vehicle_type = State()
    custom_vehicle_type = State()
    license_number = State()
    license_photo = State()
    confirm = State()
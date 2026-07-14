from __future__ import annotations

from typing import TypedDict

from bot.config import settings


WEEKDAYS_AR = {
    0: "الإثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

MONTHS_AR = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}


class LocaleDict(TypedDict, total=False):
    welcome: str
    book_button: str
    my_appointments_button: str
    my_appointments_title: str
    select_service: str
    select_individuals: str
    enter_individuals: str
    invalid_individuals: str
    select_date: str
    select_time: str
    no_slots: str
    no_services: str
    enter_name: str
    enter_phone: str
    booking_summary: str
    booking_confirmed: str
    booking_cancelled: str
    slot_taken: str
    invalid_input: str
    not_authorized: str
    admin_menu: str
    no_bookings: str
    appointment_cancelled: str
    help: str
    confirm: str
    cancel: str
    cancel_appointment: str
    admin_today: str
    admin_upcoming: str
    import_invalid_format: str
    import_success: str
    import_error: str
    admin_found_bookings: str
    admin_card_client: str
    admin_card_phone: str
    admin_card_service: str
    admin_card_individuals: str
    admin_card_schedule: str
    admin_daily_index: str


MESSAGES: dict[str, LocaleDict] = {
    "en": {
        "welcome": "👋 Welcome to the Appointment Booking System!\n\nYou can book a new appointment or view your existing ones.",
        "book_button": "📅 Book New Appointment",
        "my_appointments_button": "🗂️ My Appointments",
        "my_appointments_title": "🗂️ Your Appointments:",
        "select_service": "Please select a service:",
        "select_individuals": "How many individuals is this appointment for?",
        "enter_individuals": "Please type the number of individuals for this appointment (from {min} to {max}):",
        "invalid_individuals": "Sorry, please enter a valid whole number between {min} and {max}.",
        "select_date": "Please select a date for your appointment:",
        "select_time": "Please select a time for your appointment: {slot}",
        "no_slots": "No available time slots for the selected date. Please choose another date.",
        "no_services": "No services are currently available. Please try again later.",
        "enter_name": "Please enter your full name:",
        "enter_phone": "Please enter your phone number:",
        "booking_summary": "📋 Booking Summary:\nService: {service}\nIndividuals: {individuals_count}\nDate: {date}\nTime: {time} - {end_time}\nDuration: {duration} minutes",
        "booking_confirmed": "✅ Booking Confirmed!\nService: {service}\nIndividuals: {individuals_count}\nDate: {date}\nTime: {time} - {end_time}\nDuration: {duration} minutes",
        "booking_cancelled": "The current operation has been cancelled.",
        "slot_taken": "⚠️ This time slot is no longer available. Please start over.",
        "invalid_input": "Invalid input. Please try again.",
        "not_authorized": "You are not authorized to access this feature.",
        "admin_menu": "🔧 Admin Menu",
        "no_bookings": "You have no upcoming appointments.",
        "appointment_cancelled": "Your appointment has been cancelled.",
        "help": "Use the buttons below to navigate the system.",
        "confirm": "✅ Confirm",
        "cancel": "❌ Cancel",
        "cancel_appointment": "❌ Cancel Appointment",
        "admin_today": "☀️ Today's Bookings",
        "admin_upcoming": "📅 Upcoming Bookings",
        "import_invalid_format": "Please send a valid .xlsx or .csv file with columns: title, duration_minutes, is_active.",
        "import_success": "✅ Services imported successfully.\nCreated: {created}\nUpdated: {updated}",
        "import_error": "❌ Import failed: {error}",
        "admin_found_bookings": "📋 Found {count} appointments:",
        "admin_card_client": "👤 Client",
        "admin_card_phone": "📞 Phone",
        "admin_card_service": "🛠 Service",
        "admin_card_individuals": "👥 Individuals",
        "admin_card_schedule": "📅 Date | ⏰ Time",
        "admin_daily_index": "🔢 Daily Index: {index}",
    },
    "ar": {
        "welcome": "👋 مرحبا بك في نظام حجز المواعيد!\n\nيمكنك حجز موعد جديد أو عرض مواعيدك الحالية.",
        "book_button": "📅 حجز موعد جديد",
        "my_appointments_button": "🗂️ مواعيدي الحالية",
        "my_appointments_title": "🗂️ مواعيدك الحالية:",
        "select_service": "الرجاء اختيار الخدمة:",
        "select_individuals": "كم عدد الأفراد لهذا الموعد؟",
        "enter_individuals": "الرجاء إدخال عدد الأفراد للموعد (من {min} إلى {max}):",
        "invalid_individuals": "عفواً، الرجاء إدخال رقم صحيح بين {min} و {max}.",
        "select_date": "الرجاء اختيار تاريخ للموعد:",
        "select_time": "الرجاء اختيار وقت للموعد: {slot}",
        "no_slots": "لا توجد مواعيد متاحة في التاريخ المحدد. الرجاء اختيار تاريخ آخر.",
        "no_services": "لا توجد خدمات متاحة حالياً. الرجاء المحاولة مرة أخرى لاحقاً.",
        "enter_name": "الرجاء إدخال اسمك الكامل:",
        "enter_phone": "الرجاء إدخال رقم هاتفك:",
        "booking_summary": "📋 ملخص الحجز:\nالخدمة: {service}\nعدد الأفراد: {individuals_count}\nالتاريخ: {date}\nالوقت: {time} - {end_time}\nالمدة: {duration} دقائق",
        "booking_confirmed": "✅ تم تأكيد الحجز!\nالخدمة: {service}\nعدد الأفراد: {individuals_count}\nالتاريخ: {date}\nالوقت: {time} - {end_time}\nالمدة: {duration} دقائق",
        "booking_cancelled": "تم إلغاء العملية الحالية.",
        "slot_taken": "⚠️ هذا الموعد غير متاح بعد الآن. الرجاء البدء من جديد.",
        "invalid_input": "مدخل غير صالح. الرجاء المحاولة مرة أخرى.",
        "not_authorized": "غير مصرح لك بالوصول إلى هذه الميزة.",
        "admin_menu": "🔧 قائمة المشرف",
        "no_bookings": "ليس لديك مواعيد قادمة.",
        "appointment_cancelled": "تم إلغاء موعدك.",
        "help": "استخدم الأزرار أدناه للتنقل في النظام.",
        "confirm": "✅ تأكيد",
        "cancel": "❌ إلغاء",
        "cancel_appointment": "إلغاء الموعد ❌",
        "admin_today": "مواعيد اليوم 📌",
        "admin_upcoming": "المواعيد القادمة 📅",
        "import_invalid_format": "الرجاء إرسال ملف .xlsx أو .csv صالح يحتوي على الأعمدة: title، duration_minutes، is_active.",
        "import_success": "✅ تم استيراد الخدمات بنجاح.\nتم الإنشاء: {created}\nتم التحديث: {updated}",
        "import_error": "❌ فشل الاستيراد: {error}",
        "admin_found_bookings": "📋 تم العثور على {count} مواعيد:",
        "admin_card_client": "👤 العميل",
        "admin_card_phone": "📞 الهاتف",
        "admin_card_service": "🛠 الخدمة",
        "admin_card_individuals": "👥 عدد الأفراد",
        "admin_card_schedule": "📅 التاريخ | ⏰ الوقت",
        "admin_daily_index": "🔢 رقم الموعد اليومي: {index}",
    }
}


def t(key: str, language: str | None = None) -> str:
    if language is None:
        language = settings.default_language

    normalized_lang = language[:2]

    for lang in (settings.default_language, normalized_lang, "en"):
        if lang in MESSAGES and key in MESSAGES[lang]:
            return MESSAGES[lang][key]

    return key
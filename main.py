import datetime
import json
import telebot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from data_base import users, is_new_user, write_to_logi, accept, writes
import random

# git config --global user.email "desayt04kago@gmail.com"
# git config --global user.name "Artem"

TOKEN = open("token", "r").read()
USER_ID_MASTER = int(open("master_user_id", "r").read().replace(" ", ""))
bot = telebot.TeleBot(TOKEN)
#USER_ID_MASTER = 5803395877
bot = telebot.TeleBot(TOKEN)
date = {}
date_write_to_master = {}
photo_date = {}
data_dict = {}


@bot.message_handler(['start'])
def check_user(msg):
    kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if is_new_user(msg):
        kb.row("ДА", "НЕТ")
        bot.send_message(msg.chat.id, "Вы не зарегистрированы. Желаете пройти регистрацию?", reply_markup=kb)
        bot.register_next_step_handler(msg, register_step_one)
    else:
        menu(msg, kb)

@bot.message_handler(content_types=["text"])
def message_handler(msg):
    func = {
        "посмотреть активные записи" : show_all_writes,
        "добавить даты записи" : add_date_one,
        "сменить номер телефона" : change_settings,
        "изменить имя" : change_settings,
        "изменить фамилию" : change_settings,
        "удалить аккаунт" : change_settings,
        "меню" : menu,
        "информация" : show_information,
        "согласовать дизайн" : to_accept_design_one,
        "аккаунт" : show_user_information,
        "цены" : show_price,
    }
    if msg.text in func.keys():
        if msg.text == "меню":
            menu(msg, kb=ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True))
            return
        func[msg.text](msg)
        return
    if is_new_user(msg):
        check_user(msg)
        return
    write_to_logi(msg)
    menu(msg, kb=ReplyKeyboardMarkup(resize_keyboard=True), is_first=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('одобрить_') or call.data.startswith('отклонить_'))
def accept_of_not(call):
    r, user_id = call.data.split('_')
    user_id = int(user_id)

    bot.edit_message_reply_markup(chat_id=USER_ID_MASTER, message_id=call.message.message_id, reply_markup=None)
    kb = ReplyKeyboardRemove()
    if r == "одобрить":
        text = "Ваш дизайн одобрен!"
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.row("меню")
    else:
        text = "К сожалению ваш дизайн был отклонён, выберите другой и отправьте на одобрение"
    try:
        bot.send_message(user_id, text, reply_markup=kb)
        select_date(call.message)
    except Exception as e:
        bot.send_message(USER_ID_MASTER, f"Сообщение не было доставлено, возможно, бота заблокировали. Ошибка:\n {e}")
    if call.message.message_id in photo_date:
        del photo_date[call.message.message_id]
        accept.delete_row("user_id", user_id)
    bot.answer_callback_query(call.id, "Успешно!")

def show_all_writes(msg):
    all_line = writes.read_all()
    for line in all_line:
        all_users = users.read_all()
        for user in all_users:
            if line[0] == user[0]:
                bot.send_message(msg.chat.id, f'Запись на {line[1]} в {line[2]}\n'
                                              f'Имя: {user[2]}\nФамилия: {user[3]}\nТелефон: {user[4]}')



def add_date_one(msg):
    bot.send_message(msg.chat.id,"Отправьте свободные места в формате\n2.03 14:00;17:00\n4.03 14:00;17:00")
    bot.register_next_step_handler(msg, add_date_two)
def add_date_two(msg):
    list_data = msg.text.split("\n")
    for i in list_data:
        first_data = i.split(" ")
        print(first_data)
        day_month = first_data[0]
        data_dict[day_month] = first_data[1].split(";")
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    with open("date.json", "w") as file:
        file.truncate(0)
        file.seek(0)
        json.dump(data_dict, file, indent=4)
        bot.send_message(msg.chat.id, "Данные успешно загружены!", reply_markup=kb)
        menu(msg, kb=ReplyKeyboardMarkup(resize_keyboard=True), is_first=False)
    file.close()

def select_date(msg):
    global data_dict
    try:
        with open("date.json", "r") as file:
            data_dict = json.load(file)
    except FileNotFoundError as FNFE:
        bot.send_message(msg.chat.id, "Файл не найден! Обратитесь к Мастеру")
        return
    except json.decoder.JSONDecodeError:
        bot.send_message(msg.chat.id, "Ошибка чтения данных! Обратитесь к Мастеру")
        return
    if not data_dict:
        bot.send_message(msg.chat.id, "Нет свободных мест для записи(")
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for day in data_dict.keys():
        kb.row(day)
    kb.row("меню")
    bot.send_message(msg.chat.id, "Выберите дату записи", reply_markup=kb)
    bot.register_next_step_handler(msg, select_time_in_date)

def select_time_in_date(msg):
    if msg.text in data_dict.keys():
        date_write_to_master[msg.chat.id] = {}
        date_write_to_master[msg.chat.id]["day"] = msg.text
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for time in data_dict[msg.text]:
            kb.row(time)
        kb.row("меню")
        bot.send_message(msg.chat.id, "Выберите время записи", reply_markup=kb)
        bot.register_next_step_handler(msg, accept_select_date_and_time)

def accept_select_date_and_time(msg):
    if msg.text in data_dict[date_write_to_master[msg.chat.id]["day"]]:
        date_write_to_master[msg.chat.id]["time"] = msg.text
    bot.send_message(msg.chat.id, f"Вы записались на {date_write_to_master[msg.chat.id]["day"]} - {date_write_to_master[msg.chat.id]["time"]}", reply_markup=ReplyKeyboardRemove())
    writes.write([msg.chat.id, date_write_to_master[msg.chat.id]["day"], date_write_to_master[msg.chat.id]["time"]], "writes")
    menu(msg, kb=ReplyKeyboardMarkup(resize_keyboard=True), is_first=False)

def return_name(msg):
    name = users.read("chat_id", msg.chat.id)[2]
    return name
def menu(msg, kb, is_first : bool = False):
    name = return_name(msg)
    if is_first:
        hello_list = [f"Доброе утречко {name}! Или сейчас вечер...", f"Приветулик {name}", f"{name}! Рады видеть тебя)"]
    else:
        hello_list = [f"{name}, какой раздел ты хочешь выбрать?", f"Что хочешь выбрать, {name}?"]
    text = random.choice(hello_list)
    kb.row("информация")
    kb.row("согласовать дизайн")
    kb.row("аккаунт", "цены")
    if users.read("user_id", USER_ID_MASTER)[0] == msg.from_user.id:
        kb.row("добавить даты записи")
        kb.row("посмотреть активные записи")
    bot.send_message(msg.chat.id, text,reply_markup=kb)

def show_information(msg):
    bot.send_message(msg.chat, "Я адун")

def to_accept_design_one(msg):
    kb = ReplyKeyboardRemove()
    if not(accept.read("user_id", msg.from_user.id)):
        bot.send_message(msg.chat.id, "Отправьте фото дизайна:", reply_markup=kb)
        bot.register_next_step_handler(msg, to_accept_design_two)
    else:
        bot.send_message(msg.chat.id, "Ваш запрос уже на обработке -_-", reply_markup=kb)
        menu(msg, kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True))


def to_accept_design_two(msg):
    if not msg.photo:
        to_accept_design_one(msg)
        return
    photo_id = msg.photo[-1].file_id
    user = users.read("chat_id", msg.chat.id)
    user_id, name, last_name = user[1], user[2], user[3]
    kb_for_master = InlineKeyboardMarkup()
    kb_for_master.row(InlineKeyboardButton("✅ Одобрить", callback_data=f"одобрить_{user_id}"),
                      InlineKeyboardButton("❌ Отклонить", callback_data=f"отклонить_{user_id}"))
    caption = f"Дизайн от: {name} {last_name} | ID: {user_id}"
    id_msg_photo = bot.send_photo(USER_ID_MASTER, photo_id, caption=caption, parse_mode="HTML", reply_markup=kb_for_master)
    photo_date[id_msg_photo.message_id] = user_id
    bot.send_message(msg.chat.id, "✅ Дизайн отправлен мастеру на согласование. Ожидайте ответа.")
    accept.write([msg.chat.id], "accept")


def show_user_information(msg):
    chat_id, user_id, name, last_name, telephone, time = users.read("chat_id", msg.chat.id)
    text = (f"ID: {user_id}\nИмя: {name}\n"
            f"Фамилия: {last_name}\nТелефон: {telephone}\n"
            f"Дата регистрации: {datetime.datetime.fromtimestamp(time)}")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("сменить номер телефона")
    kb.row("изменить имя", "изменить фамилию")
    kb.row("удалить аккаунт")
    kb.row("меню")
    bot.send_message(msg.chat.id, text, reply_markup=kb)

def change_settings(msg):
    def change_name(text):
        def update_name(msg):
            chat_id, user_id, name, last_name, telephone, time = users.read("chat_id", msg.chat.id)
            name = msg.text.replace(" ", "").capitalize()
            users.write([chat_id, user_id, name, last_name, telephone, time], "users")
            show_user_information(msg)

        bot.send_message(msg.chat.id, text, reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, update_name)
    def change_last_name(text):
        def update_last_name(msg):
            chat_id, user_id, name, last_name, telephone, time = users.read("chat_id", msg.chat.id)
            last_name = msg.text.replace(" ", "").capitalize()
            users.write([chat_id, user_id, name, last_name, telephone, time], "users")
            show_user_information(msg)

        bot.send_message(msg.chat.id, text, reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, update_last_name)
    def change_telephone(text):
        def update_telephone(msg):
            chat_id, user_id, name, last_name, telephone, time = users.read("chat_id", msg.chat.id)
            telephone = msg.text.replace(" ", "")
            users.write([chat_id, user_id, name, last_name, telephone, time], "users")
            show_user_information(msg)

        bot.send_message(msg.chat.id, text, reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, update_telephone)

    def delete(text):
        def delete_profile(msg):
            if msg.text == "ПОДТВЕРДИТЬ":
                users.delete_row("chat_id", msg.chat.id)
                check_user(msg)

        bot.send_message(msg.chat.id, text, reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, delete_profile)
    prompts = {
        "изменить имя": "Введите новое имя",
        "изменить фамилию": "Введите новую фамилию",
        "сменить номер телефона": "Введите новый телефон(формат: +7)",
        "удалить аккаунт": "Вы уверены, что хотите удалить профиль? Введите ПОДТВЕРДИТЬ чтобы начать удаление профиля"
    }
    text = prompts[msg.text]
    settings = {
        "изменить имя" : change_name,
        "изменить фамилию" : change_last_name,
        "сменить номер телефона" : change_telephone,
        "удалить аккаунт" : delete
    }
    settings[msg.text](text)

def show_price(msg):
    pass

def register_step_one(msg):
    if msg.text.replace(" ", "").lower() == "да":
        date[msg.chat.id] = {}
        date[msg.chat.id]["user_id"] = msg.from_user.id
        kb = ReplyKeyboardRemove()
        bot.send_message(msg.chat.id, "Введите ваше имя", reply_markup=kb)
        bot.register_next_step_handler(msg, register_step_two)
    return
def register_step_two(msg):
    if msg.text:
        date[msg.chat.id]["name"] = msg.text.capitalize()
        bot.send_message(msg.chat.id, "Введите вашу фамилию")
        bot.register_next_step_handler(msg, register_step_thee)
    return
def register_step_thee(msg):
    if msg.text:
        date[msg.chat.id]["last_name"] = msg.text.capitalize()
        bot.send_message(msg.chat.id, "Введите ваш номер телефона(формат: +7)")
        bot.register_next_step_handler(msg, register_step_four)
    return
def register_step_four(msg, is_change : bool = False):
    if msg.text and msg.text[0] == "+":
        date[msg.chat.id]["telephone"] = msg.text
        users.write([msg.chat.id, date[msg.chat.id]["user_id"],
                     date[msg.chat.id]["name"], date[msg.chat.id]["last_name"],
                     date[msg.chat.id]["telephone"], datetime.datetime.now().timestamp()], "users")
        bot.send_message(msg.chat.id, "Вы успешно зарегистрированы!")
        menu(msg, kb = ReplyKeyboardMarkup(resize_keyboard=True), is_first=True)


bot.infinity_polling()
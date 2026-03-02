import s_taper
from s_taper.consts import *

def is_new_user(msg):
    all_users = users.read_all()
    for user in all_users:
        if user[1] == msg.from_user.id:
            return False
    return True

def write_to_logi(msg):
    logi.write([msg.chat.id, msg.from_user.id, msg.date, msg.text])


users_scheme = {
    "chat_id" : INT + KEY,
    "user_id" : INT,
    "name" : TEXT,
    "last_name" : TEXT,
    "tehephone" : TEXT,
    "date_registered" : INT,
}
users = s_taper.Taper("users", "users.db").create_table(users_scheme)

logi_cheme = {
    "chat_id": INT + KEY,
    "user_id": INT,
    "timestamp": INT,
    "text" : TEXT,
}
logi = users.create_table(logi_cheme, "logi")

accept_scheme = {
    "user_id": INT + KEY,
}
accept = users.create_table(accept_scheme, "accept")

date_write_scheme = {
    "chat_id": INT + KEY,
    "day" : TEXT,
    "time": TEXT,
}

writes = users.create_table(date_write_scheme, "writes")



import telebot
import sqlite3
from telebot import types
from dotenv import dotenv_values



def executeAll(request):
    connection = sqlite3.connect(config.get('DB_NAME'))
    cursor = connection.cursor()
    cursor.execute(request)
    data = cursor.fetchall()
    connection.close()
    return data

def executeOne(request):
    connection = sqlite3.connect(config.get('DB_NAME'))
    cursor = connection.cursor()
    cursor.execute(request)
    data = cursor.fetchone()
    connection.close()
    return data

config=dotenv_values('.env')
bot=telebot.TeleBot(config.get('TOKEN'))

#КОМАНДА СТАРТ
@bot.message_handler(commands=['start'])
def starter(message):
    connection = sqlite3.connect(config.get('DB_NAME'))
    cur = connection.cursor()

    uid = message.chat.id
    cur.execute(f"SELECT id FROM users WHERE id = {uid}")
    all = cur.fetchone()

    if all == None:
        us_id = message.chat.id
        balance = 100 
        cur.execute("INSERT INTO users (id, balance) VALUES(?, ?);", (us_id, balance))
        connection.commit()

    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('🛍⇒ Меню покупки . . .', callback_data='menu')
    button2 = types.InlineKeyboardButton('📔⇒ История покупок . . .', callback_data='history_items')
    button3 = types.InlineKeyboardButton('💸⇒ Связь с балансом . . .', callback_data='balancer')
    markup.row(button1, button2)
    markup.row(button3)
    bot.send_message(message.chat.id, f'<b>Здравствуй, {message.chat.first_name}.</b>\n\n<em>Тебя приветствует магазин "Огурчик". Переходи по кнопкам ниже, для работы с нашим ботом.</em>', reply_markup=markup, parse_mode = 'html')  


#КАТЕГОРИИ
@bot.callback_query_handler(func=lambda call: call.data == 'menu')
def menuer(call):
    connect = sqlite3.connect(config.get('DB_NAME'))
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM categories')
    d = cursor.fetchall()
    connect.close()
    
    markup = types.InlineKeyboardMarkup()

    for i in d:
        id, type = i
        markup.add(types.InlineKeyboardButton(type, callback_data=f'categories_{id}'))
        markup.add(types.InlineKeyboardButton('Обратно в меню', callback_data='back'))
    bot.send_message(call.message.chat.id, f'<b>Категории товаров, которые вы можете выбрать </b>', reply_markup=markup, parse_mode='html')

#ТОВАРЫ
@bot.callback_query_handler(func=lambda call: call.data.startswith('categories_'))
def callback_category(call):
       id_of_category = call.data.split('_')[1]  
       conn = sqlite3.connect(config.get('DB_NAME'))
       curochka = conn.cursor()

       curochka.execute(f'SELECT items.id, items.name FROM items INNER JOIN categories ON items.categories_id = categories.id WHERE categories.id = {id_of_category}')
       d = curochka.fetchall()
       conn.close()

       markup = types.InlineKeyboardMarkup()
       
       for i in d:
           id_of_item, name_of_item = i
           markup.add(types.InlineKeyboardButton(name_of_item, callback_data=f'items_{id_of_item}'))
       markup.add(types.InlineKeyboardButton('Обратно в меню', callback_data='back'))
       bot.send_message(call.message.chat.id,'Товары, которые вы можете купить:', reply_markup=markup)


#ВЫВОД ИНФОРМАЦИИ
@bot.callback_query_handler(func=lambda call: call.data.startswith('items_'))
def callback_item(call):
    connection = sqlite3.connect(config.get('DB_NAME'))
    curochka = connection.cursor()
    id_of_item = call.data.split('_')[1]   

    curochka.execute(f'SELECT name, price, desc FROM items WHERE id = {id_of_item}')
    data = curochka.fetchone()
    name_of_item, price_of_item, desk_of_item = data
    bot.send_message(call.message.chat.id,f'Название продукта: {name_of_item}\nДеньга, которую нужно заплатить: {price_of_item}\nЕго описание: {desk_of_item}')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Купить', callback_data=f'buy_{id_of_item}'))
    markup.add(types.InlineKeyboardButton('Обратно в меню', callback_data='back'))
    bot.send_message(call.message.chat.id, 'Для покупки нажмите кнопку ниже:', reply_markup=markup)


# ПОКУПКА
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def callback_buy(call):
    connection = sqlite3.connect(config.get('DB_NAME'))
    curochka = connection.cursor()
    uid = call.from_user.id
    item_id = call.data.split("_")[1]

    curochka.execute('SELECT name, price FROM items WHERE id = ?',(item_id,))
    data_of_item = curochka.fetchone()
    name_of_data, sum_str = data_of_item
    item_sum = int(sum_str)


    curochka.execute('SELECT balance FROM users WHERE id = ?',(uid,))
    users_balance = curochka.fetchone()[0]

    if users_balance >= item_sum:
        new_balance = users_balance - item_sum

        curochka.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, uid))

        curochka.execute('INSERT INTO bills (user_id, item_id,date) VALUES(?,?)', (uid, item_id))

        connection.commit()

        bot.send_message(call.message.chat.id, f'Покупка прошла успешно.\nВы приобрели продукт: {name_of_data} ')
    else:
        bot.send_message(call.message.chat.id, 'Недостаточно средств для покупки.')

        

#ОБРАТНО В МЕНЮШКУ
@bot.callback_query_handler(func=lambda call: call.data == 'back')
def backer(call):
    if call.data == 'back':
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton('🛍⇒ Меню покупки . . .', callback_data = 'menu')
        button2 = types.InlineKeyboardButton('📔⇒ История покупок . . .', callback_data = 'buy_history')
        button3 = types.InlineKeyboardButton('💸⇒ Связь с балансом . . .', callback_data = 'balancer')
        markup.row(button1, button2)
        markup.row(button3)
        bot.send_message(call.message.chat.id, f'<b>Здравствуй, {call.message.chat.first_name}.</b>\n\n<em>Тебя приветствует магазин "Огурчик". Переходи по кнопкам ниже, для работы с нашим ботом.</em>', reply_markup=markup, parse_mode = 'html')  

#ТЕКУЩИЙ БАЛАНС
@bot.callback_query_handler(func=lambda call: call.data == 'balancer')
def balancerr(call):
   if call.data == 'balancer':
        conn = sqlite3.connect(config.get('DB_NAME'))
        cursor = conn.cursor()
        uid = call.from_user.id

        cursor.execute(f'SELECT balance FROM users WHERE id = {uid}')
        itog = cursor.fetchone()

        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton('Пополнить баланс', callback_data='balancer_add')
        button2 = types.InlineKeyboardButton('Обратно в меню', callback_data='back')
        markup.row(button1)
        markup.row(button2)

        if itog:
            balance = itog[0]
            bot.send_message(call.message.chat.id, f'<b>Твой текущий баланс</b>: {balance}', reply_markup=markup, parse_mode='html')
        else:
            bot.send_message(call.message.chat.id, 'Пользователь не найден', reply_markup=markup)


#ЕГО ПОПОЛНЕНИЕ
@bot.callback_query_handler(func=lambda call: call.data == 'balancer_add')
def balancer_add(call):
   if call.data == 'balancer_add':
        connection = sqlite3.connect(config.get('DB_NAME'))
        cursor = connection.cursor()
        uid = call.from_user.id

        cursor.execute(f'SELECT balance FROM users WHERE id = {uid}')
        itog = cursor.fetchone()
        if itog:
            balance = itog[0]
            bot.send_message(call.message.chat.id, f'<b>Твой текущий баланс</b>: {balance}', parse_mode= 'html')
            bot.send_message(call.message.chat.id, '<b>Введи сумму для пополнения, на которую хочешь увеличить свой баланс:</b>', parse_mode = 'html')
            bot.register_next_step_handler(call.message, new_balancers)
        else:
            bot.send_message(call.message.chat.id, 'Пользователь не найден')

#сама функция пополнения
def new_balancers(message):

    try:
        counter = int(message.text)
        uid = message.from_user.id
        connection = sqlite3.connect(config.get('DB_NAME'))

        cursor = connection.cursor()
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton('Обратно в меню', callback_data='back')
        markup.add(button)

        cursor.execute(f'SELECT balance FROM users WHERE id = {uid}')
        itog = cursor.fetchone()
        if itog:
            balance = itog[0]
            if counter > 0 and counter <= 1000:
                nb = balance + counter
                cursor.execute(f'UPDATE users SET balance = {nb} WHERE id = {uid}')
                connection.commit()
                connection.close()
                bot.send_message(message.chat.id, f'<b>Теперь твой баланс:</b> {nb}', reply_markup=markup, parse_mode = 'html')
            elif counter < 0:
                bot.send_message(message.chat.id, '<b>Плохая новость:</b> вы до ужаса глупый человек, нельзя вводить сумму меньше 0', reply_markup=markup, parse_mode = 'html')
            else:
                bot.send_message(message.chat.id, '<b>Плохая новость</b>: вы безумно глупый человек, нельзя вводить сумму больше 1000', reply_markup=markup, parse_mode = 'html')
        else:
            connection.close()
            bot.send_message(message.chat.id, 'Пользователь не найден', reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, '<b>Мега супер плохая новость</b>: вы просто тупой человек, нельзя пополнять баланс не цифрами.', parse_mode = 'html')


#СПЕЦИАЛЬНО ДЛЯ ТУПЫХ ПОЛЬЗОВАТЕЛЕЙ
@bot.message_handler()
def yesli_user_durak(message):
    bot.send_message(message.chat.id, 'Че сказал? Я тебя не понимаю. На моем языке, пожалуйста.')

bot.polling(none_stop=True)
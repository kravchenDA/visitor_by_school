import telebot
import schedule
import time
import threading
import requests
import datetime

TOKEN = 'ENTER YOUR TOKEN'
bot = telebot.TeleBot(TOKEN)

# Хранилище для всех подписавшихся пользователей
subscribed_chats = set()
lock = threading.Lock()  # Для потокобезопасного доступа к коллекции

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    with lock:
        subscribed_chats.add(chat_id)
    bot.reply_to(
        message,
        "Вы подписались на ежедневные опросы!\n"
        "Они будут приходить в 6:00\n"
        "Отписаться: /stop"
    )

# Обработчик команды /stop
@bot.message_handler(commands=['stop'])
def handle_stop(message):
    chat_id = message.chat.id
    with lock:
        if chat_id in subscribed_chats:
            subscribed_chats.remove(chat_id)
    bot.reply_to(message, "Вы отписались от опросов")

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(10)

def send_scheduled_message():
    # Получаем текущий день недели
    current_weekday = datetime.now().weekday()

    # Проверяем, является ли день субботой (5) или воскресеньем (6)
    if current_weekday in [5,6]:
        print("Сегодня выходной, опрос не будет отправлен.")
        return

    # Копируем список chat_id для безопасного доступа
    with lock:
        target_chats = subscribed_chats.copy()

    if not target_chats:
        print("Нет активных подписчиков для отправки опроса")
        return

    QUESTION = 'Здравствуйте! Будете ли вы в школе? Если нет, укажите причину.'
    OPTIONS = ['да', 'По болезни (справка)', 'По заявлению родителей',
              'Освобождены по приказу директора (соревнования, олимпиады, конкурсы)',
              'Санаторное лечение', 'По неуважительной причине']

    url = f'https://api.telegram.org/bot{TOKEN}/sendPoll'

    for chat_id in target_chats:
        try:
            payload = {
                'chat_id': chat_id,
                'question': QUESTION,
                'options': OPTIONS,
                'is_anonymous': False
            }

            response = requests.post(url, json=payload)

            if response.status_code != 200:
                print(f"Ошибка при отправке опроса в {chat_id}: {response.text}")
            else:
                print(f"Опрос успешно отправлен в {chat_id}")

        except Exception as e:
            print(f"Ошибка при отправке в {chat_id}: {str(e)}")

# Настройка времени отправки
schedule.every().day.at("03:00").do(send_scheduled_message)# 6:00 по Минску

# Запускаем поток для проверки планировщика
threading.Thread(target=schedule_checker, daemon=True).start()

bot.polling(none_stop=True)

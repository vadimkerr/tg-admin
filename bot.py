import text
import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton,\
    ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import logging

# enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# dict for storing user data
# use database IRL
users = {}

NAME, NUMBER = range(2)


def start(bot, update):
    update.message.reply_text(text.START)
    return NAME


def name(bot, update):
    name = update.message.text
    users[update.message.chat_id] = {'name': name}

    logger.info('Name: %s' % name)

    keyboard = [
        [KeyboardButton('Отправить мой номер телефона', request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(text.ASK_PHONE, reply_markup=reply_markup)

    return NUMBER


def number_text(bot, update):
    number = update.message.text
    users[update.message.chat_id]['number'] = number

    logger.info('Number: %s' % number)
    update.message.reply_text(text.REQUEST_ACCEPTED, reply_markup=ReplyKeyboardRemove())

    request(bot, update.message.chat_id)

    return ConversationHandler.END


def number_contact(bot, update):
    number = update.message.contact.phone_number
    users[update.message.chat_id]['number'] = number

    logger.info('Number: %s' % number)
    update.message.reply_text(text.REQUEST_ACCEPTED)

    request(bot, update.message.chat_id)

    return ConversationHandler.END


def cancel(bot, update):
    logger.info('%s canceled conversation' % update.message.chat_id)
    update.message.reply_text(text.CANCEL)
    return ConversationHandler.END


def request(bot, id):
    name = users[id]['name']
    number = users[id]['number']

    keyboard = [
        [InlineKeyboardButton('Принять', callback_data='1'+str(id)),
         InlineKeyboardButton('Отклонить', callback_data='0'+str(id))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=config.ADMIN_ID, text=text.NEW_REQUEST % (name, number), reply_markup=reply_markup)


def button(bot, update):
    query = update.callback_query
    status = int(query.data[0])
    user_id = query.data[1:]

    logger.info('ID %s %s' % (user_id, status))

    bot.edit_message_text(text=query.message.text + '\n' + text.STATE[status],
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)

    # send response to user
    bot.send_message(chat_id=user_id, text=text.RESPONSE[status])


# use proxy since Telegram servers are not available in Russia
updater = Updater(token=config.API_TOKEN, request_kwargs=config.REQUEST_KWARGS)

dispatcher = updater.dispatcher

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        NAME: [MessageHandler(Filters.text, name)],
        NUMBER: [MessageHandler(Filters.text, number_text), MessageHandler(Filters.contact, number_contact)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

dispatcher.add_handler(conversation_handler)
updater.dispatcher.add_handler(CallbackQueryHandler(button))
updater.start_polling()
updater.idle()

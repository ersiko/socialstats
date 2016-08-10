import telepot
import telepot.helper
import json
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide
from telepot.delegate import per_chat_id, create_open

BOT_TOKEN= "230750512:AAF0ccxaXgs5JaTgh5M3AN5lumOOx1t260Y"

def settings():
    print("se ha ejecutado la funcion settings")
    
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(json.dumps(telepot.glance(msg),indent=4))
    print("HOLAAAAA")
    print('Chat Message:', content_type, chat_type, chat_id,msg)
    print(json.dumps(msg, indent=4))

    if content_type == 'text':
        if msg['text'] == '/start':
            bot.sendMessage(chat_id, "Bienvenido a InstagramStats! Este bot te permite recibir las estadísticas de usuarios de Instagram (en principio las de tu propio usuario, pero puedes suscribirte a cualquier perfil que sea público). \n\n¿Quieres empezar ahora suscribiéndote a un usuario?",
                                      reply_markup=ReplyKeyboardMarkup( keyboard=[
                                            [KeyboardButton(text="Sí! quiero suscribirme!")], [KeyboardButton(text="No, gracias, no me interesa")]
                                        ], one_time_keyboard=True))
 #       if msg['text'] == '/keyout':
 #           bot.sendMessage(chat_id, 'escondiendo', reply_markup=hide_keyboard)
        elif msg['text'] == "No, gracias, no me interesa":
            bot.sendMessage(chat_id, "¿Entonces para que me despiertas? 🙄 \nEs broma, no hay ningún problema 😊 Si en algún momento cambias de opinión, vuelve a usar el comando /start. Un saludo!",reply_markup=ReplyKeyboardHide())
        elif msg['text'] == "Sí! quiero suscribirme!":
#            bot = telepot.DelegatorBot(BOT_TOKEN, [(per_chat_id(types=['private']), create_open(settings, timeout=10)),])
            create_open(settings, timeout=10)
            bot.sendMessage(chat_id, "Bien! ¿A qué usuario de instagram quieres seguir?",reply_markup=ReplyKeyboardHide())
    
            
bot = telepot.Bot(BOT_TOKEN)
print('Listening ...')
bot.message_loop({'chat': on_chat_message}, run_forever=True)

import configparser
import os
import sys
import telepot
import json
import elasticsearch
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide, ForceReply
from telepot.delegate import per_chat_id, create_open

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)

BOT_TOKEN = config.get('telegram','BOT_TOKEN')
es = elasticsearch.Elasticsearch()

class InstagramStatsBot(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(InstagramStatsBot, self).__init__(seed_tuple, timeout)
        
    def user_subscription(self, iguser):
        self.sender.sendMessage('suscribiendo ...' + iguser)
        if es.exists(index="igusers", doc_type="users", id=iguser):
            print("Y ahora vas y lo cascas")
        else:
            print("hay que darlo de alta")

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print("HOLAAAAA")
#        print(json.dumps(telepot.glance(msg),indent=4))
#        print('Chat Message:', content_type, chat_type, chat_id,msg)
        print(json.dumps(msg, indent=4))
        if content_type == 'text':
            try:
                reply=msg['reply_to_message']
                is_reply = True
            except KeyError:
                is_reply = False

            if is_reply == True:
                if msg['reply_to_message']['text'] == "¿A qué usuario de instagram quieres seguir?":
                    self.sender.sendMessage("Confirmas que este el usuario al que quieres seguir? https://www.instagram.com/" + msg['text'], reply_markup=ReplyKeyboardMarkup( keyboard=[
                                            [KeyboardButton(text="Sí, quiero seguir a "+ msg['text']), KeyboardButton(text="No, me he equivocado de usuario")],
                                            [KeyboardButton(text="Ya no quiero seguir a nadie. Cancelar")]
                                        ], one_time_keyboard=True))
            elif msg['text'] == '/start':
                self.sender.sendMessage("Bienvenido a InstagramStats! Este bot te permite recibir las estadísticas de usuarios de Instagram (en principio las de tu propio usuario, pero puedes suscribirte a cualquier perfil que sea público). \n\n¿Quieres empezar ahora suscribiéndote a un usuario?",
                                      reply_markup=ReplyKeyboardMarkup( keyboard=[
                                            [KeyboardButton(text="Sí! quiero suscribirme!")], [KeyboardButton(text="No, gracias, no me interesa")]
                                        ], one_time_keyboard=True))
 #       if msg['text'] == '/keyout':
 #           bot.sendMessage(chat_id, 'escondiendo', reply_markup=hide_keyboard)
            elif msg['text'] == "No, gracias, no me interesa":
                self.sender.sendMessage("¿Entonces para que me despiertas? 🙄 \nEs broma, no hay ningún problema 😊 Si en algún momento cambias de opinión, vuelve a usar el comando /start. Un saludo!",reply_markup=ReplyKeyboardHide())
            elif msg['text'] == "Sí! quiero suscribirme!":
                self.sender.sendMessage("¡Bien!")
                self.sender.sendMessage("¿A qué usuario de instagram quieres seguir?",reply_markup=ForceReply())
            elif msg['text'] == "No, me he equivocado de usuario":
                self.sender.sendMessage("Hay taaaantos usuarios en instagram... A ver, vuelve a intentarlo.")
                self.sender.sendMessage("¿A qué usuario de instagram quieres seguir?",reply_markup=ForceReply())
            elif msg['text'] == "Ya no quiero seguir a nadie. Cancelar":
                self.sender.sendMessage("¡Si que cambias de opinión rápido! 😁 Ok, cancelando...",reply_markup=ReplyKeyboardHide())
            elif msg['text'].rsplit(' ',1)[0] == "Sí, quiero seguir a":
                iguser = msg['text'].split()[-1]
                self.sender.sendMessage("Ok, aún no sirve de nada, pero cuando siga programando te suscribiré a " + iguser)
                self.user_subscription(iguser)
            elif msg['text'].split()[0] == "/subscribe":
                if len(msg['text'].split()) == 1:
                    self.sender.sendMessage("¿A qué usuario de instagram quieres seguir?",reply_markup=ForceReply())
                else:
                    self.sender.sendMessage("Confirmas que este el usuario al que quieres seguir? https://www.instagram.com/" + msg['text'].split()[1], 
                                             reply_markup=ReplyKeyboardMarkup( keyboard=[
                                                  [KeyboardButton(text="Sí, quiero seguir a "+ msg['text'].split()[1]), KeyboardButton(text="No, me he equivocado de usuario")],
                                                  [KeyboardButton(text="Ya no quiero seguir a nadie. Cancelar")]
                                                                             ], one_time_keyboard=True))
    def on_close(self, exception):
        if isinstance(exception, telepot.exception.WaitTooLong):
            self.sender.sendMessage('A la mierda',reply_markup=ReplyKeyboardHide())

    
bot = telepot.DelegatorBot(BOT_TOKEN, [
    (per_chat_id(), create_open(InstagramStatsBot, timeout=15)),
])

bot.message_loop(run_forever='Listening ...')

import configparser
import os
import sys
import telepot
import json
import elasticsearch
import igscrape
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide, ForceReply
from telepot.delegate import per_chat_id, create_open

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)

BOT_TOKEN = config.get('telegram','BOT_TOKEN')
es = elasticsearch.Elasticsearch(['10.8.0.1'])

class InstagramStatsBot(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(InstagramStatsBot, self).__init__(seed_tuple, timeout)
        
    def user_subscription(self, iguser, telegram_id):
        self.sender.sendMessage('suscribiendo ... iguser' + iguser + " y tgid " + str(telegram_id)) 
        self.add_iguser(iguser)

        if es.exists(index="ourusers", doc_type="users", id=telegram_id):
            try:
                subscribed_to = es.get(index="ourusers", doc_type="users", id=telegram_id, fields='subscribed_to')['fields']['subscribed_to']
            except KeyError:
                subscribed_to = []

        if iguser not in subscribed_to:
            subscribed_to.append(iguser)
            res = es.update(index="ourusers", doc_type="users", id=telegram_id, body={'doc' :{'subscribed_to': subscribed_to}})
            print(str(res))
        else:
            self.sender.sendMessage('Ya estás suscrito a ' + iguser)

    def user_creation(self,msg):
        res = es.index(index="ourusers", doc_type="users", id=msg['id'], body={'username': msg['username'], 'first_name': msg['first_name'], 'subscribed_to': [] })
        print(res['created'])

    def add_iguser(self,iguser):
        if not es.exists(index="igusers", doc_type="users", id=iguser):
            iguser_data, max_id = igscrape.get_iguser_data(iguser)
            if iguser_data['entry_data']['ProfilePage'][0]['user']['is_private'] == True:
                print("This account is private, I have no access to its data")
            res = es.index(index="igusers", doc_type='users', id=iguser, body={'private': iguser_data['entry_data']['ProfilePage'][0]['user']['is_private']})
            print(res['created'])
            
        #print(json.dumps(data))
        #print(max_id)

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
                print("hola")
                if es.exists(index="ourusers", doc_type="users", id=msg['from']['id']):
                    message = "Tu usuario ya existe en InstagramStatsBot! Si vuelves a iniciar el proceso 'start' recrearás tu usuario, borrando los datos existentes... ¿Estás seguro que quieres suscribirte de nuevo?"
                else:
                    message = "Bienvenido a InstagramStatsBot! Este bot te permite recibir las estadísticas de usuarios de Instagram (en principio las de tu propio usuario, pero puedes suscribirte a cualquier perfil que sea público). \n\n¿Quieres empezar ahora suscribiéndote a un usuario?"
                self.sender.sendMessage(message, reply_markup=ReplyKeyboardMarkup( keyboard=[
                                       [KeyboardButton(text="Sí! quiero suscribirme!")], [KeyboardButton(text="No, gracias, no me interesa")]
                                        ], one_time_keyboard=True))
 #       if msg['text'] == '/keyout':
 #           bot.sendMessage(chat_id, 'escondiendo', reply_markup=hide_keyboard)
            elif msg['text'] == "No, gracias, no me interesa":
                self.sender.sendMessage("¿Entonces para que me despiertas? 🙄 \nEs broma, no hay ningún problema 😊 Si en algún momento cambias de opinión, vuelve a usar el comando /start. Un saludo!",reply_markup=ReplyKeyboardHide())
            elif msg['text'] == "Sí! quiero suscribirme!":
                self.user_creation(msg['from'])
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
                self.user_subscription(iguser, msg['from']['id'])
            elif msg['text'].split()[0] == "/subscribe":
                if len(msg['text'].split()) == 1:
                    self.sender.sendMessage("¿A qué usuario de instagram quieres seguir?",reply_markup=ForceReply())
                else:
                    self.sender.sendMessage("Confirmas que este el usuario al que quieres seguir? https://www.instagram.com/" + msg['text'].split()[1], 
                                             reply_markup=ReplyKeyboardMarkup( keyboard=[
                                                  [KeyboardButton(text="Sí, quiero seguir a "+ msg['text'].split()[1]), KeyboardButton(text="No, me he equivocado de usuario")],
                                                  [KeyboardButton(text="Ya no quiero seguir a nadie. Cancelar")]
                                                                             ], one_time_keyboard=True))
            elif msg['text'] == '/settings':
                res = es.get(index="ourusers", doc_type="users", id=msg['from']['id'])
                self.sender.sendMessage("Lo que se de ti es " + str(res['_source']))

    def on_close(self, exception):
        if isinstance(exception, telepot.exception.WaitTooLong):
            self.sender.sendMessage('Me ignoras? A la mierda',reply_markup=ReplyKeyboardHide())

    
bot = telepot.DelegatorBot(BOT_TOKEN, [
    (per_chat_id(), create_open(InstagramStatsBot, timeout=15)),
])

bot.message_loop(run_forever='Listening ...')

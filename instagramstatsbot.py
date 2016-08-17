import configparser
import os
import sys
import telepot
import json
import elasticsearch
import igscrape
import datetime
import requests
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide, ForceReply
from telepot.delegate import per_chat_id, create_open

config = configparser.ConfigParser()
scriptdir= os.path.dirname(sys.argv[0])
if scriptdir == "":
    scriptdir = os.getcwd()
conffile = scriptdir + '/socialstats.config'
config.read(conffile)
es_server = config.get('elasticsearch','server')

es = elasticsearch.Elasticsearch([es_server])

BOT_TOKEN = config.get('telegram','BOT_TOKEN')

valid_chars = '-_. abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

class InstagramStatsBot(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(InstagramStatsBot, self).__init__(seed_tuple, timeout)
    
    def sanitize(self,string):
        return ''.join(c for c in string if c in valid_chars)
    def show_current_settings(self, id):
        res = es.get(index="ourusers", doc_type="users", id=id)
        message = "Lo que se de ti es:\n"
        message = message + "Te llamas " + res['_source']['first_name'] + "\n"
        message = message + "Tu nombre en Telegram es " + res['_source']['username'] + "\n"
        message = message + "Estas suscrito a "+ str(len(res['_source']['subscribed_to'])) +" usuarios: "
        for subscription in res['_source']['subscribed_to']:
            message = message + subscription + " "
        message = message + "\n"
        self.sender.sendMessage(message)
        #self.show_current_regularity(id)
        self.show_last_notified(id)

    def show_last_notified(self, id):
        res = es.get(index="ourusers", doc_type="last_updated", id=id)
        message = "La última vez que recibiste un mensaje fue:\n"
        for regularity in ['1','3','7','30','90','180','365']:
            timestamp = int(res['_source']['date'+regularity])/1000
            last_updated = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            days_ago = datetime.datetime.now() - datetime.datetime.fromtimestamp(timestamp)
            message = message + "El mensaje de los " + regularity + " dias lo recibiste hace " + str(days_ago.days) + " días, el " + last_updated + "\n"
        self.sender.sendMessage(message)

    def show_current_regularity(self, id):
        res = es.get(index="ourusers", doc_type="users", id=id)
        message = "Frecuencia de los mensajes. Vas a recibir mensajes:\n"
        for regularity in [1,3,7,30,90,180,365]:
            message = message + "Cada " + str(regularity) + " días: "
            if res['_source'][str(regularity)]:
                message = message + "si\n"
            else:
                message = message + "no\n"
        self.sender.sendMessage(message)

    def show_regularity_toggle_keyboard(self):
        self.sender.sendMessage("Hay alguno de estos valores que quieras cambiar?", reply_markup=ReplyKeyboardMarkup( keyboard=[
                             [KeyboardButton(text="1"), KeyboardButton(text="3"),KeyboardButton(text="7"),KeyboardButton(text="30")],
                             [KeyboardButton(text="90"), KeyboardButton(text="180"),KeyboardButton(text="365")],
                             [KeyboardButton(text="No quiero cambiar ninguno, están todos bien")]
                                       ], one_time_keyboard=True))

    def set_regularity(self, id):
        self.show_current_regularity(id)
        self.show_regularity_toggle_keyboard()

    def change_regularity(self, regularity, id):
        res = es.get(index="ourusers", doc_type="users", id=id)
        if res['_source'][str(regularity)]:
            message = "Deshabilitando mensajes cada " + str(regularity) + " días"
            res['_source'][str(regularity)] = False
        else:
            message = "Habilitando mensajes cada " + str(regularity) + " días"
            res['_source'][str(regularity)] = True
        es.index(index="ourusers", doc_type="users", id=id, body=res['_source'])
        self.sender.sendMessage(message)
        self.show_current_regularity(id)
        self.show_regularity_toggle_keyboard()

    def user_subscription(self, iguser, telegram_id):
        #self.sender.sendMessage('suscribiendo ... iguser' + iguser + " y tgid " + str(telegram_id)) 
        self.add_iguser(iguser)

        if es.exists(index="ourusers", doc_type="users", id=telegram_id):
            try:
                subscribed_to = es.get(index="ourusers", doc_type="users", id=telegram_id, fields='subscribed_to')['fields']['subscribed_to']
            except KeyError:
                subscribed_to = []

        if iguser not in subscribed_to:
            subscribed_to.append(iguser)
            res = es.update(index="ourusers", doc_type="users", id=telegram_id, body={'doc' :{'subscribed_to': subscribed_to}})
            self.sender.sendMessage('Ok, ahora recibirás estadísticas del usuario ' + iguser)
        else:
            self.sender.sendMessage('Ya estás suscrito a ' + iguser)

    def user_creation(self,msg):
        res = es.index(index="ourusers", doc_type="users", id=msg['id'], body={'username': msg['username'], 'first_name': msg['first_name'], 'subscribed_to': [], '1': True, '3': False, '7': True, '30': True, '90': True, '180': True, '365': True })
        print(res['created'])
        now_epoch = datetime.datetime.now().strftime("%s")+"000"
        res = es.index(index="ourusers", doc_type="last_updated", id=msg['id'], body={'date1': now_epoch, 'date3': now_epoch, 'date7': now_epoch, 'date30': now_epoch, 'date90': now_epoch, 'date180': now_epoch, 'date365': now_epoch})
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
    def show_subscribe_dialog(self, msg):
        if msg['text'].split()[0] == "/subscribe" and len(msg['text'].split()) == 1:
                self.sender.sendMessage("¿A qué usuario de instagram quieres seguir?",reply_markup=ForceReply())
        else:
            if msg['text'].split()[0] == "/subscribe":
                user_to_subscribe = msg['text'].split()[1].lower()
            else:
                user_to_subscribe = msg['text'].split()[0].lower()
            user_to_subscribe = self.sanitize(user_to_subscribe)
            req = requests.get("https://www.instagram.com/" + user_to_subscribe + "/")
            if req.status_code == 200:
                self.sender.sendMessage("¿Confirmas que éste es el usuario al que quieres seguir? https://www.instagram.com/" + user_to_subscribe, 
                                             reply_markup=ReplyKeyboardMarkup( keyboard=[
                                                  [KeyboardButton(text="Sí, quiero seguir a "+ user_to_subscribe), KeyboardButton(text="No, me he equivocado de usuario")],
                                                  [KeyboardButton(text="Ya no quiero seguir a nadie. Cancelar")]
                                             ], one_time_keyboard=True))
            else:
                self.sender.sendMessage("Dice instagram que el usuario "+ user_to_subscribe + " no existe... Vuelve a intentarlo.")
                self.sender.sendMessage("¿A qué usuario de instagram quieres seguir?",reply_markup=ForceReply())

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
#        print("HOLAAAAA")
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
                    self.show_subscribe_dialog(msg)

            elif msg['text'] == '/start':
                print("hola")
                if es.exists(index="ourusers", doc_type="users", id=msg['from']['id']):
                    message = "¡Tu usuario ya existe en InstagramStatsBot! Si vuelves a iniciar el proceso 'start' recrearás tu usuario, borrando los datos existentes... ¿Estás seguro que quieres suscribirte de nuevo?"
                else:
                    message = "¡Bienvenido a InstagramStatsBot! Este bot te permite recibir las estadísticas de usuarios de Instagram (en principio las de tu propio usuario, pero puedes suscribirte a cualquier perfil que sea público). \n\n¿Quieres empezar ahora suscribiéndote a un usuario?"
                self.sender.sendMessage(message, reply_markup=ReplyKeyboardMarkup( keyboard=[
                                       [KeyboardButton(text="Sí! quiero suscribirme!")], [KeyboardButton(text="No, gracias, no me interesa")]
                                        ], one_time_keyboard=True))

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
                user_to_subscribe = self.sanitize(msg['text'].split()[-1].lower())
                self.user_subscription(user_to_subscribe, msg['from']['id'])

            elif msg['text'].split()[0] == "/subscribe":
                self.show_subscribe_dialog(msg)

            elif msg['text'] == '/settingsraw':
                res = es.get(index="ourusers", doc_type="users", id=msg['from']['id'])
                res2 = es.get(index="ourusers", doc_type="last_updated", id=msg['from']['id'])
                self.sender.sendMessage("Lo que se de ti es " + str(res['_source']) + str (res2['_source']))

            elif msg['text'] == '/settings':
                self.show_current_settings(msg['from']['id'])   

            elif msg['text'] in ['1','3','7','30','90','180','365']:
                #self.sender.sendMessage("Cambiando la config de " + msg['text'] + " días.")
                self.change_regularity(msg['text'], msg['from']['id'])

            elif msg['text'] == "No quiero cambiar ninguno, están todos bien":
                self.sender.sendMessage("Perfecto! Gracias 😊",reply_markup=ReplyKeyboardHide())

            elif msg['text'] == '/reg':
                self.show_last_notified(msg['from']['id'])

    def on_close(self, exception):
        pass
#        if isinstance(exception, telepot.exception.WaitTooLong):
#            self.sender.sendMessage('Me ignoras? A la mierda',reply_markup=ReplyKeyboardHide())

    
bot = telepot.DelegatorBot(BOT_TOKEN, [
    (per_chat_id(), create_open(InstagramStatsBot, timeout=15)),
])

bot.message_loop(run_forever='Listening ...')
 
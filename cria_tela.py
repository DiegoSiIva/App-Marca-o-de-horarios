import pyrebase
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel

KV = '''
ScreenManager:
    id: screen_manager
    Laboratorios:
        name: 'laboratorios'
        id: laboratorios

<Laboratorios>:
    MDBoxLayout:
        id: box_lab
        md_bg_color: 0.9607843137254902, 0.9607843137254902, 0.9607843137254902, 1
        orientation: 'vertical'
        MDTopAppBar:
            id: bar_lab
            specific_text_color: 0, 0, 0, 1
            md_bg_color: 1, 1, 1, 1
            pos_hint: {'top': 1}
            left_action_items: [['arrow-left', lambda x: app.switch_to_screen('home')]]
            right_action_items: [["account-circle-outline", lambda x: app.callback(x)]]
            elevation: .5
        MDLabel:
            text: 'ola'
            halign: 'center'

'''


firebaseConfig = {
  'apiKey': "AIzaSyBOQEPKqHnu5RToZhTQotrMMpoCbI7aD2w",
  'authDomain': "fainor-labs.firebaseapp.com",  'databaseURL': "https://fainor-labs-default-rtdb.firebaseio.com",
  'projectId': "fainor-labs",
  'storageBucket': "fainor-labs.appspot.com",
  'messagingSenderId': "505890873860",
  'appId': "1:505890873860:web:816b9fe743a2da7b4d8b51",
  'measurementId': "G-D547PSQZ7F"
}
firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()
auth = firebase.auth()

usuario = 'diegosilvardias71@gmail.com'
senha = 'D08052000'
user = auth.sign_in_with_email_and_password(usuario, senha)
user_token = user['idToken']
requisicoes = db.get(user_token)
dados = requisicoes.val()


class Laboratorios(Screen):
    def on_enter(self):
        lab_text = {}
        comp_text = ''
        equip_text = ''
        for lab, laboratorios in dados['Laboratórios'].items():
            if 'Computadores' in laboratorios:
                comp_text += 'Computadores:\n'
                comp_text += '  Hardware:\n'
                for computadores in dados['Laboratórios'][lab]['Computadores'].items():
                    comp_text += f'    {computadores[0]}: {computadores[1]}\n'
                comp_text += '  Programas:\n'
                for programas in dados['Laboratórios'][lab]['Programas'].items():
                    comp_text += f'    {programas[1]}\n'
            else:
                equip_text += 'Equipamentos:\n'
                for equipamentos in dados['Laboratórios'][lab]['Equipamentos'].items():
                    equip_text += f'  {equipamentos[1]}\n'

        print(equip_text)
        print(comp_text)


class MyApp(MDApp):
    def build(self):
        screen = Builder.load_string(KV)
        return screen


MyApp().run()

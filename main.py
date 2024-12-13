from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.list import OneLineAvatarIconListItem, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.tab import MDTabsBase
from Functions import on_tab_switch, autenticacao_login, menu_user, on_checkbox_active, on_button_press, callback, \
    menu_labs, menu_mes, menu_prog, callback_menus, update_tabs_for_month, \
    bem_vindo, del_horarios_marcados, on_button_press1, post_horarios, menu_laboratorio


class ListItemWithCheckbox(OneLineAvatarIconListItem):
    '''Custom list item.'''
    def on_checkbox_active(self, listitem, checkbox, value):
        app = MDApp.get_running_app()
        on_checkbox_active(listitem, checkbox, value, app)


class RightCheckbox(IRightBodyTouch, MDCheckbox):
    '''Custom right container.'''


class Login(Screen):
    def autenticacao(self):
        autenticacao_login(self)


class Home(Screen):
    def on_enter(self):
        post_horarios()
        bem_vindo(self)


class Escolha(Screen):
    pass


class Tab(MDFloatLayout, MDTabsBase):
    def on_button_press(self):
        app = MDApp.get_running_app()
        on_button_press(app)


class Agende(Screen):

    def on_enter(self, tab=Tab):
        from Functions import on_enter
        on_enter(self)

    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        list_class = ListItemWithCheckbox
        app = MDApp.get_running_app()
        app.current_tab = tab_text
        on_tab_switch(self, list_class, instance_tabs, instance_tab, instance_tab_label, tab_text)

    def on_leave(self):
        from Functions import on_stop
        on_stop(self)

    def start_second_thread(self):
        from Functions import start_second_thread
        start_second_thread(self)

    def load_data(self, lista=ListItemWithCheckbox):
        from Functions import load_data
        load_data(self, lista)


class Meus_horarios(Screen):
    def on_enter(self):
        from Functions import on_enter1
        on_enter1(self)

    def on_leave(self):
        from Functions import on_stop1
        on_stop1(self)

    def start_second_thread1(self):
        from Functions import start_second_thread1
        start_second_thread1(self)

    def marcados_data(self):
        from Functions import marcados_data
        marcados_data(self)

    def on_button_press1(self):
        on_button_press1(self)


class Laboratorios(Screen):
    def laboratorios_info(self):
        from Functions import laboratorios_info
        laboratorios_info(self)


class MyApp(MDApp):
    current_tab = StringProperty('')
    usuario = StringProperty('')

    def build(self):
        screen = Builder.load_file('Telas.kv')
        menu_nomes = ['Minha conta', 'Sair']
        menu_icon = ["account-outline", "exit-to-app"]
        menu_user(self, menu_nomes, menu_icon, 160)
        menu_mes(self)
        menu_labs(self)
        menu_prog(self)
        menu_laboratorio(self)
        return screen

    def on_start(self):
        # post_horarios()
        del_horarios_marcados()

    def callback(self, button):
        callback(self, button)

    def callback_labs(self, button):
        menu = self.menu_labs
        callback_menus(menu, button)

    def callback_mes(self, button):
        menu = self.menu_mes
        callback_menus(menu, button)

    def callback_prog(self, button):
        menu = self.menu_prog
        callback_menus(menu, button)

    def callback_laboratorio(self, button):
        menu = self.menu_laboratorio
        callback_menus(menu, button)

    def Avançar(self, tab=Tab):
        agende = self.root.get_screen('agende')
        escolha = self.root.get_screen('escolha')
        update_tabs_for_month(self, agende, escolha, tab)

    def switch_to_screen(self, screen_name):
        self.root.current = screen_name


MyApp().run()

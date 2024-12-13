import datetime
import threading
import time
import pyrebase

import calendar

from kivy.clock import mainthread
from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu

firebaseConfig = {
  'apiKey': "",
  'authDomain': "",
  'databaseURL': "",
  'projectId': "",
  'storageBucket': "",
  'messagingSenderId': "",
  'appId': "",
  'measurementId': ""
}
firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()
auth = firebase.auth()
#auth.create_user_with_email_and_password('email', 'senha') cadastra um usuario
#user = auth.sign_in_with_email_and_password('email', 'senha') autentica um usuario
#auth.send_password_reset_email('email') envia um email de recuperação de senha

data_atual = datetime.date.today()
autenticacao = False
user_token = ''
ocupados = {}
dados = {}
user_id = ''
lab_text = ''
mes_text = ''
prog_text = ''
lab_escolha = ''
mes_num = 1


def autenticacao_login(screen):
    global autenticacao, user_token, user_id, dados
    usuario = screen.ids.user.text
    senha = screen.ids.password.text

    try:
        # Autentica o usuário com o Firebase
        user = auth.sign_in_with_email_and_password(usuario, senha)
        autenticacao = True
        user_email = user['email']
        user_token = user['idToken']
        user_id = user['localId']
        screen.ids.password.helper_text = ''
        screen.ids.user.text = ''
        screen.ids.password.text = ''
        screen.manager.current = 'home'
        requisicoes = db.get(user_token)
        dados = requisicoes.val()
    except Exception as e:
        print('Erro', e)
        error_message = str(e)
        if 'EMAIL_NOT_FOUND' in error_message or 'INVALID_EMAIL' in error_message:
            mensagem = 'Usuário não existe!'
            set_error_wrong(screen, screen.ids.user, mensagem)
        elif 'INVALID_PASSWORD' in error_message:
            mensagem = 'Senha Incorreta!'
            set_error_wrong(screen, screen.ids.password, mensagem)
        elif 'EMAIL_NOT_VERIFIED' in error_message:
            mensagem = 'Email não verificado!'
            set_error_wrong(screen, screen.ids.user, mensagem)
        else:
            mensagem = 'Erro desconhecido!'
            set_error_wrong(screen, screen.ids.user, mensagem)

        screen.ids.user.bind(
            on_text_validate=lambda instance: set_error_wrong(screen, screen.ids.user, mensagem),
            on_focus=lambda instance, value: set_error_wrong(screen, screen.ids.user, mensagem)
        )


stop = threading.Event()


def stop_data_thread():
    stop.set()


def on_stop(screen):
    global ocupados
    stop_data_thread()
    ocupados = {}
    # Aguarda a thread terminar
    if hasattr(screen, 'data_thread'):
        screen.data_thread.join()


def on_enter(screen):
    stop.clear()
    screen.start_second_thread()


def start_second_thread(screen):
    threading.Thread(target=screen.load_data).start()


def load_data(screen, list_class):
    global db, user_token, dados
    while not stop.is_set():
        time.sleep(2)
        if autenticacao:
            try:

                requisicoes = db.child('Horarios_marcados').get(user_token)
                new_data = requisicoes.val()
                if new_data != dados['Horarios_marcados']:
                    dados['Horarios_marcados'] = new_data
                    update_tabs(screen, list_class)
            except Exception as e:
                print(f"Erro ao buscar dados: {e}")
        else:
            print("Usuário não autenticado. Faça o login primeiro.")


def update_tabs_for_month(app, agende, escolha, tab_class):
    global mes_num
    tabs = agende.ids.tabs
    laboratorio = escolha.ids.escolha_lab.text
    mes = escolha.ids.escolha_mes
    tabs_list = tabs.get_tab_list()

    if laboratorio != '':
        escolha.ids.escolha_lab.helper_text = ''
        if mes_num != 1:
            escolha.ids.escolha_mes.helper_text = ''
            escolha.ids.escolha_mes.text = ''
            escolha.ids.escolha_prog.text = ''
            escolha.ids.escolha_lab.text = ''
            if len(tabs_list) == 0:
                for dia in dados['Horarios'][mes_text]:
                    tab = tab_class(title=dia)
                    tabs.add_widget(tab)
                    app.switch_to_screen('agende')
            elif len(tabs_list) > 0:
                for tab in tabs_list:
                    tabs.remove_widget(tab)
                for dia in dados['Horarios'][mes_text]:
                    tab = tab_class(title=dia)
                    tabs.add_widget(tab)
                    app.switch_to_screen('agende')
        else:
            set_error_empty(escolha, escolha.ids.escolha_mes)
            escolha.ids.escolha_mes.bind(
                on_text_validate=lambda instance: set_error_empty(escolha, escolha.ids.escolha_mes),
                on_focus=lambda instance, value: set_error_empty(escolha, escolha.ids.escolha_mes))
    else:
        set_error_empty(escolha, escolha.ids.escolha_lab)
        escolha.ids.escolha_lab.bind(
            on_text_validate=lambda instance: set_error_empty(escolha, escolha.ids.escolha_lab),
            on_focus=lambda instance, value: set_error_empty(escolha, escolha.ids.escolha_lab))


def on_tab_switch(screen, list_class, instance_tabs, instance_tab, instance_tab_label, tab_text):
    '''Called when switching tabs.

    :type instance_tabs: <kivymd.uix.tab.MDTabs object>;
    :param instance_tab: <__main__.Tab object>;
    :param instance_tab_label: <kivymd.uix.tab.MDTabsLabel object>;
    :param tab_text: text or name icon of tab;
    '''
    global dados
    global mes_text, lab_text, user_id

    # Atualiza o texto do rótulo do mês
    mes_label = screen.ids.mes
    mes_label.text = mes_text

    # Limpa os widgets da aba atual
    tab_content = instance_tab.ids.horario
    tab_content.clear_widgets()

    # Obtém os horários disponíveis
    if mes_text not in dados['Horarios']:
        print(f"Horários para o mês {mes_text} não encontrados.")
        return

    # Cópia dos horários para evitar modificações no original
    horarios_view = dados['Horarios'][mes_text].copy()
    dia = tab_text  # Dia da aba atual

    # Inicializa a visualização dos horários para o dia atual
    horarios_dia_view = horarios_view[dia].copy()

    # Se houver horários marcados para o lab_text, atualiza os horários disponíveis
    if 'Horarios_marcados' in dados and user_id in dados['Horarios_marcados']:
        if lab_text in dados['Horarios_marcados'][user_id] and mes_text in dados['Horarios_marcados'][user_id][lab_text]:
            marcados = dados['Horarios_marcados'][user_id][lab_text][mes_text]
            if dia in marcados:
                for horario, status in marcados[dia].items():
                    if horario in horarios_dia_view:
                        horarios_dia_view[horario] = status

    # Exibe os horários livres na aba atual
    for horario_view, status_view in horarios_dia_view.items():
        if status_view == 'Livre':
            list_item = list_class(text=f"{horario_view}")  # Use OneLineListItem ou outra classe de item de lista
            tab_content.add_widget(list_item)

@mainthread
def update_tabs(screen, list_class):
    global mes_text, user_id, lab_text
    instance_tabs = screen.ids.tabs
    current_tab = instance_tabs.get_current_tab()  # Use get_current_tab()
    if not current_tab:
        print("Nenhuma aba selecionada ou tabs não inicializadas ainda.")
        return

    dia = current_tab.title
    tab_content = current_tab.ids.horario
    tab_content.clear_widgets()

    if mes_text not in dados['Horarios']:
        print(f"Horários para o mês {mes_text} não encontrados.")
        return

    # Cópia dos horários para evitar modificações no original
    horarios_view = dados['Horarios'][mes_text].copy()
    horarios_dia_view = horarios_view.get(dia, {}).copy()

    if 'Horarios_marcados' in dados and user_id in dados['Horarios_marcados']:
        marcados = dados['Horarios_marcados'][user_id].get(lab_text, {}).get(mes_text, {})
        # Se houver horários marcados para o dia específico, atualiza os horários disponíveis
        if dia in marcados:
            for horario, status in marcados[dia].items():
                if horario in horarios_dia_view:
                    horarios_dia_view[horario] = status

    # Exibe os horários livres na aba atual
    for horario_view, status_view in horarios_dia_view.items():
        if status_view == 'Livre':
            list_item = list_class(text=f"{horario_view}")  # Use OneLineListItem
            tab_content.add_widget(list_item)


def dias_da_semana(ano, mes, dia_atual):
    dias_uteis = []
    dia_sem = ('Seg', 'Ter', 'Qua', 'Qui', 'Sex')
    num_dias_no_mes = calendar.monthrange(ano, mes)
    dias_mes = num_dias_no_mes[1]
    # Iterar por todos os dias do mês
    for dia in range(dia_atual, dias_mes + 1):
        date = datetime.datetime(ano, mes, dia)
        dia_nume = date.weekday()
        # Verificar se é um dia útil (segunda a sexta)
        if dia_nume < 5:
            dias_uteis.append(date.strftime(f'%d {dia_sem[dia_nume]}'))
    return dias_uteis


def post_horarios():
    ano = data_atual.year
    data = {'07:20': 'Livre', '09:10': 'Livre', '10:50': 'Livre'}
    dia_atual = 1
    mes_atual = data_atual.month
    meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
            'Novembro', 'Dezembro']
    for mes in range(mes_atual, 13):
        if 'Horarios' not in dados or meses[mes_atual] not in dados['Horarios']:
            db.child('Horarios').child(meses[mes_atual]).child(data_atual.day).set(data, user_token)
            #requests.put(f'{link}/Horarios/{meses[mes_atual]}/{data_atual.day}.json', data=json.dumps(data))
        if f'{mes}' == f'{mes_atual}':
            qtd_dias_atual = dias_da_semana(ano, mes_atual, data_atual.day)
            primeira_chave = list(dados['Horarios'][meses[mes_atual]].keys())[0]
            for dia in qtd_dias_atual:
                if dia not in dados['Horarios'][meses[mes_atual]]:
                    db.child('Horarios').child(meses[mes_atual]).child(dia).set(data, user_token)
                    #requests.put(f'{link}/Horarios/{meses[mes_atual]}/{dia}.json', data=json.dumps(data))
                if len(qtd_dias_atual) < len(dados['Horarios'][meses[mes_atual]]):
                    db.child('Horarios').child(meses[mes_atual]).child(primeira_chave).remove(user_token)
                    #requests.delete(f'{link}/Horarios/{meses[mes_atual]}/{primeira_chave}.json')
        elif f'{mes}' != f'{mes_atual}' and meses[mes] not in dados['Horarios']:
            qtd_dias = dias_da_semana(ano, mes, dia_atual)
            for dia in qtd_dias:
                #requests.put(f'{link}/Horarios/{meses[mes]}/{dia}.json', data=json.dumps(data))
                db.child('Horarios').child(meses[mes_atual]).child(dia).set(data, user_token)


def on_checkbox_active(listitem, checkbox,  value, app):
    dia = app.current_tab
    global mes_text, prog_text
    if value:
        if mes_text not in ocupados:
            ocupados[mes_text] = {dia: {listitem.text: 'Indisponivel'}}
        elif mes_text in ocupados and dia not in ocupados[mes_text]:
            ocupados[mes_text][dia] = {listitem.text: 'Indisponivel'}
        else:
            ocupados[mes_text][dia][listitem.text] = 'Indisponivel'
        print(ocupados)
    else:
        if len(ocupados[mes_text][dia]) > 0:
            del ocupados[mes_text][dia][listitem.text]
            print(ocupados)
            print(len(ocupados[mes_text][dia]))
        if len(ocupados[mes_text][dia]) == 0:
            del ocupados[mes_text][dia]
        if len(ocupados[mes_text]) == 0:
            del ocupados[mes_text]
            print(ocupados)


def on_button_press(app):
    global ocupados
    dia = app.current_tab
    post_horarios_marcados(dia)
    app.switch_to_screen('meus_horarios')
    ocupados = {}


# def get_horarios_user(usuario, dia):
#     global mes_text
#     for i in range(len(dados['Usuarios'])):
#         user_path = f'User{i}'
#         user = dados['Usuarios'][user_path]['User']
#
#         if user == usuario:
#             # Verificar se o campo 'Horarios' existe para o usuário
#             if 'Horarios' not in dados['Usuarios'][user_path]:
#                 # Se não existir, criar o campo 'Horarios' com o ID do usuário
#                 requests.put(f'{link}/Usuarios/{user_path}/Horarios/.json', data=json.dumps(ocupados))
#             # Recuperar os horários do usuário após garantir que o campo 'Horarios' existe
#             else:
#                 horarios_user = dados['Usuarios'][user_path].get('Horarios', {})
#                 # Atualizar os horários para o dia específico
#                 if mes_text not in horarios_user:
#                     horarios_user = ocupados
#                 elif mes_text in horarios_user and dia not in horarios_user[mes_text]:
#                     horarios_user[mes_text].update(ocupados[mes_text])
#                 elif mes_text in horarios_user and dia in horarios_user[mes_text]:
#                     horarios_user[mes_text][dia].update(ocupados[mes_text][dia])
#                 requests.put(f'{link}/Usuarios/{user_path}/Horarios/.json', data=json.dumps(horarios_user))


def post_horarios_marcados(dia):
    global mes_text, user_id, lab_text, prog_text
    ocupados[mes_text][dia]['Programa'] = prog_text
    if 'Horarios_marcados' in dados:
        if user_id not in dados['Horarios_marcados']:
            #requests.put(f'{link}/Horarios_marcados/{name_user}/{lab_text}/.json', data=json.dumps(ocupados))
            db.child('Horarios_marcados').child(user_id).child(lab_text).set(ocupados, user_token)
        else:
            # Verificar se o campo 'laboratorio' existe para o usuário
            if lab_text not in dados['Horarios_marcados'][user_id]:
                # Se não existir, criar o campo 'Horarios' com o ID do usuário
                #requests.put(f'{link}/Horarios_marcados/{name_user}/{lab_text}/.json', data=json.dumps(ocupados))
                db.child('Horarios_marcados').child(user_id).child(lab_text).set(ocupados, user_token)
            # Recuperar os horários do usuário após garantir que o campo 'Horarios' existe
            else:
                marcados = dados['Horarios_marcados'][user_id][lab_text]
                # Atualizar os horários para o dia específico
                if mes_text not in marcados:
                    marcados[mes_text] = ocupados[mes_text]
                elif mes_text in marcados and dia not in marcados[mes_text]:
                    marcados[mes_text].update(ocupados[mes_text])
                elif mes_text in marcados and dia in marcados[mes_text]:
                    marcados[mes_text][dia].update(ocupados[mes_text][dia])
                #requests.put(f'{link}/Horarios_marcados/{name_user}/{lab_text}/.json', data=json.dumps(marcados))
                db.child('Horarios_marcados').child(user_id).child(lab_text).set(marcados, user_token)
    else:
        #requests.put(f'{link}/Horarios_marcados/{name_user}/{lab_text}/.json', data=json.dumps(ocupados))
        db.child('Horarios_marcados').child(user_id).child(lab_text).set(ocupados, user_token)


def del_horarios_marcados():
    global dados
    if 'Horarios_marcados' in dados:
        for usuarios, user_item in dados['Horarios_marcados'].items():
            for laboratorio, lab_item in user_item.items():
                for mes, mes_item in lab_item.items():
                    for dia in mes_item.keys():
                        if dia not in dados['Horarios'][mes]:
                            print(dia, 'não esta em ', mes)
                            #requests.delete(f'{link}/Horarios_marcados/{usuarios}/{laboratorio}/{mes}/{dia}.json')
                            db.child('Horarios_marcados').child(usuarios).child(laboratorio).child(mes).child(dia).remove(user_token)


# def check_horarios_user():
#     for user in dados['Usuarios']:
#         if 'Horarios' in dados['Usuarios'][user] and len(dados['Usuarios'][user]['Horarios']) > 0:
#             horarios_user = dados['Usuarios'][user]['Horarios']
#             for mes in horarios_user:
#                 dias = horarios_user[mes]
#                 if mes not in dados['Horarios']:
#                     requests.delete(f'{link}/Usuarios/{user}/Horarios/{mes}.json')
#                 for dia in dias:
#                     print(dia)
#                     if dia not in dados['Horarios'][mes]:
#                         requests.delete(f'{link}/Usuarios/{user}/Horarios/{mes}/{dia}.json')


def set_error_empty(screen, instance_textfield):
    instance_textfield.helper_text = "Campo obrigatório!"
    instance_textfield.helper_text_mode = "on_error"
    instance_textfield.error = True


def set_error_wrong(screen, instance_textfield, msg):
    instance_textfield.helper_text = f"{msg}"
    instance_textfield.helper_text_mode = "on_error"
    instance_textfield.error = True


def logout(screen):
    global autenticacao
    autenticacao = False
    screen.manager.current = 'login'


def menu_user(screen, menu_nomes, menu_icons, larg=240):
    menu_items = [
        {
            "text": f"{menu_nomes[i]}",
            "text_color": 'white',
            "leading_icon": f"{menu_icons[i]}",
            "leading_icon_color": "white",
            "on_release": lambda x=i: executar_acao(screen, x),
        } for i in range(len(menu_nomes))
    ]
    screen.menu_user = MDDropdownMenu(
        md_bg_color=(0.278, 0.306, 0.365, 1),
        items=menu_items,
        width=dp(larg),
    )


def menu_labs(self):
    labs = ['lab34', 'lab35', 'lab36', 'lab37']
    menu_items = [

        {
            "text": f"{i}",
            "on_release": lambda x=f"{i}": set_item1(self, x),
        } for i in labs]

    self.menu_labs = MDDropdownMenu(
        items=menu_items,
        position="bottom",
        pos_hint={'center_x': .5},
    )


def menu_mes(self):
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    mes_atual = datetime.date.today().month
    menu_items = [

        {
            "text": f"{meses[i-1]}",
            "on_release": lambda x=f"{meses[i-1]}": set_item2(self, x),
        } for i in range(mes_atual, len(meses)+1)]

    self.menu_mes = MDDropdownMenu(
        items=menu_items,
        position="bottom",
        pos_hint={'center_x': .5},
    )


def menu_prog(self):
    programas = ['AutoCad', 'Matlab', 'Logsim', 'Simulink']
    menu_items = [

        {
            "text": f"{i}",
            "on_release": lambda x=f"{i}": set_item3(self, x),
        } for i in programas]

    self.menu_prog = MDDropdownMenu(
        items=menu_items,
        position="bottom",
        pos_hint={'center_x': .5},
    )


def set_item1(self, text_item):
    global lab_text
    self.root.get_screen('escolha').ids.escolha_lab.text = text_item
    self.menu_labs.dismiss()
    lab_text = text_item
    print(lab_text)


def set_item2(self, text_item):
    global mes_text
    global mes_num
    meses = {'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6, 'Julho': 7,
             'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12}
    self.root.get_screen('escolha').ids.escolha_mes.text = text_item
    self.menu_mes.dismiss()
    mes_text = text_item
    mes_num = meses[text_item]
    print(mes_text)
    print(mes_num)


def set_item3(self, text_item):
    global prog_text
    self.root.get_screen('escolha').ids.escolha_prog.text = text_item
    self.menu_prog.dismiss()
    prog_text = text_item


def executar_acao(screen, indice):
    if indice == 0:
        screen.switch_to_screen('agende')
    elif indice == 1:
        screen.switch_to_screen('login')


def callback_menus(self, button):
    self.caller = button
    self.open()


def callback(self, button):
    self.menu_user.caller = button
    self.menu_user.open()


def horarios_laboratorios(screen):
    global dados, mes_text, lab_text
    hr_disponivel = dados['Horarios'].copy


def get_name_user(user):
    global user_id
    for i in range(len(dados['Usuarios'])):
        usuario = dados['Usuarios'][f'User{i}']['User']
        if user == usuario:
            user_id = dados['Usuarios'][f'User{i}']['Nome']


def bem_vindo(screen):
    global user_id
    name_user = dados['Usuarios'][user_id]['Nome']
    screen.ids.bv.text = f'Olá Professor(a) {name_user}'


stop1 = threading.Event()


def on_stop1(self):
    if hasattr(self, 'data_thread'):
        self.data_thread.join()


def on_enter1(self):
    self.start_second_thread1()


def start_second_thread1(self):
    threading.Thread(target=self.marcados_data).start()


#colocar uma funcionalidade para quando não tiver horarios marcados
def marcados_data(self, *args):
    try:
        requisicoes = db.child('Horarios_marcados').get(user_token)
        horarios_marcados = requisicoes.val()
        cols = ["Dia", 'Mês', 'Laboratório', 'Programa', 'Horário']
        values = []

        for lab, lab_dados in horarios_marcados.get(user_id, {}).items():
            for mes, mes_dados in lab_dados.items():
                for dia, horarios in mes_dados.items():
                    programas = []
                    indisponiveis = []
                    for key, info in horarios.items():
                        if info == 'Indisponivel':
                            indisponiveis.append(key)
                        else:
                            if info != '':
                                programas.append(info)
                            else:
                                programas.append('N/A')

                    if len(indisponiveis) > 2:
                        horas = f'{indisponiveis[0]} a {indisponiveis[-1]}'
                    elif len(indisponiveis) == 2:
                        horas = f'{indisponiveis[0]} e {indisponiveis[1]}'
                    elif len(indisponiveis) == 1:
                        horas = indisponiveis[0]
                    else:
                        horas = 'N/A'

                    for i in range(len(programas)):
                        programa = programas[i] if i < len(programas) else ''
                        horario = horas if i < len(programas) else ''
                        values.append([dia, mes, lab, programa, horario])
                        print(values)

        data_table(self, cols, values)
    except Exception as e:
        print("Erro ao carregar dados:", e)  # Debug: capturar e mostrar erros

@mainthread
def data_table(self, cols, values):
    try:
        float_layout = self.ids.float_layout
        float_layout.clear_widgets()

        self.data_tables = MDDataTable(
            pos_hint={'center_y': 0.5, 'center_x': 0.5},
            size_hint=(.9, 0.6),
            padding=0,
            column_data=[
                (col, dp(23))
                for col in cols
            ],
            background_color_header="#FAFAFA",
            background_color_cell="#FAFAFA",
            background_color_selected_cell="#FAFAFA",
            elevation=0,
            row_data=values,
            check=True
        )

        float_layout.add_widget(self.data_tables)

        print("Tabela de dados adicionada com sucesso")  # Debug: confirmar adição da tabela
    except Exception as e:
        print("Erro ao criar tabela de dados:", e)  # Debug: capturar e mostrar erros


def on_button_press1(self) -> None:
    global user_id
    '''Called when a control button is clicked.'''
    selecionado = self.data_tables.get_row_checks()
    print(f"Checked rows: {selecionado}")
    for horario in selecionado:
        dia = horario[0]
        mes = horario[1]
        lab = horario[2]
        #requests.delete(f'{link}/Horarios_marcados/{name_user}/{lab}/{mes}/{dia}.json')
        db.child('Horarios_marcados').child(user_id).child(lab).child(mes).child(dia).remove(user_token)
    marcados_data(self)


def menu_laboratorio(self):
    laboratorios = ['Lab 34', 'Lab 35', 'Lab 36', 'Lab 37']
    menu_items = [

        {
            "text": f"{i}",
            "on_release": lambda x=f"{i}": set_item4(self, x),
        } for i in laboratorios]

    self.menu_laboratorio = MDDropdownMenu(
        items=menu_items,
        position="bottom",
        pos_hint={'center_x': .5},
    )


def set_item4(self, text_item):
    global lab_escolha
    self.root.get_screen('laboratorios').ids.escolha.text = text_item
    self.menu_laboratorio.dismiss()
    lab_escolha = text_item


def laboratorios_info(self):
    global lab_escolha
    comp_text = ''

    if 'Computadores' in dados['Laboratórios'][lab_escolha]:
        comp_text += 'Quantidade de maquinas:\n 22 Computadores\n\n'
        comp_text += 'Hardware:\n'
        for computadores in dados['Laboratórios'][lab_escolha]['Computadores'].items():
            comp_text += f'{computadores[0]}: {computadores[1]}\n'
        comp_text += '\nProgramas:\n'
        for programas in dados['Laboratórios'][lab_escolha]['Programas'].items():
            comp_text += f'{programas[1]}\n'
    else:
        comp_text += 'Equipamentos:\n'
        for equipamentos in dados['Laboratórios'][lab_escolha]['Equipamentos'].items():
            comp_text += f'{equipamentos[1]}\n'

    self.ids.lab_label.clear_widgets()

    self.ids.lab_label.add_widget(
        MDLabel(
            text=comp_text,
            halign='center',
            valign='middle',
            font_name='Poppins-Medium.ttf'

        )
    )
    

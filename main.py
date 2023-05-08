import mysql.connector
from validator import Validator
from converter import SQL_TO_ALGEBRA
from tree_generator import gera_arvore
from PySimpleGUI import PySimpleGUI as psg

layout = [
    [psg.Text('Comando SQL:'), psg.Input(key='query'), psg.Button('Confirma', key='confirm')],
    [psg.Output(size=(150, 20), key='output')]
]


def setup():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="6172",  # MUDAR PARA SENHA DO ROOT USER
        database="exercicios"
    )
    mycursor = mydb.cursor()

    mycursor.execute("Show tables;")
    database_tables = mycursor.fetchall()
    table_names = list()

    for (table_name,) in database_tables:
        table_names.append(table_name)

    column_names = dict()
    for name in table_names:
        mycursor.execute(f'Show columns from {name};')
        table_columns = mycursor.fetchall()
        column_names[name] = list()
        for (column_name, _, _, _, _, _) in table_columns:
            column_names[name].append(column_name)

    global validator
    validator = Validator(table_names, column_names)


def verify_and_fix_list_spacings(query_list):
    quote_start_index = None
    result = list()

    for idx in range(len(query_list)):
        word = query_list[idx]
        if word[0] != '\'' and quote_start_index == None or word[0] == '\'' and word[-1] == '\'':
            result.append(word)
            continue
        elif word[0] == '\'' and word[-1] != '\'':
            quote_start_index = idx
            continue
        elif word[-1] == '\'' and quote_start_index == None or quote_start_index != None and word[0] == '\'':
            return {"isFixed": False, "message": f'(ERROR) MISPLACED QUOTATION MARK ON {word}'}
        elif quote_start_index != None and word[-1] == '\'':
            result.append(' '.join(query_list[quote_start_index: idx+1]))
            quote_start_index = None
    if quote_start_index != None:
        return {"isFixed": False, "message": f'(ERROR) MISSING CLOSING MARK ON QUERY'}
    return {"isFixed": True, "result": result}


setup()


def onQuerySubmit(query: str):
    query_word_list = query.split(' ')

    fixResult = verify_and_fix_list_spacings(query_word_list)
    if fixResult['isFixed']:
        query_word_list = fixResult["result"]
        validator.syntax_validation(query_word_list)

        if validator.validation_status:
            relational_algebra = SQL_TO_ALGEBRA(validator.select_section, validator.join_sections,
                                                validator.where_sections, validator.existing_columns)
            gera_arvore(relational_algebra)
            return relational_algebra
        else:
            return validator.error_message

    else:
        return fixResult["message"]


query = "SELECT nome, datanascimento, descricao, saldoinicial FROM usuario JOIN contas ON usuario.idUsuario = contas.Usuario_idUsuario WHERE saldoinicial >= 235 AND uf = 'ce' AND cep <> '62930000'"
query2 = "SELECT nome, datanascimento, descricao, saldoinicial FROM usuario WHERE saldoinicial >= 235 AND uf = 'ce' AND cep <> '62930000'"
query3 = "SELECT * FROM usuario JOIN contas ON usuario.idUsuario = contas.Usuario_idUsuario"
query4 = "SELECT * FROM usuario WHERE saldoinicial >= 235 AND uf = 'ce' AND cep <> '629300001'"
query5 = "SELECT idusuario, nome, datanascimento, descricao, saldoinicial, UF, Descrição FROM usuario JOIN contas ON usuario.idUsuario = contas.Usuario_idUsuario JOIN tipoconta ON tipoconta.idTipoConta = contas.TipoConta_idTipoConta"
badquery = "SELECT * FROM usuario SELECT contas ON usuario.idUsuario = contas.Usuario_idUsuario"
badquery2 = "JOIN * FROM usuario SELECT contas ON usuario.idUsuario = contas.Usuario_idUsuario"
badquery3 = "SELECT * FROM usuario JOIN = ON usuario.idUsuario = contas.Usuario_idUsuario"


window = psg.Window('SQL Processor', layout)

while True:
    events, values = window.read()
    if events == 'confirm':
        window['output'].update(value='')  # Limpa a caixa de texto
        print("Algebra: "+onQuerySubmit(values['query']))
    elif events == psg.WIN_CLOSED:  # Window close button event
        break


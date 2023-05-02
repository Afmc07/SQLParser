import mysql.connector
from validator import Validator

mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="PLACEHOLDER", #MUDAR PARA SENHA DO ROOT USER
        database="exercicios"
        )
mycursor = mydb.cursor()

mycursor.execute("Show tables;")
database_tables = mycursor.fetchall() 
table_names= list()

for (table_name,) in database_tables:
    table_names.append(table_name)
    
column_names = dict();
for name in table_names:
    mycursor.execute(f'Show columns from {name};')
    table_columns = mycursor.fetchall()
    column_names[name] = list()
    for (column_name, _, _, _, _, _) in table_columns:
        column_names[name].append(column_name)
    
validator = Validator(table_names, column_names)
    

query = "SELECT nome, datanascimento, descricao, saldoinicial FROM usuario JOIN contas ON usuario.idUsuario = contas.Usuario_idUsuario WHERE saldoinicial >= 235 AND uf = 'ce' AND cep <> '62930000'"
query2 = "SELECT nome, datanascimento, descricao, saldoinicial FROM usuario WHERE saldoinicial >= 235 AND uf = 'ce' AND cep <> '62930000'"
query3 = "SELECT * FROM usuario JOIN contas ON usuario.idUsuario = contas.Usuario_idUsuario"
query4 = "SELECT * FROM usuario WHERE saldoinicial >= 235 AND uf = 'ce' AND cep <> '62930000'"
badquery = "SELECT * FROM usuario SELECT contas ON usuario.idUsuario = contas.Usuario_idUsuario"
badquery2 = "JOIN * FROM usuario SELECT contas ON usuario.idUsuario = contas.Usuario_idUsuario"
badquery3 = "SELECT * FROM usuario JOIN = ON usuario.idUsuario = contas.Usuario_idUsuario"

query_word_list = query.split(' ')

validator.syntax_validation(query_word_list)


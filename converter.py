import re


def SQL_TO_ALGEBRA(select_section: list, join_sections: list, where_sections: list, existing_columns: dict):
    expression = ''
    columns_used = None

    from_table = select_section[select_section.index(
        "FROM")+1] if 'FROM' in select_section else select_section[select_section.index("from")+1]
    if len(join_sections) > 0:
        result = create_join_chunk(join_sections)
        expression = result["algebra"]
        columns_used = result["data"]

    result = create_select_chunk(
        select_section, columns_used, existing_columns)
    expression = f'{result["algebra"]} {expression}'
    columns_used = result["data"]

    if len(where_sections) > 0:
        result = include_where_sections(
            expression, from_table, where_sections, columns_used, existing_columns)
        expression = result

    return expression


def find_table_by_column(column_dictionary: dict, column_name: str):
    for key in column_dictionary:
        if column_name.lower() in [x.lower() for x in column_dictionary[key]]:
            return key


def create_select_chunk(select_section: list, columns_used: dict, existing_columns: dict):
    if columns_used == None:
        cols_used_in_select = dict()
    else:
        cols_used_in_select = columns_used

    chunk = 'PI'
    from_index = select_section.index('FROM')
    columns = select_section[1:from_index]

    for idx, column in enumerate(columns):
        if '.' in column:
            references = column.split('.')

            if references[0] not in cols_used_in_select.keys():
                cols_used_in_select[references[0]] = list()
            if references[1] not in cols_used_in_select[references[0]]:
                cols_used_in_select[references[0]].append(references[1])
        else:
            column_name = column.rstrip(',')
            table = find_table_by_column(
                existing_columns, column_name)

            if table not in cols_used_in_select.keys():
                cols_used_in_select[table] = list()
            if column_name not in cols_used_in_select[table]:
                cols_used_in_select[table].append(column_name)

        chunk = f'{chunk} {column}'

    return {"algebra": chunk, "data": cols_used_in_select}


def create_join_chunk(join_sections: list()):
    chunk = ''
    columns_used = dict()

    for idx, section in enumerate(join_sections):
        table_names = list()
        on_index = section.index(
            'ON') if 'ON' in section else section.index('on')
        post_on_arg = ' '.join(section[on_index+1:])

        for pos, word in enumerate(section[on_index+1:]):
            if pos % 2 == 0:
                args = word.split('.')
                table = args[0]
                column = args[1]
                table_names.append(table)

                if table not in columns_used.keys():
                    columns_used[table] = list()
                if column not in columns_used[table]:
                    columns_used[table].append(column)
            else:
                continue

        if idx == 0:
            chunk = f'( {table_names[0]} |X| {post_on_arg} {table_names[1]} )'
        else:
            new_chunk = f'( {table_names[0]} |X| {post_on_arg} {table_names[1]} )'

            for table in table_names:
                if table in chunk:
                    pattern = rf"(?<!\S){table}(?!\S)"
                    chunk = re.sub(pattern, new_chunk, chunk)
    return {"algebra": chunk, "data": columns_used}


def include_where_sections(current_expression: str, from_table: str, where_sections: str, columns_used: dict, existing_columns: dict):
    if "|X|" in current_expression:
        table_sigma_strings = dict()

        for section in where_sections:
            post_where_section = section[1:]

            for i in range(0, len(post_where_section), 4):
                chunk = " ".join(post_where_section[i:i+3])

                if '.' in post_where_section[i]:
                    references = post_where_section[i].split('.')
                    if references[0] not in table_sigma_strings.keys():
                        table_sigma_strings[references[0]
                                            ] = f'( SIGMA {chunk} ( {references[0]} ) )'
                    else:
                        sigma_string = table_sigma_strings[references[0]]
                        idx = sigma_string.rfind("(")
                        table_sigma_strings[references[0]] = sigma_string[:idx] + \
                            "^ " + chunk + " " + sigma_string[idx:]
                else:
                    table = find_table_by_column(
                        existing_columns, post_where_section[i])
                    if table not in table_sigma_strings.keys():
                        table_sigma_strings[table] = f'SIGMA {chunk} ( {table} )'
                    else:
                        sigma_string = table_sigma_strings[table]
                        idx = sigma_string.rfind("(")
                        table_sigma_strings[table] = sigma_string[:idx] + \
                            "^ " + chunk + " " + sigma_string[idx:]

        for table in table_sigma_strings.keys():
            columns_in_pi = columns_used[table]
            table_sigma_strings[table] = f'( PI {", ".join(columns_in_pi)} ( {table_sigma_strings[table]} ) )'

        new_expression = current_expression
        for table in table_sigma_strings.keys():
            if table in new_expression:
                pattern = rf"(?<!\S){table}(?!\S)"
                new_expression = re.sub(
                    pattern, table_sigma_strings[table], new_expression)
        return new_expression
    else:
        sigma_expression = ''
        for section in where_sections:
            post_where_section = section[1:]

            for i in range(0, len(post_where_section), 4):
                chunk = " ".join(post_where_section[i:i+3])

                if sigma_expression == '':
                    sigma_expression = f'SIGMA {chunk} ( {from_table} )'
                else:
                    sigma_string = sigma_expression
                    idx = sigma_string.rfind("(")
                    sigma_expression = sigma_string[:idx] + \
                        "^ " + chunk + " " + sigma_string[idx:]

        return f'{current_expression} ( {sigma_expression} )'

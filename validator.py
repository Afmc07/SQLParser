import re

SELECT_REGEX = r'(?i)SELECT\s+((?:\*|[A-Za-zÀ-ÿ0-9_]+(?:\.[A-Za-zÀ-ÿ0-9_]+)*)\s*(?:,\s*(?:\*|[A-Za-zÀ-ÿ0-9_]+(?:\.[A-Za-zÀ-ÿ0-9_]+)*))*)\s+FROM\s+\w+$'
JOIN_REGEX = r'(?i)JOIN\s+\w+\s?(?:ON\s+(?:(?:[A-Za-zÀ-ÿ0-9_]+\.)?[A-Za-zÀ-ÿ0-9_]+\s*(?:[<>=!]+\s*[A-Za-zÀ-ÿ0-9_]+(?:\.[A-Za-zÀ-ÿ0-9_]+)?)?\s*(?:AND|OR)\s*)*(?:[A-Za-zÀ-ÿ0-9_]+\.)?[A-Za-zÀ-ÿ0-9_]+\s*(?:[<>=!]+\s*[A-Za-zÀ-ÿ0-9_]+(?:\.[A-Za-zÀ-ÿ0-9_]+)?)?\s*)?$'
WHERE_REGEX = r'(?i)WHERE\s+(?:(?:\w+\.)?\w+\s*(?:[<>=!]+\s*(?:\w+|\'.*?\'))\s*(?:AND|OR)\s*)*(?:\w+\.)?\w+\s*(?:[<>=!]+\s*(?:\w+|\'.*?\'))\s*$'

operators = ['=', '>=', ">", "<", "<=", "<>", "AND", "IN", 'and', 'in']
key_words = ['SELECT', 'JOIN', 'WHERE', 'select', 'join', 'where']


class Validator:
    def __init__(self, existing_tables: list, existing_columns: dict):
        self.existing_tables = existing_tables
        self.existing_columns = existing_columns
        self.select_section = list()
        self.join_sections = list()
        self.where_sections = list()
        self.validation_status = False
        self.error_message = ''

    def get_status(self):
        return self.validation_status

    def syntax_validation(self, query: list):
        if (query.index("SELECT") != 0 or query.count("SELECT") != 1 if 'SELECT' in query else query.index("select") != 0 or query.count("select") != 1):
            self.error_message = "(ERROR) A QUERY CAN ONLY HAVE ONE SELECT KEYWORD OR SELECT MUST BE PRESENT AT THE START OF QUERY"
            self.validation_status = False
            return

        select_end_index = [i for i, n in enumerate(
            query) if n in key_words][1]

        self.select_section = query[:select_end_index]

        join_count = query.count("JOIN")
        where_count = query.count("WHERE")

        post_select_query = query[select_end_index:]
        self.join_sections = [None] * join_count
        self.where_sections = [None] * where_count

        for x in range(join_count+where_count):
            key_word_finder = [i for i, n in enumerate(
                post_select_query) if n in key_words]
            end_index = key_word_finder[1] if len(
                key_word_finder) > 1 else len(post_select_query)

            if post_select_query[0] == 'JOIN' or post_select_query[0] == 'join':
                self.join_sections[self.join_sections.index(
                    None)] = post_select_query[:end_index]
            elif post_select_query[0] == 'WHERE' or post_select_query[0] == 'where':
                self.where_sections[self.where_sections.index(
                    None)] = post_select_query[:end_index]
            post_select_query = post_select_query[end_index:len(
                post_select_query)]

        select_status = self.__validate_select(self.select_section)
        if not select_status:
            self.validation_status = select_status
            return

        join_status = True
        for statement in self.join_sections:
            join_status = self.__validate_join(statement)
            if not join_status:
                self.validation_status = join_status
                return

        where_status = True
        for statement in self.where_sections:
            where_status = self.__validate_where(statement)
            if not where_status:
                self.validation_status = where_status
                return

        self.validation_status = True

    def verify_if_table_exists(self, table_name):
        return table_name in self.existing_tables

    def verify_if_column_exists(self, column_name: str, table_name=None):
        if table_name != None:
            return column_name.lower() in [x.lower() for x in self.existing_columns[table_name]]
        else:
            for table in self.existing_columns.keys():
                exists = column_name.lower() in [x.lower(
                ) for x in self.existing_columns[table]]
                if exists:
                    return True
            return False

    def __validate_select(self, select_statement: list):
        select_pattern = re.compile(SELECT_REGEX)

        if not select_pattern.match(' '.join(select_statement)):
            self.error_message = '(ERROR) INVALID SELECT STATEMENT (Verify Syntax): ' + \
                ' '.join(select_statement)
            return False

        from_position = select_statement.index('FROM')

        if (select_statement[from_position-1] != '*'):
            for word in select_statement[1:from_position]:
                if word in key_words or word in operators:
                    self.error_message = f'(ERROR) INVALID COLUMN NAME ({word}) ON SELECT: '+' '.join(
                        select_statement)
                    return False

                if '.' not in word:
                    if not self.verify_if_column_exists(word.rstrip(',')):
                        self.error_message = F'(ERROR) NONEXISTENT COLUMN NAME ({word.rstrip(",")}) ON SELECT: '+' '.join(
                            select_statement)
                        return False
                else:
                    if word.count('.') > 1 or word[0] == '.':
                        self.error_message = f'(ERROR) INVALID OR EMPTY TABLE REFERENCE IN "JOIN ON" ARGUMENT ({word}) IN SELECT STATEMENT: '+' '.join(
                            select_statement)
                        return False
                    if '.' == word[-1]:
                        self.error_message = f'(ERROR) INVALID OR EMPTY COLUMN REFERENCE IN "JOIN ON" ARGUMENT ({word}) IN SELECT STATEMENT: '+' '.join(
                            select_statement)
                        return False

                    referece_sections = word.split('.')

                    if not self.verify_if_column_exists(referece_sections[1].rstrip(','), referece_sections[0]):
                        self.error_message = F'(ERROR) NONEXISTENT COLUMN NAME ({word.rstrip(",")}) ON SELECT: '+' '.join(
                            select_statement)
                        return False

        if select_statement[from_position+1] in key_words or select_statement[from_position+1] in operators:
            self.error_message = F'(ERROR) INVALID TABLE NAME ({select_statement[from_position+1]}) ON SELECT FROM: '+' '.join(
                select_statement)
            return False
        if not self.verify_if_table_exists(select_statement[from_position+1]):
            self.error_message = F'(ERROR) NONEXISTENT TABLE NAME ({select_statement[from_position+1]}) ON SELECT: '+' '.join(
                select_statement)
            return False

        return True

    def __validate_join(self, join_statement: list):
        join_pattern = re.compile(JOIN_REGEX)

        if not join_pattern.match(' '.join(join_statement)):
            self.error_message = '(ERROR) INVALID JOIN STATEMENT (Verify Syntax): ' + \
                ' '.join(join_statement)
            return False

        if join_statement[1] in operators:
            self.error_message = f'(ERROR) INVALID TABLE NAME ({join_statement[1]}) IN JOIN STATEMENT:'+' '.join(
                join_statement)
            return False
        if not self.verify_if_table_exists(join_statement[1]):
            self.error_message = F'(ERROR) NONEXISTENT TABLE NAME ({join_statement[1]}) IN JOIN STATEMENT:'+' '.join(
                join_statement[1])
            return False

        if "ON" in join_statement or 'on' in join_statement:
            on_position = join_statement.index(
                "ON") if "ON" in join_statement else join_statement.index("on")
            post_on_items = join_statement[on_position+1:]
            not_flag = False

            for idx, word in enumerate(post_on_items):
                if not_flag and word != 'IN' and word != 'in':
                    self.error_message = f'(ERROR) MSSING IN OPERATOR AFTER NOT IN JOIN STATEMENT: '.join(
                        join_statement)
                    return False
                elif not_flag and word == 'IN' and word == 'in':
                    not_flag = False
                    continue
                if (idx % 2) == 0:
                    if word in operators:
                        self.error_message = f'(ERROR) MISPLACED OPERATOR ({word}) IN JOIN STATEMENT:  '+' '.join(
                            join_statement)
                        return False
                    if '.' not in word or word.count('.') > 1 or word[0] == '.':
                        self.error_message = f'(ERROR) INVALID OR EMPTY TABLE REFERENCE IN "JOIN ON" ARGUMENT ({word}) IN JOIN STATEMENT: '+' '.join(
                            join_statement)
                        return False
                    if '.' == word[-1]:
                        self.error_message = f'(ERROR) INVALID OR EMPTY COLUMN REFERENCE IN "JOIN ON" ARGUMENT ({word}) IN JOIN STATEMENT: '+' '.join(
                            join_statement)
                        return False

                    referece_sections = word.split('.')

                    if not self.verify_if_table_exists(referece_sections[0]):
                        self.error_message = F'(ERROR) NONEXISTENT TABLE NAME ({referece_sections[0]}) IN JOIN STATEMENT: ' + \
                            referece_sections[0]
                        return False
                    if not self.verify_if_column_exists(referece_sections[1], referece_sections[0]):
                        self.error_message = F'(ERROR) NONEXISTENT COLUMN NAME ({referece_sections[1]}) IN JOIN STATEMENT: ' + \
                            referece_sections[1]
                        return False

                elif (idx % 2) == 1:
                    if word not in operators:
                        self.error_message = f'(ERROR) INVALID OPERATOR ({word}) IN JOIN STATEMENT:'+' '.join(
                            join_statement)
                        return False
                    if word == 'NOT' or word == 'not':
                        not_flag = True
        return True

    def __validate_where(self, where_statement: list):
        where_pattern = re.compile(WHERE_REGEX)

        if not where_pattern.match(' '.join(where_statement)):
            self.error_message = '(ERROR) INVALID WHERE STATEMENT (Verify Syntax): ' + \
                ' '.join(where_statement)
            return False

        post_where_items = where_statement[1:]
        comparator_flag = False  # when column is compared to value, be forgiving
        not_flag = False

        for idx, word in enumerate(post_where_items):
            if not_flag and word != 'IN' and word != 'in':
                self.error_message = f'(ERROR) MSSING IN OPERATOR AFTER NOT IN WHERE STATEMENT: '.join(
                    where_statement)
                return False
            elif not_flag and word == 'IN' and word != 'in':
                not_flag = False
                continue
            if (idx % 2) == 0:
                if word in operators:
                    self.error_message = f'(ERROR) MISPLACED OPERATOR ({word}) IN  STATEMENT: '+' '.join(
                        where_statement)
                    return False
                if not self.verify_if_column_exists(word):
                    if not comparator_flag:
                        self.error_message = F'(ERROR) NONEXISTENT COLUMN NAME ({word}) IN WHERE STATEMENT: '+' '.join(
                            word)
                        return False
                    else:
                        comparator_flag = False
                else:
                    comparator_flag = True

            elif (idx % 2) == 1:
                if word not in operators:
                    self.error_message = f'(ERROR) INVALID OPERATOR ({word}) IN WHERE STATEMENT: '+' '.join(
                        where_statement)
                    return False
                if word == 'NOT' or word == 'not':
                    not_flag = True

        return True

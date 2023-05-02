import re

SELECT_REGEX = r'SELECT\s+((?:\*|\w+(?:\.\w+)*)\s*(?:,\s*(?:\*|\w+(?:\.\w+)*))*)\s+FROM\s+\w+$'
JOIN_REGEX = r'JOIN\s+\w+\s?(?:ON\s+(?:(?:\w+\.)?\w+\s*(?:[<>=!]+\s*\w+(?:\.\w+)?)?\s*(?:AND|OR)\s*)*(?:\w+\.)?\w+\s*(?:[<>=!]+\s*\w+(?:\.\w+)?)?\s*)?$'
WHERE_REGEX = r'WHERE\s+(?:(?:\w+\.)?\w+\s*(?:[<>=!]+\s*(?:\w+|\'.*?\'))\s*(?:AND|OR)\s*)*(?:\w+\.)?\w+\s*(?:[<>=!]+\s*(?:\w+|\'.*?\'))\s*$'

operators = ['=','>=', ">", "<", "<=" "<>", "AND", "IN", "NOT", ]
key_words = ['SELECT', 'JOIN', 'WHERE']

class Validator:
    def __init__(self, existing_tables: list, existing_columns: dict):
        self.existing_tables = existing_tables
        self.existing_columns = existing_columns
        # self.referenced_tables = list()
        # self.referenced_columns = dict()

    def syntax_validation(self, query: list):
        if (query.index("SELECT") != 0 or query.count("SELECT") != 1):
            print("(ERROR) A QUERY CAN ONLY HAVE ONE SELECT KEYWORD OR SELECT MUST BE PRESENT AT THE START OF QUERY")
            return False
        
        select_end_index = [i for i, n in enumerate(query) if n in key_words][1]

        select_section = query[:select_end_index]
        
        join_count = query.count("JOIN")
        where_count = query.count("WHERE")

        post_select_query = query[select_end_index:]
        join_sections = [None] * join_count
        where_sections = [None] * where_count
            
        for x in range(join_count+where_count):
            key_word_finder = [i for i, n in enumerate(post_select_query) if n in key_words]
            end_index = key_word_finder[x+1] if len(key_word_finder) > 1 else len(post_select_query)

            if post_select_query[0] == 'JOIN':
                join_sections[0] = post_select_query[:end_index]
            elif post_select_query[0] == 'WHERE':
                where_sections[0] = post_select_query[:end_index]
            post_select_query = post_select_query[end_index:len(post_select_query)]
        
        select_status = self.__validate_select(select_section)
        if not select_status:
            return select_status
        
        join_status = True
        for statement in join_sections:
            join_status = self.__validate_join(statement)
            if not join_status:
                return join_status
            
        where_status = True
        for statement in where_sections:
            where_status = self.__validate_where(statement)
            if not where_status:
                return where_status
        
        print("verified")

    def verify_if_table_exists(self, table_name):
        return table_name in self.existing_tables
    
    def verify_if_column_exists(self, column_name: str, table_name=None):
        if table_name != None:
            return column_name.lower() in [x.lower() for x in self.existing_columns[table_name]] 
        else:
            for table in self.existing_columns.keys():
                exists = column_name.lower() in [x.lower() for x in self.existing_columns[table]] 
                if exists:
                    return True
            return False
    
    def __validate_select(self, select_statement: list):
        select_pattern = re.compile(SELECT_REGEX)

        if not select_pattern.match(' '.join(select_statement)):
            print('(ERROR) INVALID SELECT STATEMENT (Verify Syntax):'+' '.join(select_statement))
            return False
        
        from_position = select_statement.index('FROM')

        if (select_statement[from_position-1] != '*'):
            for word in select_statement[1:from_position]:
                if word in key_words or word in operators:
                    print(F'(ERROR) INVALID COLUMN NAME ({word}) ON SELECT:'+' '.join(select_statement))
                    return False
                if not self.verify_if_column_exists(word.rstrip(',')):
                    print(F'(ERROR) NONEXISTENT COLUMN NAME ({word.rstrip(",")}) ON SELECT:'+' '.join(select_statement))
                    return False
        
        if select_statement[from_position+1] in key_words or select_statement[from_position+1] in operators:
            print(F'(ERROR) INVALID TABLE NAME ({select_statement[from_position+1]}) ON SELECT FROM:'+' '.join(select_statement))
            return False
        if not self.verify_if_table_exists(select_statement[from_position+1]):
                    print(F'(ERROR) NONEXISTENT TABLE NAME ({select_statement[from_position+1]}) ON SELECT:'+' '.join(select_statement))
                    return False

        return True

    def __validate_join(self, join_statement: list):
        join_pattern = re.compile(JOIN_REGEX)

        if not join_pattern.match(' '.join(join_statement)):
            print('(ERROR) INVALID JOIN STATEMENT (Verify Syntax):'+' '.join(join_statement))
            return False
        
        if join_statement[1] in operators:
            print(f'(ERROR) INVALID TABLE NAME ({join_statement[1]}) IN JOIN STATEMENT:'+' '.join(join_statement))
            return False
        if not self.verify_if_table_exists(join_statement[1]):
            print(F'(ERROR) NONEXISTENT TABLE NAME ({join_statement[1]}) IN JOIN STATEMENT:'+' '.join(join_statement[1]))
            return False

        if "ON" in join_statement:
            on_position = join_statement.index("ON")
            post_on_items = join_statement[on_position+1:]

            for idx, word in enumerate(post_on_items):
                if (idx % 2) == 0:
                    if word in operators:
                        print(f'(ERROR) MISPLACED OPERATOR ({word}) IN JOIN STATEMENT:'+' '.join(join_statement))
                        return False
                    if '.' not in word or word.count('.') > 1:
                        print(f'(ERROR) INVALID OR EMPTY TABLE REFERENCE IN "JOIN ON" ARGUMENT ({word}) IN JOIN STATEMENT:'+' '.join(join_statement))
                        return False
                    
                    referece_sections = word.split('.')

                    if not self.verify_if_table_exists(referece_sections[0]):
                        print(F'(ERROR) NONEXISTENT TABLE NAME ({referece_sections[0]}) IN JOIN STATEMENT:'+referece_sections[0])
                        return False
                    if not self.verify_if_column_exists(referece_sections[1], referece_sections[0]):
                        print(F'(ERROR) NONEXISTENT COLUMN NAME ({referece_sections[1]}) IN JOIN STATEMENT:'+referece_sections[1])
                        return False

                elif (idx % 2) == 1:
                    if word not in operators:
                        print(f'(ERROR) INVALID OPERATOR ({word}) IN JOIN STATEMENT:'+' '.join(join_statement))
                        return False
        return True


    def __validate_where(self, where_statement: list):
        where_pattern = re.compile(WHERE_REGEX)

        if not where_pattern.match(' '.join(where_statement)):
            print('(ERROR) INVALID WHERE STATEMENT (Verify Syntax):'+' '.join(where_statement))
            return False
        
        post_where_items = where_statement[1:]
        
        for idx, word in enumerate(post_where_items):
                if (idx % 2) == 0:
                    if word in operators:
                        print(f'(ERROR) MISPLACED OPERATOR ({word}) IN WHERE:'+where_statement)
                        return False
                    if not self.verify_if_column_exists(word):
                        print(F'(ERROR) NONEXISTENT COLUMN NAME ({word}) IN WHERE:'+' '.join(word))
                        return False

                elif (idx % 2) == 1:
                    if word not in operators:
                        print(f'(ERROR) INVALID OPERATOR ({word}) IN WHERE:'+where_statement)
                        return False
                    
        return True
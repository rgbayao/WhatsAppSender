import sqlite3

PRIMARY_COL = 'celular'

TEMPLATE_TABLE = "templates"

CONFIG_TABLE = "configurations"

CREATE = "CREATE"
IF_NOT_EXISTS = "IF NOT EXISTS"
TABLE = "TABLE"
TEXT_TYPE = "TEXT"
INT_TYPE = "INTEGER"
REAL_TYPE = "REAL"
INSERT = "INSERT INTO"
VALUES = "VALUES"
SELECT = "SELECT"
SELECT_ALL = "SELECT * FROM"
FROM = "FROM"
UPDATE = "UPDATE"
DELETE = "DELETE"
WHERE = "WHERE"
AND = "AND"
OR = "OR"
PRIMARY_KEY = "PRIMARY KEY"
SET = "SET"


def concat_words(*args):
    return " ".join(args)


def create_columns_types_parameter(params):
    cols = []
    for i in params.keys():
        col = concat_words(i, params[i])
        cols.append(col)
    s = ",".join(cols)
    return "(" + s + ")"


def create_if_not_exists(table_name, **kwargs):
    params = create_columns_types_parameter(kwargs)
    return concat_words(CREATE, TABLE, IF_NOT_EXISTS, table_name, params)


def and_clauses(*args):
    return " AND ".join(args)


def or_clauses(*args):
    return " OR ".join(args)


def equal_clauses(column_name, target_value):
    return str(column_name) + "=" + str(target_value)


def select_all_where(table_name, where_clause):
    return concat_words(SELECT_ALL, table_name, WHERE, where_clause)


def make_columns_table_specific(cols, table_name):
    return [table_name + "." + i for i in cols]


def select_cols_from_table(cols, table_name):
    return concat_words(SELECT, ",".join(make_columns_table_specific(cols, table_name)), FROM, table_name)


def insert_into_table(table_name, cols, values):
    return concat_words(INSERT, table_name, "({})".format(",".join([str(i) for i in cols])), VALUES,
                        "({})".format(",".join([str(i) for i in values])))


def delete_from_table_where(table_name, where_clause):
    return concat_words(DELETE, FROM, table_name, WHERE, where_clause)


class TextType:
    def __init__(self, string):
        self.string = string
        self.text = "'" + string + "'"

    def __str__(self):
        return self.text

    def __add__(self, other):
        return self.text + other

    def __radd__(self, other):
        return other + self.text


def update_where(table_name, params, where_clause):
    return concat_words(UPDATE, table_name, SET, params, WHERE, where_clause)


class SQLTable:
    def __init__(self):
        self.columns = []
        self.columns_types = {}
        self.default_values = [[]]


class TemplatesTable(SQLTable):
    def __init__(self):
        super().__init__()
        self.name = TEMPLATE_TABLE
        self.columns = ["_id", 'name', 'message', 'cols']
        self.columns_types = {"_id": concat_words(INT_TYPE, PRIMARY_KEY), "name": TEXT_TYPE,
                              "message": TEXT_TYPE, 'cols': TEXT_TYPE}
        self.default_values = [[1, TextType("Template Padrão"),
                                TextType("Todas tabelas devem conter a coluna celular.\n"
                                         "Essa mensagem vai para o número: {celular}"), TextType("celular")]]


class ConfigTable(SQLTable):
    def __init__(self):
        super().__init__()
        self.name = CONFIG_TABLE
        self.columns = ["_id", '_values']
        self.columns_types = {"_id": concat_words(TEXT_TYPE, PRIMARY_KEY), '_values': TEXT_TYPE}
        self.default_values = [["'sleeping_time'", "'15'"],
                               ["'date_format'", "'%d/%m/%Y'"],
                               ["'time_format'", "'%H:%M'"],
                               ["'number_of_attempts'", "'1'"]]


class SQLParser:
    def __init__(self, path_to_database):
        self.con = None
        self.cur = None
        self.tables = [TemplatesTable(), ConfigTable()]
        if path_to_database is not None:
            self.connect_to_db_and_start(path_to_database)

    def connect_to_db_and_start(self, path_to_database):
        self.con = sqlite3.connect(path_to_database)
        self.cur = self.con.cursor()
        self.start_db()

    def start_db(self):
        self.create_tables()
        self.set_tables_defaults()

    def create_tables(self):
        for table in self.tables:
            self.execute_and_commit(create_if_not_exists(table.name, **table.columns_types))

    def set_tables_defaults(self):
        for table in self.tables:
            for item in table.default_values:
                try:
                    self.execute_and_commit(insert_into_table(table.name, table.columns, item))
                except sqlite3.IntegrityError:
                    continue

    def get_all_config_as_dict(self):
        self.execute(concat_words(SELECT_ALL, CONFIG_TABLE))
        data = self.fetch_all()[0]
        configs = {}
        for line in data:
            configs[line[0]] = line[1]
        return configs

    def get_config(self, config_name):
        self.execute(select_all_where(CONFIG_TABLE, equal_clauses("_id", TextType(config_name))))
        return self.fetch_all()[0][1]

    def set_config(self, config_name, value):
        self.execute_and_commit(update_where(CONFIG_TABLE, equal_clauses("_values", TextType(value)),
                                             equal_clauses("_id", TextType(config_name))))

    def execute(self, statement):
        self.cur.execute(statement)

    def fetch_all(self):
        return self.cur.fetchall()

    def get_template_data_as_object(self, template_name):
        return ExistingTemplate(template_name, self)

    def get_template_data(self, template_name):
        self.execute(select_all_where(TEMPLATE_TABLE, equal_clauses("name", str(TextType(template_name)))))
        return self.fetch_all()[0]

    def get_template_data_by_id(self, _id):
        self.execute(select_all_where(TEMPLATE_TABLE, equal_clauses("_id", _id)))
        return self.fetch_all()[0]

    def update_template_by_id(self, _id, **kwargs):
        if len(kwargs) == 0:
            return
        s = ""
        for i in kwargs.keys():
            s += equal_clauses(i, TextType(kwargs.get(i)).text)
            s += ","
        params = s[:-1]
        self.execute_and_commit(update_where(TEMPLATE_TABLE, params, equal_clauses("_id", _id)))

    def get_template_names(self):
        self.execute(select_cols_from_table(["name"], TEMPLATE_TABLE))
        result = self.fetch_all()
        names = [i[0] for i in result]
        return names

    def is_table_empty(self, table_name):
        self.execute("SELECT COUNT(*) FROM " + table_name)
        b = self.fetch_all()[0][0]
        return True if b == 0 else False

    def execute_and_commit(self, statement):
        self.cur.execute(statement)
        self.con.commit()

    def add_template(self, template_name, message, cols):
        self.execute("SELECT MAX(_id) FROM " + TEMPLATE_TABLE)
        try:
            next_id = self.fetch_all()[0][0] + 1
        except TypeError:
            next_id = 1
        self.execute_and_commit(insert_into_table(TEMPLATE_TABLE, ["_id", "name", "message", "cols"],
                                                  [str(next_id), TextType(template_name).text, TextType(message).text,
                                                   TextType(cols).text]))

    def delete_template_by_id(self, id):
        self.execute_and_commit(delete_from_table_where(TEMPLATE_TABLE, equal_clauses("_id", id)))


class Template:
    def __init__(self):
        self.id = ""
        self.name = ""
        self.message = ""
        self.cols = []

    def __str__(self):
        return self.name

    def get_cols(self):
        return self.cols

    def get_message(self):
        return self.message


class TemplateParser(Template):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def add_new_template(self, name, message, cols):
        string_cols = ",".join
        self.db.add_template(name, message, cols)


class ExistingTemplate(Template):
    def __init__(self, template_name, db=None, ):
        super().__init__()
        self.db = db
        self.get_template(template_name, db)

    def get_template(self, template_name, db):
        template = db.get_template_data(template_name)
        self.attribute_values_from_data(template)

    def get_template_by_id(self, _id=None):
        if _id is None:
            _id = self.id
        template = self.db.get_template_data_by_id(_id)
        self.attribute_values_from_data(template)

    def attribute_values_from_data(self, template):
        self.id = template[0]
        self.name = template[1]
        self.message = template[2]
        self.cols = template[3].split(",")

    def edit_template(self, new_name, new_message, new_cols):
        self.db.update_template_by_id(self.id, name=new_name, message=new_message, cols=new_cols)
        self.get_template_by_id()

from whattsapp_sender.tools import sql_manipulator
from whattsapp_sender.tools.data_runner import *
from tkinter import *
from tkinter.ttk import *
import threading
import whattsapp_sender.application.application_commands as comm
from whattsapp_sender.tools.sql_manipulator import ExistingTemplate
from whattsapp_sender.tools.sql_manipulator import PRIMARY_COL

VERSION = "1.1.0"

COL_TAG_PATTERN = "(?<={).[^}|{]*(?=})"


class TemplateHandler:
    def __init__(self, parent):
        self.top = Toplevel(parent)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.create_widgets()
        self.pack_widgets()
        self.cols_names = []
        self.db = sql_manipulator.SQLParser(None)

    def set_db(self, db):
        self.db = db

    def format_cols_names_as_comma_string(self, key):
        s = comm.clean_columns_list_as_comma_string(self.cols_names_stringvar.get())
        if s == "":
            self.cols_names = []
        else:
            new_cols_names = s.split(",")
            try:
                new_cols_names.remove("")
            except ValueError:
                pass
            self.cols_names = new_cols_names
        self.cols_names_stringvar.set(s)
        self.tag_columns_in_message(None)

    def tag_columns_in_message(self, event):
        comm.clean_tags(self.txt_message)
        if len(self.cols_names) != 0:
            self.tag_message_text()

    def tag_message_text(self):
        text = self.txt_message.get("1.0", 'end')
        counter = 0
        for line in text.split("\n"):
            counter += 1
            it = re.finditer(COL_TAG_PATTERN, line)
            for match in it:
                if match.group() in self.cols_names:
                    self.txt_message.tag_add('ValCol', comm.build_tktext_index(counter, match.start()),
                                             comm.build_tktext_index(counter, match.end()))
                else:
                    self.txt_message.tag_add('InvCol', comm.build_tktext_index(counter, match.start()),
                                             comm.build_tktext_index(counter, match.end()))

    def create_widgets(self):
        self.ctn_template_name = Frame(self.top)
        self.lb_template_name = Label(self.ctn_template_name, text="Nome do template: ")
        self.ety_template_name = Entry(self.ctn_template_name)

        self.ctn_message = Frame(self.top)
        self.ctn_message_label = Frame(self.ctn_message)
        self.lb_message = Label(self.ctn_message_label, text="Mensagem: ")

        self.txt_message = Text(self.ctn_message, width=60, height=6)
        self.txt_message.bind("<KeyRelease>", self.tag_columns_in_message)
        self.txt_message.tag_configure("InvCol", foreground="red")
        self.txt_message.tag_configure("ValCol", foreground="blue")

        self.ctn_cols = Frame(self.top)
        self.lb_cols = Label(self.ctn_cols, text="Colunas - separadas por vírgula"
                                                 f" (obrigatório possuir coluna {PRIMARY_COL}):\n"
                                                 "Os nomes serão utilizados em letra minúscula e sem acentos")
        self.cols_names_stringvar = StringVar()
        self.cols_names_stringvar.set("")
        self.ety_cols = Entry(self.ctn_cols, textvariable=self.cols_names_stringvar)
        self.ety_cols.bind("<KeyRelease>", self.format_cols_names_as_comma_string)

    def pack_widgets(self):
        self.ctn_template_name.pack(side=TOP, fill=X, pady=(5, 5))
        self.ctn_cols.pack(side=TOP, fill=X, pady=(5, 5))
        self.ctn_message.pack(side=TOP, fill=X, pady=(5, 5))
        self.ctn_message_label.pack(side=TOP, fill=X)

        self.lb_template_name.pack(side=LEFT, padx=(10, 10))
        self.ety_template_name.pack(side=LEFT, fill=X, padx=(10, 10))

        self.lb_message.pack(side=LEFT, padx=(10, 10))
        self.txt_message.pack(side=TOP, padx=(10, 10))

        self.lb_cols.pack(side=TOP, padx=(10, 10))
        self.ety_cols.pack(side=TOP, fill=X, padx=(10, 10))

    def quit_dialog(self):
        self.top.destroy()

    def is_cols_consistent(self):
        cols = self.ety_cols.get().split(",")
        if not self.has_standard_col():
            messagebox.showerror("Erro", f'A coluna {PRIMARY_COL} é obrigatória e deve ser incluída')
            return False
        for i in cols:
            if not comm.is_word_repeated_in_list(i, cols):
                messagebox.showerror("Erro", "Não pode haver duas colunas com o mesmo nome.")
                return False
        return True

    def check_for_invalid_tags(self):
        if self.has_invalid_tags():
            messagebox.showerror("Erro", "Existem colunas erradas na mensagem. Todas devem estar na cor azul.")
            return True
        else:
            return False

    def has_invalid_tags(self):
        return True if len(self.txt_message.tag_ranges('InvCol')) > 0 else False

    def check_if_has_empty_fields(self):
        if self.has_empty_fields():
            messagebox.showerror("Erro", "Há campos vazios.")
            return True
        else:
            return False

    def has_empty_fields(self):
        if len(self.ety_template_name.get()) == 0 or \
                len(self.txt_message.get('1.0', 'end')) == 0 or \
                len(self.ety_cols.get()) == 0:
            return True
        else:
            return False

    def has_standard_col(self):
        if PRIMARY_COL in self.cols_names:
            return True
        else:
            return False

    def check_if_name_is_valid(self):
        names = self.db.get_template_names()
        current_name = self.ety_template_name.get().rstrip()
        if current_name in names:
            messagebox.showerror("Erro", f"O nome {current_name} já está em uso.")
            return False
        else:
            return True

    def check_template_entries(self):
        if not self.is_cols_consistent():
            return False
        elif self.check_for_invalid_tags():
            return False
        elif self.check_if_has_empty_fields():
            return False
        elif not self.check_if_name_is_valid():
            return False
        return True

    def clean_entries(self):
        self.ety_template_name.delete(0, 'end')
        self.cols_names_stringvar.set("")
        self.txt_message.delete("1.0", 'end')

    def disable_entries(self):
        self.ety_template_name['state'] = DISABLED
        self.ety_cols['state'] = DISABLED
        self.txt_message['state'] = DISABLED

    def enable_entries(self):
        self.ety_template_name['state'] = NORMAL
        self.ety_cols['state'] = NORMAL
        self.txt_message['state'] = NORMAL


class NewTemplate(TemplateHandler):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_buttons()
        self.pack_buttons()
        self.cols_names_stringvar.set(PRIMARY_COL)
        self.cols_names.append(PRIMARY_COL)
        self.new_template = None

    def create_buttons(self):
        self.ctn_buttons = Frame(self.top)
        self.btn_add = Button(self.top, text="Adicionar", command=self.add_template)
        self.btn_cancel = Button(self.top, text="Cancelar", command=self.quit_dialog)

    def pack_buttons(self):
        self.ctn_buttons.pack(side=TOP, fill=X, expand=1)
        self.btn_add.pack(side=LEFT, fill=X, expand=1, pady=(5, 5))
        self.btn_cancel.pack(side=LEFT, fill=X, expand=1, pady=(5, 5))

    def add_template(self):
        if not self.check_template_entries():
            return
        else:
            self.db.add_template(self.ety_template_name.get().rstrip(),
                                 self.txt_message.get('1.0', 'end'),
                                 self.cols_names_stringvar.get())
            self.new_template = self.db.get_template_data_as_object(self.ety_template_name.get().rstrip())
            self.quit_dialog()


class EditTemplate(TemplateHandler):
    def __init__(self, parent, template):
        super().__init__(parent)
        self.template = template
        self.create_buttons()
        self.pack_buttons()
        self.ety_template_name.insert(index=0, string=self.template.name)
        self.cols_names_stringvar.set(",".join(self.template.cols))
        self.cols_names = [i for i in self.template.cols]
        self.txt_message.insert('1.0', self.template.message)
        self.tag_columns_in_message(None)

    def create_buttons(self):
        self.ctn_buttons = Frame(self.top)
        self.btn_edit = Button(self.top, text="Editar", command=self.edit_template)
        self.btn_cancel = Button(self.top, text="Cancelar", command=self.quit_dialog)

    def pack_buttons(self):
        self.ctn_buttons.pack(side=TOP, fill=X, expand=1)
        self.btn_edit.pack(side=LEFT, fill=X, expand=1, pady=(5, 5))
        self.btn_cancel.pack(side=LEFT, fill=X, expand=1, pady=(5, 5))

    def check_if_name_is_valid(self):
        names = self.db.get_template_names()
        current_name = self.ety_template_name.get().rstrip()
        other_names = [i for i in names if i != self.template.name]
        if current_name in other_names:
            messagebox.showerror("Erro", f"O nome {current_name} já está em uso.")
            return False
        else:
            return True

    def edit_template(self):
        if not self.check_template_entries():
            return
        else:
            self.template.edit_template(self.ety_template_name.get(), self.txt_message.get('1.0', 'end'),
                                        self.cols_names_stringvar.get())
        self.quit_dialog()


class RemoveTemplate(TemplateHandler):
    def __init__(self, parent, templates_list):
        self.templates = templates_list
        super().__init__(parent)
        self.active_template = None
        self.disable_entries()
        self.active_template = None

    def select_template(self, event):
        self.enable_entries()
        template_name = self.cb_templates.get()
        self.clean_entries()
        self.active_template = ExistingTemplate(template_name, self.db)
        self.ety_template_name.insert(0, self.active_template.name)
        self.txt_message.insert('1.0', self.active_template.message)
        self.cols_names_stringvar.set(",".join(self.active_template.cols))
        self.disable_entries()

    def create_widgets(self):
        super().create_widgets()
        self.ctn_cb_templates = Frame(self.top)
        self.cb_templates = Combobox(self.ctn_cb_templates, state='readonly', values=self.templates)
        self.cb_templates.bind('<<ComboboxSelected>>', self.select_template)

        self.ctn_buttons = Frame(self.top)
        self.btn_delete = Button(self.top, text="Deletar", command=self.delete_template)
        self.btn_cancel = Button(self.top, text="Cancelar", command=self.quit_dialog)

    def pack_widgets(self):
        self.ctn_cb_templates.pack(side=TOP, expand=1, pady=(5, 5), fill=X)
        self.cb_templates.pack(side=LEFT, padx=(5, 5))
        super().pack_widgets()

        self.ctn_buttons.pack(side=TOP, fill=X, expand=1)
        self.btn_delete.pack(side=LEFT, fill=X, expand=1, pady=(5, 5))
        self.btn_cancel.pack(side=LEFT, fill=X, expand=1, pady=(5, 5))

    def delete_template(self):
        if self.active_template is None:
            return
        self.db.delete_template_by_id(self.active_template.id)
        self.quit_dialog()


class ConfigurationsMenu:
    def __init__(self, parent):
        self.top = Toplevel(parent)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.data_formats = ["31/12/99", "31/12/1999", "31/12", "12/99", "12/1999"]
        self.data_formats_parser = {"31/12/99": "%d/%m/%y",
                                    "31/12/1999": "%d/%m/%Y",
                                    "31/12": "%d/%y",
                                    "12/99": "%m/%y",
                                    "12/1999": "%m/%Y"}
        self.time_formats = ["24:59:59", "24:59", "12:59:59 pm", "12:59 pm"]
        self.time_formats_parser = {"24:59:59": "%H:%M:%S",
                                    "24:59": "%H:%M",
                                    "12:59:59 pm": "%I:%M:%S %p",
                                    "12:59 pm": "%I:%M %p"}
        self.create_widgets()
        self.pack_widgets()
        self.db = None

    def set_db(self, db):
        self.db = db
        self.fill_values()

    def fill_values(self):
        sleeping_time = self.db.get_config("sleeping_time")
        date_format = self.db.get_config("date_format")
        time_format = self.db.get_config("time_format")
        number_of_attempts = self.db.get_config("number_of_attempts")

        self.ety_sleeping_time.insert(0, sleeping_time)

        self.ety_num_of_attempts.insert(0, number_of_attempts)

        for key, value in self.data_formats_parser.items():
            if date_format == value:
                index = self.data_formats.index(key)
                self.cb_data_format.current(index)
        for key, value in self.time_formats_parser.items():
            if time_format == value:
                index = self.time_formats.index(key)
                self.cb_time_format.current(index)

    def create_widgets(self):
        # self.ctn_sleeping_time = Frame(self.top)
        # self.ctn_time_format = Frame(self.top)
        # self.ctn_data_format = Frame(self.top)

        self.lb_sleeping_time = Label(self.top, text="Tempo entre mensagens (s):")
        self.ety_sleeping_time = Entry(self.top)

        self.lb_data_format = Label(self.top, text="Formato de variáveis de data:")
        self.cb_data_format = Combobox(self.top, values=self.data_formats, state='readonly')

        self.lb_time_format = Label(self.top, text="Formato de variáveis de hora:")
        self.cb_time_format = Combobox(self.top, values=self.time_formats, state='readonly')

        self.lb_num_of_attempts = Label(self.top, text="Número de tentativas: ")
        self.ety_num_of_attempts = Entry(self.top)

        self.ctn_buttons = Frame(self.top)
        self.btn_save = Button(self.ctn_buttons, text="Salvar", command=self.save_configs)
        self.btn_cancel = Button(self.ctn_buttons, text="Cancelar", command=self.quit_dialog)

    def pack_widgets(self):
        self.lb_sleeping_time.grid(row=0, column=0, padx=(5, 5), pady=(5, 5))
        self.ety_sleeping_time.grid(row=0, column=1, padx=(5, 5), pady=(5, 5))

        self.lb_data_format.grid(row=1, column=0, padx=(5, 5), pady=(5, 5))
        self.cb_data_format.grid(row=1, column=1, padx=(5, 5), pady=(5, 5))

        self.lb_time_format.grid(row=2, column=0, padx=(5, 5), pady=(5, 5))
        self.cb_time_format.grid(row=2, column=1, padx=(5, 5), pady=(5, 5))

        self.lb_num_of_attempts.grid(row=3, column=0, padx=(5, 5), pady=(5, 5))
        self.ety_num_of_attempts.grid(row=3, column=1, padx=(5, 5), pady=(5, 5))

        self.ctn_buttons.grid(row=4, column=0, columnspan=2, pady=(5, 5), sticky='ew')
        self.btn_save.pack(side=LEFT, expand=1, fill=X)
        self.btn_cancel.pack(side=LEFT, expand=1, fill=X)

    def quit_dialog(self):
        self.top.destroy()

    def save_configs(self):
        if (not self.ety_sleeping_time.get().isdigit()) or \
                (not self.ety_num_of_attempts.get().isdigit()):
            messagebox.showerror("Error", '"Tempo entre mensagens" e "Número de tentativas" dever ser números')
            return

        self.db.set_config("sleeping_time", self.ety_sleeping_time.get())
        self.db.set_config("date_format", self.data_formats_parser[self.cb_data_format.get()])
        self.db.set_config("time_format", self.time_formats_parser[self.cb_time_format.get()])
        self.db.set_config("number_of_attempts", self.ety_num_of_attempts.get())
        self.quit_dialog()


class Application(Frame):
    def __init__(self, master=None, db=None, base_path=None):
        super().__init__(master, width=450)
        self.master = master
        self.master.title("Mensagens autom. WhattsApp - Versão: " + VERSION)
        self.db = db
        self.templates = []
        self.active_template = None
        self.get_templates()
        self.pack()
        self.create_widgets()
        self.pack_widgets()
        self.sender = Sender(None, self.active_template)
        self.data = DataSource(None)
        if base_path is not None:
            Sender.base_path = base_path
            DataSource.base_path = base_path

    def get_templates(self):
        templates_names = self.db.get_template_names()
        self.templates = [ExistingTemplate(i, self.db) for i in templates_names]
        self.active_template = self.templates[0]

    def create_widgets(self):
        self.create_menu()

        # Defining containers
        self.ctn_template_selec = Frame(self.master)
        self.lb_template = Label(self.ctn_template_selec, text="Escolha o template: ")
        self.cb_template_selection = Combobox(self.ctn_template_selec, state='readonly', values=self.templates)
        self.cb_template_selection.bind('<<ComboboxSelected>>', self.select_template)
        self.cb_template_selection.current(0)

        self.ctn_reader = Frame(self.master)
        # Progress bar reading
        self.barFileReading = Progressbar(self.ctn_reader, orient=HORIZONTAL, length=300, mode='indeterminate')
        # Reading container widgets
        self.reading_status = StringVar()

        self.ctn_reader_buttons = Frame(self.ctn_reader)
        self.reading_status.set("Por favor, selecione um arquivo.")
        self.lbFileReading = Label(self.ctn_reader_buttons, textvariable=self.reading_status)

        self.btnDataSetChooser = Button(self.ctn_reader_buttons, command=self.start_reading, text="Selecionar")

        self.ctn_sender = Frame(self.master)
        self.ctn_sender_buttons = Frame(self.ctn_sender)

        self.sending_status = StringVar()
        self.sending_status.set("Clique para iniciar o envio.")
        self.lbSendMessages = Label(self.ctn_sender_buttons, textvariable=self.sending_status)

        self.barMessageSend = Progressbar(self.ctn_sender, orient=HORIZONTAL, length=300, mode='indeterminate')

        self.btnSendMessages = Button(self.ctn_sender_buttons, command=self.send_messages, text='Enviar mensagens',
                                      state="disabled")

    def select_template(self, event):
        selected = self.cb_template_selection.get()
        for i in self.templates:
            if selected == i.name:
                self.active_template = i

    def get_data(self):
        return self.data

    def start_reading(self):
        self.data = DataSource(None)
        self.btnSendMessages["state"] = "disabled"

        comm.run_progress_bar(self.barFileReading, self.get_data, self.reading_status, )

        data = comm.read_table()

        if data is None:
            self.data = DataSource(None)
        else:
            self.data = DataSource(comm.prepare_data_cols(data, self.active_template.cols))

        # self.data = comm.get_data(self.active_template.cols)

        if not self.data.error and self.data.error is not None:
            self.btnSendMessages["state"] = "active"
        else:
            self.data.error = True

        self.barFileReading.pack_forget()

    def get_sender(self):
        return self.sender

    def send_messages(self):
        self.sender = Sender(self.data, self.active_template)
        self.sender.sleeping_time = int(self.db.get_config("sleeping_time"))
        self.sender.date_format = self.db.get_config("date_format")
        self.sender.time_format = self.db.get_config("time_format")
        self.sender.num_of_tries = int(self.db.get_config("number_of_attempts"))
        self.btnSendMessages["state"] = "disabled"

        t = threading.Thread(target=comm.execute_progress_bar,
                             args=(self.barMessageSend, self.get_sender, self.sending_status,))
        t.daemon = True
        t.start()

        t1 = threading.Thread(target=self.sender.prepare_and_send_all)
        t1.daemon = True
        t1.start()

    def pack_widgets(self):
        self.ctn_template_selec.pack(side=TOP, pady=(5, 5), expand=1, fill=X)
        self.ctn_reader.pack(side=TOP, pady=(10, 10), expand=1, fill=X)
        self.ctn_reader_buttons.pack(side=TOP, expand=1, fill=X)
        self.ctn_sender.pack(side=TOP, pady=(10, 10), expand=1, fill=X)
        self.ctn_sender_buttons.pack(side=TOP, expand=1, fill=X)

        self.lb_template.pack(side=LEFT, padx=(10, 10))
        self.cb_template_selection.pack(side=LEFT, padx=(10, 10))

        self.btnDataSetChooser.pack(side=LEFT, padx=(10, 10))
        self.lbFileReading.pack(side=LEFT, padx=(10, 10))
        self.barFileReading.pack(side=TOP, padx=(10, 10))
        self.barFileReading.pack_forget()

        self.btnSendMessages.pack(side=LEFT, padx=(10, 10))
        self.lbSendMessages.pack(side=LEFT, padx=(10, 10))
        self.barMessageSend.pack(side=TOP, padx=(10, 10))
        self.barMessageSend.pack_forget()

    def create_menu(self):
        self.menu_bar = Menu()
        self.create_file_menu()
        self.create_options_menu()
        self.master.config(menu=self.menu_bar)

    def create_file_menu(self):
        self.menu_file = Menu(self.menu_bar)
        self.menu_file.add_command(label="Novo template", command=self.open_new_template_dialog)
        self.menu_file.add_command(label="Editar templates", command=self.edit_selected_template)
        self.menu_file.add_command(label="Excluir template", command=self.delete_template)
        self.menu_file.add_command(label="Sair")

        self.menu_bar.add_cascade(label="File", menu=self.menu_file)

    def create_options_menu(self):
        self.menu_options = Menu(self.menu_bar)
        self.menu_options.add_command(label="Editar configurações...", command=self.open_configurations)

        self.menu_bar.add_cascade(label="Opções", menu=self.menu_options)

    def open_configurations(self):
        diag = ConfigurationsMenu(self.master)
        diag.set_db(self.db)

        self.master.wait_window(diag.top)

    def open_new_template_dialog(self):
        diag = NewTemplate(self.master)
        diag.set_db(self.db)
        self.master.wait_window(diag.top)
        new_template = diag.new_template
        if new_template is None:
            return
        else:
            self.templates.append(new_template)
            new_list = [i for i in self.cb_template_selection['values']]
            new_list.append(new_template.name)
            self.cb_template_selection['values'] = new_list

    def edit_selected_template(self):
        diag = EditTemplate(self.master, self.active_template)
        diag.set_db(self.db)
        self.master.wait_window(diag.top)
        self.get_templates()
        self.cb_template_selection['values'] = self.templates
        self.cb_template_selection.current(0)

    def delete_template(self):
        diag = RemoveTemplate(self.master, self.templates)
        diag.set_db(self.db)
        self.master.wait_window(diag.top)
        self.get_templates()
        self.cb_template_selection['values'] = self.templates
        self.cb_template_selection.current(0)

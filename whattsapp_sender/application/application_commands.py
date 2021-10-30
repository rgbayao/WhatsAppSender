from tkinter import filedialog as fd
import pandas as pd
import time
import threading
from tkinter import messagebox
from whattsapp_sender.tools.string_manipulation import *

from whattsapp_sender.tools.data_runner import DataSource


def run_progress_bar(bar, subject, message=None):
    t = threading.Thread(target=execute_progress_bar,
                         args=(bar, subject, message,))
    t.daemon = True
    t.start()


def open_file():
    filetypes = (
        ('Excel files', '*.xls *.xlsx'),
        ('All files', '*.*')
    )
    filename = fd.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)

    return filename


def normalize_data_columns(data):
    cols = []
    for i in data.columns:
        cols.append(normalize_string(i))
    data.columns = cols


def replace_columns_with_target_names(data, target_cols):
    new_columns = []
    for col_name in data.columns:
        match = match_any_target_word_in_string(col_name, target_cols)
        if match is not None:
            new_columns.append(match)
        else:
            new_columns.append(col_name)
    data.columns = new_columns


def read_table():
    filename = open_file()
    if filename is None or filename == ():
        return None
    try:
        df = pd.read_excel(filename)
    except Exception:
        messagebox.showerror("Error", "Não foi possível ler o arquivo, tente novamente")
        df = None
    return df


def check_source_uniqueness_in_list(source, list_to_iterate):
    for i in source:
        if not is_word_repeated_in_list(i, list_to_iterate):
            messagebox.showerror("Error", "As palavras chaves só devem aparecer apenas uma vez nas colunas."
                                          f'\nHouve repetição da palavra: "{i}"')
            return False
    return True


def prepare_data_cols(data, target_cols):
    normalize_data_columns(data)
    if not check_source_uniqueness_in_list(target_cols, data.columns):
        return None
    replace_columns_with_target_names(data, target_cols)
    return data


def get_data(target_cols):
    data = read_table()
    if data is None:
        return DataSource(None)
    return DataSource(prepare_data_cols(data, target_cols))


def move_bar(bar, subject):
    to_right = True

    def finish_condition():
        return subject().has_finished() or subject().has_error()

    aux = finish_condition()
    while not aux:
        if to_right:
            bar['value'] += 1
            if bar['value'] == 100:
                to_right = False
            time.sleep(0.01)
            aux = finish_condition()
            continue
        else:
            bar['value'] -= 1
            if bar['value'] == 0:
                to_right = True
            time.sleep(0.01)
            aux = finish_condition()
            continue


def move_bar_without_message(bar, subject):
    move_bar(bar, subject)
    bar.pack_forget()


def move_bar_with_message(bar, subject, textvariable):
    textvariable.set("Processando...")
    move_bar(bar, subject)
    bar.pack_forget()
    if subject().has_error():
        textvariable.set("Por favor selecione um arquivo válido.")
    else:
        textvariable.set("Finalizado.")


def execute_progress_bar(bar, subject, textvariable):
    bar.pack()
    if textvariable is None:
        move_bar_without_message(bar, subject)
    else:
        move_bar_with_message(bar, subject, textvariable)


def clean_columns_list_as_comma_string(string):
    s = normalize_string(string)
    return s.rstrip().replace("{", "").replace("}", "")


def clean_tags(tk_text):
    tags = tk_text.tag_names()
    for tag in tags:
        tk_text.tag_remove(tag, '1.0', 'end')


def build_tktext_index(line, chars):
    return str(line) + ".0+" + str(chars) + "c"

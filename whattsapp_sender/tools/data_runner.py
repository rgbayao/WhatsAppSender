import re
from tkinter import messagebox
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException
import time
import datetime
import urllib
import traceback
import os


def get_ddi(i):
    if i[0] == "+":
        return i.split("(")[0]
    else:
        return "+55"


def get_ddd(number):
    str_search = re.search("(?<=\()\d+(?=\))", number)
    if str_search is not None:
        return str_search.group()
    elif number[:3] == "+55":
        return number[3:5]
    elif number[0] != "+":
        return number[:2]


def get_cellphone(number):
    return number.replace("-", "")[-9:]


def get_cellphone_without_extra_9(number):
    return get_cellphone(number)[1:]


class DataSource(object):
    def __init__(self, data):
        if data is None:
            self.error = None
            self.was_read = None
        else:
            try:
                self.data = data[data["celular"].notna()]
                self.data.reset_index(drop=True, inplace=True)
                self.error = False
            except Exception:
                self.error = True
            self.was_read = True
            self.DDD = []
            self.DDI = []
            self.NUM = []
            self.fill_number_list()

    def has_finished(self):
        return self.was_read

    def has_error(self):
        return self.error

    def fill_number_list(self):
        for i in self.data.loc[:, 'celular']:
            cel_without_blank = i.replace(" ", "")
            self.DDI.append(get_ddi(cel_without_blank))
            self.DDD.append(get_ddd(cel_without_blank))
            self.NUM.append(get_cellphone_without_extra_9(cel_without_blank))


class Sender:
    def __init__(self, data, template):
        self.data_source = data
        self.cols = template.cols
        self.message = template.message
        self.sent_all = False
        self.error = False
        self.date_columns = []
        self.time_columns = []
        self.errors_index = []
        self.num_of_tries = 1
        self._num_of_tries = 0
        self.date_format = "%d/%m/%Y"
        self.time_format = "%H:%M"
        self.sleeping_time = 15
        self.navigator = None
        self.link = ""
        self.text = ""

    def has_finished(self):
        return self.sent_all

    def has_error(self):
        return self.error

    def start_navigator(self):
        if os.path.exists("../../chromedriver.exe"):
            self.navigator = webdriver.Chrome(executable_path="../../chromedriver.exe")
        elif os.path.exists("../../chromedriver"):
            self.navigator = webdriver.Chrome(executable_path="../../chromedriver.exe")
        else:
            raise FileNotFoundError("Can't find chromedriver in main.py folder")

        self.navigator.get("http://web.whatsapp.com/")
        while len(self.navigator.find_elements_by_id("side")) < 1:
            time.sleep(0.5)

    def prepare_and_send_all(self):
        self.sent_all = False

        self.find_date_and_time_columns()

        self.show_preview()

        if not self.should_continue:
            self.sent_all = True
            return

        try:
            self.start_navigator()
        except FileNotFoundError:
            messagebox.showerror("Error", "O arquivo chromedriver não foi encontrado na pasta que se encontra main.py")
            self.error = True
            return

        self.send_messages()

        self.sent_all = True
        self.navigator.quit()

    def show_preview(self):
        text = self.prepare_message(0)
        text += "\n\nDeseja continuar?"
        self.should_continue = messagebox.askyesno("Pré-visualização da menssagem", message=text)

    def find_date_and_time_columns(self):
        for i in self.cols:
            if isinstance(self.data_source.data[i][0], pd.Timestamp):
                self.date_columns.append(i)
            elif isinstance(self.data_source.data[i][0], datetime.time):
                self.time_columns.append(i)

    def prepare_vars(self, index):
        vars_dict = dict()
        for i in self.cols:
            if i in self.date_columns:
                try:
                    col_data = self.data_source.data.loc[index, i].strftime(self.date_format)
                except AttributeError:
                    col_data = self.data_source.data.loc[index, i]
            elif i in self.time_columns:
                try:
                    col_data = self.data_source.data.loc[index, i].strftime(self.time_format)
                except AttributeError:
                    col_data = self.data_source.data.loc[index, i]
            else:
                col_data = self.data_source.data.loc[index, i]
            vars_dict[i] = col_data
        return vars_dict

    def send_messages(self, index=None):
        if index is None:
            data_to_send = self.data_source.data
        else:
            errors_index = [i for i in self.errors_index]
            data_to_send = self.data_source.data.loc[errors_index]

        self.errors_index = []

        for index, row in data_to_send.iterrows():
            self.text = self.prepare_message(index)

            number = self.data_source.DDI[index] + self.data_source.DDD[index] + self.data_source.NUM[index]

            self.open_whatsapp_dialog(number, self.text)

            self.send_prepared_message(index)

            time.sleep(self.sleeping_time)

        self._num_of_tries += 1
        if len(self.errors_index) > 0:
            today = datetime.date.today()
            with open("erros_" + today.strftime("%d_%m_%y") + ".txt", "a") as file:
                file.write(f"\nFIM DA TENTATIVA {self._num_of_tries} - TOTAL DE ERRORS = {len(self.errors_index)}")
                file.write("\n\n")

            print(self.errors_index)
            if self.num_of_tries > self._num_of_tries:
                with open("erros_" + today.strftime("%d_%m_%y") + ".txt", "a") as file:
                    file.write(f"COMEÇANDO TENTATIVA {self._num_of_tries + 1}")
                    file.write("\n")
                self.send_messages(index=self.errors_index)

    def prepare_message(self, index):
        vars_dict = self.prepare_vars(index)
        text = self.message

        for i in self.cols:
            text = text.replace('{' + str(i) + '}', str(vars_dict[i]))
        return text

    def open_whatsapp_dialog(self, number, text):
        formatted_text = urllib.parse.quote(text)
        self.link = f"http://web.whatsapp.com/send?phone={number}&text={formatted_text}"

        self.navigator.get(self.link)

        b = 0
        while b < 1:
            try:
                a = self.navigator.find_elements_by_id("side")
                b = len(a)
            except UnexpectedAlertPresentException:
                today = datetime.date.today()
                with open("log_" + today.strftime("%d_%m_%y"), "a") as file:
                    file.write(traceback.format_exc())
                    file.write("\n")
                continue
            time.sleep(0.5)

    def send_prepared_message(self, index):
        try:
            time.sleep(5)
            self.navigator.find_element_by_xpath(
                '//*[@id="main"]/footer/div[1]/div/div/div[2]/div[1]/div/div[2]').send_keys(
                Keys.ENTER)
            return True
        except NoSuchElementException:
            self.errors_index.append(index)
            try:
                today = datetime.date.today()
                with open("erros_" + today.strftime("%d_%m_%y") + ".txt", "a") as file:
                    complete_number = self.data_source.DDI[index] + self.data_source.DDD[index] \
                                      + "9" + self.data_source.NUM[index]
                    file.write(f"{index} - Falha ao enviar para número: {complete_number} | dados: \n" +
                               str(self.data_source.data.loc[index]))
                    file.write("\n")
                    file.write("Texto: \n" + self.text + "\n")
                    file.write("Link: " + self.link + "\n")

            except IOError:
                pass
            except Exception as e:
                today = datetime.date.today()
                with open("log_" + today.strftime("%d_%m_%y"), "a") as file:
                    file.write(traceback.format_exc())
                    file.write("\n")
        except Exception as e:
            self.errors_index.append(index)
            today = datetime.date.today()
            with open("log_" + today.strftime("%d_%m_%y"), "a") as file:
                file.write(traceback.format_exc())
                file.write("\n")
        return False

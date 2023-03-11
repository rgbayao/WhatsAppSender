import re
from tkinter import messagebox
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
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
    base_path = '.'
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
    base_path = '.'
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
        self.first_try=True

        self.html_class_name_file_path = 'html_class_name_wpp'
        self.html_class_name = None

        self.end_run = False

    def has_finished(self):
        return self.sent_all

    def has_error(self):
        return self.error

    def start_navigator(self):
        if os.path.exists(os.path.join(Sender.base_path, "chromedriver.exe")):
            self.navigator = webdriver.Chrome(executable_path=os.path.join(Sender.base_path, "chromedriver.exe"))
        elif os.path.exists("../../chromedriver"):
            self.navigator = webdriver.Chrome(executable_path="chromedriver")
        else:
            raise FileNotFoundError("Can't find chromedriver in ./configs/ folder")

        self.navigator.get("http://web.whatsapp.com/")
        #while len(self.navigator.find_elements_by_id("side")) < 1:
        while len(self.navigator.find_elements(By.ID, "side")) < 1:
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
            messagebox.showerror("Error", "O arquivo chromedriver não foi encontrado na pasta ./.configs/")
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

            if self.end_run:
                return

            time.sleep(self.sleeping_time)

        self._num_of_tries += 1
        if len(self.errors_index) > 0:
            today = datetime.date.today()
            with open(os.path.join(Sender.base_path, "erros_" + today.strftime("%d_%m_%y") + ".txt"), "a") as file:
                file.write(f"\nFIM DA TENTATIVA {self._num_of_tries} - TOTAL DE ERRORS = {len(self.errors_index)}")
                file.write("\n\n")

            print(self.errors_index)
            if self.num_of_tries > self._num_of_tries:
                with open(os.path.join(Sender.base_path, "erros_" + today.strftime("%d_%m_%y") + ".txt"), "a") as file:
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
                # a = self.navigator.find_elements_by_id("side")
                a = self.navigator.find_elements(By.ID, "side")
                b = len(a)
            except UnexpectedAlertPresentException:
                self.write_log_error()
                continue
            time.sleep(0.5)

    def send_prepared_message(self, index):
        try:
            if self.first_try:
                self.handle_html_class()

            b = 0
            while b < 1:
                try:
                    a = self.navigator.find_element(By.XPATH,
                            f'//*[@id="main"]/footer//div[@class="{self.html_class_name}"]')
                    b=1
                except NoSuchElementException:
                    time.sleep(0.5)
                    continue
                except UnexpectedAlertPresentException:
                    self.write_log_error()
                    continue
                time.sleep(0.5)

            self.navigator.find_element(By.XPATH,
                f'//*[@id="main"]/footer//div[@class="{self.html_class_name}"]').send_keys(
                Keys.ENTER)
            return True
        except NoSuchElementException:
            self.errors_index.append(index)
            self.write_send_error(index)
        except Exception as e:
            self.errors_index.append(index)
            self.write_log_error()
        return False

    def write_send_error(self, index):
        try:
            today = datetime.date.today()
            with open(os.path.join(Sender.base_path, "erros_" + today.strftime("%d_%m_%y") + ".txt"), "a") as file:
                complete_number = self.data_source.DDI[index] + self.data_source.DDD[index] \
                                  + "9" + self.data_source.NUM[index]
                file.write(f"{index} - Falha ao enviar para número: {complete_number} | dados: \n" +
                           str(self.data_source.data.loc[index]))
                file.write("Texto: \n" + self.text + "\n")
                file.write("Link:\n" + self.link + "\n\n")
        except IOError:
            pass
        except Exception as e:
            today = datetime.date.today()
            with open(os.path.join(Sender.base_path, "log_" + today.strftime("%d_%m_%y")), "a") as file:
                file.write(traceback.format_exc())
                file.write("\n\n")

    def write_log_error(self):
        today = datetime.date.today()
        with open(os.path.join(Sender.base_path, "log_" + today.strftime("%d_%m_%y")), "a") as file:
            file.write(traceback.format_exc())
            file.write("\n")

    def handle_html_class(self):
        has_footer = -1
        while has_footer == -1:
            try:
                html_txt = self.navigator.page_source
                has_footer = html_txt.find('<footer')
            except Exception:
                self.write_log_error()
                continue
            time.sleep(0.5)


        with open(os.path.join(Sender.base_path, self.html_class_name_file_path), 'r', encoding='utf-8') as f:
            txt = f.readlines()
        txt = [i.replace("\n","") for i in txt]
        self.html_class_name = txt[-1]

        footer_idx = self.navigator.page_source.find('<footer')
        footer_txt = self.navigator.page_source[footer_idx:]

        is_same_name = re.search(self.html_class_name, footer_txt)
        if is_same_name is None:
            self.manage_html_class_name(html_section = footer_txt)
        # self.first_try = False
            

    def manage_html_class_name(self, html_section = None):
        if html_section is None:
            html = self.navigator.page_source
        else:
            html = html_section
        
        html_class_name_splited = self.html_class_name.split(' ')
        test_strings = self.html_class_name.split(' ')
        success = False

        while len(test_strings) > 3:
            match_group = '(?<=class=")[^"]*(' + ')[^"]*('.join(["|".join(html_class_name_splited) for i in test_strings]) + ')[^"]*(?=")'
            matches = re.findall(match_group, html)
            if len(matches)==1:
                success = True
                break
            elif len(matches)>1:
                break
            else:
                test_strings.pop()
        if success:
            match_string = '(?<=class=")[^"]*' + '[^"]*'.join(matches[0]) + '[^"]*(?=")'
            new_match = re.search(match_string, html)
            self.html_class_name = new_match[0]
            self.save_new_class_name()
            
        else:
            messagebox.showerror("Error", "Código 42: Tente fechar o programa e rodar novamente. Se o erro persistir contate o fornecedor para manutenção.\
                                            Lembre-se de informar o código do erro.")

    def save_new_class_name(self):
        with open(os.path.join(Sender.base_path, self.html_class_name_file_path), 'a', encoding='utf-8') as f:
            f.write('\n' + self.html_class_name)
            
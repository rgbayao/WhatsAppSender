from whattsapp_sender.tools.sql_manipulator import SQLParser
from whattsapp_sender.application.application_gui import Application
from tkinter import Tk
import os

if not os.path.exists(os.path.join('.', '.configs')):
    os.makedirs(os.path.join('.', '.configs'))

base_path = os.path.join('.', '.configs')


def main():
    root = Tk()
    db = SQLParser(os.path.join(base_path, "config.db"))
    app = Application(master=root, db=db, base_path=base_path)
    root.resizable(False, False)

    def on_closing():
        db.con.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()


if __name__ == '__main__':
    main()

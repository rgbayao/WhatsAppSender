from whattsapp_sender.tools.sql_manipulator import SQLParser
from whattsapp_sender.application.application_gui import Application
from tkinter import Tk


def main():
    root = Tk()
    db = SQLParser("config.db")
    app = Application(master=root, db=db)
    root.resizable(False, False)

    def on_closing():
        db.con.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()


if __name__ == '__main__':
    main()

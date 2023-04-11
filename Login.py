from tkinter import *
from tkinter import messagebox
from random import randint
import sqlite3
import re
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet
import random
import os
import win32api
import win32con
import string


# Creating SQLite3 database file
conn = sqlite3.connect('user_credentials.db')

conn.execute('''CREATE TABLE IF NOT EXISTS user_credentials
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             username TEXT NOT NULL,
             password TEXT NOT NULL,
             email TEXT NOT NULL,
             fernet_key TEXT NOT NULL);''')


# Hiding database file
cwd = os.getcwd()
filepath = os.path.join(cwd, 'user_credentials.db')
win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_HIDDEN)

# Creating main window
root = Tk()

# Centering main window to screen
window_width = 150
window_height = 370

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)

root.geometry('{}x{}+{}+{}'.format(window_width, window_height, x, y))
root.title("Login/Register App")
root.config(bg="black")
root.resizable(False, False)


# Text clearing functions for tkinter messages
def clear_error_message():
    error_label.config(text="")


def clear_success_message():
    success_label.config(text="")


# Registration function. Registers user after pushing register_button
def register_user():
    username = username_entry.get()
    password = password_entry.get()
    email = email_entry.get()

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        error_label.config(text="Invalid email\n address!")
        root.after(5000, clear_error_message)
        return

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_credentials WHERE username=?", (username,))
    result = cursor.fetchone()

    if result:
        error_label.config(text="Username already\n exists!")
        root.after(5000, clear_error_message)
    else:
        key = Fernet.generate_key()

        encoded_key = key

        hashed_password = hashlib.sha256((password + username).encode()).hexdigest()

        conn.execute("INSERT INTO user_credentials (username, password, email, fernet_key) VALUES (?, ?, ?, ?)",
                     (username, hashed_password, email, encoded_key))
        conn.commit()
        success_label.config(text="Registration successful!")
        root.after(5000, clear_success_message)

    username_entry.delete(0, END)
    password_entry.delete(0, END)
    email_entry.delete(0, END)


# Login function. Logs in user after pushing login_button
def login_user():
    username = username_entry.get()
    password = password_entry.get()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_credentials WHERE username=?", (username,))
    result = cursor.fetchone()

    if not result:
        error_label.config(text="Incorrect username\n or password!")
        root.after(5000, clear_error_message)
        return

    hashed_password = hashlib.sha256((password + username).encode()).hexdigest()

    if result[2] == hashed_password:
        global key
        global id
        key = result[4]
        id = result[0]
        root.destroy()
        fernet = Fernet(key)

        # Opens up main program window after successful log in.

        root_inside = Tk()

        window_width = 320
        window_height = 870

        screen_width = root_inside.winfo_screenwidth()
        screen_height = root_inside.winfo_screenheight()

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        root_inside.geometry('{}x{}+{}+{}'.format(window_width, window_height, x, y))
        root_inside.resizable(False, False)
        root_inside.title("Password Generator")
        root_inside.config(bg="black")

        last_passwords = []

        connection = sqlite3.connect('passwords.db')
        cursor = connection.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS passwords
                                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                          site TEXT,
                                          password TEXT,
                                          logged_user TEXT)''')

        # Hiding database file
        cwd = os.getcwd()
        filepath = os.path.join(cwd, 'passwords.db')
        win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_HIDDEN)

        def new_rand():
            pw_entry.delete(0, END)
            pw_length = my_entry.get()

            if not pw_length:
                messagebox.showerror("Input Error", "Please enter a value for password length.")
                return

            try:
                pw_length = int(pw_length)
            except ValueError:
                messagebox.showerror("Input Error", "Please enter an integer for password length.")
                return

            if pw_length <= 3 or pw_length >= 19:
                messagebox.showerror("Password Length Error", "Password must be between 4 and 18 characters long.")
                return

            my_psw = ""
            for x in range(pw_length):
                my_psw += chr(randint(33, 126))

            pw_entry.insert(0, my_psw)
            last_passwords.append(my_psw)
            if len(last_passwords) > 3:
                last_passwords.pop(0)
            show_last_passwords()

        def clipper():
            root_inside.clipboard_clear()
            root_inside.clipboard_append(pw_entry.get())
            success_label.config(text="Generated password has been copied to clipboard!")

        def show_last_passwords():
            for child in last_passwords_frame.winfo_children():
                child.destroy()
            for i, password in enumerate(last_passwords):
                password_label = Label(last_passwords_frame, text=f"{i + 1}. {password}", bg="black", fg="white",
                                       cursor="circle")
                password_label.pack(pady=5)
                password_label.bind("<Button-1>",
                                    lambda e, password=password: (
                                        pw_entry.delete(0, END), pw_entry.insert(0, password)))

        def add_password():

            site = site_entry.get()
            password = password_entry_inside.get()

            cursor.execute("SELECT site FROM passwords WHERE site=?", (site,))
            result = cursor.fetchone()
            if result is not None:
                messagebox.showerror("Error", "Site already exists!")
                return

            # Encrypt the password using the Fernet key

            fernet = Fernet(key)
            encrypted_password = fernet.encrypt(password.encode()).decode()

            cursor.execute("INSERT INTO passwords (site, password, logged_user) VALUES (?, ?, ?)",
                           (site, encrypted_password, id))
            connection.commit()

            site_entry.delete(0, END)
            password_entry_inside.delete(0, END)
            load_passwords(id)

        def load_passwords(id):
            password_listbox.delete(0, 'end')

            cursor.execute("SELECT site, password FROM passwords WHERE logged_user=?", (id,))
            rows = cursor.fetchall()
            for row in rows:
                site, password = row
                password_d = fernet.decrypt(password)
                password_d = password_d.decode()
                password_listbox.insert(END, f"{site}: {password_d}")

        def modify_password(event):
            global selected_site

            selection = password_listbox.curselection()
            if len(selection) == 1:
                selected_item = password_listbox.get(selection[0])
                site, password = selected_item.split(": ")
                site_entry.delete(0, END)
                site_entry.insert(END, site)
                password_entry_inside.delete(0, END)
                password_entry_inside.insert(END, password)
                selected_site = site

        def save_modified_password():
            global selected_site

            new_site = site_entry.get()
            new_password = password_entry_inside.get()
            encrypted_password = fernet.encrypt(new_password.encode()).decode()
            cursor.execute("UPDATE passwords SET site = ?, password = ? WHERE site = ?",
                           (new_site, encrypted_password, selected_site))
            connection.commit()
            site_entry.delete(0, END)
            password_entry_inside.delete(0, END)
            load_passwords(id)

        def delete_password():
            global selected_site

            cursor.execute("DELETE FROM passwords WHERE site = ?", (selected_site,))
            connection.commit()

            site_entry.delete(0, END)
            password_entry_inside.delete(0, END)
            load_passwords(id)

        def copy_to():
            pw_value = pw_entry.get()
            password_entry_inside.delete(0, END)
            password_entry_inside.insert(0, pw_value)
            success_label.config(text="Password has been copied to password manager!")

        def copy_from():
            root_inside.clipboard_clear()
            root_inside.clipboard_append(password_entry_inside.get())
            success_label.config(text="Password has been copied from clipboard\n to password field!")

        entry_var = StringVar()

        def password_strength(*args):
            gen_psw = pw_entry.get()

            if 1 <= len(gen_psw) <= 6:
                xxx.config(text="Password would be cracked\nINSTANTANEOUS!", fg="red")

            elif 7 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 31 SECONDS!", fg="yellow")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 7 SECONDS!", fg="yellow")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 2 SECONDS!", fg="yellow")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nINSTANTANEOUS!", fg="red")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nINSTANTANEOUS!", fg="red")

            elif 8 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 31 MINUTES!", fg="yellow")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 7 MINUTES!", fg="yellow")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 2 MINUTES!", fg="yellow")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nINSTANTANEOUS!", fg="red")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nINSTANTANEOUS!", fg="red")

            elif 9 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 2 DAYS!", fg="yellow")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 7 HOURS!", fg="yellow")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 1 HOUR!", fg="yellow")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 10 SECONDS!", fg="yellow")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nINSTANTANEOUS!", fg="red")

            elif 10 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 5 MONTHS!", fg="yellow")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 3 WEEKS!", fg="yellow")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 3 DAYS!", fg="yellow")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 4 MINUTES!", fg="yellow")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nINSTANTANEOUS!", fg="red")

            elif 11 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 34 YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 3 YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 5 MONTHS!", fg="yellow")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 2 HOURS!", fg="yellow")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nINSTANTANEOUS!", fg="red")

            elif 12 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 3 THOUSAND YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 200 YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 24 YEARS!", fg="green")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 2 DAYS!", fg="yellow")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nIN 2 SECONDS!", fg="yellow")

            elif 13 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 202 THOUSAND YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 12 THOUSAND YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 1 THOUSAND YEARS!", fg="green")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 2 MONTHS!", fg="yellow")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nIN 19 SECONDS!", fg="yellow")

            elif 14 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 16 MILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 750 THOUSAND YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 64 THOUSAND YEARS!", fg="green")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 4 YEARS!", fg="green")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nIN 3 MINUTES!", fg="yellow")

            elif 15 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 1 BILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 46 MILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 3 MILLION YEARS!", fg="green")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 100 YEARS!", fg="green")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nIN 32 MINUTES!", fg="yellow")

            elif 16 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 92 BILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 3 BILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 173 MILLION YEARS!", fg="green")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 3 THOUSAND YEARS!", fg="green")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nIN 5 HOURS!", fg="yellow")

            elif 17 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 7 TRILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 179 BILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 9 BILLION YEARS!", fg="green")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 69 THOUSAND YEARS!", fg="green")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nIN 2 DAYS!", fg="yellow")

            elif 18 == len(gen_psw):
                if any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw) and any(char in string.punctuation for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 438 TRILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw) and any(
                        char.isdigit() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 11 TRILLION YEARS!", fg="green")
                elif any(char.islower() for char in gen_psw) and any(char.isupper() for char in gen_psw):
                    xxx.config(text="Password would be cracked\nIN 467 BILLION YEARS!", fg="green")
                elif gen_psw.islower():
                    xxx.config(text="Password would be cracked\nIN 2 MILLION YEARS!", fg="green")
                elif gen_psw.isdigit():
                    xxx.config(text="Password would be cracked\nIN 3 WEEKS!", fg="yellow")

            elif len(gen_psw) >= 19:
                xxx.config(text="Password is unbreakable\nusing current technology.", fg="green")

        entry_var.trace("w", password_strength)

        # -------------------------------
        new = LabelFrame(root_inside, text="Password Manager", bg="black", fg="white")
        new.pack(pady=5, padx=10)

        site_label = Label(new, text="Site:", bg="black", fg="white")
        site_label.grid(row=0, column=0)

        site_entry = Entry(new)
        site_entry.grid(row=0, column=1)

        password_label = Label(new, text="Password:", bg="black", fg="white")
        password_label.grid(row=1, column=0)

        password_entry_inside = Entry(new)
        password_entry_inside.grid(row=1, column=1)

        save_button = Button(new, text="Save", command=add_password, padx=10, bg="black", fg="white")
        save_button.grid(row=2, column=0)

        password_listbox = Listbox(new, height=10, font=("Helvetica", 10), cursor="circle", bg="black", fg="white",
                                   justify="center")
        password_listbox.grid(row=3, column=0, columnspan=5, ipadx=65, padx=10, pady=10)

        modify_save_button = Button(new, text="Save Modified", command=save_modified_password, padx=20, bg="black",
                                    fg="white")
        modify_save_button.grid(row=2, column=1)

        delete_button = Button(new, text="Delete", command=delete_password, padx=15, bg="black", fg="white")
        delete_button.grid(row=2, column=3)

        password_listbox.bind('<Button-1>', modify_password)

        copy_from_button = Button(new, text="Copy from", padx=3, bg="black", fg="white", command=copy_from)
        copy_from_button.grid(row=1, column=3)

        succ = LabelFrame(bg="black")
        succ.pack(ipadx=143, pady=5, padx=10)
        success_label = Label(succ, fg="green", bg="black")
        success_label.pack()

        # ---------------------------------

        load_passwords(id)

        # -------------------------------
        lf = LabelFrame(root_inside, text="Password Generator", bg="black", fg="white")
        lf.pack(pady=0, padx=10)

        entry_frame = LabelFrame(lf, text="What length do you want your password to be?", bg="black", fg="white")
        entry_frame.pack(pady=5, padx=10)

        my_entry = Entry(entry_frame, font=("Helvetica", 16), bg="black", fg="white", justify="center")
        my_entry.pack(pady=10, padx=10)

        pw_frame = LabelFrame(lf, text="Generated password", bg="black", fg="white")
        pw_frame.pack(pady=5, padx=15)

        pw_entry = Entry(pw_frame, text="", font=("Helvetica", 16), bg="black", fg="white", justify="center",
                         textvariable=entry_var)
        pw_entry.pack(pady=10, padx=10)

        pw_label = Label(pw_frame, text=u'\u2B9D  Enter a password to assess its strength  \u2B9D',
                         font=("Helvetica", 8), bg="black", fg="white", justify="center")
        pw_label.pack(pady=5, padx=0)

        xxx_frame = LabelFrame(lf, text="Password strength", bg="black", fg="white")
        xxx_frame.pack(ipadx=100, pady=10, padx=15)

        xxx = Label(xxx_frame, text="", font=("Helvetica", 12), bd=0, bg="black", fg="yellow", justify="center")
        xxx.pack(pady=10, padx=10)

        my_frame = Frame(root_inside, bg="black")
        my_frame.pack(pady=5)

        my_button = Button(my_frame, text="Generate strong password", command=new_rand, bg="black", fg="white")
        my_button.grid(row=0, column=0, padx=10, ipadx=76)

        clip_button = Button(my_frame, text="Copy to clipboard", command=clipper, bg="black", fg="white")
        clip_button.grid(row=1, column=0, padx=10, ipadx=97)

        copy_to_button = Button(my_frame, text="Copy to password field", bg="black", fg="white", command=copy_to)
        copy_to_button.grid(row=2, column=0, padx=10, ipadx=84)

        last_frame = LabelFrame(root_inside, text="Last 3 passwords:", bg="black", fg="white")
        last_frame.pack(pady=10, padx=10, ipadx=100, ipady=30)

        last_passwords_frame = Frame(last_frame, bg="black")
        last_passwords_frame.pack(pady=5)

        show_last_passwords()

        root_inside.mainloop()

    else:
        error_label.config(text="Incorrect username\n or password!")
        root.after(5000, clear_error_message)
        return None


# Password reminder function. Pushing remind_button reminds users password sending it to usesr's email  pushing remind_button

def reset_password():
    email = email_entry.get()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_credentials WHERE email=?", (email,))
    result = cursor.fetchone()

    if result:
        temp_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))

        username = result[1]
        hashed_temp_password = hashlib.sha256((temp_password + username).encode()).hexdigest()

        cursor.execute("UPDATE user_credentials SET password=? WHERE email=?", (hashed_temp_password, email))
        conn.commit()

        sender_email = "marijusknabikas@gmail.com"
        sender_password = "cawpqkieaahxuhmv"
        recipient_email = email

        subject = "Temporary Password for Login/Register App"
        body = f"Hello,\n\nYour temporary password for the Login/Register App is: {temp_password}\n\nPlease log in using this temporary password and change your password as soon as possible.\n\nBest regards,\nThe Login/Register App Team"

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(message)

        success_label.config(text="An email has been\n sent with your\n temporary password.")
        root.after(5000, clear_success_message)

    else:
        error_label.config(text="This email address\n is not registered.")
        root.after(5000, clear_error_message)

    username_entry.delete(0, END)
    password_entry.delete(0, END)
    email_entry.delete(0, END)


def change_password():
    # ---------------------------------------------

    root_main = Tk()
    root_main.title("Password Reset")
    root_main.config(bg="black")

    window_width = 150
    window_height = 370

    screen_width = root_main.winfo_screenwidth()
    screen_height = root_main.winfo_screenheight()

    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    root_main.geometry('{}x{}+{}+{}'.format(window_width, window_height, x, y))
    root_main.resizable(False, False)
    root.title("Change password")
    root.config(bg="black")

    def change_password():
        username = username_entry.get()
        password = password_entry.get()
        email = email_entry.get()
        new_password = new_password_entry.get()

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_credentials WHERE username=? AND password=? AND email=?",
                       (username, hashlib.sha256((password + username).encode()).hexdigest(), email))
        result = cursor.fetchone()

        if result:
            hashed_new_password = hashlib.sha256((new_password + username).encode()).hexdigest()

            conn.execute("UPDATE user_credentials SET password=? WHERE username=? AND password=? AND email=?",
                         (hashed_new_password, username, password, email))
            conn.commit()

            success_label.config(text="Password changed\nsuccessfully!")
            root_main.after(5000, clear_success_message)
            root_main.destroy()
        else:
            error_label.config(text="Invalid login\ncredentials!\nAll fields are required!")
            root_main.after(5000, clear_error_message)

        username_entry.delete(0, END)
        password_entry.delete(0, END)
        email_entry.delete(0, END)
        new_password_entry.delete(0, END)

    username_label = Label(root_main, text="Username")
    username_label.config(font=("Courier", 14), bg="black", fg="white")
    username_label.pack()
    username_entry = Entry(root_main, width=22, )
    username_entry.pack(pady=5)

    password_label = Label(root_main, text="Password")
    password_label.config(font=("Courier", 14), bg="black", fg="white")
    password_label.pack()
    password_entry = Entry(root_main, show="*", width=22)
    password_entry.pack(pady=5)

    email_label = Label(root_main, text="Email")
    email_label.config(font=("Courier", 14), bg="black", fg="white")
    email_label.pack()
    email_entry = Entry(root_main, width=22)
    email_entry.pack(pady=5)

    new_password_label = Label(root_main, text="New password")
    new_password_label.config(font=("Courier", 14), bg="black", fg="white")
    new_password_label.pack()
    new_password_entry = Entry(root_main, show="*", width=22)
    new_password_entry.pack(pady=5)

    padding_label = Label(root_main, bg="black")
    padding_label.pack()

    change_button = Button(root_main, font=("Courier", 10), text="Change password", command=change_password, width=18,
                           bg="black", fg="white", activebackground="yellow", activeforeground="black")
    change_button.pack()

    success_label = Label(root_main, fg="green", bg="black")
    success_label.pack()
    error_label = Label(root_main, fg="red", bg="black")
    error_label.pack()

    root_main.mainloop()

# Username label and entry
username_label = Label(root, text="Username")
username_label.config(font=("Courier", 14), bg="black", fg="white")
username_label.pack()
username_entry = Entry(root, width=22)
username_entry.pack(pady=5)

# Password label and entry
password_label = Label(root, text="Password")
password_label.config(font=("Courier", 14), bg="black", fg="white")
password_label.pack()
password_entry = Entry(root, show="*", width=22)
password_entry.pack(pady=5)

# Email label and entry
email_label = Label(root, text="Email")
email_label.config(font=("Courier", 14), bg="black", fg="white")
email_label.pack()
email_entry = Entry(root, width=22)
email_entry.pack(pady=5)

# padding label and entry
padding_label = Label(root, bg="black")
padding_label.pack()

# Registration button
register_button = Button(root, font=("Courier", 10), text="Register", command=register_user, width=18, bg="black",
                         fg="white", activebackground="yellow", activeforeground="black")
register_button.pack()

# Log in button
login_button = Button(root, font=("Courier", 10), text="Login", command=login_user, width=18, bg="black", fg="white",
                      activebackground="yellow", activeforeground="black")
login_button.pack()

# Password remind button
remind_button = Button(root, font=("Courier", 10), text="Remind Password", command=reset_password, width=18, bg="black",
                       fg="white", activebackground="yellow", activeforeground="black")
remind_button.pack()

# Opens tkinter window to change password
change_button = Button(root, font=("Courier", 10), text="Password Reset", command=change_password, width=18, bg="black",
                       fg="white", activebackground="yellow", activeforeground="black")
change_button.pack()

# Tkinter message labels
success_label = Label(root, fg="green", bg="black")
success_label.pack()
error_label = Label(root, fg="red", bg="black")
error_label.pack()

# Start the main loop
root.mainloop()

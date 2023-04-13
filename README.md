# Secure Password Manager/Generator

Secure password manager for your passwords with our all-in-one platform that includes password generation, strength checking, and even login functionality.

#Installation

This program could be used as it is (just runing Python script). But making .exe file makes this program way more userfriendly.

Steps for making launchable .exe file:

1.Most modules used in this project are pre-installed with Python. Only modules you need to instal are: cryptography, pywin32 and pyinstaller. To do install these modules you should run these lines in CMD:
pip install cryptography
pip install pywin32
pip install pyinstaller
2. From directory where projects files are located (don't forget locked.ico file) in CMD launch this line of code:
pyinstaller --name=PasswordManager --noconsole --onefile --icon=locked.ico Login.py
3. After file conversion is done you'll be able to find PasswordManager.exe file in folder /dist.


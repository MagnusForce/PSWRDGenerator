# Secure Password Manager/Generator

A secure password manager that includes password generation, strength checking, and even login functionality all in one platform.

# Installation

This program can be used as is by simply running the Python script. However, creating an .exe file makes the program more user-friendly.

Steps for making a launchable .exe file:

1.Most modules used in this project are pre-installed with Python. The only modules you need to install are cryptography, pywin32, and pyinstaller. To install these modules, run these commands in CMD:

`pip install cryptography`
`pip install pywin32`
`pip install pyinstaller`

2.From the directory where project files are located (don't forget the locked.ico file), launch this command in CMD:

`pyinstaller --name=PasswordManager --noconsole --onefile --icon=locked.ico Login.py`


3.After the file conversion is done, you will be able to find the PasswordManager.exe file in the /dist folder.

# Explanation

<img src="login.png"> 
<div style="position:relative;">
  <img src="login.png"  />
  <div style="position:absolute; top:0; right:0;">
    This is the text that will appear at the top right corner of the image.<br>
    This is the second line of text.
  </div>
</div>
<img src="password_change.png">
<img src="password_manager.png">

# telegram-slurm-alarm

Telegram bot to ease and automate the interaction with the SLURM capabilities of a remote server

For more information about the Slurm Workload Manager visit their [website](https://slurm.schedmd.com/overview.html).

## Features

- Display the number of SLURM jobs currently running / pending execution
- Alarm the user when the number of currently submitted SLURM jobs drops below a specific limit

## Ideas for the future

- Add instructions for Telegram bot setup

## Dependencies

- The bot is written in Python 3.10
- Interactions with the Telegram API are managed by [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Remote access to the server is accomplished with the help of [Paramiko](https://github.com/paramiko/paramiko)

Further information about the python package versions can be found in [package list](requirements.txt).

## How to get started on linux (setup of virtual environment)
Copy files to workplace and navigate to directory

`cd telegram-slurm-alarm`

Install necessary software packages (for linux)

`sudo apt install python3 python3-pip python3-venv`

Create virtual enironment with `venv`

`python3 -m venv .env`

Working with virtual environment on CLI:

- Activate with `source .env/bin/activate`
- Deactivate with `deactivate`

Installing dependencies from text file in repository

`python3 -m pip install -r requirements.txt`

Record currently installed packages for duplication

`python3 -m pip freeze > requirements.txt`

### Author

Tim Fehler
import logging, os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import configparser
import paramiko

# Settings for logging
if not os.path.isdir("tmp"):
    os.makedirs("tmp")
    logging.info("Created folder tmp/")

logging.basicConfig(
    filename="tmp/telegram_bot.log",
    filemode="w",
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-10s | %(name)-15s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Read config files
config = configparser.ConfigParser()
config.read("configs/main.ini")
SECRETS_PATH = config.get("Active Config File", "secrets_path")

config.read(SECRETS_PATH)
TOKEN = config.get("Telegram access", "token")
CHAT_ID = config.getint("Telegram access", "chat_id") # Chat ID for passive commands

SSH_ADDRESS = config.get("Server access", "ssh_address")
SSH_PORT = config.getint("Server access", "ssh_port")
SSH_USER = config.get("Server access", "ssh_user")
SSH_PWD = config.get("Server access", "ssh_pwd")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Use /getChatId to get the ID of this chat, paste it into the config file and finish the setup.")

async def getChatId(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.effective_chat.id}")

# ===========================
#
# SLURM commands
#
# ===========================

slurm_commands = []

def runSSHCommand(cmd: str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.WarningPolicy)
    ssh.connect(SSH_ADDRESS, SSH_PORT, SSH_USER, SSH_PWD)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('ascii')
    ssh.close()
    return output

def countSLURMjobs(ignore_pending=False) -> int:
    if not ignore_pending:
        output = runSSHCommand(f"sh -lc 'squeue -hu {SSH_USER} | wc -l'")
    else:
        output = runSSHCommand(f"sh -lc 'squeue -hu {SSH_USER} -t running | wc -l'")

    return int(output.strip())

# Info about SLURM related commands
async def slurmInfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Currently the following SLURM related commands are available:\n\n" + '\n'.join(slurm_commands))

# Setup SLURM alarm
slurm_commands.append("/SLURMalarm <limit> Activates the notification when submitted SLURM jobs drop under limit")
async def activateSLURMAlarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == CHAT_ID:
        context.bot_data["SLURM alarm limit"] = context.args[0]
        context.bot_data["SLURM alarm active"] = True
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You activated the SLURM alarm with limit {context.args[0]}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You have no access to this command")

# Notifies the user when the currently running jobs drop below their limit 
async def SLURMAlarm(context: ContextTypes.DEFAULT_TYPE):
    if context.bot_data.get("SLURM alarm active"):
        if countSLURMjobs() < int(context.bot_data.get("SLURM alarm limit")): 
            await context.bot.send_message(chat_id=CHAT_ID, text=f"Your SLURM jobs dropped below the limit!")
            context.bot_data["SLURM alarm active"] = False

# Return the number of currently scheduled SLURM jobs 
slurm_commands.append("/SLURMjobcount displays the number of currently submitted SLURM jobs by the user.")
async def jobcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == CHAT_ID:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"Total number of jobs currently submitted: {countSLURMjobs()}")
        await context.bot.send_message(chat_id=CHAT_ID, text=f"Total number of jobs currently running: {countSLURMjobs(ignore_pending=True)}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You have no access to this command")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler(['start', 'help'], start)
    getChatId_handler = CommandHandler('getChatId', getChatId)
    
    slurmInfo_handler = CommandHandler('slurm', slurmInfo)
    jobcount_handler = CommandHandler('SLURMjobcount', jobcount)
    slurmAlarm_handler = CommandHandler('SLURMalarm', activateSLURMAlarm)

    application.add_handler(start_handler)
    application.add_handler(getChatId_handler)
    application.add_handler(jobcount_handler)
    application.add_handler(slurmInfo_handler)
    application.add_handler(slurmAlarm_handler)

    job_queue = application.job_queue
    
    application.bot_data["SLURM alarm active"] = False
    application.bot_data["SLURM alarm limit"] = 100
    job_SLURM_alarm = job_queue.run_repeating(SLURMAlarm, interval=600, first=5)

    application.run_polling()


from dotenv import load_dotenv
import os
load_dotenv()


BOT_TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=[5306481482,5384513793]
# ADMIN_ID = os.getenv("ADMIN_ID")

# BOT_TOKEN=7399635739:AAF669_ELVJflNO0pr9Y44DIenwQNG1wKZg
GROUP_ID=4654916473
# GROUP_ID = int(os.getenv("GROUP_ID"))

DB_NAME = os.getenv("DB_NAME", "logistics.db")
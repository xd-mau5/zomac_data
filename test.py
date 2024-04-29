import dropbox
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DROPBOX_TOKEN')
KEY = os.getenv('DROPBOX_KEY')
SECRET = os.getenv('DROPBOX_SECRET')

folder = (r'data/Dropbox')

if not os.path.exists(folder):
    os.makedirs(folder)

dbx = dropbox.Dropbox(TOKEN)

print(dbx.files_list_folder(r'/test'))
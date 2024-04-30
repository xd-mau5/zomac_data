import dropbox
import os
from dotenv import load_dotenv
import dropbox.files
import dropbox.oauth

load_dotenv()

KEY = os.getenv('DROPBOX_KEY')
SECRET = os.getenv('DROPBOX_SECRET')
folder = (r'data/Dropbox')


def dropbox_oauth():
    flow = dropbox.DropboxOAuth2FlowNoRedirect(KEY, SECRET)
    authorize_url = flow.start()
    print("1. Ir a: " + authorize_url)
    print("2. Click 'Permitir' (iniciar sesión primero).")
    print("3. Copiar el código de autorización.")
    auth_code = input("Ingrese el código de autorización aquí: ").strip()

    try:
        oauth_result = flow.finish(auth_code)
    except Exception as e:
        print('Error: %s' % (e,))
        return

    return oauth_result.access_token

def files_download(dbx: dropbox.Dropbox, folder: str, file: str, remote_folder: str = '/test'):
    with open(os.path.join(folder, file), 'wb') as f:
        metadata, res = dbx.files_download(path=f'/test/{file}')
        f.write(res.content)

def search_excel_rdt(dbx: dropbox.Dropbox, folder: str, remote_folder: str):
    for entry in dbx.files_list_folder(remote_folder).entries:
        if entry.name.endswith('.xlsx') and entry.name.startswith('RDT'):
            files_download(dbx, folder, entry.name)
            if entry.name.endswith('.xlsx') and entry.name.startswith('RDT'):
                print(f'Archivo {entry.name} descargado con éxito')

# Verificar si el token todavia es valido, si no, solicitar uno nuevo
if os.getenv('DROPBOX_TOKEN'):
    try:
        dbx = dropbox.Dropbox(os.getenv('DROPBOX_TOKEN'))
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError:
        os.putenv('DROPBOX_TOKEN', dropbox_oauth())
else:
    os.putenv('DROPBOX_TOKEN', dropbox_oauth())

if not os.path.exists(folder):
    os.makedirs(folder)
TOKEN = os.getenv('DROPBOX_TOKEN')
dbx = dropbox.Dropbox(TOKEN)


if __name__ == '__main__':
    search_excel_rdt(dbx, folder, '/test')
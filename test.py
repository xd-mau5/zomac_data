import dropbox
import os
from dotenv import load_dotenv, dotenv_values, set_key
import dropbox.files
import dropbox.oauth

env_vars = dotenv_values('.env')
print('Varaibles de entorno actuales:')
for key, value in env_vars.items():
    print(f'{key}={value}')

KEY = env_vars['DROPBOX_KEY']
SECRET = env_vars['DROPBOX_SECRET']
folder = (r'data/Dropbox')
TOKEN = env_vars['DROPBOX_TOKEN']
dbx = dropbox.Dropbox(TOKEN)

def dropbox_oauth():
    flow = dropbox.DropboxOAuth2FlowNoRedirect(KEY, SECRET, token_access_type='legacy')
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
def check_token(TOKEN: str):
    print('Verificando token...')
    dbx = dropbox.Dropbox(TOKEN)
    print('Token recibido en la variable dbx', TOKEN)
    while True:
        try:
            print('Accediendo a la cuenta de Dropbox...')
            dbx.users_get_current_account()
            break
        except dropbox.exceptions.AuthError as e:
            print('Token invalido')
            TOKEN = dropbox_oauth()
            # Eliminamos las comillas simples del token
            TOKEN = TOKEN.replace("'", "")
            set_key('.env', 'DROPBOX_TOKEN', TOKEN)
            dbx = dropbox.Dropbox(TOKEN)
            print('Token actualizado')

if not os.path.exists(folder):
    os.makedirs(folder)

if __name__ == '__main__':
    check_token(TOKEN)
    search_excel_rdt(dbx, folder, '/test')
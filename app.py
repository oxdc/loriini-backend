from fastapi import FastAPI
from pathlib import Path
from mdict.core.index import MDictServer, MDictIndex
from hashlib import sha1
import dataset

APP_ROOT = ''

app_db = dataset.connect(f'sqlite:///{APP_ROOT}/app.db')
user_db = dataset.connect(f'sqlite:///{APP_ROOT}/user.db')

dictionaries = app_db['dictionaries']
settings = app_db['settings']

app = FastAPI()
dictionary_server = dict()
for row in dictionaries.all():
    dictionary_server[row['dict_id']] = {
        'name': row['name'],
        'path': row['path'],
        'server': row['server'],
        'active': row['active']
    }


@app.get('/')
async def root():
    return {'description': 'Loriini backend', 'version': '0.1a'}


@app.post('/api/dictionary/add')
async def add_dictionary(path: str):
    results = []
    for mdx in Path(path).glob('**/*.mdx'):
        dict_id = sha1(str(mdx).encode('utf-8')).hexdigest()
        if dict_id in dictionary_server:
            continue
        db_file = mdx.parent / mdx.name.replace('.mdx', '.db')
        if not db_file.exists():
            MDictIndex(mdx).build_index()
        server = MDictServer(mdx)
        dictionary_info = {
            'name': mdx.name.replace('.mdx', ''),
            'path': str(mdx),
            'server': server,
            'active': True
        }
        dictionary_server[dict_id] = dictionary_info
        results.append({
            'name': mdx.name.replace('.mdx', ''),
            'path': str(mdx)
        })
        dictionary_info['dict_id'] = dict_id
        dictionaries.insert_one(dictionary_info)
    return {'status': 'ok', 'results': results}


@app.get('/api/dictionary/list')
async def list_dictionary():
    return {
        'status': 'ok',
        'results': list(
            dict_id for dict_id in dictionary_server.keys()
            if dictionary_server[dict_id]['active']
        )
    }


@app.delete('/api/dictionary/{dict_id}')
async def delete_dictionary(dict_id: str):
    if dict_id not in dictionary_server:
        return {'status': 'error', 'message': 'no such dictionary found.'}
    else:
        del dictionary_server[dict_id]
        dictionaries.delete(dict_id=dict_id)
        return {'status': 'ok'}


@app.post('/api/dictionary/activate/{dict_id}')
async def activate_dictionary(dict_id: str):
    if dict_id not in dictionary_server:
        return {'status': 'error', 'message': 'no such dictionary found.'}
    else:
        dictionary_server[dict_id]['active'] = True
        dictionary_info = dictionary_server[dict_id]
        dictionary_info['dict_id'] = dict_id
        dictionaries.update(dictionary_info, ['dict_id'])
        return {'status': 'ok'}


@app.post('/api/dictionary/deactivate/{dict_id}')
async def deactivate_dictionary(dict_id: str):
    if dict_id not in dictionary_server:
        return {'status': 'error', 'message': 'no such dictionary found.'}
    else:
        dictionary_server[dict_id]['active'] = False
        dictionary_info = dictionary_server[dict_id]
        dictionary_info['dict_id'] = dict_id
        dictionaries.update(dictionary_info, ['dict_id'])
        return {'status': 'ok'}


@app.get('/api/favorite/list')
async def list_favorites():
    pass


@app.post('/api/favorite/{words}')
async def add_favorites(words: str):
    pass


@app.delete('/api/favorite/{words}')
async def delete_favorites(words: str):
    pass


@app.get('/api/app-settings/{key}')
async def get_setting(key: str):
    pass


@app.post('/api/app-settings/{key}')
async def update_setting(key: str, value: str):
    pass


@app.delete('/api/app-settings/{key}')
async def delete_settings(key: str):
    pass


@app.get('/{dict_id}/entry/{word}')
async def fetch_word(dict_id: str, word: str):
    pass


@app.get('/{dict_id}/{path:path}')
async def fetch_file(dict_id: str, path: str):
    pass

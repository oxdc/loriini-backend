from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from io import BytesIO
from pathlib import Path
from mdict.core.index import MDictServer, MDictIndex
from hashlib import sha1
import dataset

APP_ROOT = ''

app_db = dataset.connect(f'sqlite:///{APP_ROOT}/app.db')
user_db = dataset.connect(f'sqlite:///{APP_ROOT}/user.db')

dictionaries = app_db['dictionaries']
settings = app_db['settings']
favorites = user_db['favorites']

app = FastAPI()
dictionary_server = dict()
for row in dictionaries.all():
    dictionary_server[row['dict_id']] = {
        'name': row['name'],
        'path': row['path'],
        'server': MDictServer(Path(row['path']), base_url=f"/{row['dict_id']}/"),
        'active': row['active']
    }


@app.get('/')
async def root():
    return {'description': 'Loriini backend', 'version': '0.1a'}


@app.post('/api/dictionary/add')
async def add_dictionary(path: str, rebuild: bool = False):
    results = []
    for mdx in Path(path).glob('**/*.mdx'):
        dict_id = sha1(str(mdx).encode('utf-8')).hexdigest()
        if not rebuild and dict_id in dictionary_server:
            continue
        db_file = mdx.parent / mdx.name.replace('.mdx', '.db')
        if not db_file.exists():
            MDictIndex(mdx).build_index()
        elif rebuild:
            MDictIndex(mdx, rebuild=True).build_index()
        server = MDictServer(mdx, base_url=f'/{dict_id}/')
        dictionary_info = {
            'name': mdx.name.replace('.mdx', ''),
            'path': str(mdx),
            'server': server,
            'active': True
        }
        dictionary_server[dict_id] = dictionary_info
        results.append({
            'dict_id': dict_id,
            'name': mdx.name.replace('.mdx', ''),
            'path': str(mdx)
        })
        db_row = {
            'dict_id': dict_id,
            'name': mdx.name.replace('.mdx', ''),
            'path': str(mdx),
            'active': True
        }
        dictionaries.upsert(db_row, ['dict_id'])
    return {'status': 'ok', 'results': results}


@app.get('/api/dictionary/list')
async def list_dictionary():
    return {
        'status': 'ok',
        'results': list(
            {
                'dict_id': dict_id,
                'name': dictionary_server[dict_id]['name'],
                'path': dictionary_server[dict_id]['path']
            }
            for dict_id in dictionary_server.keys()
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
        db_row = {
            'dict_id': dict_id,
            'name': dictionary_server[dict_id]['name'],
            'path': dictionary_server[dict_id]['path'],
            'active': True
        }
        dictionaries.update(db_row, ['dict_id'])
        return {'status': 'ok'}


@app.post('/api/dictionary/deactivate/{dict_id}')
async def deactivate_dictionary(dict_id: str):
    if dict_id not in dictionary_server:
        return {'status': 'error', 'message': 'no such dictionary found.'}
    else:
        dictionary_server[dict_id]['active'] = False
        db_row = {
            'dict_id': dict_id,
            'name': dictionary_server[dict_id]['name'],
            'path': dictionary_server[dict_id]['path'],
            'active': False
        }
        dictionaries.update(db_row, ['dict_id'])
        return {'status': 'ok'}


@app.get('/api/favorite/list')
async def list_favorites():
    return {'status': 'ok', 'results': list(favorites.all())}


@app.post('/api/favorite/{words}')
async def add_favorites(words: str):
    favorites.insert_many([{'word': word.strip()} for word in words.split(',')])
    return {'status': 'ok'}


@app.delete('/api/favorite/{words}')
async def delete_favorites(words: str):
    for word in words.split(','):
        favorites.delete(word=word.strip())
    return {'status': 'ok'}


@app.get('/api/app-settings/{key}')
async def get_setting(key: str):
    result = settings.find_one(key=key)
    if result is None:
        return {'status': 'error', 'value': 'null', 'message': 'no such key found.'}
    else:
        return {'status': 'ok', 'value': result['value']}


@app.post('/api/app-settings/{key}')
async def update_setting(key: str, value: str):
    settings.upsert({'key': key, 'value': value}, ['key'])
    return {'status': 'ok'}


@app.delete('/api/app-settings/{key}')
async def delete_settings(key: str):
    settings.delete(key=key)
    return {'status': 'ok'}


@app.get('/{dict_id}/entry/{word}')
async def fetch_word(dict_id: str, word: str):
    if dict_id not in dictionary_server:
        return {'status': 'error', 'message': 'no such dictionary found.'}
    return HTMLResponse(content=dictionary_server[dict_id]['server'].query(word))


@app.get('/{dict_id}/{file_path:path}')
async def fetch_file(dict_id: str, file_path: str):
    if dict_id not in dictionary_server:
        return {'status': 'error', 'message': 'no such dictionary found.'}
    return StreamingResponse(BytesIO(dictionary_server[dict_id]['server'].fetch_file(file_path)))

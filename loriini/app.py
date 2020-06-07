from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def root():
    return {'description': 'Loriini backend', 'version': '0.1a'}


@app.post('/api/dictionary/add')
async def add_dictionary(path: str):
    pass


@app.get('/api/dictionary/list')
async def list_dictionary():
    pass


@app.delete('/api/dictionary/{dict_id}')
async def delete_dictionary(dict_id: str):
    pass


@app.post('/api/dictionary/activate/{dict_id}')
async def activate_dictionary(dict_id: str):
    pass


@app.post('/api/dictionary/deactivate/{dict_id}')
async def activate_dictionary(dict_id: str):
    pass


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

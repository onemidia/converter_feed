import feedparser
import requests
import time
import os
import json
from flask import Flask, Response

app = Flask(__name__)

# Variáveis de ambiente (configure no Render.com)
XIBO_URL = os.environ.get('XIBO_URL')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
DATASET_ID = os.environ.get('DATASET_ID')
FEED_URL = os.environ.get('FEED_URL')  # URL do feed RSS a ser configurada no Render

# Variável para armazenar o token de acesso
access_token_data = {'token': None, 'expires_at': 0}

def get_xibo_token():
    """Obtém um token de acesso da API do Xibo."""
    global access_token_data
    if access_token_data['token'] and access_token_data['expires_at'] > time.time():
        print("Token de acesso ainda válido, reutilizando.")
        return access_token_data['token']

    token_url = f'{XIBO_URL}authorize/access_token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        access_token_data['token'] = token_data['access_token']
        access_token_data['expires_at'] = time.time() + token_data['expires_in']
        print("Novo token de acesso obtido com sucesso.")
        return access_token_data['token']
    except requests.exceptions.RequestException as e:
        print(f'Erro ao obter token de acesso: {e}')
        return None

def fetch_feed_data(feed_url):
    """Busca e processa os dados do feed RSS."""
    feed = feedparser.parse(feed_url)
    data = []
    for entry in feed.entries:
        title = entry.get('title', '')
        link = entry.get('link', '')
        linkfoto = entry.get('media_content', [{}])[0].get('url', '') if hasattr(entry, 'media_content') and entry.media_content else ''
        data.append({'title': title, 'link': link, 'linkfoto': linkfoto})
    return data

def send_data_to_xibo(data, token):
    """Envia dados para a API do Xibo usando o endpoint /dataset/row."""
    url = f'{XIBO_URL}dataset/row/{DATASET_ID}'
    headers = {'Authorization': f'Bearer {token}'} # Content-Type será auto definido para form-data

    try:
        for item in data:
            fields_json = json.dumps(item) # Converte o dicionário da linha para uma string JSON
            payload = {'fields': fields_json}
            print(f"Enviando linha de dados para o Xibo: {payload}")
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            print(f'Linha de dados enviada com sucesso: {response.text}') # Imprime a resposta para debugging
        print('Todos os dados enviados para o Xibo com sucesso!')
        return "Dados enviados para o Xibo com sucesso!"
    except requests.exceptions.RequestException as e:
        print(f'Erro ao enviar dados para o Xibo: {e} - Response: {e.response.text if e.response else None}')
        return f"Erro ao enviar dados para o Xibo: {e}"

@app.route('/update_xibo')
def update_xibo():
    """Função para atualizar os dados no Xibo."""
    token = get_xibo_token()
    if not token:
        return "Erro ao obter o token do Xibo.", 500

    feed_data = fetch_feed_data(FEED_URL)
    if not feed_data:
        return "Erro ao buscar ou processar os dados do feed.", 500

    result = send_data_to_xibo(feed_data, token)
    return result, 200

@app.route('/')
def home():
    return "Serviço de conversão de feed para Xibo está rodando.", 200

if __name__ == '__main__':
    app.run(debug=False, port=10000, host='0.0.0.0')
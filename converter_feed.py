from flask import Flask, Response
import requests
import xml.etree.ElementTree as ET
import re
import json
import time
import os

app = Flask(__name__)

# Configurações da API do Xibo (agora como variáveis de ambiente)
XIBO_URL = os.environ.get('XIBO_URL')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
DATASET_ID = os.environ.get('DATASET_ID')

# Variável global para armazenar o access_token e sua data de expiração
access_token_data = {'token': None, 'expires_at': 0}

def get_xibo_token():
    """Obtém um access_token da API do Xibo."""
    global access_token_data

    if access_token_data['token'] and access_token_data['expires_at'] > time.time():
        return access_token_data['token']

    url = f'{XIBO_URL}authorize/access_token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        access_token_data['token'] = token_data['access_token']
        access_token_data['expires_at'] = time.time() + token_data['expires_in']
        return access_token_data['token']
    except requests.exceptions.RequestException as e:
        print(f'Erro ao obter access_token: {e}')
        return None

def send_data_to_xibo(data, token):
    """Envia dados para a API do Xibo."""
    url = f'{XIBO_URL}dataset/data/{DATASET_ID}'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    print(f"Enviando dados para o Xibo: {json.dumps(data, indent=4)}") # Adicione esta linha
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print('Dados enviados para o Xibo com sucesso!')
        return "Dados enviados para o Xibo com sucesso!"
    except requests.exceptions.RequestException as e:
        print(f'Erro ao enviar dados para o Xibo: {e}')
        return f"Erro ao enviar dados para o Xibo: {e}"

def converter_feed(url_original):
    """Converte o feed RSS e envia os dados para o Xibo."""
    try:
        resposta = requests.get(url_original)
        resposta.raise_for_status()
        feed_original = resposta.text
        feed_original = re.sub(r'^.*?<\?xml', '<?xml', feed_original, flags=re.DOTALL)
        raiz_original = ET.fromstring(feed_original)
        dados_xibo = []
        for item_original in raiz_original.find('channel').findall('item'):
            titulo = item_original.find('title').text
            link = item_original.find('link').text
            descricao = item_original.find('description').text
            linkfoto = re.search(r'src="([^"]+)"', descricao)
            linkfoto = linkfoto.group(1) if linkfoto else ''
            dados_xibo.append({
                'title': titulo,
                'link': link,
                'linkfoto': linkfoto
            })

        if dados_xibo:
            token = get_xibo_token()
            if token:
                result = send_data_to_xibo(dados_xibo, token)
                return result
            else:
                return "Falha ao obter o token do Xibo."
        else:
            return "Nenhuma notícia encontrada no feed."

    except requests.exceptions.RequestException as e:
        return f'Erro ao baixar o feed ou interagir com a API: {e}'
    except ET.ParseError as e:
        return f'Erro ao analisar o XML: {e}'
    except Exception as e:
        return f'Ocorreu um erro inesperado: {e}'

@app.route('/update_xibo')
def update_xibo():
    """Endpoint web para atualizar o Xibo com o feed."""
    url_original = 'https://www.tribunaonline.net/feed/'
    result = converter_feed(url_original)
    return Response(result, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
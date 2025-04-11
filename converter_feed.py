import os
import requests
import time
from flask import Flask, jsonify

app = Flask(__name__)

XIBO_URL = os.environ.get('XIBO_URL', 'http://m.onemidia.tv.br/api/')
CLIENT_ID = os.environ.get('XIBO_CLIENT_ID', 'seu_client_id')
CLIENT_SECRET = os.environ.get('XIBO_CLIENT_SECRET', 'seu_client_secret')

access_token_data = {
    'token': None,
    'expires_at': 0
}

def get_xibo_token():
    global access_token_data

    # Verifica se o token ainda é válido
    if access_token_data['token'] and access_token_data['expires_at'] > time.time():
        print("✅ Token ainda válido. Reutilizando.")
        return access_token_data['token']

    # Monta URL de autenticação
    token_url = f'{XIBO_URL}authorize/access_token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    print(f"🔐 Solicitando novo token: {token_url}")
    print(f"📨 Dados enviados: {data}")

    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        access_token_data['token'] = token_data['access_token']
        access_token_data['expires_at'] = time.time() + token_data['expires_in']
        print("✅ Novo token obtido com sucesso.")
        return access_token_data['token']

    except requests.exceptions.HTTPError as e:
        error_text = e.response.text if e.response else 'Sem resposta'
        print(f"❌ Erro HTTP ao obter token: {e} - Detalhes: {error_text}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição ao obter token: {e}")
        return None

@app.route('/')
def home():
    return 'API Xibo Token Atualizador rodando!'

@app.route('/update_xibo')
def update_xibo():
    token = get_xibo_token()
    if not token:
        return jsonify({'error': 'Não foi possível obter token de acesso.'}), 500

    # Aqui você pode colocar a lógica de atualização do Xibo.
    # Exemplo: puxar layouts, enviar dados, atualizar campanhas, etc.

    return jsonify({'message': 'Token de acesso atualizado com sucesso!', 'token': token})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

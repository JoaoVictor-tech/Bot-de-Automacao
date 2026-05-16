# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import requests
import time
import json
import os

app = Flask(__name__)

# =================================================================
# CONFIGURAÇÕES TÉCNICAS
# =================================================================
URL_API = "http://localhost:8080"
INSTANCIA = "finalteste"
TOKEN = "2FD14A9E01BE-4AB9-AB92-60592A7EE44B"
ARQUIVO_BD = "banco_bot.json"
FUSO_HORARIO = pytz.timezone('America/Sao_Paulo')

# =================================================================
# GESTÃO DE DADOS (JSON)
# =================================================================
def carregar_bd():
    """Carrega os estados e registos de saudação do ficheiro local."""
    if os.path.exists(ARQUIVO_BD):
        try:
            with open(ARQUIVO_BD, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"estados": {}, "ultima_saudacao": {}}

bd = carregar_bd()
estados_clientes = bd.get("estados", {})
ultima_saudacao = bd.get("ultima_saudacao", {})
mensagens_processadas = set()

def salvar_bd():
    """Guarda os dados para persistência após reiniciar o bot."""
    try:
        with open(ARQUIVO_BD, "w", encoding="utf-8") as f:
            json.dump({
                "estados": estados_clientes, 
                "ultima_saudacao": ultima_saudacao
            }, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar BD: {e}")

# =================================================================
# LÓGICA DE HORÁRIO DE FUNCIONAMENTO
# =================================================================
def esta_aberto():
    """Verifica se a oficina está aberta no momento atual."""
    agora = datetime.now(FUSO_HORARIO)
    dia_semana = agora.weekday() # 0=Segunda, 5=Sábado, 6=Domingo
    hora = agora.hour
    minuto = agora.minute
    tempo_atual = hora * 100 + minuto

    # Segunda a Sexta: 08:00 às 18:00
    if 0 <= dia_semana <= 4:
        return 800 <= tempo_atual <= 1800
    # Sábado: 08:00 às 13:00
    elif dia_semana == 5:
        return 800 <= tempo_atual <= 1300
    
    return False

# =================================================================
# FUNÇÃO DE ENVIO DE MENSAGENS
# =================================================================
def enviar_msg(jid_destino, texto, msg_id_original=None):
    """Envia texto para o WhatsApp via Evolution API."""
    headers = {"apikey": TOKEN, "Content-Type": "application/json"}
    
    # Simulação de digitação para o cliente ver "a escrever..."
    espera = min((len(texto) * 0.04) + 1.5, 10)
    time.sleep(espera)

    url = f"{URL_API}/message/sendText/{INSTANCIA}"
    payload = {
        "number": jid_destino, 
        "text": texto,
        "options": {"delay": 1000, "presence": "composing"}
    }

    if msg_id_original:
        payload["options"]["quoted"] = {"key": {"id": msg_id_original, "fromMe": False}}

    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro no envio de mensagem: {e}")

# =================================================================
# WEBHOOK PRINCIPAL (ACEITA GET E POST)
# =================================================================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Se alguém aceder pelo navegador ou o ngrok fizer health check
    if request.method == "GET":
        return "<h1>🤖 Refri Auto Bot Ativo!</h1><p>Pronto para receber mensagens via POST.</p>", 200

    dados = request.get_json()
    if not dados or dados.get("event") != "messages.upsert":
        return jsonify({"status": "ignorado"}), 200

    try:
        data = dados.get('data', {})
        key = data.get('key', {})
        msg_id = key.get('id')
        remote_jid = key.get('remoteJid', '')

        # Ignora mensagens de grupos ou do próprio bot
        if key.get('fromMe') or "@g.us" in remote_jid:
            return jsonify({"status": "ignorado"}), 200

        # Bloqueio de duplicados
        if msg_id in mensagens_processadas: return jsonify({"status": "duplicado"}), 200
        mensagens_processadas.add(msg_id)

        push_name = data.get('pushName', 'Cliente')
        msg_obj = data.get('message', {})
        texto_recebido = (msg_obj.get("conversation") or 
                          msg_obj.get("extendedTextMessage", {}).get("text", "")).strip()

        if not texto_recebido: return jsonify({"status": "sem_texto"}), 200

        opcao = texto_recebido.lower()
        hoje = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d")

        # ---------------------------------------------------------
        # FLUXO FORA DE HORÁRIO
        # ---------------------------------------------------------
        if not esta_aberto():
            if ultima_saudacao.get(remote_jid) != hoje:
                msg_fechado = (
                    f"Olá {push_name}! No momento estamos fora do nosso horário de atendimento.\n\n"
                    "*Nosso horário é:*\n"
                    "❄️ Segunda a Sexta: 08:00 às 18:00\n"
                    "❄️ Sábado: 08:00 às 13:00\n\n"
                    "Deixe sua mensagem e retornaremos assim que possível! ❄️🚗"
                )
                enviar_msg(remote_jid, msg_fechado, msg_id)
                ultima_saudacao[remote_jid] = hoje
                salvar_bd()
            return jsonify({"status": "fechado"}), 200

        # ---------------------------------------------------------
        # FLUXO DENTRO DO HORÁRIO (MENU E OPÇÕES)
        # ---------------------------------------------------------
        
        # Reset automático: se o cliente digitar 1-5, ignora o estado anterior
        if opcao in ["1", "2", "3", "4", "5"]:
            if remote_jid in estados_clientes: del estados_clientes[remote_jid]

            if opcao == "1":
                enviar_msg(remote_jid, "Para facilitar o seu atendimento, por favor, nos envie as seguintes informações:\n\n• Modelo do veículo:\n• Endereço do local (com CEP e número):", msg_id)
                estados_clientes[remote_jid] = "aguardando_dados"
            
            elif opcao == "2":
                enviar_msg(remote_jid, "Nós trabalhamos por ondem de chegada, só trazer seu carro para avaliarmos!", msg_id)
             
            elif opcao == "3":
                enviar_msg(remote_jid, "O valor da nossa carga de gás é a partir de R$ 60 a cada 100 gramas, mas pode variar dependendo do sistema do seu veículo. Para um orçamento exato e seguro, traga seu carro para uma avaliação na nossa oficina! Atendemos por ondem de chegada.", msg_id)
            
            elif opcao == "4":
                enviar_msg(remote_jid, "A nossa higienização é a partir de R$ 240,00! Esse valor pode ter uma pequena alteração dependendo do modelo do filtro de cabine do seu carro.\nVamos agendar o seu horário conosco? 😊", msg_id)
            
            elif opcao == "5":
                enviar_msg(remote_jid, "Entendi! Para assuntos financeiros, por favor, chame nossa equipe diretamente através do contacto abaixo:\n📞 WhatsApp: [FINANCEIRO]\n🔗 Link: [LINK]\nEles vão te ajudar por lá! 👋", msg_id)
            
            ultima_saudacao[remote_jid] = hoje
            salvar_bd()
            return jsonify({"status": f"opcao_{opcao}"}), 200

        # Captura de dados (fluxo contínuo da opção 1)
        elif estados_clientes.get(remote_jid) == "aguardando_dados":
            enviar_msg(remote_jid, "Perfeito! Já recebemos os seus dados. Estamos a verificar a disponibilidade na nossa agenda para melhor te atender. Retornaremos o mais breve possível! ⏱️", msg_id)
            del estados_clientes[remote_jid]
            salvar_bd()
            return jsonify({"status": "dados_capturados"}), 200

        # Saudação Diária (Manda o menu apenas uma vez por dia)
        else:
            if ultima_saudacao.get(remote_jid) != hoje:
                menu = (f"Olá {push_name}, tudo bem? Somos da Refri Auto Ar Condicionado Automotivo! ❄️🚗\n"
                        "Para melhor te atender, por favor, digite o número da opção que deseja:\n\n"
                        "1 - Agendamento de atendimento externo\n"
                        "2 - Agendamento na oficina\n"
                        "3 - Carga de gás\n"
                        "4 - Higienização\n"
                        "5 - Falar com o financeiro")
                enviar_msg(remote_jid, menu, msg_id)
                ultima_saudacao[remote_jid] = hoje
                salvar_bd()

    except Exception as e:
        print(f"Erro no processamento do webhook: {e}")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # Inicia o servidor na porta 5000
    app.run(host="0.0.0.0", port=5000, threaded=True)
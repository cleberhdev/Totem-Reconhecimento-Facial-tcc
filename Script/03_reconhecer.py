import cv2
import face_recognition
import pickle
import numpy as np
import threading
import time
import os
import sqlite3
import requests 
import math
import sys
import socket
import jwt
import hashlib

from datetime import datetime, timedelta, timezone
from flask import Flask, Response, jsonify, request
from cryptography.fernet import Fernet

# Tenta importar o módulo do Laser (Labrador/Raspberry). Se não achar (Desktop), não quebra o código.
try:
    sys.path.append("./VL53L0X_rasp_python/python")
    import VL53L0X
    SENSOR_DISPONIVEL = True
except ImportError:
    print("[AVISO] Biblioteca VL53L0X não encontrada. Modo Desktop (sem laser) ativado.")
    SENSOR_DISPONIVEL = False

# ==============================================================================
# GESTÃO AUTOMÁTICA DE CHAVES (Não precisa mais passar via terminal)
# ==============================================================================
ARQUIVO_CHAVES = ".env"

def carregar_ou_gerar_chaves():
    if not os.path.exists(ARQUIVO_CHAVES):
        # Gera chaves perfeitas se não existirem
        nova_fernet = Fernet.generate_key().decode()
        nova_jwt = hashlib.sha256(os.urandom(32)).hexdigest()
        
        with open(ARQUIVO_CHAVES, "w") as f:
            f.write(f"CHAVE_BIOMETRIA={nova_fernet}\n")
            f.write(f"CHAVE_JWT={nova_jwt}\n")
        print("\n[SEGURANÇA LGPD] Chaves MESTRAS geradas e guardadas em '.env'!")
    
    chaves = {}
    with open(ARQUIVO_CHAVES, "r") as f:
        for linha in f:
            if "=" in linha:
                k, v = linha.strip().split("=", 1)
                chaves[k] = v
                
    return chaves.get("CHAVE_BIOMETRIA"), chaves.get("CHAVE_JWT")

CHAVE_SESSAO, CHAVE_JWT = carregar_ou_gerar_chaves()
fernet_cipher = Fernet(CHAVE_SESSAO.encode())

# ==============================================================================
# CONFIGURAÇÕES PRINCIPAIS
# ==============================================================================
ARQUIVO_DADOS = "encodings.pickle"
BANCO_DADOS = "totem_banco.db"
URL_CAMERA =  "http://192.168.1.37/stream" # Coloque o IP do Droidcam ou da Câmera IP
INTERVALO_SCAN_IA = 4.0
DELAY_RECONHECIMENTO = 5.0

LARGURA_TELA = 1024
ALTURA_TELA = 600

COR_RECONHECIDO = (0, 255, 0)
COR_TEXTO = (255, 255, 255)

MODO_RECONHECIMENTO = 0
MODO_CAPTURANDO = 1
MODO_INFO_REMOTO = 2

estado_atual = MODO_RECONHECIMENTO

app = Flask(__name__)
lock = threading.Lock()

# Variáveis globais para a UI
frame_atual = None
lista_encodings = []
lista_nomes = []
nome_novo_cadastro = ""
buffer_fotos_novas = []

# Variáveis partilhadas para a Thread da IA
ia_processando = False
caixas_detectadas = []
nomes_detectados = []
ultimo_sucesso = 0
nome_detectado = ""
ultimo_nome_reconhecido = None 

# Módulo Laser
DISTANCIA_GATILHO_MM = 800
# Se o sensor não existir (Desktop), assume que sempre tem alguém na frente para poder testar.
pessoa_na_frente = not SENSOR_DISPONIVEL 

# ==============================================================================
# SEGURANÇA E MATEMÁTICA LGPD
# ==============================================================================
ARQUIVO_MATRIZ = "matriz_projecao.npy"

def carregar_ou_gerar_matriz_ortogonal(dimensao=128):
    if os.path.exists(ARQUIVO_MATRIZ):
        return np.load(ARQUIVO_MATRIZ)
    else:
        H = np.random.randn(dimensao, dimensao)
        Q, R = np.linalg.qr(H)
        np.save(ARQUIVO_MATRIZ, Q)
        print("[SEGURANÇA LGPD] Nova Matriz Ortogonal de Bio-hashing gerada!")
        return Q

MATRIZ_PROJECAO = carregar_ou_gerar_matriz_ortogonal(128)

def ofuscar_nome(nome_real):
    texto_para_hash = f"CLINICA_TCC_{nome_real}"
    return hashlib.sha256(texto_para_hash.encode()).hexdigest()

def gerar_token_acesso(usuario_id, nome):
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario_id,
        "nome": nome,
        "nivel_acesso": "Paciente",
        "iat": agora,
        "exp": agora + timedelta(hours=2),
        "iss": "Totem_Recepcao_Labrador"
    }
    return jwt.encode(payload, CHAVE_JWT, algorithm="HS256")

# ==============================================================================
# HARDWARE E SENSORES (O RETORNO)
# ==============================================================================
def thread_sensor_distancia():
    global pessoa_na_frente
    if not SENSOR_DISPONIVEL:
        return

    try:
        sensor = VL53L0X.VL53L0X(address=0x29)
        sensor.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        print("[SENSOR] Laser VL53L0X Inicializado!")
    except Exception as e:
        print(f"[ERRO I2C] Falha fatal: {e}. Desativando trava do laser.")
        pessoa_na_frente = True
        return

    falhas = 0
    while True:
        try:
            dist = sensor.get_distance()
            if dist > 0:
                falhas = 0
                if 20 < dist < DISTANCIA_GATILHO_MM:
                    pessoa_na_frente = True
                else:
                    pessoa_na_frente = False
            else:
                falhas += 1
                pessoa_na_frente = False

            # Watchdog de reinicialização
            if falhas >= 3:
                try:
                    sensor.stop_ranging()
                    time.sleep(0.5)
                    sensor.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
                except: pass
                falhas = 0
            time.sleep(0.2)
        except:
            time.sleep(0.5)

def ler_temperatura():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000.0
        return round(temp, 1)
    except:
        return 0.0

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ==============================================================================
# BANCO DE DADOS
# ==============================================================================
def iniciar_banco():
    conn = sqlite3.connect(BANCO_DADOS)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS Usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE, data_cadastro DATETIME, nivel_acesso TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS Logs_Acesso (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER, data_hora DATETIME, confianca_reconhecimento REAL,
                    foto_momento TEXT, status_acesso TEXT DEFAULT 'LIBERADO',
                    tempo_inferencia_ms INTEGER DEFAULT 0, hardware_temp_c REAL DEFAULT 0.0,
                    FOREIGN KEY(usuario_id) REFERENCES Usuarios(id))""")
    conn.commit()
    conn.close()

def cadastrar_usuario_db(nome):
    conn = sqlite3.connect(BANCO_DADOS)
    c = conn.cursor()
    nome_ofuscado = ofuscar_nome(nome)
    try:
        c.execute("INSERT INTO Usuarios (nome, data_cadastro, nivel_acesso) VALUES (?, ?, ?)",
                  (nome_ofuscado, datetime.now(), "Aluno"))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def registrar_acesso_db(nome, confianca, frame_capturado, tempo_ms):
    conn = sqlite3.connect(BANCO_DADOS)
    c = conn.cursor()
    nome_ofuscado = ofuscar_nome(nome)
    
    c.execute("SELECT id FROM Usuarios WHERE nome = ?", (nome_ofuscado,))
    row = c.fetchone()
    
    if not row:
        c.execute("INSERT INTO Usuarios (nome, data_cadastro, nivel_acesso) VALUES (?, ?, ?)",
                  (nome_ofuscado, datetime.now(), "Migrado"))
        conn.commit()
        user_id = c.lastrowid
    else:
        user_id = row[0]

    agora_dt = datetime.now()
    temp_c = ler_temperatura()

    c.execute("""INSERT INTO Logs_Acesso (usuario_id, data_hora, confianca_reconhecimento, 
                 foto_momento, tempo_inferencia_ms, hardware_temp_c) VALUES (?, ?, ?, ?, ?, ?)""",
              (user_id, agora_dt, confianca, "FOTO_DESCARTADA", tempo_ms, temp_c))
    
    conn.commit()
    print(f"[AUDITORIA] Acesso salvo | Confiança: {confianca}% | Temp: {temp_c}ºC")
    conn.close()
    return user_id
# ==============================================================================
# VÍDEO STREAM (O MELHOR DO ANTIGO + PROTEÇÕES DO NOVO)
# ==============================================================================
class VideoStream:
    def __init__(self, src):
        self.src = src
        self.stream = None
        self.bytes_buffer = bytes()
        self.ultimo_frame = None
        self.rodando = False
        self.lock = threading.Lock()

    def start(self):
        self.rodando = True
        t = threading.Thread(target=self.update)
        t.daemon = True
        t.start()
        return self

    def update(self):
        while self.rodando:
            try:
                if self.stream is None:
                    print(f"\n[REDE] Tentando conectar na câmera: {self.src}...")
                    # Timeout de 10s para a conexão inicial não ser abortada precipitadamente
                    self.stream = requests.get(self.src, stream=True, timeout=10)
                    print("[REDE] Conexão bem-sucedida! Recebendo vídeo...")

                for chunk in self.stream.iter_content(chunk_size=4096):
                    if not self.rodando:
                        if self.stream:
                            self.stream.close()
                        break
                    
                    self.bytes_buffer += chunk
                    
                    if len(self.bytes_buffer) > 307200:
                        print("[AVISO] Buffer estourou. Limpando lixo da rede...")
                        self.bytes_buffer = bytes()
                        continue

                    a = self.bytes_buffer.find(b"\xff\xd8")
                    b = self.bytes_buffer.find(b"\xff\xd9")
                    
                    if a != -1 and b != -1:
                        if a < b:
                            jpg = self.bytes_buffer[a : b + 2]
                            self.bytes_buffer = self.bytes_buffer[b + 2 :]
                            img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            
                            if img is not None:
                                with self.lock:
                                    self.ultimo_frame = img
                            else:
                                print("[AVISO] Imagem corrompida descartada.")
                        else:
                            self.bytes_buffer = self.bytes_buffer[a:]
                            
            except requests.exceptions.RequestException as e:
                # Agora o terminal vai exibir exatamente porque a câmera não aparece!
                print(f"[ERRO DE REDE] O Labrador não consegue falar com a ESP32! Erro: {e}")
                if self.stream:
                    self.stream.close()
                self.stream = None
                self.bytes_buffer = bytes()
                time.sleep(3)
            except Exception as e:
                print(f"[ERRO DESCONHECIDO] {e}")
                if self.stream:
                    self.stream.close()
                self.stream = None
                self.bytes_buffer = bytes()
                time.sleep(3)

    def read(self):
        with self.lock:
            if self.ultimo_frame is not None:
                return self.ultimo_frame.copy()
            return None

    def stop(self):
        self.rodando = False
# ==============================================================================
# GESTÃO DA BIOMETRIA (PICKLE + FERNET)
# ==============================================================================
def carregar_dados():
    global lista_encodings, lista_nomes
    try:
        with open(ARQUIVO_DADOS, "rb") as f:
            dados_cifrados = f.read()
        dados_em_bytes = fernet_cipher.decrypt(dados_cifrados)
        data = pickle.loads(dados_em_bytes)
        lista_encodings = data["encodings"]
        lista_nomes = data["names"]
    except FileNotFoundError:
        lista_encodings, lista_nomes = [], []
    except Exception as e:
        print(f"[ERRO CRÍTICO LGPD] Falha na biometria: {e}")
        lista_encodings, lista_nomes = [], []

def salvar_dados():
    global lista_encodings, lista_nomes
    data = {"encodings": lista_encodings, "names": lista_nomes}
    dados_em_bytes = pickle.dumps(data)
    dados_cifrados = fernet_cipher.encrypt(dados_em_bytes)
    with open(ARQUIVO_DADOS, "wb") as f:
        f.write(dados_cifrados)

def treinar_novas_fotos(nome, lista_fotos):
    global lista_encodings, lista_nomes
    rostos_extraidos = 0

    for img in lista_fotos:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        encs = face_recognition.face_encodings(rgb, boxes, num_jitters=5)
        
        for enc in encs:
            with lock:
                enc_cancelavel = np.dot(enc, MATRIZ_PROJECAO)
                lista_encodings.append(enc_cancelavel)
                lista_nomes.append(nome)
                rostos_extraidos += 1
    
    if rostos_extraidos > 0:
        cadastrar_usuario_db(nome)
        salvar_dados()
        print(f"[IA] {rostos_extraidos} vetores salvos para '{nome}'.")

# ==============================================================================
# THREAD DA IA (ASSÍNCRONA)
# ==============================================================================
def processar_ia_async(frame_ia, frame_cru_ia):
    global ia_processando, caixas_detectadas, nomes_detectados, ultimo_sucesso, nome_detectado
    global ultimo_nome_reconhecido
    
    try:
        inicio_inferencia = time.time()
        agora = inicio_inferencia

        small = cv2.resize(frame_ia, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        locs_small = face_recognition.face_locations(rgb_small)
        
        if not locs_small:
            with lock:
                ultimo_nome_reconhecido = None
                caixas_detectadas = []
                nomes_detectados = []
            return

        locs_full = [(top * 4, right * 4, bottom * 4, left * 4) for (top, right, bottom, left) in locs_small]
        rgb_full = cv2.cvtColor(frame_ia, cv2.COLOR_BGR2RGB)
        encs = face_recognition.face_encodings(rgb_full, locs_full, num_jitters=1)

        novas_caixas = locs_small
        novos_nomes = []

        for enc in encs:
            name = "Desconhecido"
            with lock:
                enc_cancelavel = np.dot(enc, MATRIZ_PROJECAO)
                face_distances = face_recognition.face_distance(lista_encodings, enc_cancelavel)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if face_distances[best_match_index] < 0.45:
                        name = lista_nomes[best_match_index]

            with lock:
                if name == "Desconhecido":
                    ultimo_sucesso = agora
                    nome_detectado = name
                    ultimo_nome_reconhecido = None
                else:
                    if name != ultimo_nome_reconhecido:
                        tempo_ms = int((time.time() - inicio_inferencia) * 1000)
                        confianca_pct = round((1.0 - face_distances[best_match_index]) * 100, 2) if len(face_distances) > 0 else 0.0
                        
                        id_pac = registrar_acesso_db(name, confianca_pct, frame_cru_ia.copy(), tempo_ms)
                        token_jwt = gerar_token_acesso(id_pac, name)
                        
                        ultimo_nome_reconhecido = name  
                        ultimo_sucesso = agora
                        nome_detectado = name

            novos_nomes.append(name)

        with lock:
            caixas_detectadas = novas_caixas
            nomes_detectados = novos_nomes

    except Exception as e:
        print(f"[ERRO IA] {e}")
    finally:
        ia_processando = False

# ==============================================================================
# UI E CLIQUES
# ==============================================================================
def desenhar_interface(frame):
    # Fundo sólido cinza escuro para a barra inferior (MUITO mais leve que addWeighted)
    cv2.rectangle(frame, (0, ALTURA_TELA - 100), (LARGURA_TELA, ALTURA_TELA), (30, 30, 30), -1) 
    
    # Botão 1
    cv2.rectangle(frame, (50, ALTURA_TELA - 80), (300, ALTURA_TELA - 20), (100, 0, 0), -1)    
    cv2.rectangle(frame, (50, ALTURA_TELA - 80), (300, ALTURA_TELA - 20), COR_TEXTO, 1)
    cv2.putText(frame, "Capturar Rosto", (90, ALTURA_TELA - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COR_TEXTO, 2)
    
    # Botão 2
    cv2.rectangle(frame, (350, ALTURA_TELA - 80), (600, ALTURA_TELA - 20), (100, 0, 0), -1)   
    cv2.rectangle(frame, (350, ALTURA_TELA - 80), (600, ALTURA_TELA - 20), COR_TEXTO, 1)
    cv2.putText(frame, "Modo Servidor", (390, ALTURA_TELA - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COR_TEXTO, 2)
    
def gerenciar_cliques(event, x, y, flags, param):
    global estado_atual, nome_novo_cadastro, buffer_fotos_novas
    if event == cv2.EVENT_LBUTTONDOWN:
        if estado_atual == MODO_RECONHECIMENTO:
            if (ALTURA_TELA - 80) < y < (ALTURA_TELA - 20):
                if 50 < x < 300:
                    estado_atual = MODO_CAPTURANDO
                    nome_novo_cadastro = ""
                    buffer_fotos_novas = []
                elif 350 < x < 600:
                    estado_atual = MODO_INFO_REMOTO
        elif y < (ALTURA_TELA - 100):
            estado_atual = MODO_RECONHECIMENTO

# ==============================================================================
# LOOP PRINCIPAL DO TOTEM
# ==============================================================================
def loop_principal():
    global frame_atual, estado_atual, nome_novo_cadastro, buffer_fotos_novas
    global ia_processando, caixas_detectadas, nomes_detectados, ultimo_sucesso, nome_detectado

    stream = VideoStream(URL_CAMERA).start()
    time.sleep(2)

    cv2.namedWindow("Totem", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Totem", gerenciar_cliques)
    cv2.resizeWindow("Totem", LARGURA_TELA, ALTURA_TELA)
    cv2.setWindowProperty("Totem", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    ultimo_ia = 0
    meu_ip = obter_ip_local()

    while True:
        frame_cru = stream.read()
        if frame_cru is None:
            frame_vazio = np.zeros((ALTURA_TELA, LARGURA_TELA, 3), dtype=np.uint8)
            cv2.putText(frame_vazio, "CONECTANDO A ESP32-CAM...", (LARGURA_TELA//2 - 250, ALTURA_TELA//2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            cv2.imshow("Totem", frame_vazio)
            cv2.waitKey(33)
            continue

        frame = cv2.resize(frame_cru, (LARGURA_TELA, ALTURA_TELA))
        agora = time.time()

        if estado_atual == MODO_RECONHECIMENTO:
            desenhar_interface(frame)

            if pessoa_na_frente:
                # O bloqueio da IA também respeita a barra de aviso (DELAY_RECONHECIMENTO)
                if not ia_processando and (agora - ultimo_ia) > INTERVALO_SCAN_IA and (agora - ultimo_sucesso) > DELAY_RECONHECIMENTO:
                    ultimo_ia = agora
                    ia_processando = True
                    
                    t_ia = threading.Thread(target=processar_ia_async, args=(frame.copy(), frame_cru.copy()))
                    t_ia.daemon = True
                    t_ia.start()

                with lock:
                    caixas_locais = caixas_detectadas.copy()
                    nomes_locais = nomes_detectados.copy()

                for (top, right, bottom, left), name in zip(caixas_locais, nomes_locais):
                    top, right, bottom, left = top*4, right*4, bottom*4, left*4
                    cor = COR_RECONHECIDO if name != "Desconhecido" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), cor, 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), cor, cv2.FILLED)
                    cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COR_TEXTO, 1)
            else:
                with lock:
                    caixas_detectadas = []
                    nomes_detectados = []
                cv2.putText(frame, "Aproxime-se do Totem para liberar acesso", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

            if (agora - ultimo_sucesso) < DELAY_RECONHECIMENTO:
                tempo_restante = int(DELAY_RECONHECIMENTO - (agora - ultimo_sucesso))
                
                if nome_detectado == "Desconhecido":
                    cor_fundo = (0, 0, 200) 
                    texto_principal = "ACESSO NEGADO: Desconhecido"
                else:
                    cor_fundo = (0, 200, 0)
                    texto_principal = f"ACESSO LIBERADO: {nome_detectado}"

                cv2.rectangle(frame, (0, 0), (LARGURA_TELA, 80), cor_fundo, -1)
                cv2.putText(frame, texto_principal, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, COR_TEXTO, 3)
                # Afastado 250 pixels da borda para não sobrepor o texto principal
                cv2.putText(frame, f"Aguarde {tempo_restante}s...", (LARGURA_TELA - 250, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COR_TEXTO, 2)

        elif estado_atual == MODO_CAPTURANDO:
            cv2.rectangle(frame, (0, 0), (LARGURA_TELA, 170), (30, 30, 30), -1)
            
            cv2.putText(frame, f"NOME: {nome_novo_cadastro}_", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, COR_TEXTO, 2)
            cv2.putText(frame, f"[+] TIRAR FOTO ({len(buffer_fotos_novas)})  |  [ENTER] SALVAR  |  [ESC] VOLTAR", (50, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

            qtd = len(buffer_fotos_novas)
            inst = "PASSO 1: Olhe para a frente e aperte [+]" if qtd == 0 else \
                   "PASSO 2: Vire o rosto para a ESQUERDA e aperte [+]" if qtd == 1 else \
                   "PASSO 3: Vire o rosto para a DIREITA e aperte [+]" if qtd == 2 else \
                   "PASSO 4: Incline o rosto para CIMA e aperte [+]" if qtd == 3 else \
                   "PASSO 5: Feche os OLHOS e aperte [+]" if qtd == 4 else \
                   "EXCELENTE! Aperte [ENTER] para salvar."
            cv2.putText(frame, inst, (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        elif estado_atual == MODO_INFO_REMOTO:
            cv2.rectangle(frame, (150, 150), (LARGURA_TELA - 150, ALTURA_TELA - 100), (15, 15, 15), -1)
            
            cv2.rectangle(frame, (150, 150), (LARGURA_TELA - 150, ALTURA_TELA - 100), COR_RECONHECIDO, 2)
            cv2.putText(frame, "MODO SERVIDOR", (320, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.5, COR_RECONHECIDO, 2)
            cv2.putText(frame, f"Servidor ativo em: {meu_ip}:5000", (220, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(frame, "- Relatorio Logs: /api/relatorio", (220, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COR_TEXTO, 2)
            cv2.putText(frame, "- API Cadastro:   /api/cadastrar_direto", (220, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COR_TEXTO, 2)
            cv2.putText(frame, "[ESC] VOLTAR", (430, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COR_TEXTO, 2)
            
        cv2.imshow("Totem", frame)
        with lock:
            frame_atual = frame.copy()

        key = cv2.waitKey(33) & 0xFF
        if estado_atual == MODO_CAPTURANDO:
            if key == 13: # ENTER
                if buffer_fotos_novas and nome_novo_cadastro:
                    cv2.rectangle(frame, (0, 0), (LARGURA_TELA, ALTURA_TELA), (20, 20, 20), -1)
                    cv2.putText(frame, "PROCESSANDO BIOMETRIA...", (200, ALTURA_TELA // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, COR_RECONHECIDO, 3)
                    cv2.imshow("Totem", frame)
                    cv2.waitKey(100) 
                    treinar_novas_fotos(nome_novo_cadastro, buffer_fotos_novas)
                    estado_atual = MODO_RECONHECIMENTO
            elif key == 27: estado_atual = MODO_RECONHECIMENTO
            elif key == 43: buffer_fotos_novas.append(frame_cru.copy())
            elif key == 32: nome_novo_cadastro += " "
            elif key == 8: nome_novo_cadastro = nome_novo_cadastro[:-1]
            elif 33 <= key <= 126: nome_novo_cadastro += chr(key)

        if key == 9: # Pressione TAB para sair
            break

    stream.stop()
    cv2.destroyAllWindows()

# ==============================================================================
# API FLASK
# ==============================================================================
@app.route("/api/cadastrar_direto", methods=["POST"])
def cadastrar_direto():
    global lista_encodings, lista_nomes
    if "foto" not in request.files or "nome" not in request.form:
        return jsonify({"erro": "Dados incompletos"}), 400

    file = request.files["foto"]
    name = request.form["nome"]
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    if img is None: return jsonify({"erro": "Imagem invalida"}), 400

    rgb = cv2.cvtColor(cv2.resize(img, (800, int(img.shape[0] * (800.0 / img.shape[1])))), cv2.COLOR_BGR2RGB)

    with lock:
        boxes = face_recognition.face_locations(rgb)
        if boxes:
            encs = face_recognition.face_encodings(rgb, boxes, num_jitters=5)
            if encs:
                enc_cancelavel = np.dot(encs[0], MATRIZ_PROJECAO)
                cadastrar_usuario_db(name)
                lista_encodings.append(enc_cancelavel)
                lista_nomes.append(name)
                salvar_dados()
                return jsonify({"msg": f"Sucesso! {name} cadastrado."}), 201

    return jsonify({"erro": "Rosto nao encontrado"}), 400

@app.route("/video_feed")
def video_feed():
    def gen():
        while True:
            with lock:
                if frame_atual is not None:
                    _, enc = cv2.imencode(".jpg", frame_atual)
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + bytearray(enc) + b"\r\n")
            time.sleep(0.1)
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

def rodar_servidor():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    iniciar_banco()
    carregar_dados()

    t_sensor = threading.Thread(target=thread_sensor_distancia)
    t_sensor.daemon = True
    t_sensor.start()

    t_flask = threading.Thread(target=rodar_servidor)
    t_flask.daemon = True
    t_flask.start()

    loop_principal()
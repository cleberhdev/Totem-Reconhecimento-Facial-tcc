# 🛡️ Sistema de Reconhecimento Facial Seguro (Adequado à LGPD)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![LGPD](https://img.shields.io/badge/Compliance-LGPD-success)
![Security](https://img.shields.io/badge/Security-AES--128%20%7C%20JWT%20%7C%20SHA--256-red)

**Autor:** Cleber Henrique Lacerda Duarte  
**Projeto:** Trabalho de Conclusão de Curso (TCC) - IFPI Campus Floriano  

## 📖 Sobre o Projeto
Este projeto consiste em um protótipo de **Totem de Reconhecimento Facial** voltado para o registro de consultas clínicas. O seu grande diferencial é a implementação rigorosa de protocolos de segurança da informação para garantir a **privacidade e a proteção de dados biométricos**, em total conformidade com a Lei Geral de Proteção de Dados (LGPD).

O sistema atua como um **Provedor de Identidade (IdP)**: ele valida a face do paciente localmente e interage com o sistema da clínica apenas através de tokens efêmeros, garantindo que o dado biométrico bruto nunca trafegue na rede.

---

## 🔒 Pilares de Segurança e LGPD Implementados

1. **Privacy by Design (Não-persistência):** Imagens brutas (`.jpg`, `.png`) capturadas pela câmera ou enviadas via rede vivem exclusivamente na memória RAM volátil. Elas são destruídas imediatamente após a extração matemática do vetor facial.
2. **Biometria Cancelável (Bio-hashing):** Os vetores biométricos (128D) são multiplicados por uma Matriz Ortogonal secreta (`numpy`) antes de serem armazenados. Isso distorce a face matematicamente, tornando a reversão impossível caso a base vaze.
3. **Criptografia Data-at-Rest (Fernet):** O banco de biometrias é criptografado em repouso usando o padrão AES-128. O sistema não grava chaves no disco; elas são injetadas via Variáveis de Ambiente do Sistema Operacional.
4. **Tokenização (JWT):** Após reconhecer o paciente, o Totem emite um *JSON Web Token* assinado criptograficamente com 2 horas de validade para a API da clínica.
5. **Pseudonimização (SQLite):** Nomes civis e identidades reais não são gravados no banco de dados local. Utiliza-se *hashing* unidirecional (SHA-256) com *salt* para registrar logs e métricas de forma anônima.

---

## 📂 Organização de Arquivos

Devido à arquitetura focada em segurança, pastas comuns em projetos de visão computacional (como `dataset/` ou `logs_imagens/`) foram **eliminadas**. A estrutura atual é minimalista:

```text
/
├── 03_reconhecer.py          # Script principal (Totem + API Flask local)
├── matriz_projecao.npy       # [GERADO AUTOMATICAMENTE] Matriz ortogonal secreta (Bio-hashing)
├── encodings.pickle          # [GERADO AUTOMATICAMENTE] Cofre biométrico cifrado (Fernet)
├── totem_banco.db            # [GERADO AUTOMATICAMENTE] Banco SQLite pseudonimizado (Logs)
└── README.md                 # Documentação do projeto

```

---

## 🛠️ Tecnologias e Bibliotecas

O projeto utiliza bibliotecas nativas do Python para segurança e bibliotecas externas para Visão Computacional.

**Bibliotecas Externas (Requerem Instalação):**

* `opencv-python` (`cv2`): Captura e renderização de vídeo/interface.
* `face_recognition`: Extração de *embeddings* faciais com IA.
* `numpy`: Álgebra linear, geração da matriz ortogonal (Decomposição QR) e Bio-hashing.
* `cryptography`: Camada *Fernet* para Criptografia Simétrica (AES) do banco de dados.
* `PyJWT`: Geração e assinatura dos tokens de acesso.
* `Flask`: Servidor web integrado para recebimento de cadastros remotos e consultas de logs.

**Bibliotecas Nativas (Embutidas no Python):**

* `hashlib` (SHA-256 para pseudonimização), `os`, `sys`, `sqlite3`, `pickle`, `threading`, `time`, `datetime`, `socket`.

---

## 🚀 Como Configurar e Executar

### 1. Instalação das Dependências

Abra o terminal e instale os pacotes necessários:

```bash
pip install opencv-python face_recognition numpy cryptography PyJWT flask

```

### 2. Configuração das Variáveis de Ambiente (Chaves de Segurança)

O Totem não inicia se as chaves criptográficas não estiverem configuradas na memória do Sistema Operacional.

* Gere uma chave Fernet válida (você pode rodar `from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())` em um terminal Python para obter uma).
* Configure no seu terminal/sistema antes de rodar o script:

**No Windows (PowerShell):**

```powershell
$env:CHAVE_BIOMETRIA="sua_chave_fernet_gerada_aqui"
$env:CHAVE_JWT="sua_senha_super_secreta_para_assinar_tokens"

```

**No Linux/Labrador (Terminal):**

```bash
export CHAVE_BIOMETRIA="sua_chave_fernet_gerada_aqui"
export CHAVE_JWT="sua_senha_super_secreta_para_assinar_tokens"

```

### 3. Execução

Com a câmera conectada (ou o IP do DroidCam configurado no script), inicie o Totem:

```bash
python 03_reconhecer.py

```

*(Na primeira execução, o sistema gerará automaticamente a matriz ortogonal, o banco SQLite e iniciará o cofre biométrico).*

---

## 🧠 Estrutura do Código (`03_reconhecer.py`)

O script funciona baseado em **Processamento Assíncrono (Multithreading)** para não travar o vídeo da câmera durante cálculos matemáticos pesados:

1. **Thread Principal (Loop Visual):** Mantém a interface gráfica rodando a 30+ FPS, lendo os *frames* da câmera e desenhando retângulos de reconhecimento. Ocupa-se estritamente de UI/UX.
2. **Thread da IA (`processar_ia_async`):** Disparada a cada `X` segundos. Captura um *frame* congelado, extrai a biometria, aplica o Bio-hashing, compara com o banco de dados descriptografado em memória, gera o log pseudonimizado e emite o Token JWT no terminal.
3. **Thread do Servidor (`rodar_servidor`):** Mantém o Flask rodando na porta 5000. Fornece rotas para o sistema central da clínica:
* `POST /api/cadastrar_direto`: Recebe uma foto da recepção, extrai o *embedding*, aplica Bio-hashing, salva no cofre criptografado e descarta a imagem.
* `GET /api/relatorio`: Retorna os logs do SQLite.
* `GET /video_feed`: Rota para monitoramento remoto do Totem.



---

*Projeto desenvolvido para fins acadêmicos e pesquisa em Segurança da Informação e Visão Computacional.*

```

```
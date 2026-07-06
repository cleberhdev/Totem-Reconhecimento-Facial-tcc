
# 🛡️ Sistema de Reconhecimento Facial Seguro na Borda (*Edge Computing*)

## 🔐 Arquitetura Privada e Compatível com LGPD

**Autor:** Cleber Henrique Lacerda Duarte
**Projeto:** Trabalho de Conclusão de Curso (TCC) — IFPI Campus Floriano

---

### 📌 Visão Geral

Este projeto implementa um Totem Inteligente de Reconhecimento Facial voltado para ambientes clínicos, com foco absoluto em segurança da informação e privacidade de dados biométricos.

Diferente de sistemas tradicionais centralizados na nuvem, esta solução foi projetada sob o paradigma da **Computação de Borda (*Edge Computing*)**, processando a Inteligência Artificial localmente e operando sob o princípio de **Zero exposição de dados sensíveis**. O sistema atua como um Provedor de Identidade (IdP), comunicando-se com sistemas externos exclusivamente por meio de *tokens* seguros e efêmeros.

---

### 🖥️ Arquitetura de Hardware Distribuída

Para otimizar o processamento e reduzir o custo de implantação, o sistema físico foi dividido em nós especializados:

* **Nó Sensor (Captura):** Microcontrolador **ESP32-CAM** (sensor óptico OV2640), responsável por transmitir o vídeo via rede local Wi-Fi (fluxo HTTP/MJPEG contínuo).
* **Nó de Processamento:** Microcomputador de placa única **Labrador 32-bits**, responsável pela interface gráfica (display HDMI touch), processamento multithreading e inferência biométrica (rodando de 20 a 30 FPS).
* **Gatilho de Hardware (*Event-Driven*):** Sensor de Tempo de Voo (ToF) a laser **VL53L0X** via I2C, que acorda a Inteligência Artificial apenas quando um paciente se aproxima a menos de 80 cm, poupando a CPU de sobrecargas térmicas.

---

### 🔐 Arquitetura de Segurança (LGPD *by Design*)

O sistema foi desenvolvido com múltiplas camadas de proteção, mitigando ataques físicos e lógicos:

1. **🧠 *Privacy by Design* (Não-persistência):**
* Nenhuma imagem bruta (.jpg, .png) é salva em disco.
* Os dados visuais existem exclusivamente na memória RAM volátil.
* Descarte matemático imediato logo após a extração das características fiduciais.


2. **🔄 Biometria Cancelável (*Bio-hashing*):**
* Vetores faciais (128D) são multiplicados por uma Matriz Ortogonal gerada aleatoriamente.
* A face original é matematicamente destruída (inviabilizando reconstrução facial via GANs).
* Em caso de violação, o *template* pode ser descartado e substituído.


3. **🔐 Criptografia de Dados em Repouso (*Data-at-rest*):**
* O arquivo de *embeddings* (`encodings.pickle`) é cifrado com **AES-128** (via biblioteca Fernet).
* As chaves criptográficas são lidas dinamicamente do arquivo `.env` restrito na Labrador, embaralhando os bytes caso o hardware seja subtraído.


4. **🕶️ Pseudonimização Estrutural:**
* O banco de dados relacional (SQLite) não armazena nomes em texto claro.
* Identificadores são ofuscados via função unidirecional **SHA-256**.


5. **🎟️ Tokenização Segura:**
* Emissão de **JWT** (JSON Web Token) com validade limitada.
* Comunicação segura com APIs e sistemas legados da clínica sem trafegar biometria.



---

### ⚙️ Tecnologias Utilizadas

**Linguagens e Firmwares:**

* Python 3.x (Motor de IA e Servidor na Labrador)
* C++ / API ESP-IDF (Firmware do ESP32-CAM)

**Bibliotecas Principais:**

* `opencv-python` → Captura de vídeo de rede e interface
* `face_recognition` → Extração de *embeddings* faciais baseada na rede FaceNet
* `numpy` → Processamento de tensores e matrizes de *Bio-hashing*
* `cryptography` → Cifragem simétrica AES-128
* `PyJWT` e `Flask` → Geração de *tokens* e orquestração de API local
* `python-dotenv` → Gerenciamento seguro de variáveis de ambiente no Totem
* `hashlib` e `sqlite3` → Anonimização e persistência local

---

### 🚀 Configuração e Execução no Totem

**1. Instale as dependências na placa Labrador**

```bash
pip install opencv-python face_recognition numpy cryptography PyJWT flask python-dotenv

```

**2. Geração Segura do Arquivo `.env**`
O sistema é blindado e não inicializará sem as chaves de segurança. Na primeira execução (ou via script de setup), o código gerará automaticamente as chaves fortes e criará um arquivo oculto `.env` na raiz do projeto na Labrador.

Este arquivo conterá as credenciais que serão carregadas diretamente para a memória RAM durante a execução, mantendo a arquitetura segura sem a necessidade de injeção manual a cada reinicialização da placa.

*Estrutura gerada no arquivo `.env`:*

```env
CHAVE_BIOMETRIA=SuaChaveFernetGeradaEmBase64=
CHAVE_JWT=SuaChaveJWTGeradaAleatoriamente

```

*(Atenção: O arquivo `.env` deve permanecer restrito na Labrador e jamais ser versionado no GitHub ou compartilhado).*

**3. Execute o nó principal**

```bash
python 03_reconhecer.py

```

---

### 🧠 Orquestração de Threads

Para garantir tempo de resposta de *check-in* inferior a 1 segundo e não travar a interface gráfica (mantendo fluidez na recepção), o Python opera com processamento assíncrono:

* **Thread Principal:** Busca os *frames* HTTP do ESP32-CAM via rede e atualiza a interface de vídeo em tempo real.
* **Thread de IA:** Captura um quadro limpo, processa a matriz, realiza a distância Euclidiana, gera o token e descarta a imagem.
* **Thread do Servidor (Flask):** Mantém os *endpoints* (ex: `/api/cadastrar_direto`) abertos para receber comandos remotos sem interromper a vigilância da câmera.

---

### 📊 Diferenciais do Projeto

* ✔️ Validação empírica de robustez facial contra oclusões (óculos, chapéus).
* ✔️ Arquitetura *Privacy by Design* documentada e auditada com provas matemáticas.
* ✔️ Proteção total contra roubo de *hardware* e injeção lógica de dados (*spoofing* do vetor).
* ✔️ Solução de borda totalmente automatizada, com gerenciamento seguro de chaves via `.env`.

---

### ⚠️ Aviso

Este projeto é um artefato tecnológico acadêmico desenvolvido sob a ótica da **Design Science Research (DSR)**, voltado para pesquisa aplicada em Segurança da Informação e Visão Computacional no Setor de Saúde.

### 📄 Licença e Contato

Desenvolvido para fins de estudo e defesa acadêmica. Para escalabilidade comercial ou integração em sistemas hospitalares reais em produção, recomenda-se auditoria de infraestrutura e aplicação de hardware biométrico com sensores liveness (*Anti-spoofing 3D*).

🔐 *Segurança não é um recurso — é um requisito.*

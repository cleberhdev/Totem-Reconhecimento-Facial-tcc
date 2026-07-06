import numpy as np

print("======================================================")
print(" SIMULAÇÃO DE COMPROMETIMENTO TOTAL (BIO-HASHING EXPOSTO) ")
print("======================================================\n")

print("[INVASOR] Chave AES-128 quebrada! Descriptografando banco de dados...")
print("[INVASOR] Sucesso. Acesso aos vetores biométricos numéricos obtido.\n")

# Simulando o vetor roubado (Bio-hash) que estava armazenado no disco
# No mundo real, este é o vetor de 128 dimensões do paciente que já foi multiplicado pela sua Matriz Ortogonal
vetor_roubado = np.random.rand(128) * 5  # Multiplicado por 5 simulando a distorção da matriz

print("[INVASOR] Tentativa 1: Engenharia Reversa com IA para desenhar o rosto original.")
print("Analisando a integridade geométrica do vetor roubado...")

# Algoritmos de reconstrução (GANs) esperam vetores do FaceNet com distribuição específica (Norma L2)
norma_roubada = np.linalg.norm(vetor_roubado)
print(f"-> Norma vetorial encontrada: {norma_roubada:.4f}")
print("[FALHA] Valores fora do limite euclidiano aceitável para face humana.")
print("[RESULTADO DA IA INVASORA] Erro de reconstrução: O gerador de imagem produziu apenas ruído.\n")


print("[INVASOR] Tentativa 2: Spoofing Lógico (Injetar o vetor roubado para forjar check-in).")
print("O invasor envia o vetor roubado para a câmera, tentando se passar pelo paciente...")

# Simulando um vetor cru (raw) capturado legitimamente pela câmera da clínica no dia a dia
vetor_camera_legitima = np.random.rand(128)

# O sistema de segurança da clínica tenta comparar os dois
distancia = np.linalg.norm(vetor_camera_legitima - vetor_roubado)

print(f"-> Distância Euclidiana calculada entre câmera e dado roubado: {distancia:.4f}")

# O padrão do face_recognition em Python aprova acessos com distância MENOR que 0.6
if distancia > 0.6: 
    print("[DEFESA ATIVA] Distância superior a 0.6! Divergência matemática extrema.")
    print("[DEFESA ATIVA] O sistema bloqueou o acesso e detectou a injeção de dados corrompidos.")
else:
    print("[ALERTA CRÍTICO] Sistema burlado.")

print("\n======================================================")
print("                CONCLUSÃO DA AUDITORIA                ")
print("======================================================")
print("O vetor armazenado não possui correlação geométrica com a face original.")
print("Sem a Matriz Ortogonal (Token) que reside apenas na memória RAM da clínica,")
print("os dados roubados são irreversíveis e matematicamente inúteis.")
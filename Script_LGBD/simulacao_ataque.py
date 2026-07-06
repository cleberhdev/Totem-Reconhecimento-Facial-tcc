import pickle

# Coloque aqui o nome exato do arquivo físico que guarda as biometrias no seu projeto
arquivo_roubado = "encodings.pickle"

print("======================================================")
print("   SIMULAÇÃO DE ENGENHARIA REVERSA (ROUBO DE DADOS)   ")
print("======================================================\n")

print(f"[INVASOR] Tentando acessar o arquivo físico: '{arquivo_roubado}'...")

try:
    # O invasor consegue acessar o disco e ler os bytes do arquivo
    with open(arquivo_roubado, "rb") as file:
        dados_brutos = file.read()
        
    print("[INVASOR] Sucesso! Arquivo lido do disco.")
    print("[INVASOR] Tentando extrair as matrizes faciais usando pickle...\n")
    
    # O invasor tenta desserializar os dados (transformar os bytes de volta em arrays/dicionários)
    dados_roubados = pickle.loads(dados_brutos)
    
    # Se o código chegar nesta linha, significa que o arquivo NÃO estava criptografado
    print("[FALHA DE SEGURANÇA CRÍTICA] Os dados foram expostos!")
    print(dados_roubados)

except pickle.UnpicklingError:
    # O pickle não consegue ler bytes criptografados pelo Fernet
    print("-------------------- RESULTADO --------------------")
    print("[DEFESA ATIVA] Falha ao ler o arquivo (pickle.UnpicklingError).")
    print("[DEFESA ATIVA] O arquivo está cifrado com AES-128 e é matematicamente ilegível sem a chave simétrica.")
    print("\n[!] O que o invasor realmente enxerga ao abrir o arquivo (Bytes Ofuscados):")
    print(str(dados_brutos[:80]) + " ... (truncado)")

except Exception as e:
    # Captura outros erros genéricos de leitura de bytes inválidos
    print("-------------------- RESULTADO --------------------")
    print(f"[DEFESA ATIVA] Erro de decodificação detectado: {e}")
    print("[DEFESA ATIVA] Os dados em repouso estão protegidos conforme exigido pela LGPD.")
    print("\n[!] O que o invasor realmente enxerga ao abrir o arquivo (Bytes Ofuscados):")
    print(str(dados_brutos[:80]) + " ... (truncado)")

print("\n======================================================")
print("                SIMULAÇÃO CONCLUÍDA                   ")
print("======================================================")
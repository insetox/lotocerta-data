import json
import os
import requests
import time

LOTERIAS = [
    "megasena", "lotofacil", "quina", "lotomania", 
    "timemania", "duplasena", "diadesorte", "maismilionaria"
]

BASE_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api"
# Usa o mesmo User-Agent do seu app C# para não ser bloqueado pela Caixa
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppLotoCerta/1.0"}

def formatar_assinatura(dezenas):
    """Ordena e formata as dezenas no padrão XX-XX-XX idêntico ao C#"""
    numeros = sorted([int(d) for d in dezenas])
    return "-".join([f"{n:02d}" for n in numeros])

def atualizar_loterias():
    for loteria in LOTERIAS:
        arquivo = f"historico_resultados_{loteria}.json"
        
        # 1. Carrega o arquivo local do GitHub
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
        else:
            dados = {"LoteriaChave": loteria, "UltimoConcursoProcessado": 0, "Assinaturas": []}
            
        assinaturas_set = set(dados["Assinaturas"])
        ultimo_processado = dados["UltimoConcursoProcessado"]
        
        # 2. Descobre o último concurso sorteado
        try:
            r = requests.get(f"{BASE_URL}/{loteria}", headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            ultimo_api = r.json().get("numero", 0)
        except Exception as e:
            print(f"Erro ao consultar {loteria}: {e}")
            continue
            
        # 3. Baixa apenas o que falta
        if ultimo_api > ultimo_processado:
            print(f"Atualizando {loteria}: do {ultimo_processado} até o {ultimo_api}...")
            
            for concurso in range(ultimo_processado + 1, ultimo_api + 1):
                try:
                    res = requests.get(f"{BASE_URL}/{loteria}/{concurso}", headers=HEADERS, timeout=10)
                    if res.status_code == 200:
                        dezenas = res.json().get("listaDezenas", [])
                        if dezenas:
                            assinaturas_set.add(formatar_assinatura(dezenas))
                    time.sleep(0.5) # Pausa pequena para não sobrecarregar a Caixa
                except Exception as e:
                    print(f"Falha no concurso {concurso} de {loteria}: {e}")
                    
            # 4. Salva o JSON atualizado
            dados["UltimoConcursoProcessado"] = ultimo_api
            dados["Assinaturas"] = list(assinaturas_set)
            
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            print(f"✅ {loteria} atualizada!")
        else:
            print(f"⚡ {loteria} já está na última versão.")

if __name__ == "__main__":
    atualizar_loterias()
import json
import time
import unicodedata
from typing import Dict, Optional
from google_play_scraper import app, search

# ==============================
# CONFIG
# ==============================
SLEEP_TIME = 1
MAX_RETRIES = 2
OUTPUT_FILE = "versoes.json"

# ==============================
# BASE ORIGINAL
# ==============================
APP_IDS = {
    "ABC": "br.com.abcbrasil.bancoabcbrasil",
    "Accreditto": "",
    "Ailos": "br.com.ailos.app",
    "Ame Digital": "br.com.amedigital.ame",
    "Asaas": "br.com.asaas",
    "Banco do Brasil": "br.com.bb.android",
    "Banrisul": "br.com.banrisul",
    "BMG": "br.com.bancobmg.bmg",
    "Bradesco": "com.bradesco",
    "BTG Banking": "com.btg.app.retail",
    "C6": "com.c6bank.app",
    "Caixa": "br.gov.caixa.android",
    "Cora": "br.com.cora",
    "Digio": "br.com.digio.app",
    "Inter": "br.com.intermedium",
    "Itaú": "com.itau",
    "Mercado Pago": "com.mercadopago.wallet",
    "Neon": "br.com.neon",
    "Next": "br.com.bradesco.next",
    "Nubank": "com.nu.production",
    "PagBank": "br.com.uol.ps",
    "Pan": "br.com.bancopan.app",
    "Pic Pay": "com.picpay",
    "RecargaPay": "com.recargapay.recargapay",
    "Santander": "com.santander.app",
    "Sicoob": "br.com.sicoob.net",
    "Sicredi": "br.com.sicredi.mob",
    "Sofisa": "br.com.sofisadireto",
    "XP": "br.com.xp.carteira",
    "Crefisa": "br.com.crefisa.mobile",
    "Belvo": "",
    "Klavi": "",
    "Lina Openx": ""
}

# ==============================
# UTIL
# ==============================

def normalizar_nome(nome: str) -> str:
    """Remove acentos e padroniza string"""
    return unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII').lower()


def buscar_app_por_nome(nome: str) -> Optional[str]:
    """Busca appId automaticamente na Play Store"""
    try:
        resultados = search(nome, lang="pt", country="br", n_hits=3)

        if not resultados:
            return None

        # heurística simples: pega o mais relevante
        return resultados[0]["appId"]

    except Exception:
        return None


def obter_detalhes_app(package_id: str) -> Optional[dict]:
    """Busca detalhes com retry"""
    for tentativa in range(MAX_RETRIES):
        try:
            return app(package_id, lang='pt', country='br')
        except Exception:
            if tentativa < MAX_RETRIES - 1:
                time.sleep(1)
            else:
                return None


def extrair_versao(detalhes: dict) -> str:
    """Extrai versão tratada"""
    if not detalhes:
        return "Erro na loja"

    versao = detalhes.get("version")

    if not versao:
        return "Varia por dispositivo"

    if isinstance(versao, str) and "varia" in versao.lower():
        return "Varia por dispositivo"

    return versao


# ==============================
# CORE
# ==============================

def atualizar_versoes() -> Dict:
    resultados = {}
    cache_busca = {}

    print("🚀 Iniciando varredura inteligente...\n")

    for marca, package_id in APP_IDS.items():
        nome_normalizado = normalizar_nome(marca)

        print(f"🔎 Processando: {marca}")

        # ==============================
        # DISCOVERY (fallback)
        # ==============================
        if not package_id:
            if nome_normalizado in cache_busca:
                package_id = cache_busca[nome_normalizado]
            else:
                package_id = buscar_app_por_nome(marca)
                cache_busca[nome_normalizado] = package_id

        if not package_id:
            resultados[marca] = {
                "status": "SEM_APP",
                "versao": None
            }
            print(f"⚠️ {marca}: Sem app (provável B2B/Web)\n")
            continue

        # ==============================
        # FETCH
        # ==============================
        time.sleep(SLEEP_TIME)

        detalhes = obter_detalhes_app(package_id)

        if not detalhes:
            resultados[marca] = {
                "status": "ERRO",
                "package": package_id,
                "versao": None
            }
            print(f"❌ {marca}: erro ao consultar\n")
            continue

        versao = extrair_versao(detalhes)

        resultados[marca] = {
            "status": "OK",
            "package": package_id,
            "versao": versao
        }

        print(f"✅ {marca}: {versao}\n")

    # ==============================
    # SAVE
    # ==============================
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("🎯 Finalizado com sucesso!")

    return resultados


# ==============================
# ENTRYPOINT
# ==============================

if __name__ == "__main__":
    atualizar_versoes()
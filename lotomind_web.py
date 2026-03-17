import streamlit as st
import pandas as pd
import random
import requests
import json
import os
import urllib.parse
from collections import Counter, defaultdict
import datetime
import time
from supabase import create_client, Client
from itertools import combinations
from streamlit_cookies_manager import CookieManager
import streamlit.components.v1 as components

# Configuração da Página Web
st.set_page_config(
    page_title="Lotomind Web",
    page_icon="🍀",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ===== ESCONDE MENU 3 PONTINHOS, CABEÇALHO E RODAPÉ ===== */
#MainMenu {
    visibility: hidden;
}
header {
    visibility: hidden;
}
footer {
    display: none !important;
}

/* ===== REMOVE ESPAÇO SUPERIOR EXTRA ===== */
div.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* ===== ABAS DE NAVEGAÇÃO PRINCIPAL ===== */
/* Alinha as abas à direita, logo abaixo do cabeçalho */
div[data-testid="stTabs"] {
    margin-top: -60px; 
}
div[data-testid="stTabs"] div[role="tablist"] {
    justify-content: center;
    border-bottom: none !important;
    gap: 5px;
}
/* Estilo das abas */
div[data-testid="stTabs"] button[role="tab"] {
    background-color: transparent;
    border: none;
    color: #888; /* Cor para abas não selecionadas */
    font-weight: 700;
    font-size: 30px;
    transition: all 0.2s;
    border-radius: 8px 8px 0 0;
}
div[data-testid="stTabs"] button[role="tab"]:hover {
    color: {ROXO_MEDIO};
    background-color: #f0f2f6;
}
/* Aba selecionada */
div[data-testid="stTabs"] button[aria-selected="true"] {
    background-color: transparent;
    color: {ROXO_MEDIO};
    border-bottom: 3px solid {ROXO_MEDIO};
    border-radius: 0;
}

/* Popover de Conta (Menu do Usuário) */
div[data-testid="stPopover"] {
    display: flex;
    justify-content: flex-end; /* Alinha o botão do popover à direita */
    width: 100% !important;
}
div[data-testid="stPopover"] button[data-testid="baseButton-secondary"] {
    background-color: {ROXO_MEDIO} !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 20px;
    padding: 5px 15px;
}
div[data-testid="stPopover"] button[data-testid="baseButton-secondary"]:hover {
    background-color: {ROXO_CLARO} !important;
    color: white !important;
    border-color: {ROXO_CLARO} !important;
}

/* Botões dentro do Popover (Atualizar, Sair) */
div[data-testid="stPopover"] div[data-testid="stVerticalBlock"] button {
    background-color: {ROXO_MEDIO} !important;
    color: white !important;
    border: none !important;
    border-radius: 5px;
}
div[data-testid="stPopover"] div[data-testid="stVerticalBlock"] button:hover {
    background-color: {ROXO_ESCURO} !important;
}

</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DE IDIOMA ---
# Define o idioma para pt-BR para evitar pop-up de tradução do navegador
components.html("""
    <script>
        window.parent.document.documentElement.lang = 'pt-BR';
    </script>
""", height=0)

# --- CONFIGURAÇÕES ---
ARQUIVO_CACHE = "loto_completo_cache.json"
ARQUIVO_PALPITES = "meus_palpites.json"

# --- DEFINIÇÃO DE VARIÁVEIS DE CORES ---
# Roxo (3 Tons)
ROXO_CLARO = "#9370DB"   # MediumPurple
ROXO_MEDIO = "#4b0082"   # Indigo (Original)
ROXO_ESCURO = "#2E0050"  # Dark Indigo

# Verde (3 Tons)
VERDE_CLARO = "#D4EDDA"  # Light Green (Fundo suave)
VERDE_MEDIO = "#28a745"  # Green (Bootstrap Success)
VERDE_ESCURO = "#155724" # Dark Green (Texto/Hover)

# --- APLICAÇÃO DAS CORES (SEPARAÇÃO POR CONTEXTO) ---
# Geral
VAR_COR_FUNDO_APP = "#ffffff"       # Onde usar: Fundo geral da aplicação
VAR_COR_TEXTO_PRINCIPAL = "#31333F" # Onde usar: Texto padrão

# Títulos (H1, H2, H3...)
VAR_COR_TITULOS = ROXO_MEDIO        # Onde usar: Cabeçalhos principais

# Botões (Botão Principal 'Gerar')
VAR_COR_BOTAO_BG = VERDE_MEDIO      # Onde usar: Fundo do botão principal
VAR_COR_BOTAO_TXT = "#ffffff"       # Onde usar: Texto do botão principal
VAR_COR_BOTAO_HOVER = "#218838"     # Onde usar: Cor ao passar o mouse (Verde um pouco mais escuro)

# Sidebar (Barra Lateral)
VAR_COR_SIDEBAR_TITULOS = ROXO_MEDIO # Onde usar: Títulos dentro da sidebar
VAR_COR_SIDEBAR_TEXTO = VAR_COR_TEXTO_PRINCIPAL # Onde usar: Texto comum na sidebar
VAR_COR_SIDEBAR_BG = "#ffffff" # Fundo da Sidebar
VAR_COR_SIDEBAR_BORDER = ROXO_MEDIO # Borda da Sidebar
VAR_COR_SIDEBAR_MENU = ROXO_MEDIO # Cor independente para itens do menu (Navegação)

# Mensagem de Confiança (Aviso Específico)
VAR_COR_MSG_CONFIANCA_BG = VERDE_CLARO  # Onde usar: Fundo da caixa de mensagem de confiança
VAR_COR_MSG_CONFIANCA_TXT = VERDE_ESCURO # Onde usar: Texto da mensagem de confiança
VAR_COR_MSG_CONFIANCA_BORDA = VERDE_MEDIO # Onde usar: Borda da caixa de mensagem

# Números do Jogo (Display Grande)
VAR_COR_NUMEROS_JOGO = ROXO_MEDIO   # Onde usar: Números grandes do palpite gerado

# Bolas do Sorteio (Resultado)
VAR_COR_BOLAS_SORTEIO_BG = ROXO_MEDIO # Onde usar: Fundo das bolinhas do resultado
VAR_COR_BOLAS_SORTEIO_TXT = "#ffffff" # Onde usar: Número dentro das bolinhas

# Textos dos Resultados (API)
VAR_COR_TEXTO_RESULTADOS = "#000000" # Onde usar: Métricas e informações da API
VAR_COR_TEXTO_PROXIMO_CONCURSO = "#ffffff" # Onde usar: Texto do prêmio estimado e labels do card

# Tela de Login
VAR_COR_LOGIN_BEMVINDO = ROXO_MEDIO      # Onde usar: Texto "Bem-vindo!"
VAR_COR_LOGIN_TABS_TEXT = ROXO_MEDIO    # Onde usar: Texto das abas "Entrar", "Criar Conta"
VAR_COR_LOGIN_LABELS = ROXO_ESCURO # Onde usar: Labels "Usuário", "Senha"
VAR_COR_LOGIN_BOTAO_BG = ROXO_MEDIO     # Onde usar: Fundo do botão de login/cadastro
VAR_COR_LOGIN_BOTAO_TXT = "#ffffff"     # Onde usar: Texto do botão de login/cadastro
VAR_COR_LOGIN_BOTAO_HOVER = ROXO_ESCURO # Onde usar: Hover do botão de login/cadastro
VAR_COR_LOGIN_RADIO_LABEL = ROXO_MEDIO  # Onde usar: Texto dos radio buttons "Entrar" e "Criar Conta"

# Componentes de Formulário
VAR_COR_MULTISELECT_TAG_TXT = "#FFFFFF" # Onde usar: Texto da tag no multiselect

# --- ESTILOS VISUAIS (Fundo Branco + Compacto) ---
st.markdown(f"""
    <style>
        /* PALETA: Fundo Branco, Texto Escuro, Detalhes em Roxo */
        .stApp {{
            background-color: {VAR_COR_FUNDO_APP};
            color: {VAR_COR_TEXTO_PRINCIPAL};
        }}
        /* Títulos em Roxo da Lotofácil */
        h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
            color: {VAR_COR_TITULOS} !important;
        }}
        /* Sidebar com fundo branco e borda roxa */
        [data-testid="stSidebar"] {{
            background-color: {VAR_COR_SIDEBAR_BG} !important;
            border-right: 1px solid {VAR_COR_SIDEBAR_BORDER} !important; 
        }}
        /* Botões da Sidebar (Sair, Forçar Atualização) em Roxo */
        [data-testid="stSidebar"] div[data-testid="stButton"] > button {{
            background-color: {VAR_COR_SIDEBAR_TITULOS} !important;
            color: #ffffff !important;
            border: none !important;
        }}
        [data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {{
            background-color: {ROXO_ESCURO} !important;
            color: #ffffff !important;
        }}
        /* Botão Primário (Padrão - Sair) em ROXO */
        div[data-testid="stButton"] > button[kind="primary"] {{
            background-color: {ROXO_MEDIO} !important;
            color: {VAR_COR_BOTAO_TXT} !important;
            border: none;
        }}
        /* Garante que o texto dentro do botão (tag p) seja branco */
        div[data-testid="stButton"] > button[kind="primary"] p {{
            color: {VAR_COR_BOTAO_TXT} !important;
        }}
        div[data-testid="stButton"] > button[kind="primary"]:hover {{
            background-color: {ROXO_ESCURO} !important;
            color: {VAR_COR_BOTAO_TXT} !important;
        }}
        /* Botão Primário DENTRO DE ABAS (Gerar Palpite) em VERDE */
        div[data-testid="stTabs"] div[data-testid="stButton"] > button[kind="primary"] {{
            background-color: {VAR_COR_BOTAO_BG} !important;
        }}
        div[data-testid="stTabs"] div[data-testid="stButton"] > button[kind="primary"]:hover {{
            background-color: {VAR_COR_BOTAO_HOVER} !important;
            color: {VAR_COR_BOTAO_TXT} !important;
        }}
        /* Botão Secundário (Salvar/Outros na área principal) em PRETO */
        section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="secondary"] {{
            background-color: #000000 !important;
            color: #ffffff !important;
            border: none !important;
        }}
        /* Garante texto branco no botão secundário (Salvar) */
        section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="secondary"] p {{
            color: #ffffff !important;
        }}
        section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="secondary"]:hover {{
            background-color: #333333 !important;
            color: #ffffff !important;
        }}
        /* Botão de Link (WhatsApp) em PRETO */
        section[data-testid="stMain"] a[data-testid="stLinkButton"] {{
            background-color: #000000 !important;
            color: #ffffff !important;
            border: none !important;
        }}
        section[data-testid="stMain"] a[data-testid="stLinkButton"]:hover {{
            background-color: #333333 !important; /* Cinza escuro para hover de links genéricos (ex: WhatsApp) */
            color: #ffffff !important;
        }}
        /* Estilo específico para o botão Loterias Online */
        .loterias-button-wrapper a[data-testid="stLinkButton"] {{
            background-color: {ROXO_MEDIO} !important;
            color: #ffffff !important;
        }}
        .loterias-button-wrapper a[data-testid="stLinkButton"]:hover {{
            background-color: {ROXO_ESCURO} !important;
            color: #ffffff !important;
        }}
        /* SOBRESCREVE: Botão Primário DENTRO DE FORMS (Login/Cadastro) para Roxo */
        div[data-testid="stForm"] button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button {{
            background-color: {VAR_COR_LOGIN_BOTAO_BG} !important;
            color: {VAR_COR_LOGIN_BOTAO_TXT} !important;
            border-color: {VAR_COR_LOGIN_BOTAO_BG} !important;
        }}
        /* Forçar texto branco no elemento interno do botão (p) */
        div[data-testid="stForm"] button[kind="primary"] p,
        div[data-testid="stFormSubmitButton"] button p {{
            color: {VAR_COR_LOGIN_BOTAO_TXT} !important;
        }}
        /* Cor VERDE ao passar o mouse ou clicar */
        div[data-testid="stForm"] button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stForm"] button[kind="primary"]:active,
        div[data-testid="stFormSubmitButton"] button:active {{
            background-color: {VERDE_MEDIO} !important;
            border-color: {VERDE_MEDIO} !important;
            color: {VAR_COR_LOGIN_BOTAO_TXT} !important; /* Garante texto branco */
        }}
        /* Labels de Usuário/Senha na tela de login */
        div[data-testid="stForm"] label {{
            color: {VAR_COR_LOGIN_LABELS} !important;
        }}
        /* Texto dos Radio Buttons de Login (Entrar / Criar Conta) */
        div[role="radiogroup"] label p {{
            color: {VAR_COR_LOGIN_RADIO_LABEL} !important;
            font-weight: bold;
        }}
        /* Texto do Checkbox (Permanecer logado) em PRETO */
        div[data-testid="stForm"] [data-testid="stCheckbox"] label p,
        div[data-testid="stForm"] [data-testid="stCheckbox"] label span {{
            color: #000000 !important;
        }}
        /* Textos de Resultados (Metrics e Captions) em PRETO */
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stCaptionContainer"] p {{
            color: {VAR_COR_TEXTO_RESULTADOS} !important;
        }}
        /* Abas de Login/Navegação */
        [data-testid="stTabs"] button p {{
            color: {VAR_COR_LOGIN_TABS_TEXT} !important;
        }}
        /* Reduzir margens para ficar mais compacto */
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }}
        /* FORÇAR REMOÇÃO DO FUNDO AMARELO (WARNING) OU AZUL (INFO) */
        div[data-testid="stAlert"] {{
            background-color: #f9f9f9 !important;
            border: 1px solid #eeeeee !important;
            color: {VAR_COR_TEXTO_PRINCIPAL} !important;
        }}

/* === NOVOS BOTÕES DE GERAR PALPITE === */
.btn-verde-claro button {{
    background-color: {VERDE_MEDIO} !important;
    color: white !important;
    border: none !important;
}}
.btn-verde-claro button:hover {{
    background-color: {VERDE_ESCURO} !important;
}}

.btn-verde-escuro button {{
    background-color: {VERDE_ESCURO} !important;
    color: white !important;
    border: none !important;
}}
.btn-verde-escuro button:hover {{
    background-color: {VERDE_MEDIO} !important;
}}

/* === DIALOG PERSONALIZADO COM FUNDO BRANCO === */
div[data-testid="stDialog"] > div:first-child > div:first-child {{
    background-color: white;
}}
div[data-testid="stDialog"] h2, div[data-testid="stDialog"] p, div[data-testid="stDialog"] span, div[data-testid="stDialog"] label {{
    color: #31333F !important;
}}
div[data-testid="stDialog"] button[kind="primary"] p {{
     color: white !important;
}}

/* === NOVO: ESTILO PARA MÉTRICAS SELECIONADAS NO DIALOG === */
div[data-testid="stDialog"] div[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
    background-color: {ROXO_MEDIO} !important;
    padding-top: 4px;
    padding-bottom: 4px;
}}
/* Força a cor do texto dentro da tag, que é um span */
div[data-testid="stDialog"] div[data-testid="stMultiSelect"] [data-baseweb="tag"] span {{
    color: {VAR_COR_MULTISELECT_TAG_TXT} !important;
}}
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS E LÓGICA (Mantendo a original) ---

# Cache do CookieManager para evitar recriação e perda de sessão
cookie_manager = CookieManager()

if not cookie_manager.ready():
    st.stop()


# Conexão com Supabase
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        print(f"⚠️ Erro ao conectar Supabase: {e}")
        return None

supabase_client = init_supabase()

# --- FUNÇÕES DE AUTENTICAÇÃO (SISTEMA PRÓPRIO) ---
def get_user_db(username):
    if not supabase_client: return None
    try:
        # Busca usuário na tabela 'users'
        response = supabase_client.table("users").select("*").eq("username", username).execute()
        if response.data: return response.data[0]
    except: pass
    return None

def register_user_db(username, email, password):
    if not supabase_client: return False, "Sem conexão com banco."
    if not username or not email or not password: return False, "Preencha todos os campos."
    
    if get_user_db(username): return False, "Nome de usuário já existe."
    
    try:
        data = {"username": username, "email": email, "password": password}
        supabase_client.table("users").insert(data).execute()
        return True, "Cadastro realizado! Faça login."
    except Exception as e: return False, f"Erro: {e}"

def login_user_db(username, password):
    user = get_user_db(username)
    if user:
        # Verifica senha (armazenada simples conforme solicitado)
        if str(user.get('password')) == str(password):
            return user
    return None

def recover_password_email(email):
    if not supabase_client: return False, "Sem conexão."
    try:
        response = supabase_client.table("users").select("password").eq("email", email).execute()
        if response.data:
            senha = response.data[0]['password']
            # Simulação de envio de email (print no console)
            print(f"--- RECUPERAÇÃO DE SENHA ---\nEmail: {email}\nSenha: {senha}\n----------------------------")
            return True, f"Sua senha foi enviada para {email}!"
        else:
            return False, "Email não encontrado."
    except Exception as e:
        return False, f"Erro: {e}"

def carregar_palpites(user_email=None):
    # Se tiver Supabase e usuário logado, busca do banco
    if supabase_client and user_email:
        try:
            # Busca todos os palpites do usuário, ordenados por data de criação
            response = supabase_client.table("palpites").select("*").eq("user_email", user_email).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            st.error(f"Erro ao carregar da nuvem: {e}")
            return []

    # Fallback para local (se não tiver internet ou login)
    if os.path.exists(ARQUIVO_PALPITES):
        try:
            with open(ARQUIVO_PALPITES, "r") as f:
                # Carrega todos os palpites do arquivo local
                return json.load(f)
        except:
            return []
    return []

@st.cache_data(ttl=300)
def carregar_todos_palpites_globais():
    if not supabase_client: return [], {}
    try:
        # Busca últimos 2000 palpites para garantir pegar os recentes
        response = supabase_client.table("palpites").select("*").order("created_at", desc=True).limit(2000).execute()
        palpites = response.data
        
        # Busca usernames
        emails = list(set([p['user_email'] for p in palpites if p.get('user_email')]))
        users_map = {}
        if emails:
            # Batch request if needed, but for now direct
            resp_u = supabase_client.table("users").select("email, username").in_("email", emails).execute()
            for u in resp_u.data:
                users_map[u['email']] = u['username']
                
        return palpites, users_map
    except:
        return [], {}

def get_palpites_for_concurso(concurso_num):
    """Busca todos os palpites já gerados para um concurso específico."""
    if not supabase_client or not concurso_num:
        return []
    try:
        # Busca apenas a coluna 'numeros' para otimizar
        response = supabase_client.table("palpites").select("numeros").eq("concurso", concurso_num).execute()
        # Retorna uma lista de listas de números. Ex: [[1,2,3...], [4,5,6...]]
        return [p['numeros'] for p in response.data if 'numeros' in p]
    except Exception as e:
        print(f"Erro ao buscar palpites para o concurso {concurso_num}: {e}")
        return []

def salvar_novo_palpite(novo_palpite, user_email=None, tipo="gerado"):
    # Se tiver Supabase, salva na nuvem
    if supabase_client and user_email:
        # Adiciona o email ao objeto antes de salvar
        novo_palpite['user_email'] = user_email
        novo_palpite['tipo'] = tipo
        try:
            # Modificado para retornar o ID do novo registro
            response = supabase_client.table("palpites").insert(novo_palpite).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get('id')
            return True # Fallback
        except Exception as e:
            st.error(f"Erro ao salvar na nuvem: {e}")
            return False
    
    # Fallback Local (Modo antigo)
    palpites_locais = carregar_palpites()
    novo_palpite['tipo'] = tipo
    palpites_locais.append(novo_palpite)
    with open(ARQUIVO_PALPITES, "w") as f:
        json.dump(palpites_locais, f, indent=4)
    return True

def excluir_palpite(palpite_id, user_email=None, index_local=None):
    if supabase_client and user_email and palpite_id:
        try:
            supabase_client.table("palpites").delete().eq("id", palpite_id).execute()
            return True
        except: return False
    
    # Fallback Local
    if index_local is not None:
        p = carregar_palpites()
        if 0 <= index_local < len(p):
            p.pop(index_local)
            with open(ARQUIVO_PALPITES, "w") as f:
                json.dump(p, f, indent=4)
            return True
    return False

def salvar_palpites_estudo_db(palpites_para_salvar):
    """Salva uma lista de palpites de estudo no banco de dados."""
    if not supabase_client or not palpites_para_salvar:
        return False, "Sem conexão ou sem palpites para salvar."
    try:
        # O método insert do Supabase aceita uma lista de dicionários
        supabase_client.table("palpites_estudo").insert(palpites_para_salvar).execute()
        return True, f"{len(palpites_para_salvar)} palpites de estudo salvos com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar palpites de estudo: {e}"

def carregar_palpites_estudo(concurso_num=None):
    """Carrega palpites de estudo. Se concurso_num for fornecido, filtra por ele."""
    if not supabase_client: return []
    try:
        query = supabase_client.table("palpites_estudo").select("concurso, numeros, confianca, metricas_usadas")
        if concurso_num:
            query = query.eq("concurso", concurso_num)
        
        response = query.order("concurso", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Erro ao carregar palpites de estudo: {e}")
        return []

def buscar_dados_api():
    try:
        r = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/", timeout=7)
        if r.status_code == 200:
            dados = r.json()[:63] # Pega os últimos 63 (Ajustado para Atraso Quântico)
            with open(ARQUIVO_CACHE, "w") as f:
                json.dump(dados, f)
            return dados
    except:
        return None

def buscar_dados_manuais():
    """Busca TODOS os sorteios inseridos manualmente no Supabase"""
    if not supabase_client: return []
    try:
        response = supabase_client.table("sorteios_manuais").select("*").order("concurso", desc=True).execute()
        if not response.data:
            return []
        
        dados_formatados = []
        for manual in response.data:
            dados_formatados.append({
                "concurso": manual['concurso'],
                "data": manual['data_sorteio'],
                "dezenas": manual['dezenas'],
                "premiacoes": [
                    {
                        "descricao": "15 acertos",
                        "faixa": 1,
                        "ganhadores": manual['ganhadores'],
                        "valorPremio": float(manual['premio_pago'])
                    }
                ],
                "proximoConcurso": manual['prox_concurso'],
                "dataProximoConcurso": manual['prox_data'],
                "valorEstimadoProximoConcurso": float(manual['prox_premio'])
            })
        return dados_formatados
    except Exception as e:
        print(f"Erro ao buscar dados manuais: {e}")
        return []

def salvar_sorteio_manual_db(dados_sorteio):
    """Salva os dados manuais no Supabase"""
    if not supabase_client: return False, "Sem conexão com banco."
    try:
        # Verifica se já existe esse concurso para atualizar ou insere novo
        existing = supabase_client.table("sorteios_manuais").select("id").eq("concurso", dados_sorteio['concurso']).execute()
        if existing.data:
            supabase_client.table("sorteios_manuais").update(dados_sorteio).eq("id", existing.data[0]['id']).execute()
        else:
            supabase_client.table("sorteios_manuais").insert(dados_sorteio).execute()
        return True, "Sorteio salvo com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar: {e}"

# --- AUTO-LOGIN FROM COOKIE ---
if 'logged_user' not in st.session_state:
    st.session_state['logged_user'] = None

if not st.session_state['logged_user']:
    try:
        # O get() precisa ser chamado antes de qualquer outro elemento do Streamlit
        username_from_cookie = cookie_manager.get('lotomind_user')
        if username_from_cookie:
            user_data = get_user_db(username_from_cookie)
            if user_data:
                st.session_state['logged_user'] = user_data
    except Exception:
        pass
# --------------------------

def carregar_dados():
    dados_lista = []
    # 1. Tenta carregar do cache primeiro
    if os.path.exists(ARQUIVO_CACHE):
        try:
            with open(ARQUIVO_CACHE, "r") as f:
                dados_lista = json.load(f)
        except:
            pass
    
    # 2. Se não tiver cache, busca da API
    if not dados_lista:
        dados_lista = buscar_dados_api() or []

    # 3. Busca TODOS os dados manuais e faz o merge para garantir que entrem nas estatísticas
    dados_manuais = buscar_dados_manuais()
    if dados_manuais:
        # Cria um dicionário para merge eficiente, dando prioridade aos dados da API/Cache inicialmente
        concursos_merged = {d['concurso']: d for d in dados_lista}
        
        # Sobrescreve ou adiciona os dados manuais
        for manual in dados_manuais:
            concursos_merged[manual['concurso']] = manual
            
        # Converte de volta para lista e ordena
        dados_lista = sorted(concursos_merged.values(), key=lambda x: x['concurso'], reverse=True)
    
    return dados_lista

def check_max_sequence(numbers, max_len=4):
    """Verifica se a maior sequência de números consecutivos é no máximo max_len."""
    if not numbers or len(numbers) < max_len + 1:
        return True
    sorted_numbers = sorted(numbers)
    max_seq = 0
    current_seq = 1
    for i in range(1, len(sorted_numbers)):
        if sorted_numbers[i] == sorted_numbers[i-1] + 1:
            current_seq += 1
        else:
            max_seq = max(max_seq, current_seq)
            current_seq = 1
    max_seq = max(max_seq, current_seq)
    return max_seq <= max_len

def rastreador_faltantes_ciclo4(historico):
    """
    Analisa os últimos 3 sorteios e retorna as dezenas que ainda não saíram.
    Essas são as dezenas 'faltantes' para fechar o ciclo de 4.
    """
    if len(historico) < 3:
        return []

    ultimos_3_sorteios = historico[:3]
    dezenas_sorteadas_no_ciclo = set()

    for sorteio in ultimos_3_sorteios:
        dezenas = [int(n) for n in (sorteio.get('dezenas') or sorteio.get('listaDezenas'))]
        dezenas_sorteadas_no_ciclo.update(dezenas)

    universo_completo = set(range(1, 26))
    dezenas_faltantes = sorted(list(universo_completo - dezenas_sorteadas_no_ciclo))
    
    return dezenas_faltantes

@st.cache_data(ttl=3600) # Cache por 1 hora
def calcular_assertividade_metricas(historico):
    if not historico or len(historico) < 2:
        return {}

    total_sorteios = len(historico) - 1
    stats = {
        "Repetidos": 0, "Paridade": 0, "Top 10": 0, 
        "Bottom 6": 0, "Sequencial": 0, "Rastreador de Faltantes": 0
    }

    for i in range(total_sorteios):
        resultado_atual = historico[i]
        historico_anterior = historico[i+1:]
        
        metricas_ok = analisar_metricas_resultado(resultado_atual, historico_anterior)
        if metricas_ok:
            ok_rep, ok_par, ok_top, ok_bot, ok_seq, ok_rastreador = metricas_ok
            if ok_rep: stats["Repetidos"] += 1
            if ok_par: stats["Paridade"] += 1
            if ok_top: stats["Top 10"] += 1
            if ok_bot: stats["Bottom 6"] += 1
            if ok_seq: stats["Sequencial"] += 1
            if ok_rastreador: stats["Rastreador de Faltantes"] += 1

    assertividade = {metrica: (count / total_sorteios) * 100 for metrica, count in stats.items()}
    return assertividade

def gerar_palpite_logica(historico, ultimo_resultado, numeros_incluir=None, numeros_excluir=None, palpites_existentes=None, metricas_selecionadas=None):
    """Lógica original do Lotomind adaptada para função pura"""
    if not historico or not ultimo_resultado:
        return None, 0, "Dados insuficientes para gerar palpite."

    numeros_incluir = numeros_incluir or []; numeros_excluir = numeros_excluir or []; palpites_existentes = palpites_existentes or []
    TODAS_METRICAS = ["Repetidos", "Paridade", "Sequencial", "Rastreador de Faltantes", "Top 10", "Bottom 6"]
    if metricas_selecionadas is None: metricas_selecionadas = TODAS_METRICAS

    # Define o universo de dezenas disponíveis para o sorteio
    universo_dezenas = [n for n in range(1, 26) if n not in numeros_excluir]

    # Validações de conflito
    if len(universo_dezenas) < 15:
        return None, 0, "Conflito: Muitas dezenas excluídas, impossível gerar jogo."
    if any(n in numeros_excluir for n in numeros_incluir):
        return None, 0, "Conflito: Um número não pode ser incluído e excluído ao mesmo tempo."

    # Pool para a parte aleatória do jogo
    pool_aleatorio = [n for n in universo_dezenas if n not in numeros_incluir]
    qtd_aleatoria = 15 - len(numeros_incluir)

    if len(pool_aleatorio) < qtd_aleatoria:
        return None, 0, "Conflito: Não há dezenas suficientes para completar o jogo com as inclusões/exclusões."

    ult_40 = historico[:40]
    ult_3 = historico[:3]
    
    dezenas_ultimo = [int(n) for n in (ultimo_resultado.get('dezenas') or ultimo_resultado.get('listaDezenas'))]

    # Frequência
    contagem = Counter()
    for s in ult_40:
        contagem.update([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])
    
    top_10 = [n for n, c in contagem.most_common(10)]
    bottom_6 = [n for n, c in contagem.most_common()[-6:]]

    # NOVA MÉTRICA: Rastreador de Faltantes (Ciclo de 4)
    dezenas_obrigatorias_ciclo = rastreador_faltantes_ciclo4(historico)
    # Requisito: incluir pelo menos 80% dessas dezenas
    min_ciclo_obrigatorias = int(len(dezenas_obrigatorias_ciclo) * 0.8)

    tentativas = 0
    while tentativas < 10000: # Limite aumentado para garantir unicidade
        tentativas += 1
        # Gera a parte aleatória e combina com os números fixos
        parte_aleatoria = random.sample(pool_aleatorio, qtd_aleatoria)
        jogo = sorted(numeros_incluir + parte_aleatoria)

        # NOVA REGRA: Garantir que o palpite é único para este concurso
        if jogo in palpites_existentes:
            continue # Jogo já existe, gera outro

        # --- Verificação de todas as 6 métricas ---

        # 1. Repetidos
        r_count = len([n for n in jogo if n in dezenas_ultimo])
        repetidos_ok = r_count in [8, 9]
        if "Repetidos" in metricas_selecionadas and not repetidos_ok: continue

        # 2. Paridade
        pares = len([n for n in jogo if n % 2 == 0])
        impares = 15 - pares
        paridade_ok = (impares == 8 and pares == 7) or (impares == 7 and pares == 8)
        if "Paridade" in metricas_selecionadas and not paridade_ok: continue

        # 4. Sequencial (NOVA)
        sequencial_ok = check_max_sequence(jogo, 5)
        if "Sequencial" in metricas_selecionadas and not sequencial_ok: continue

        # NOVA REGRA OBRIGATÓRIA: Rastreador de Faltantes
        qtd_ciclo_presentes = len([n for n in jogo if n in dezenas_obrigatorias_ciclo])
        ciclo_faltantes_ok = qtd_ciclo_presentes >= min_ciclo_obrigatorias
        if "Rastreador de Faltantes" in metricas_selecionadas and not ciclo_faltantes_ok: continue

        # 7. Top 10 (Obrigatório)
        top10_ok = 5 <= len([n for n in jogo if n in top_10]) <= 7
        if "Top 10" in metricas_selecionadas and not top10_ok: continue
        
        # 8. Bottom 6 (Obrigatório)
        bottom6_ok = 3 <= len([n for n in jogo if n in bottom_6]) <= 4
        if "Bottom 6" in metricas_selecionadas and not bottom6_ok: continue

        # --- Novo Cálculo de Confiança (baseado em 6 métricas) ---
        metricas_atendidas = 0
        if "Repetidos" in metricas_selecionadas and repetidos_ok: metricas_atendidas += 1
        if "Paridade" in metricas_selecionadas and paridade_ok: metricas_atendidas += 1
        if "Sequencial" in metricas_selecionadas and sequencial_ok: metricas_atendidas += 1
        if "Rastreador de Faltantes" in metricas_selecionadas and ciclo_faltantes_ok: metricas_atendidas += 1
        if "Top 10" in metricas_selecionadas and top10_ok: metricas_atendidas += 1
        if "Bottom 6" in metricas_selecionadas and bottom6_ok: metricas_atendidas += 1
        
        total_metricas_usadas = len(metricas_selecionadas)
        confianca = int((metricas_atendidas / total_metricas_usadas) * 100) if total_metricas_usadas > 0 else 100

        if metricas_atendidas == total_metricas_usadas:
            msg = f"Todas as {total_metricas_usadas} métricas selecionadas foram atendidas!" if total_metricas_usadas > 0 else "Nenhuma métrica selecionada."
            return jogo, confianca, f"Confiança: {confianca}% | {msg}"

    return None, 0, "Não foi possível gerar um palpite exclusivo que atenda a todas as métricas selecionadas. Tente novamente."

def analisar_metricas_resultado(resultado, historico_anterior):
    if not historico_anterior:
        return None
    
    dezenas = [int(n) for n in (resultado.get('dezenas') or resultado.get('listaDezenas'))]
    dezenas_ant = [int(n) for n in (historico_anterior[0].get('dezenas') or historico_anterior[0].get('listaDezenas'))]
    
    # 1. Repetidos (8 or 9)
    repetidos = len(set(dezenas) & set(dezenas_ant))
    ok_repetidos = repetidos in [8, 9]
    
    # 2. Paridade (8/7 or 7/8)
    pares = len([n for n in dezenas if n % 2 == 0])
    impares = 15 - pares
    ok_paridade = (pares == 8 and impares == 7) or (pares == 7 and impares == 8)
    
    # 4. Top 10 e Bottom 6
    ult_40 = historico_anterior[:40]
    contagem = Counter()
    for s in ult_40:
        contagem.update([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])
    
    top_10 = [n for n, c in contagem.most_common(10)]
    bottom_6 = [n for n, c in contagem.most_common()[-6:]]
    
    qtd_top10 = len([n for n in dezenas if n in top_10])
    qtd_bottom6 = len([n for n in dezenas if n in bottom_6])
    
    ok_top10 = 5 <= qtd_top10 <= 7
    ok_bottom6 = 3 <= qtd_bottom6 <= 4
    
    # 5. Sequencial (NOVA)
    ok_sequencial = check_max_sequence(dezenas, 5)
    
    # 6. Rastreador de Faltantes
    dezenas_obrigatorias_ciclo = rastreador_faltantes_ciclo4(historico_anterior)
    min_ciclo_obrigatorias = int(len(dezenas_obrigatorias_ciclo) * 0.8)
    qtd_ciclo_presentes = len([n for n in dezenas if n in dezenas_obrigatorias_ciclo])
    ok_rastreador_faltantes = qtd_ciclo_presentes >= min_ciclo_obrigatorias

    return ok_repetidos, ok_paridade, ok_top10, ok_bottom6, ok_sequencial, ok_rastreador_faltantes

@st.dialog("Gerador de Palpite Personalizado")
def gerar_palpite_personalizado_dialog():
    """Cria uma mini-tela (popup) para a geração de palpites com filtros."""
    # Inicializa o estado do dialog se não existir
    if 'dialog_palpite' not in st.session_state: st.session_state.dialog_palpite = None
    if 'dialog_msg' not in st.session_state: st.session_state.dialog_msg = None
    if 'dialog_confianca' not in st.session_state: st.session_state.dialog_confianca = 0

    st.markdown(f"<h2 style='color: {ROXO_MEDIO};'>✨ Palpite Personalizado</h2>", unsafe_allow_html=True)
    st.caption("Ajuste as métricas e filtros para criar um palpite com a sua estratégia.")

    METRICAS_DISPONIVEIS = {
        "Repetidos": "Manter 8 ou 9 dezenas do sorteio anterior.",
        "Paridade": "Equilibrar entre 7/8 dezenas pares e ímpares.",
        "Top 10": "Usar de 5 a 7 dezenas das 10 mais sorteadas recentemente.",
        "Bottom 6": "Usar de 3 a 4 dezenas das 6 menos sorteadas.",
        "Sequencial": "Evitar sequências de 6 ou mais números consecutivos.",
        "Rastreador de Faltantes": "Incluir dezenas que faltam para fechar o ciclo de 4 sorteios."
    }

    metricas_selecionadas = st.multiselect(
        "Selecione as métricas para o seu palpite:",
        options=list(METRICAS_DISPONIVEIS.keys()),
        default=[],
        key="metricas_palpite_dialog"
    )

    c_incluir, c_excluir = st.columns(2)
    with c_incluir:
        numeros_incluir = st.multiselect(
            "➕ Incluir Números (até 3)",
            options=list(range(1, 26)), max_selections=3, key="incluir_numeros_dialog"
        )
    with c_excluir:
        numeros_excluir = st.multiselect(
            "➖ Excluir Números (até 3)",
            options=list(range(1, 26)), max_selections=3, key="excluir_numeros_dialog"
        )

    st.markdown("---")
    
    if st.button("✨ Gerar Palpite Agora", type="primary", use_container_width=True):
        dados = st.session_state['dados']
        ultimo_resultado = dados[0] if dados else None

        if dados and ultimo_resultado:
            with st.spinner("Analisando estatísticas e padrões..."):
                proximo_concurso = ultimo_resultado.get('proximoConcurso')
                palpites_ja_gerados = get_palpites_for_concurso(proximo_concurso) if proximo_concurso else []

                jogo, confianca, msg = gerar_palpite_logica(
                    dados, ultimo_resultado,
                    numeros_incluir=st.session_state.get('incluir_numeros_dialog', []),
                    numeros_excluir=st.session_state.get('excluir_numeros_dialog', []),
                    palpites_existentes=palpites_ja_gerados,
                    metricas_selecionadas=st.session_state.get('metricas_palpite_dialog', list(METRICAS_DISPONIVEIS.keys()))
                )
                
                # Salva o resultado no estado do dialog, sem fechar
                st.session_state.dialog_palpite = jogo
                st.session_state.dialog_msg = msg
                st.session_state.dialog_confianca = confianca

        else:
            st.session_state.dialog_palpite = None
            st.session_state.dialog_msg = "Erro ao carregar dados para geração."
            st.session_state.dialog_confianca = 0

    # Exibe o resultado (palpite ou erro) dentro do próprio dialog
    if st.session_state.dialog_palpite:
        jogo = st.session_state.dialog_palpite
        msg = st.session_state.dialog_msg
        
        st.markdown("---")
        st.markdown("<p style='text-align:center; font-weight:bold;'>Palpite Gerado:</p>", unsafe_allow_html=True)
        
        rows_html = []
        for i in range(0, 15, 5):
            chunk = jogo[i:i+5]
            row_content = ''.join([f'<div style="width: 40px; height: 40px; background-color: {ROXO_MEDIO}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">{n:02d}</div>' for n in chunk])
            rows_html.append(f'<div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 8px;">{row_content}</div>')
        
        numeros_html = "".join(rows_html)

        st.markdown(f"""
            <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 20px; text-align: center;">
                {numeros_html}
            </div>
            <div style="background-color: {VERDE_CLARO}; color: {VERDE_ESCURO}; padding: 8px; border-radius: 5px; font-size: 14px; border: 1px solid {VERDE_MEDIO}; margin-top: 10px; text-align: center;">
                {msg}
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Usar este Palpite", use_container_width=True, type="primary"):
                # Define o estado da página principal com os dados do dialog
                st.session_state.palpite_atual = st.session_state.dialog_palpite
                st.session_state.msg_palpite = st.session_state.dialog_msg
                st.session_state.confianca_atual = st.session_state.dialog_confianca

                # Salva o palpite no banco de dados
                user_email = st.session_state.get('logged_user', {}).get('email')
                if user_email:
                    ultimo_resultado = st.session_state['dados'][0]
                    proximo_concurso = ultimo_resultado.get('proximoConcurso')
                    novo_auto = { 
                        "concurso": proximo_concurso, 
                        "data": ultimo_resultado.get('dataProximoConcurso'), 
                        "numeros": st.session_state.dialog_palpite, 
                        "confianca": st.session_state.dialog_confianca 
                    }
                    st.session_state['palpite_id_atual'] = salvar_novo_palpite(novo_auto, user_email, tipo="personalizado")

                # Fecha o dialog e atualiza a página principal
                st.session_state.show_custom_dialog = False
                st.rerun()
        with c2:
            if st.button("❌ Fechar", use_container_width=True):
                st.session_state.show_custom_dialog = False
                st.rerun()
    elif st.session_state.get('dialog_msg'):
        st.error(st.session_state.dialog_msg)

# --- INTERFACE DO APP WEB ---

# Inicialização de Estado (Memória do App)
if 'dados' not in st.session_state:
    st.session_state['dados'] = carregar_dados()
if 'palpite_atual' not in st.session_state:
    st.session_state['palpite_atual'] = None
if 'msg_palpite' not in st.session_state:
    st.session_state['msg_palpite'] = ""
if 'confianca_atual' not in st.session_state:
    st.session_state['confianca_atual'] = 0
if 'palpite_id_atual' not in st.session_state:
    st.session_state['palpite_id_atual'] = None

# Define user_email para ser usado em todo o app
user_email = None
if supabase_client and st.session_state.get('logged_user'):
    user = st.session_state['logged_user']
    user_email = user.get('email')
    
# --- TELA DE LOGIN / CADASTRO (BLOQUEANTE) ---
if not st.session_state['logged_user']:
    # Limpeza diferida dos campos de cadastro (para evitar erro de modificação de widget ativo)
    if st.session_state.get('clear_register_form'):
        st.session_state['reg_user'] = ""
        st.session_state['reg_email'] = ""
        st.session_state['reg_pass'] = ""
        st.session_state['clear_register_form'] = False

    # Troca de aba diferida (para evitar erro de modificação de widget ativo)
    if st.session_state.get('force_login_tab'):
        st.session_state['login_tab_select'] = "Entrar"
        st.session_state['force_login_tab'] = False

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Centralizando Logo
        c_logo_1, c_logo_2, c_logo_3 = st.columns([1, 1, 1])
        with c_logo_2:
            if os.path.exists("logo.png"):
                st.image("logo.png", use_container_width=True)
            elif os.path.exists("../logo.png"):
                st.image("../logo.png", use_container_width=True)
            else:
                st.markdown(f"<h1 style='text-align: center; color: {VAR_COR_TITULOS};'>Lotomind</h1>", unsafe_allow_html=True)
        
        # Texto "Bem-vindo!" com a variável de cor
        st.markdown(f"<h3 style='color:{VAR_COR_LOGIN_BEMVINDO}; text-align: center;'>Bem-vindo!</h3>", unsafe_allow_html=True)
        
        # Controle de estado para alternar abas programaticamente
        if 'login_tab_select' not in st.session_state: st.session_state['login_tab_select'] = "Entrar"
        login_mode = st.radio("Modo", ["Entrar", "Criar Conta"], horizontal=True, label_visibility="collapsed", key="login_tab_select")
        
        if login_mode == "Entrar":
            with st.form("login_form"):
                l_user = st.text_input("Usuário")
                l_pass = st.text_input("Senha", type="password")
                permanecer = st.checkbox("Permanecer logado")
                submit_login = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
                if submit_login:
                    if not supabase_client:
                        st.error("Erro de conexão com banco de dados.")
                        st.error("Erro de conexão. Verifique se as credenciais do banco de dados (secrets) estão configuradas.")
                    else:
                        u = login_user_db(l_user, l_pass)
                        if u:
                            st.session_state['logged_user'] = u
                            if permanecer:
                                cookie_manager['lotomind_user'] = u['username']
                                cookie_manager.save()
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos.")
            
            with st.expander("Esqueci minha senha"):
                st.caption("Informe seu email para receber a senha.")
                rec_email = st.text_input("Email cadastrado", key="rec_email")
                if st.button("Enviar Senha por Email"):
                    ok, msg = recover_password_email(rec_email)
                    if ok: st.success(msg)
                    else: st.error(msg)

        else:
            with st.form("register_form"):
                st.write("Preencha para criar sua conta:")
                # Adicionando chaves (keys) para poder resetá-los
                c_user = st.text_input("Escolha um Usuário", key="reg_user")
                c_email = st.text_input("Seu Email", key="reg_email")
                c_pass = st.text_input("Escolha uma Senha", type="password", key="reg_pass")
                submit_cad = st.form_submit_button("Cadastrar", use_container_width=True)
                
                if submit_cad:
                    ok, msg = register_user_db(c_user, c_email, c_pass)
                    if ok: 
                        st.success(msg)
                        # Marca para limpar os campos na próxima execução (evita StreamlitAPIException)
                        st.session_state['clear_register_form'] = True
                        time.sleep(1.5)
                        # Muda para a aba de login
                        st.session_state['force_login_tab'] = True
                        st.rerun()
                    else: 
                        st.error(msg)

    st.stop() # Interrompe a execução aqui se não estiver logado

# --- HEADER E MENU DE NAVEGAÇÃO ---
c_esq, c_centro, c_dir = st.columns([1, 2, 1])
with c_centro:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    elif os.path.exists("../logo.png"):
        st.image("../logo.png", use_container_width=True)
    else:
        st.markdown(f"<h1 style='text-align: center; color: {ROXO_MEDIO};'>Lotomind</h1>", unsafe_allow_html=True)

# --- DEFINIÇÃO DE ABAS (COM ADMIN SE NECESSÁRIO) ---
abas_labels = [" 🍀 Início ", " 📜 Meus Palpites ", " 📊 Estatísticas ", " 🏆 Premiações "]
is_admin = False

# Verifica se é admin
if st.session_state.get('logged_user') and st.session_state['logged_user'].get('type') == 'admin':
    is_admin = True
    abas_labels.append("🔬 Estudo")
    abas_labels.append(" 📈 Static Lotomind ")
    abas_labels.append(" ⚙️ Admin ")

tabs = st.tabs(abas_labels)

# Desempacota as abas padrão
tab_inicio, tab_palpites, tab_stats, tab_premios = tabs[0], tabs[1], tabs[2], tabs[3]
tab_estudo = tabs[4] if is_admin else None
tab_static = tabs[5] if is_admin else None
tab_admin = tabs[6] if is_admin else None

dados = st.session_state['dados']
ultimo_resultado = dados[0] if dados else None

# --- TELA: INÍCIO ---
with tab_inicio:
    if ultimo_resultado:
        # --- HERO SECTION: PRÓXIMO CONCURSO ---
        valor_estimado = ultimo_resultado.get('valorEstimadoProximoConcurso', 0)
        prox_concurso = ultimo_resultado.get('proximoConcurso')
        prox_data = ultimo_resultado.get('dataProximoConcurso')
        
        # Card de Destaque (Roxo com Sombra)
        st.markdown(f"""
<div style="background-color: {ROXO_MEDIO}; padding: 25px; border-radius: 15px; text-align: center; color: white; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(75, 0, 130, 0.3);">
<p style="margin: 0; font-size: 14px; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase; color: {VAR_COR_TEXTO_PROXIMO_CONCURSO} !important;">Próximo Concurso <b>{prox_concurso}</b> • {prox_data}</p>
<div style="margin: 10px 0; font-size: 42px; color: {VAR_COR_TEXTO_PROXIMO_CONCURSO} !important; font-weight: 800; line-height: 1.2;">R$ {valor_estimado:,.2f}</div>
<div style="display: inline-block; background-color: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px;">
<p style="margin: 0; font-size: 12px; font-weight: bold; color: {VAR_COR_TEXTO_PROXIMO_CONCURSO} !important;">PRÊMIO ESTIMADO</p>
</div>
</div>
        """, unsafe_allow_html=True)

        # --- NOVA SEÇÃO: MÉTRICAS E FILTROS ---
        st.markdown("---")

        if st.button("ℹ️ O que são as Métricas e qual a eficácia?", use_container_width=True):
            with st.spinner("Calculando assertividade histórica..."):
                taxas_sucesso = calcular_assertividade_metricas(dados)
            
            @st.dialog("Eficácia das Métricas")
            def show_metrics_dialog():
                st.markdown(f"<h2 style='color: {ROXO_MEDIO};'>🧠 Entendendo as Métricas</h2>", unsafe_allow_html=True)
                st.caption("Abaixo, a descrição de cada métrica e a porcentagem de vezes que ela foi observada nos resultados oficiais da Lotofácil.")
                
                if not taxas_sucesso:
                    st.warning("Não foi possível calcular as taxas de sucesso.")
                else:
                    METRICAS_DISPONIVEIS = {
                        "Repetidos": "Manter 8 ou 9 dezenas do sorteio anterior.",
                        "Paridade": "Equilibrar entre 7/8 dezenas pares e ímpares.",
                        "Top 10": "Usar de 5 a 7 dezenas das 10 mais sorteadas recentemente.",
                        "Bottom 6": "Usar de 3 a 4 dezenas das 6 menos sorteadas.",
                        "Sequencial": "Evitar sequências de 6 ou mais números consecutivos.",
                        "Rastreador de Faltantes": "Incluir dezenas que faltam para fechar o ciclo de 4 sorteios."
                    }
                    for metrica, desc in METRICAS_DISPONIVEIS.items():
                        taxa = taxas_sucesso.get(metrica, 0)
                        st.markdown(f"**{metrica}** (`{taxa:.1f}%`)")
                        st.write(desc)
                if st.button("Entendi", use_container_width=True, type="primary"):
                    st.rerun()
            show_metrics_dialog()

        # --- GERADOR DE PALPITE (SEM ABAS) ---
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botões de Ação (Gerar + Atualizar)
        c_rapido, c_pers, c_update = st.columns([2, 2, 1])

        with c_rapido:
            st.markdown('<div class="btn-verde-claro">', unsafe_allow_html=True)
            btn_rapido = st.button("🍀 Gerar Palpite (Rápido)", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c_pers:
            st.markdown('<div class="btn-verde-escuro">', unsafe_allow_html=True)
            if st.button("✨ Gerar Personalizado", use_container_width=True):
                # Limpa o estado do diálogo anterior e define flag para mostrá-lo
                st.session_state.dialog_palpite = None
                st.session_state.dialog_msg = None
                st.session_state.dialog_confianca = 0
                st.session_state.show_custom_dialog = True
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c_update:
            if st.button("🔄 Atualizar Dados", use_container_width=True):
                with st.spinner("Buscando dados..."):
                    novos = buscar_dados_api()
                    if novos:
                        st.session_state['dados'] = novos
                        st.success("Atualizado!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro.")
        
        # Este bloco agora controla a visibilidade do diálogo
        if st.session_state.get("show_custom_dialog", False):
            gerar_palpite_personalizado_dialog()
        
        if btn_rapido:
            if dados and ultimo_resultado:
                with st.spinner("Analisando estatísticas e padrões..."):
                    proximo_concurso = ultimo_resultado.get('proximoConcurso')
                    palpites_ja_gerados = get_palpites_for_concurso(proximo_concurso) if proximo_concurso else []

                    # Chama a lógica com todas as métricas (padrão) e sem filtros de incluir/excluir
                    jogo, confianca, msg = gerar_palpite_logica(
                        dados, 
                        ultimo_resultado,
                        palpites_existentes=palpites_ja_gerados
                    )
                    
                    if jogo is None:
                        st.error(msg)
                        st.session_state['palpite_atual'] = None
                    else:
                        st.session_state.update(palpite_atual=jogo, msg_palpite=msg, confianca_atual=confianca)
                        if user_email:
                            novo_auto = { "concurso": proximo_concurso, "data": ultimo_resultado.get('dataProximoConcurso'), "numeros": jogo, "confianca": confianca }
                            st.session_state['palpite_id_atual'] = salvar_novo_palpite(novo_auto, user_email)
                        st.rerun()
            else:
                st.error("Erro ao carregar dados.")

        # Exibição do Palpite Gerado
        if st.session_state['palpite_atual']:
            jogo = st.session_state['palpite_atual']
            confianca = st.session_state.get('confianca_atual', 0)
            msg = st.session_state['msg_palpite']
            
            st.markdown("---")
            
            rows_html = []
            for i in range(0, 15, 5):
                chunk = jogo[i:i+5]
                row_content = ''.join([f'<div style="width: 40px; height: 40px; background-color: {ROXO_MEDIO}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">{n:02d}</div>' for n in chunk])
                rows_html.append(f'<div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 8px;">{row_content}</div>')
            
            numeros_html = "".join(rows_html)

            st.markdown(f"""
<div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 20px; text-align: center;">
<p style="color: {ROXO_MEDIO}; font-weight: bold; margin-bottom: 15px;">SUGESTÃO</p>
{numeros_html}
</div>
<div style="background-color: {VERDE_CLARO}; color: {VERDE_ESCURO}; padding: 8px; border-radius: 5px; font-size: 14px; border: 1px solid {VERDE_MEDIO}; margin-top: 10px; text-align: center;">
{msg}
</div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            nums_str = " ".join([f"{n:02d}" for n in jogo])
            texto_wpp = f"🍀 *Lotomind* sugere:\nConcurso: {ultimo_resultado.get('proximoConcurso')}\n\n`{nums_str}`"
            link_wpp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_wpp)}"
            st.link_button("📱 Enviar por WhatsApp", link_wpp, use_container_width=True)

            st.markdown("---")
            st.subheader("🚀 Apostar Online")
            st.info("O Lotomind **não** realiza apostas. Siga os passos abaixo para apostar no site oficial da Caixa.", icon="ℹ️")

            numeros_para_copiar = " ".join([f"{n:02d}" for n in jogo])
            st.markdown("**1. Copie os números do seu palpite:**")
            st.code(numeros_para_copiar, language=None)

            st.markdown("**2. Acesse o site oficial ou o app e cole os números:**")
            st.markdown('<div class="loterias-button-wrapper">', unsafe_allow_html=True)
            st.link_button("➡️ Abrir Loterias Online (Lotofácil)", "https://www.loteriasonline.caixa.gov.br/silce-web/#/lotofacil", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption("Você precisará fazer login no site ou app da Caixa para completar a aposta. Esta função é um atalho para o site oficial e não possui vínculo com a Caixa Econômica Federal.")

        st.markdown("---")
        st.subheader("Último Resultado")
        
        premiacoes = ultimo_resultado.get('premiacoes')
        premiacao_15 = premiacoes[0] if premiacoes and isinstance(premiacoes, list) else {}
        
        ganhadores = premiacao_15.get('ganhadores', 0)
        valor_premio = premiacao_15.get('valorPremio', 0)
        dezenas = ultimo_resultado.get('dezenas') or ultimo_resultado.get('listaDezenas') or []
        
        html_bolas = ''.join([f'<div style="width: 32px; height: 32px; background-color: #eee; color: #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; border: 1px solid #ccc;">{n}</div>' for n in dezenas])

        st.markdown(f"""
<div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
<h4 style="text-align: center; color: {ROXO_MEDIO}; margin-bottom: 5px;">Concurso {ultimo_resultado.get('concurso')}</h4>
<p style="text-align: center; color: grey; font-size: 13px; margin-bottom: 20px;">Realizado em {ultimo_resultado.get('data')}</p>
<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 5px; margin-bottom: 25px;">
{html_bolas}
</div>
<div style="display: flex; justify-content: space-around; background-color: #f8f9fa; padding: 15px; border-radius: 8px;">
<div style="text-align: center;">
<span style="font-size: 12px; color: #666; text-transform: uppercase;">Ganhadores (15)</span><br>
<span style="font-size: 20px; font-weight: bold; color: {ROXO_MEDIO};">{ganhadores}</span>
</div>
<div style="width: 1px; background-color: #ddd;"></div>
<div style="text-align: center;">
<span style="font-size: 12px; color: #666; text-transform: uppercase;">Prêmio Pago</span><br>
<span style="font-size: 20px; font-weight: bold; color: {VERDE_MEDIO};">R$ {valor_premio:,.2f}</span>
</div>
</div>
</div>
        """, unsafe_allow_html=True)

    else:
        st.error("Não foi possível carregar os dados dos sorteios. Verifique sua conexão ou tente atualizar.")
        if st.button("Tentar Atualizar Dados"):
            st.rerun()

# --- TELA: MEUS PALPITES ---
with tab_palpites:
    st.markdown(f"<h2 style='color: {ROXO_MEDIO};'>📜 Meus Palpites</h2>", unsafe_allow_html=True)
    palpites = carregar_palpites(user_email)

    if not palpites:
        st.markdown("ℹ️ *Nenhum palpite salvo nesta conta.*")
    else:
        # --- CÁLCULO DAS ESTATÍSTICAS ---
        lista_acertos = []
        contagem_faixas = Counter()
        total_ganho = 0.0
        jogos_com_resultado = 0

        if dados:
            for p in palpites:
                for sorteio in dados:
                    if str(sorteio['concurso']) == str(p.get('concurso')):
                        jogos_com_resultado += 1
                        sorteados = [int(x) for x in (sorteio.get('dezenas') or sorteio.get('listaDezenas'))]
                        acertos = len(set(p['numeros']) & set(sorteados))
                        lista_acertos.append(acertos)
                        contagem_faixas.update([acertos])
                        
                        # Cálculo financeiro estimado
                        if acertos >= 11:
                            premio_encontrado = 0
                            # Tenta pegar valor real da API
                            for faixa in sorteio.get('premiacoes', []):
                                if str(acertos) in faixa.get('descricao', ''):
                                    premio_encontrado = faixa.get('valorPremio', 0)
                                    break
                            # Fallback valores fixos aproximados
                            if premio_encontrado == 0:
                                if acertos == 11: premio_encontrado = 6.0
                                elif acertos == 12: premio_encontrado = 12.0
                                elif acertos == 13: premio_encontrado = 30.0
                            
                            total_ganho += premio_encontrado
                        break
        
        # --- DASHBOARD DE ESTATÍSTICAS MODERNO ---
        total_jogos = len(palpites)
        media_acertos = sum(lista_acertos) / len(lista_acertos) if lista_acertos else 0
        max_acertos = max(lista_acertos) if lista_acertos else 0
        min_acertos = min(lista_acertos) if lista_acertos else 0
        
        st.markdown(f"""
        <div style="display: flex; gap: 10px; margin-bottom: 20px;">
            <div style="flex: 1; background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; text-align: center;">
                <span style="font-size: 24px; font-weight: bold; color: {ROXO_MEDIO};">{total_jogos}</span><br>
                <span style="font-size: 11px; color: #666; text-transform: uppercase;">Jogos</span>
            </div>
            <div style="flex: 1; background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; text-align: center;">
                <span style="font-size: 24px; font-weight: bold; color: {VERDE_MEDIO};">{max_acertos}</span><br>
                <span style="font-size: 11px; color: #666; text-transform: uppercase;">Máx. Acertos</span>
            </div>
            <div style="flex: 1; background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; text-align: center;">
                <span style="font-size: 24px; font-weight: bold; color: #dc3545;">{min_acertos}</span><br>
                <span style="font-size: 11px; color: #666; text-transform: uppercase;">Mín. Acertos</span>
            </div>
            <div style="flex: 1; background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; text-align: center;">
                <span style="font-size: 24px; font-weight: bold; color: #333;">{media_acertos:.1f}</span><br>
                <span style="font-size: 11px; color: #666; text-transform: uppercase;">Média</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- DETALHAMENTO DE ACERTOS ---
        st.markdown(f"<h4 style='color: {ROXO_MEDIO}; margin-top: 20px;'>🎯 Detalhamento de Acertos</h4>", unsafe_allow_html=True)
        
        faixas = range(15, 4, -1) # 15 até 5
        html_list = ""
        
        for n_acertos in faixas:
            qtd = contagem_faixas.get(n_acertos, 0)
            style_row = "display: flex; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid #eee;"
            
            if n_acertos >= 11 and qtd > 0:
                style_row += f" background-color: {VERDE_CLARO if n_acertos >= 14 else '#e8f4f8'}; font-weight: bold; color: {VERDE_ESCURO if n_acertos >= 14 else ROXO_MEDIO}; border-radius: 5px; border-bottom: none; margin-bottom: 2px;"
            
            html_list += f'<div style="{style_row}"><span>{n_acertos} Acertos</span><span>{qtd} vezes</span></div>'
            
        st.markdown(f"<div style='border: 1px solid #ddd; border-radius: 10px; padding: 10px;'>{html_list}</div>", unsafe_allow_html=True)

        # --- NOVA ESTATÍSTICA: ANÁLISE FINANCEIRA ---
        st.markdown(f"<h4 style='color: {ROXO_MEDIO}; margin-top: 20px;'>💰 Análise Financeira (Estimada)</h4>", unsafe_allow_html=True)
        
        custo_aposta = 3.00
        total_investido = jogos_com_resultado * custo_aposta
        lucro_prejuizo = total_ganho - total_investido
        cor_lucro = VERDE_MEDIO if lucro_prejuizo >= 0 else "#dc3545"
        
        st.markdown(f"""
        <div style="background-color: white; border: 1px solid #ddd; border-radius: 10px; padding: 20px; display: flex; justify-content: space-around; align-items: center;">
            <div style="text-align: center;">
                <span style="font-size: 12px; color: #666; text-transform: uppercase;">Investido</span><br>
                <span style="font-size: 18px; font-weight: bold; color: #333;">R$ {total_investido:,.2f}</span>
            </div>
            <div style="width: 1px; height: 40px; background-color: #eee;"></div>
            <div style="text-align: center;">
                <span style="font-size: 12px; color: #666; text-transform: uppercase;">Retorno</span><br>
                <span style="font-size: 18px; font-weight: bold; color: {VERDE_MEDIO};">R$ {total_ganho:,.2f}</span>
            </div>
            <div style="width: 1px; height: 40px; background-color: #eee;"></div>
            <div style="text-align: center;">
                <span style="font-size: 12px; color: #666; text-transform: uppercase;">Balanço</span><br>
                <span style="font-size: 18px; font-weight: bold; color: {cor_lucro};">R$ {lucro_prejuizo:,.2f}</span>
            </div>
        </div>
        <p style="font-size: 11px; color: #999; text-align: center; margin-top: 5px;">*Considerando apenas jogos com resultado apurado.</p>
        """, unsafe_allow_html=True)

        # --- BOTÃO WHATSAPP ---
        if ultimo_resultado:
            prox_concurso_num = ultimo_resultado.get('proximoConcurso')
            palpites_proximo_sorteio = [p for p in palpites if str(p.get('concurso')) == str(prox_concurso_num)]
            
            if palpites_proximo_sorteio:
                texto_wpp = f"🍀 *Meus Palpites Lotomind para o Concurso {prox_concurso_num}*\n\n"
                for i, p in enumerate(palpites_proximo_sorteio):
                    nums_str = " ".join([f"{n:02d}" for n in p['numeros']])
                    texto_wpp += f"*{i+1}º Jogo:*\n`{nums_str}`\n\n"
                
                link_wpp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_wpp)}"
                st.link_button("📱 Compartilhar Palpites do Próximo Sorteio", link_wpp, use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)

        # --- PAGINAÇÃO ---
        if 'pag_atual' not in st.session_state:
            st.session_state['pag_atual'] = 1
            
        items_por_pagina = 20
        total_paginas = (len(palpites) - 1) // items_por_pagina + 1
        
        # Ajusta página atual se necessário
        if st.session_state['pag_atual'] > total_paginas:
            st.session_state['pag_atual'] = max(1, total_paginas)
            
        pag_atual = st.session_state['pag_atual']
        inicio = (pag_atual - 1) * items_por_pagina
        fim = inicio + items_por_pagina
        palpites_pagina = palpites[inicio:fim]

        # --- LISTA DE PALPITES (CARDS) ---
        c_tit, c_pag = st.columns([1, 1])
        with c_tit:
            st.subheader("Seus Jogos")
        with c_pag:
            if total_paginas > 1:
                c_prev, c_lbl, c_next = st.columns([1, 2, 1])
                with c_prev:
                    if pag_atual > 1 and st.button("◀", key="btn_prev"):
                        st.session_state['pag_atual'] -= 1
                        st.rerun()
                with c_lbl:
                    st.markdown(f"<p style='text-align: center; margin-top: 5px; font-size: 12px;'>Pág <b>{pag_atual}/{total_paginas}</b></p>", unsafe_allow_html=True)
                with c_next:
                    if pag_atual < total_paginas and st.button("▶", key="btn_next"):
                        st.session_state['pag_atual'] += 1
                        st.rerun()
        
        for i, p in enumerate(palpites_pagina):
            index_real = inicio + i # Índice real na lista completa para exclusão
            acertos = 0
            
            # Lógica de Status e Cores
            found_result = False
            status_display = "Aguardando Sorteio"
            
            if dados:
                for sorteio in dados:
                    if str(sorteio['concurso']) == str(p.get('concurso')):
                        found_result = True
                        sorteados = [int(x) for x in (sorteio.get('dezenas') or sorteio.get('listaDezenas'))]
                        acertos = len(set(p['numeros']) & set(sorteados))
                        
                        if acertos >= 11:
                            status_display = f":green[{acertos} Acertos]"
                        else:
                            status_display = f":red[{acertos} Acertos]"
                        break
            
            # Layout Compacto (Expander)
            if not found_result:
                label_header = f"⏳ Concurso {p.get('concurso', 'N/A')}  |  {status_display}"
            else:
                label_header = f"Concurso {p.get('concurso', 'N/A')}  |  {status_display}"
            
            with st.expander(label_header):
                st.caption(f"Data: {p.get('data', 'N/A')}")
                
                numeros = p['numeros']
                html_numeros = ''.join([f'<div style="width: 30px; height: 30px; background-color: {ROXO_MEDIO}; color: white; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin: 2px;">{n:02d}</div>' for n in numeros])
                st.markdown(f"<div style='text-align: center; margin: 10px 0;'>{html_numeros}</div>", unsafe_allow_html=True)
                
                col_conf, col_trash = st.columns([3, 1])
                with col_conf:
                    st.markdown(f"🤖 Confiança: **{p.get('confianca', 0)}%**")
                with col_trash:
                    if st.button("🗑️ Excluir", key=f"del_{index_real}"):
                        if excluir_palpite(p.get('id'), user_email, index_local=index_real):
                            st.rerun()

# --- TELA: ESTATÍSTICAS ---
with tab_stats:
    if not dados:
        st.error("Sem dados carregados.")
    else:
        ult_40 = dados[:40]
        all_nums = []
        for s in ult_40:
            all_nums.extend([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])
        
        contagem = Counter(all_nums)
        
        # --- FREQUÊNCIA (HOT & COLD) ---
        st.subheader("🔥 Termômetro dos Números")
        c1, c2 = st.columns(2)
        
        with c1:
            top_10 = contagem.most_common(10)
            html_hot = f"""
<div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; height: 100%;">
<h4 style='color: {ROXO_MEDIO}; margin-top:0; text-align: center;'>🔥 Mais Sorteados </h4>
<div style='height: 1px; background-color: #eee; margin: 10px 0;'></div>
"""
            for n, c in top_10:
                html_hot += f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0;">
<div style="display: flex; align-items: center;">
<div style="width: 32px; height: 32px; background-color: {ROXO_MEDIO}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-right: 10px;">{n:02d}</div>
<span style="font-weight: 500; color: #333;">Dezena {n:02d}</span>
</div>
<div style="font-weight: bold; color: {ROXO_MEDIO}; font-size: 16px;">{c}x</div>
</div>
"""
            html_hot += "</div>"
            st.markdown(html_hot, unsafe_allow_html=True)
            
        with c2:
            bottom_6 = contagem.most_common()[:-7:-1]
            html_cold = f"""
<div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; height: 100%;">
<h4 style='color: #0c5460; margin-top:0; text-align: center;'>❄️ Menos Sorteados </h4>
<div style='height: 1px; background-color: #eee; margin: 10px 0;'></div>
"""
            for n, c in bottom_6:
                html_cold += f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0;">
<div style="display: flex; align-items: center;">
<div style="width: 32px; height: 32px; background-color: #6c757d; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-right: 10px;">{n:02d}</div>
<span style="font-weight: 500; color: #333;">Dezena {n:02d}</span>
</div>
<div style="font-weight: bold; color: #0c5460; font-size: 16px;">{c}x</div>
</div>
"""
            html_cold += "</div>"
            st.markdown(html_cold, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Cálculos de Sequência
        sequencias = []

        for n in range(1, 26):
            # Sequência
            curr_seq = 0
            for s in dados:
                nums = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]
                if n in nums: curr_seq += 1
                else: break
            if curr_seq >= 2:
                sequencias.append((n, curr_seq))
        
        # Ordenação
        sequencias.sort(key=lambda x: x[1], reverse=True)

        st.subheader("⚠️ Alertas de Padrões")
        st.markdown("**⚡ Em Sequência**")
        if sequencias:
            for n, s in sequencias[:5]:
                st.markdown(f"""
                <div style="background-color: white; border: 1px solid #eee; padding: 10px; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 20px; margin-right: 10px;">🔥</span>
                        <span style="font-weight: bold; color: #333; font-size: 16px;">Dezena {n:02d}</span>
                    </div>
                    <span style="background-color: {VERDE_CLARO}; color: {VERDE_ESCURO}; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">{s} seguidos</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Sem sequências longas.")

        # --- GRÁFICO DE FREQUÊNCIA ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📊 Frequência Geral")
        
        chart_data = pd.DataFrame.from_dict(contagem, orient='index', columns=['Frequência']).reset_index()
        chart_data.columns = ['Dezena', 'Frequência']
        chart_data['Dezena'] = chart_data['Dezena'].apply(lambda x: f"{x:02d}")
        chart_data = chart_data.sort_values(by='Dezena')
        
        st.bar_chart(chart_data, x='Dezena', y='Frequência', use_container_width=True)

        # --- HISTÓRICO ---
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📜 Ver Histórico (Ultimos 40 sorteios)"):
            df_hist = pd.DataFrame([
                {"Concurso": s['concurso'], "Data": s['data'], "Dezenas": str(sorted([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])).replace('[','').replace(']','')} 
                for s in ult_40
            ])
            st.dataframe(df_hist, hide_index=True, use_container_width=True)

# --- TELA: PREMIAÇÕES ---
with tab_premios:
    st.markdown(f"<h2 style='color: {ROXO_MEDIO};'>🏆 Galeria de Premiados</h2>", unsafe_allow_html=True)
    st.caption("Palpites gerados pelo Lotomind que foram premiados.")
    
    all_palpites, users_map = carregar_todos_palpites_globais()
    
    if not all_palpites:
        st.info("Nenhum palpite registrado na base de dados ainda.")
    else:
        # Processar vencedores
        vencedores = []
        
        if dados: # dados = st.session_state['dados']
            for p in all_palpites:
                p_concurso = str(p.get('concurso'))
                # Encontrar resultado correspondente
                sorteio_match = next((s for s in dados if str(s['concurso']) == p_concurso), None)
                
                if sorteio_match:
                    sorteados = [int(x) for x in (sorteio_match.get('dezenas') or sorteio_match.get('listaDezenas'))]
                    numeros_palpite = p.get('numeros', [])
                    acertos = len(set(numeros_palpite) & set(sorteados))
                    
                    if acertos >= 11:
                        # Calcular prêmio
                        premio = 0
                        for faixa in sorteio_match.get('premiacoes', []):
                            if str(acertos) in faixa.get('descricao', ''):
                                premio = faixa.get('valorPremio', 0)
                                break
                        # Fallback valores fixos
                        if premio == 0:
                            if acertos == 11: premio = 6.0
                            elif acertos == 12: premio = 12.0
                            elif acertos == 13: premio = 30.0
                        
                        username = "Usuário Lotomind"
                            
                        vencedores.append({
                            "username": username,
                            "concurso": p_concurso,
                            "acertos": acertos,
                            "premio": premio,
                            "numeros": numeros_palpite,
                            "tipo": p.get('tipo', 'salvo'),
                            "data": p.get('created_at', '')[:10]
                        })
        
        if not vencedores:
            st.info("Ainda não identificamos palpites premiados nos sorteios recentes.")
        else:
            # Ordenar por prêmio (maior primeiro) e depois acertos
            vencedores.sort(key=lambda x: (x['acertos'], x['premio']), reverse=True)
            
            # Exibir
            for v in vencedores:
                cor_destaque = VERDE_MEDIO if v['acertos'] >= 14 else ROXO_MEDIO
                bg_card = "#fdfdfd" if v['acertos'] < 14 else "#f0fff4"
                border_card = "#eee" if v['acertos'] < 14 else VERDE_CLARO
                
                st.markdown(f"""
                <div style="background-color: {bg_card}; border: 1px solid {border_card}; border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: bold; color: {ROXO_MEDIO}; font-size: 16px;">👤 {v['username']}</div>
                            <div style="font-size: 12px; color: #666; margin-bottom: 4px;">Concurso {v['concurso']} • {v['data']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: bold; font-size: 18px; color: {cor_destaque};">{v['acertos']} Acertos</div>
                            <div style="font-size: 14px; color: #333; font-weight: bold;">R$ {v['premio']:,.2f}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- TELA: STATIC LOTOMIND ---
if tab_static:
    with tab_static:
        st.markdown(f"<h2 style='color: {ROXO_MEDIO};'>📈 Static Lotomind</h2>", unsafe_allow_html=True)
        
        # SEÇÃO 1: JOGOS DA COMUNIDADE
        st.subheader("🌍 Jogos da Comunidade")
        st.caption("Todos os jogos gerados e salvos pelos usuários.")
        
        all_palpites_static, users_map_static = carregar_todos_palpites_globais()
        
        if not all_palpites_static:
            st.info("Nenhum jogo encontrado.")
        else:
            lista_static = []
            for p in all_palpites_static:
                # Identificar acertos se houver resultado
                acertos_static = "-"
                if dados:
                    sorteio_match = next((s for s in dados if str(s['concurso']) == str(p.get('concurso'))), None)
                    if sorteio_match:
                        sorteados = [int(x) for x in (sorteio_match.get('dezenas') or sorteio_match.get('listaDezenas'))]
                        acertos_static = len(set(p.get('numeros', [])) & set(sorteados))
                
                # Nome real do usuário
                u_email = p.get('user_email')
                u_name = users_map_static.get(u_email, u_email) if u_email else "Anônimo"
                
                lista_static.append({
                    "Usuário": u_name,
                    "Concurso": p.get('concurso'),
                    "Números": str(p.get('numeros')),
                    "Acertos": acertos_static
                })
            
            df_static = pd.DataFrame(lista_static)
            st.dataframe(df_static, use_container_width=True, hide_index=True)

        st.markdown("---")
        
        # SEÇÃO 2: ANÁLISE DE RESULTADOS (METRICAS)
        st.subheader("🔍 Análise de Resultados (Métricas)")
        st.caption("Verificação da efetividade das métricas do Lotomind nos últimos sorteios.")
        
        if dados and len(dados) > 1:
            # --- RANKING DE MÉTRICAS ---
            qtd_analise = len(dados) - 1
            stats = {"Top 10": 0, "Paridade": 0, "Repetidos": 0, "Bottom 6": 0, "Sequencial": 0, "Rastreador Faltantes": 0}
            
            if qtd_analise > 0:
                for i in range(qtd_analise):
                    res = dados[i]
                    hist = dados[i+1:]
                    if not hist: continue
                    
                    metricas_result = analisar_metricas_resultado(res, hist)
                    if not metricas_result: continue
                    ok_rep, ok_par, ok_top, ok_bot, ok_seq, ok_rastreador = metricas_result
                    
                    if ok_rep: stats["Repetidos"] += 1
                    if ok_par: stats["Paridade"] += 1
                    if ok_top: stats["Top 10"] += 1
                    if ok_bot: stats["Bottom 6"] += 1
                    if ok_seq: stats["Sequencial"] += 1
                    if ok_rastreador: stats["Rastreador Faltantes"] += 1
                
                ranking = sorted(stats.items(), key=lambda x: x[1], reverse=True)
                
                st.markdown("### 🏆 Ranking de Métricas (Histórico Completo)")
                html_rank = "<div style='background-color: #fff; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 20px;'>"
                for idx, (metrica, count) in enumerate(ranking):
                    pct = (count / qtd_analise) * 100 if qtd_analise > 0 else 0
                    cor_bar = VERDE_MEDIO if pct >= 80 else (ROXO_MEDIO if pct >= 60 else "#dc3545")
                    html_rank += f"<div style='display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 14px;'><span style='font-weight: bold; color: #555;'>{idx+1}. {metrica}</span><span style='font-weight: bold; color: {cor_bar};'>{pct:.0f}%</span></div><div style='width: 100%; background-color: #f0f0f0; height: 8px; border-radius: 4px; margin-bottom: 15px;'><div style='width: {pct}%; background-color: {cor_bar}; height: 8px; border-radius: 4px;'></div></div>"
                html_rank += "</div>"
                st.markdown(html_rank, unsafe_allow_html=True)

            # Analisar os últimos 10 resultados
            for i in range(min(10, len(dados)-1)):
                res = dados[i]
                hist = dados[i+1:] # Histórico anterior a este sorteio
                
                if not hist: continue
                metricas_result = analisar_metricas_resultado(res, hist)
                if not metricas_result: continue
                ok_rep, ok_par, ok_top, ok_bot, ok_seq, ok_rastreador = metricas_result
                
                # Calculo %
                metricas_vals = [ok_rep, ok_par, ok_top, ok_bot, ok_seq, ok_rastreador]
                perc = (sum(metricas_vals) / 6) * 100
                
                cor_perc = VERDE_MEDIO if perc >= 80 else (ROXO_MEDIO if perc >= 60 else "#dc3545")
                def fmt_bool(b): return "✅ OK" if b else "❌ Não"
                
                # Monta o HTML para o expander customizado
                summary_html = f"""
                <summary style="display: flex; justify-content: space-between; align-items: center; width: 100%; cursor: pointer; padding: 12px 15px; background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 10px;">
                    <h4 style="margin: 0; color: {ROXO_MEDIO}; font-size: 16px;">Concurso {res['concurso']}</h4>
                    <span style="background-color: {cor_perc}; color: white; padding: 5px 10px; border-radius: 15px; font-weight: bold; font-size: 14px;">{perc:.0f}% Efetividade</span>
                </summary>
                """

                details_content_html = f"""
                <div style="padding: 15px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 10px 10px; margin-top: -10px;">
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 14px;">
                        <div style="flex: 1; min-width: 120px;"><b>Top 10:</b> {fmt_bool(ok_top)}</div>
                        <div style="flex: 1; min-width: 120px;"><b>Bottom 6:</b> {fmt_bool(ok_bot)}</div>
                        <div style="flex: 1; min-width: 120px;"><b>Paridade:</b> {fmt_bool(ok_par)}</div>
                        <div style="flex: 1; min-width: 120px;"><b>Repetidos:</b> {fmt_bool(ok_rep)}</div>
                        <div style="flex: 1; min-width: 120px;"><b>Sequencial:</b> {fmt_bool(ok_seq)}</div>
                        <div style="flex: 1; min-width: 120px;"><b>Rastreador:</b> {fmt_bool(ok_rastreador)}</div>
                    </div>
                    <div style="margin-top: 15px; font-size: 12px; color: #666; border-top: 1px solid #eee; padding-top: 10px;">
                        <b>Dezenas:</b> {sorted([int(x) for x in (res.get('dezenas') or res.get('listaDezenas'))])}
                    </div>
                </div>
                """
                
                st.markdown(f"""
                <details style='margin-bottom: 10px;'>
                    {summary_html}
                    {details_content_html}
                </details>
                """, unsafe_allow_html=True)

# --- TELA: ESTUDO (ADMIN) ---
if is_admin and tab_estudo:
    with tab_estudo:
        st.markdown(f"<h2 style='color: {ROXO_MEDIO};'>🔬 Box de Estudos</h2>", unsafe_allow_html=True)
        st.info("Esta funcionalidade gera automaticamente 100 jogos para **todas as 20 combinações possíveis de 3 métricas**, permitindo uma análise completa de desempenho de cada estratégia.")

        if 'study_blocks' not in st.session_state:
            st.session_state.study_blocks = []
        
        if ultimo_resultado:
            proximo_concurso_estudo = ultimo_resultado.get('proximoConcurso')
            st.subheader(f"Geração de Caixas de Estudo para o Concurso: {proximo_concurso_estudo}")

            if st.button("🤖 Gerar Box de Estudos (Cruzamento de 3 Métricas)", type="primary", use_container_width=True):
                METRICAS_TOTAIS = ["Repetidos", "Paridade", "Top 10", "Bottom 6", "Sequencial", "Rastreador de Faltantes"]
                combinacoes = list(combinations(METRICAS_TOTAIS, 3))
                
                st.session_state.study_blocks = [] # Reseta os blocos anteriores
                palpites_para_salvar_db = []
                
                progress_bar = st.progress(0, text="Iniciando geração...")
                
                for i, combo in enumerate(combinacoes):
                    combo_list = list(combo)
                    progress_text = f"Gerando box {i+1}/{len(combinacoes)}: {', '.join(combo_list)}"
                    progress_bar.progress((i + 1) / len(combinacoes), text=progress_text)
                    
                    palpites_gerados = []
                    for _ in range(100):
                        jogo, confianca, _ = gerar_palpite_logica(
                            dados,
                            ultimo_resultado,
                            palpites_existentes=palpites_gerados,
                            metricas_selecionadas=combo_list
                        )
                        if jogo:
                            palpites_gerados.append(jogo)
                            # Adiciona o palpite à lista para salvar no banco de dados
                            # Nota: A tabela 'palpites_estudo' precisa ter uma coluna 'metricas_usadas' (tipo texto ou json)
                            palpites_para_salvar_db.append({
                                "concurso": proximo_concurso_estudo,
                                "numeros": jogo,
                                "confianca": confianca,
                                "metricas_usadas": combo_list
                            })
                        else:
                            # Se não conseguir gerar um jogo, para de tentar para este combo
                            break 

                    if palpites_gerados:
                        st.session_state.study_blocks.append({
                            "concurso": proximo_concurso_estudo,
                            "metricas": combo_list,
                            "palpites": palpites_gerados,
                            "timestamp": datetime.datetime.now()
                        })

                # Salva todos os palpites gerados no banco de uma vez
                if palpites_para_salvar_db:
                    ok, msg = salvar_palpites_estudo_db(palpites_para_salvar_db)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

                progress_bar.empty()
                st.success(f"{len(st.session_state.study_blocks)} caixas de estudo geradas com sucesso!")
                time.sleep(1)
                st.rerun()

            st.markdown("---")
            st.subheader("🔍 Análise das Caixas de Estudo")

            if not st.session_state.study_blocks:
                st.write("Nenhuma caixa de estudo foi gerada nesta sessão. Clique no botão acima para gerar.")
            else:
                resultado_real = next((s for s in dados if str(s['concurso']) == str(proximo_concurso_estudo)), None)

                if not resultado_real:
                    st.warning(f"Aguardando o resultado do concurso {proximo_concurso_estudo} para analisar as caixas de estudo.")
                
                for i, block in enumerate(st.session_state.study_blocks):
                    ts = block['timestamp'].strftime("%H:%M:%S")
                    metrics_str = ", ".join(block['metricas'])
                    expander_title = f"Caixa {i+1}: {metrics_str}"
                    
                    with st.expander(expander_title):
                        if not resultado_real:
                            st.info("Aguardando resultado para análise.")
                            st.write(f"**{len(block['palpites'])} palpites gerados:**")
                            st.dataframe(pd.DataFrame({"Palpites": [str(p) for p in block['palpites']]}), hide_index=True, use_container_width=True)
                        else:
                            dezenas_sorteadas = [int(x) for x in (resultado_real.get('dezenas') or resultado_real.get('listaDezenas'))]
                            st.markdown(f"**Resultado do Concurso {proximo_concurso_estudo}:**")
                            st.code(str(sorted(dezenas_sorteadas)), language=None)

                            contagem_acertos = Counter()
                            total_ganho_bloco = 0.0
                            for palpite in block['palpites']:
                                acertos = len(set(palpite) & set(dezenas_sorteadas))
                                contagem_acertos.update([acertos])
                                if acertos >= 11:
                                    premio_encontrado = 0
                                    for faixa in resultado_real.get('premiacoes', []):
                                        if str(acertos) in faixa.get('descricao', ''):
                                            premio_encontrado = faixa.get('valorPremio', 0)
                                            break
                                    if premio_encontrado == 0: # Fallback
                                        if acertos == 11: premio_encontrado = 6.0
                                        elif acertos == 12: premio_encontrado = 12.0
                                        elif acertos == 13: premio_encontrado = 30.0
                                    total_ganho_bloco += premio_encontrado

                            # --- Novas Estatísticas de Análise ---
                            total_investido_bloco = len(block['palpites']) * 3.00
                            lucro_prejuizo_bloco = total_ganho_bloco - total_investido_bloco
                            cor_lucro = VERDE_MEDIO if lucro_prejuizo_bloco >= 0 else "#dc3545"
                            
                            jogos_premiados = sum(contagem_acertos.get(n, 0) for n in range(11, 16))
                            percentual_premiado = (jogos_premiados / len(block['palpites'])) * 100
                            jogos_nao_premiados = len(block['palpites']) - jogos_premiados

                            st.markdown(f"##### 💰 Balanço Financeiro do Box")
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Investimento", f"R$ {total_investido_bloco:,.2f}", delta=None)
                            m2.metric("Retorno", f"R$ {total_ganho_bloco:,.2f}", delta=None)
                            m3.metric("Balanço Final", f"R$ {lucro_prejuizo_bloco:,.2f}", delta_color="normal" if lucro_prejuizo_bloco >= 0 else "inverse")

                            st.markdown(f"##### 🎯 Desempenho do Box")
                            d1, d2 = st.columns(2)
                            d1.metric("Jogos Premiados (11+)", f"{jogos_premiados}", f"{percentual_premiado:.1f}% do total")
                            d2.metric("Jogos Não Premiados (0-10)", f"{jogos_nao_premiados}")
                            
                            st.markdown(f"##### Resumo de Acertos")
                            faixas_estudo = range(15, 10, -1)
                            html_list_estudo = ""
                            for n_acertos in faixas_estudo:
                                qtd = contagem_acertos.get(n_acertos, 0)
                                style_row = "display: flex; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid #eee;"
                                if qtd > 0:
                                    style_row += f" background-color: {VERDE_CLARO}; font-weight: bold; color: {VERDE_ESCURO}; border-radius: 5px; border-bottom: none; margin-bottom: 2px;"
                                html_list_estudo += f'<div style="{style_row}"><span>{n_acertos} Acertos</span><span>{qtd} jogos</span></div>'
                            
                            st.markdown(f"<div style='border: 1px solid #ddd; border-radius: 10px; padding: 10px;'>{html_list_estudo}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📚 Recuperar e Analisar Estudos Salvos")
        st.caption("Recupere estudos gerados anteriormente para conferência após o sorteio.")

        concurso_analise_input = st.number_input("Número do Concurso para Análise", value=int(ultimo_resultado['concurso']) if ultimo_resultado else 0, step=1)
        
        if st.button("🔎 Buscar no Banco de Dados"):
            with st.spinner("Buscando estudos..."):
                estudos_db = carregar_palpites_estudo(concurso_analise_input)
                
            if not estudos_db:
                st.warning(f"Nenhum estudo encontrado no banco de dados para o concurso {concurso_analise_input}.")
            else:
                # Agrupa os estudos por métricas usadas
                boxes_recuperados = defaultdict(list)
                for item in estudos_db:
                    m = item.get('metricas_usadas')
                    # Normaliza a chave para agrupar corretamente
                    if isinstance(m, list):
                        key = tuple(sorted(m))
                    elif isinstance(m, str):
                        try: key = tuple(sorted(json.loads(m.replace("'", '"')))) 
                        except: key = (str(m),)
                    else:
                        key = ("Métricas não identificadas",)
                    
                    boxes_recuperados[key].append(item['numeros'])

                # Busca resultado para conferência
                resultado_conf = next((s for s in dados if str(s['concurso']) == str(concurso_analise_input)), None)
                
                if resultado_conf:
                    dezenas_sorteadas = [int(x) for x in (resultado_conf.get('dezenas') or resultado_conf.get('listaDezenas'))]
                    st.success(f"Resultado Oficial do Concurso {concurso_analise_input} carregado!")
                    st.code(str(sorted(dezenas_sorteadas)), language=None)

                    # --- RANKING DE CAIXAS ---
                    st.markdown("### 🏆 Ranking de Desempenho das Caixas")
                    ranking_data = []
                    
                    for metrics_tuple, jogos in boxes_recuperados.items():
                        metrics_str = " + ".join(metrics_tuple)
                        hits_counter = Counter()
                        ganho_box = 0.0
                        
                        for jogo in jogos:
                            acertos = len(set(jogo) & set(dezenas_sorteadas))
                            hits_counter[acertos] += 1
                            
                            # Calculo financeiro estimado para o ranking
                            if acertos >= 11:
                                v_premio = 0
                                for f in resultado_conf.get('premiacoes', []):
                                    if str(acertos) in f.get('descricao', ''):
                                        v_premio = f.get('valorPremio', 0)
                                        break
                                if v_premio == 0: # Fallback
                                    if acertos == 11: v_premio = 6.0
                                    elif acertos == 12: v_premio = 12.0
                                    elif acertos == 13: v_premio = 30.0
                                ganho_box += v_premio
                        
                        investimento_box = len(jogos) * 3.00
                        saldo_box = ganho_box - investimento_box
                        
                        ranking_data.append({
                            "Caixa (Métricas)": metrics_str,
                            "15 Pts": hits_counter[15],
                            "14 Pts": hits_counter[14],
                            "13 Pts": hits_counter[13],
                            "12 Pts": hits_counter[12],
                            "11 Pts": hits_counter[11],
                            "Saldo (R$)": saldo_box
                        })
                    
                    if ranking_data:
                        df_rank = pd.DataFrame(ranking_data)
                        # Ordena: Mais 15, depois mais 14, ..., por fim maior Saldo
                        df_rank = df_rank.sort_values(by=["15 Pts", "14 Pts", "13 Pts", "Saldo (R$)"], ascending=False)
                        st.dataframe(df_rank, hide_index=True, use_container_width=True, 
                                     column_config={"Saldo (R$)": st.column_config.NumberColumn(format="R$ %.2f")})
                else:
                    st.info(f"Resultado do concurso {concurso_analise_input} ainda não disponível na base local. Mostrando apenas estatísticas de volume.")

                # Exibe cada Box recuperado
                for metrics_tuple, jogos in boxes_recuperados.items():
                    metrics_str = " + ".join(metrics_tuple)
                    with st.expander(f"📦 Box: {metrics_str} ({len(jogos)} jogos)"):
                        if resultado_conf:
                            hits_counter = Counter()
                            for jogo in jogos:
                                acertos = len(set(jogo) & set(dezenas_sorteadas))
                                hits_counter[acertos] += 1
                            
                            # Estatísticas textuais solicitadas
                            msg_stats = []
                            for k in [15, 14, 13, 12, 11]:
                                count = hits_counter.get(k, 0)
                                if count > 0: msg_stats.append(f"**{count}** jogos com **{k}** acertos")
                            
                            count_low = sum(hits_counter.get(i, 0) for i in range(11))
                            if count_low > 0: msg_stats.append(f"**{count_low}** jogos com **10 ou menos** acertos")
                            
                            st.markdown(" • ".join(msg_stats))
                            
                            # Gráfico simples de distribuição
                            st.bar_chart(hits_counter)
                        else:
                            st.write(f"Contém {len(jogos)} jogos gerados. Aguardando sorteio para conferência de acertos.")

# --- TELA: ADMIN (VISÍVEL APENAS PARA ADMINS) ---
if is_admin and tab_admin:
    with tab_admin:
        st.markdown(f"<h2 style='color: {ROXO_MEDIO};'>⚙️ Administração</h2>", unsafe_allow_html=True)
        st.info("Utilize esta tela para inserir manualmente os dados do sorteio caso a API esteja instável.")
        
        with st.form("form_admin_sorteio_main"):
            st.subheader("📝 Dados do Último Sorteio Realizado")
            c_adm_1, c_adm_2 = st.columns(2)
            with c_adm_1:
                adm_concurso = st.number_input("Concurso", min_value=1, step=1, value=int(ultimo_resultado['concurso']) if ultimo_resultado else 3000)
                adm_data = st.text_input("Data do Sorteio (dd/mm/aaaa)", value=ultimo_resultado.get('data', datetime.datetime.now().strftime('%d/%m/%Y')) if ultimo_resultado else "")
            with c_adm_2:
                # Tenta pegar ganhadores e premio do ultimo resultado para preencher
                last_ganhadores = 0
                last_premio = 0.0
                if ultimo_resultado and ultimo_resultado.get('premiacoes'):
                    last_ganhadores = ultimo_resultado['premiacoes'][0].get('ganhadores', 0)
                    last_premio = ultimo_resultado['premiacoes'][0].get('valorPremio', 0.0)
                
                adm_ganhadores = st.number_input("Ganhadores (15 acertos)", min_value=0, step=1, value=int(last_ganhadores))
                adm_premio = st.number_input("Prêmio Pago (R$)", min_value=0.0, step=1000.0, format="%.2f", value=float(last_premio))
            
            st.markdown("**Números Sorteados:**")
            # Multiselect para as dezenas
            default_dezenas = [int(x) for x in (ultimo_resultado.get('dezenas') or ultimo_resultado.get('listaDezenas'))] if ultimo_resultado else []
            adm_dezenas = st.multiselect("Selecione as 15 dezenas:", options=list(range(1, 26)), default=default_dezenas)
            
            st.markdown("---")
            st.subheader("🔮 Dados do Próximo Sorteio")
            c_prox_1, c_prox_2, c_prox_3 = st.columns(3)
            with c_prox_1:
                adm_prox_concurso = st.number_input("Próximo Concurso", min_value=1, step=1, value=int(ultimo_resultado.get('proximoConcurso', adm_concurso + 1)) if ultimo_resultado else adm_concurso + 1)
            with c_prox_2:
                adm_prox_data = st.text_input("Data Próximo (dd/mm/aaaa)", value=ultimo_resultado.get('dataProximoConcurso', '') if ultimo_resultado else "")
            with c_prox_3:
                adm_prox_premio = st.number_input("Estimativa Prêmio (R$)", min_value=0.0, step=100000.0, format="%.2f", value=float(ultimo_resultado.get('valorEstimadoProximoConcurso', 1700000.0)) if ultimo_resultado else 1700000.0)
            
            btn_salvar_manual = st.form_submit_button("💾 Salvar Sorteio Manual", type="primary", use_container_width=True)
            
            if btn_salvar_manual:
                if len(adm_dezenas) != 15:
                    st.error("Selecione exatamente 15 dezenas.")
                else:
                    payload = {
                        "concurso": adm_concurso,
                        "data_sorteio": adm_data,
                        "dezenas": sorted(adm_dezenas),
                        "ganhadores": adm_ganhadores,
                        "premio_pago": adm_premio,
                        "prox_concurso": adm_prox_concurso,
                        "prox_data": adm_prox_data,
                        "prox_premio": adm_prox_premio
                    }
                    ok, msg = salvar_sorteio_manual_db(payload)
                    if ok: 
                        st.success(msg)
                        st.session_state['dados'] = carregar_dados() # Recarrega dados
                        time.sleep(1)
                        st.rerun()
                    else: st.error(msg)

# Rodapé
st.markdown("---")
c_cred, c_sair = st.columns([4, 1])
with c_cred:
    st.caption("Developed by Rodrigo Carielo | Lotomind Web Version")
with c_sair:
    if st.button("Sair", key="btn_sair_footer", use_container_width=True, type="primary"):
        st.session_state['logged_user'] = None
        if 'lotomind_user' in cookie_manager:
            del cookie_manager['lotomind_user']
        cookie_manager.save()
        st.rerun()
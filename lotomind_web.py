import streamlit as st
import pandas as pd
import random
import requests
import json
import os
import urllib.parse
from collections import Counter
import datetime
import time
from supabase import create_client, Client
from streamlit_cookies_manager import CookieManager
import streamlit.components.v1 as components

st.markdown("""
<style>
/* ===== ESCONDE MENU 3 PONTINHOS E RODAPÉ ===== */
#MainMenu {
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
    justify-content: flex-end;
    border-bottom: none !important;
    gap: 5px;
}
/* Estilo das abas */
div[data-testid="stTabs"] button[role="tab"] {
    background-color: transparent;
    border: none;
    color: #888; /* Cor para abas não selecionadas */
    font-weight: 700;
    font-size: 26px;
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

# --- CONFIGURAÇÕES ---
ARQUIVO_CACHE = "loto_completo_cache.json"
ARQUIVO_PALPITES = "meus_palpites.json"

# Configuração da Página Web
st.set_page_config(
    page_title="Lotomind Web",
    page_icon="🍀",
    layout="centered",
    initial_sidebar_state="expanded"
)

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
            background-color: #333333 !important;
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
            response = supabase_client.table("palpites").select("*").eq("user_email", user_email).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            st.error(f"Erro ao carregar da nuvem: {e}")
            return []

    # Fallback para local (se não tiver internet ou login)
    if os.path.exists(ARQUIVO_PALPITES):
        try:
            with open(ARQUIVO_PALPITES, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_novo_palpite(novo_palpite, user_email=None):
    # Se tiver Supabase, salva na nuvem
    if supabase_client and user_email:
        # Adiciona o email ao objeto antes de salvar
        novo_palpite['user_email'] = user_email
        try:
            supabase_client.table("palpites").insert(novo_palpite).execute()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar na nuvem: {e}")
            return False
    
    # Fallback Local (Modo antigo)
    palpites_locais = carregar_palpites()
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

def buscar_dados_api():
    try:
        r = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/", timeout=7)
        if r.status_code == 200:
            dados = r.json()[:60] # Pega os últimos 60
            with open(ARQUIVO_CACHE, "w") as f:
                json.dump(dados, f)
            return dados
    except:
        return None

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
    # Tenta carregar do cache primeiro para ser rápido
    if os.path.exists(ARQUIVO_CACHE):
        try:
            with open(ARQUIVO_CACHE, "r") as f:
                return json.load(f)
        except:
            pass
    # Se não der, busca da API
    return buscar_dados_api()

def gerar_palpite_logica(historico, ultimo_resultado):
    """Lógica original do Lotomind adaptada para função pura"""
    if not historico or not ultimo_resultado:
        return None, 0, "Dados insuficientes para gerar palpite."

    ult_60 = historico[:60]
    ult_3 = historico[:3]
    
    dezenas_ultimo = [int(n) for n in (ultimo_resultado.get('dezenas') or ultimo_resultado.get('listaDezenas'))]

    # Frequência
    contagem = Counter()
    for s in ult_60:
        contagem.update([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])
    
    top_10 = [n for n, c in contagem.most_common(10)]
    bottom_6 = [n for n, c in contagem.most_common()[-6:]]

    # Atrasados (Obrigatórios pela lógica original)
    obrigatorios_atraso = []
    for n in range(1, 26):
        saiu_nos_3 = False
        for s in ult_3:
            res_sorteio = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]
            if n in res_sorteio: 
                saiu_nos_3 = True
                break
        if not saiu_nos_3: 
            obrigatorios_atraso.append(n)

    tentativas = 0
    while tentativas < 5000:
        tentativas += 1
        jogo = sorted(random.sample(range(1, 26), 15))

        # Regras Imutáveis
        r_count = len([n for n in jogo if n in dezenas_ultimo])
        if r_count not in [8, 9]: continue
        
        # Regra: 8 impares e 7 pares ou 8 pares e 7 impares (obrigatorio)
        pares = len([n for n in jogo if n % 2 == 0])
        impares = 15 - pares
        if not ((impares == 8 and pares == 7) or (impares == 7 and pares == 8)): continue
        
        # Regra: numero que tiver atrasado a 3 ou + sorteios (obrigatorio)
        if not all(n in jogo for n in obrigatorios_atraso): continue

        # Regras Flexíveis
        t_ok = 5 <= len([n for n in jogo if n in top_10]) <= 7
        b_ok = 3 <= len([n for n in jogo if n in bottom_6]) <= 4

        # Cálculo de Confiança (3 obrigatórias = 60%, + 20% cada flexível)
        confianca = 60
        if t_ok: confianca += 20
        if b_ok: confianca += 20

        # Se atingir 100% ou estourar o limite de tentativas
        if confianca == 100 or tentativas > 4500:
            motivos = []
            if not t_ok: motivos.append("Top10 fora")
            if not b_ok: motivos.append("Bottom6 fora")
            
            msg = "Todas as métricas atendidas!" if not motivos else f"Ajuste: {', '.join(motivos)}"
            return jogo, confianca, f"Confiança: {confianca}% | {msg}"

    return jogo, 60, "Gerado por exaustão (Confiança Baixa)"

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

# Define user_email para ser usado em todo o app
user_email = None
if supabase_client and st.session_state.get('logged_user'):
    user = st.session_state['logged_user']
    user_email = user.get('email')
    
# --- TELA DE LOGIN / CADASTRO (BLOQUEANTE) ---
if not st.session_state['logged_user']:
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
                c_user = st.text_input("Escolha um Usuário")
                c_email = st.text_input("Seu Email")
                c_pass = st.text_input("Escolha uma Senha", type="password")
                submit_cad = st.form_submit_button("Cadastrar", use_container_width=True)
                
                if submit_cad:
                    ok, msg = register_user_db(c_user, c_email, c_pass)
                    if ok: 
                        st.success(msg)
                        time.sleep(1.5)
                        st.session_state['login_tab_select'] = "Entrar"
                        st.rerun()
                    else: 
                        st.error(msg)

    st.stop() # Interrompe a execução aqui se não estiver logado

# --- HEADER E MENU DE NAVEGAÇÃO ---
logo_col, menu_col = st.columns([2, 3])
with logo_col:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    elif os.path.exists("../logo.png"):
        st.image("../logo.png", use_container_width=True)
    else:
        st.markdown(f"<h1 style='color: {ROXO_MEDIO};'>Lotomind</h1>", unsafe_allow_html=True)

tab_inicio, tab_palpites, tab_stats = st.tabs([" 🍀 Início ", " 📜 Meus Palpites ", " 📊 Estatísticas "])

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

        # --- GERADOR DE PALPITE (SEM ABAS) ---
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botões de Ação (Gerar + Atualizar)
        c_gerar, c_update = st.columns([3, 1])
        with c_gerar:
            btn_gerar = st.button("✨ GERAR PALPITE", type="primary", use_container_width=True)
        
        with c_update:
            if st.button("🔄 Atualizar", use_container_width=True):
                with st.spinner("Buscando dados..."):
                    novos = buscar_dados_api()
                    if novos:
                        st.session_state['dados'] = novos
                        st.success("Atualizado!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro.")
        
        if btn_gerar:
            if dados and ultimo_resultado:
                with st.spinner("Analisando estatísticas e padrões..."):
                    time.sleep(0.8) # Pequeno delay para sensação de processamento
                    jogo, confianca, msg = gerar_palpite_logica(dados, ultimo_resultado)
                    st.session_state['palpite_atual'] = jogo
                    st.session_state['msg_palpite'] = msg
                    st.session_state['confianca_atual'] = confianca
            else:
                st.error("Erro ao carregar dados.")

        # Exibição do Palpite Gerado
        if st.session_state['palpite_atual']:
            jogo = st.session_state['palpite_atual']
            confianca = st.session_state.get('confianca_atual', 0)
            msg = st.session_state['msg_palpite']
            
            st.markdown("---")
            
            # Organizar números em 3 linhas de 5
            rows_html = []
            for i in range(0, 15, 5):
                chunk = jogo[i:i+5]
                row_content = ''.join([f'<div style="width: 40px; height: 40px; background-color: {ROXO_MEDIO}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">{n:02d}</div>' for n in chunk])
                rows_html.append(f'<div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 8px;">{row_content}</div>')
            
            numeros_html = "".join(rows_html)

            # Card do Palpite
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

            # Botões de Ação Secundários
            c_salvar, c_share = st.columns(2)
            with c_salvar:
                # Botão Salvar com fundo PRETO (agora usa o estilo secondary customizado)
                if st.button("💾 Salvar Palpite", use_container_width=True):
                    novo = {
                        "concurso": ultimo_resultado.get('proximoConcurso', 'N/A'),
                        "data": ultimo_resultado.get('dataProximoConcurso', 'S/D'),
                        "numeros": jogo,
                        "confianca": confianca
                    }
                    if salvar_novo_palpite(novo, user_email):
                        st.toast("Palpite salvo com sucesso!", icon="✅")
            
            with c_share:
                nums_str = " ".join([f"{n:02d}" for n in jogo])
                texto_wpp = f"🍀 *Lotomind* sugere:\nConcurso: {ultimo_resultado.get('proximoConcurso')}\n\n`{nums_str}`"
                link_wpp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_wpp)}"
                st.link_button("📱 Enviar por WhatsApp", link_wpp, use_container_width=True)

        # --- ÚLTIMO RESULTADO (MOVIDO PARA BAIXO) ---
        st.markdown("---")
        st.subheader("Último Resultado")
        
        # Card do Último Resultado
        # Tratamento de erro para evitar falhas se a API retornar dados incompletos
        premiacoes = ultimo_resultado.get('premiacoes')
        premiacao_15 = premiacoes[0] if premiacoes and isinstance(premiacoes, list) else {}
        
        ganhadores = premiacao_15.get('ganhadores', 0)
        valor_premio = premiacao_15.get('valorPremio', 0)
        dezenas = ultimo_resultado.get('dezenas') or ultimo_resultado.get('listaDezenas') or []
        
        # Gera o HTML das bolinhas separadamente para evitar erros de renderização
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
        
        cols_acertos = st.columns(4)
        faixas = range(15, 4, -1) # 15 até 5
        
        for i, n_acertos in enumerate(faixas):
            qtd = contagem_faixas.get(n_acertos, 0)
            cor_bg = "#f0f2f6"
            cor_txt = "#333"
            border = "1px solid #eee"
            
            if n_acertos >= 14: 
                cor_bg = VERDE_CLARO
                cor_txt = VERDE_ESCURO
                border = f"1px solid {VERDE_MEDIO}"
            elif n_acertos >= 11:
                cor_bg = "#e8f4f8"
                cor_txt = ROXO_MEDIO
            
            with cols_acertos[i % 4]:
                st.markdown(f"""
                <div style="background-color: {cor_bg}; border: {border}; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px;">
                    <span style="font-size: 18px; font-weight: bold; color: {cor_txt};">{qtd}</span><br>
                    <span style="font-size: 12px; color: #666;">{n_acertos} Acertos</span>
                </div>
                """, unsafe_allow_html=True)

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
    st.markdown(f"<h2 style='color: {ROXO_MEDIO};'>📊 Estatísticas (Últimos 60)</h2>", unsafe_allow_html=True)
    
    if not dados:
        st.error("Sem dados carregados.")
    else:
        ult_60 = dados[:60]
        all_nums = []
        for s in ult_60:
            all_nums.extend([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])
        
        contagem = Counter(all_nums)
        
        # --- FREQUÊNCIA (HOT & COLD) ---
        st.subheader("🔥 Termômetro dos Números")
        c1, c2 = st.columns(2)
        
        with c1:
            top_10 = contagem.most_common(10)
            html_hot = f"""
<div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; height: 100%;">
<h4 style='color: {ROXO_MEDIO}; margin-top:0; text-align: center;'>🔥 Mais Sorteados (Top 10)</h4>
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
<h4 style='color: #0c5460; margin-top:0; text-align: center;'>❄️ Menos Sorteados (Top 6)</h4>
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

        # Cálculos de Atraso e Sequência
        atrasados = []
        sequencias = []

        for n in range(1, 26):
            # Atraso
            curr_atraso = 0
            for s in dados:
                nums = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]
                if n not in nums: curr_atraso += 1
                else: break
            if curr_atraso >= 2:
                atrasados.append((n, curr_atraso))

            # Sequência
            curr_seq = 0
            for s in dados:
                nums = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]
                if n in nums: curr_seq += 1
                else: break
            if curr_seq >= 2:
                sequencias.append((n, curr_seq))
        
        # Ordenação
        atrasados.sort(key=lambda x: x[1], reverse=True)
        sequencias.sort(key=lambda x: x[1], reverse=True)

        st.subheader("⚠️ Alertas de Padrões")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**🐢 Mais Atrasados**")
            if atrasados:
                for n, d in atrasados[:5]:
                    st.markdown(f"""
                    <div style="background-color: white; border: 1px solid #eee; padding: 10px; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="display: flex; align-items: center;">
                            <span style="font-size: 20px; margin-right: 10px;">⏳</span>
                            <span style="font-weight: bold; color: #333; font-size: 16px;">Dezena {n:02d}</span>
                        </div>
                        <span style="background-color: #ffc107; color: #333; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">{d} jogos</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Sem atrasos significativos.")
        
        with c4:
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
        with st.expander("📜 Ver Histórico Completo (Tabela)"):
            df_hist = pd.DataFrame([
                {"Concurso": s['concurso'], "Data": s['data'], "Dezenas": str(sorted([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])).replace('[','').replace(']','')} 
                for s in ult_60
            ])
            st.dataframe(df_hist, hide_index=True, use_container_width=True)

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
import streamlit as st
import random
import requests
import json
import os
import urllib.parse
from collections import Counter
import datetime
from supabase import create_client, Client
from streamlit_cookies_manager import CookieManager

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

# --- ESTILOS VISUAIS (Fundo Branco + Compacto) ---
st.markdown("""
    <style>
        /* PALETA: Fundo Branco, Texto Escuro, Detalhes em Roxo */
        .stApp {
            background-color: #ffffff;
            color: #31333F;
        }
        /* Títulos em Roxo da Lotofácil */
        h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #4b0082 !important;
        }
        /* Botão Primário (Gerar Palpite) em VERDE */
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #28a745 !important;
            color: white !important;
            border: none;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #218838 !important;
            color: white !important;
        }
        /* Reduzir margens para ficar mais compacto */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS E LÓGICA (Mantendo a original) ---

# Initialize cookie manager
cookie_manager = CookieManager()

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

# --- AUTO-LOGIN FROM COOKIE ---
if 'logged_user' not in st.session_state:
    st.session_state['logged_user'] = None

if not st.session_state['logged_user']:
    # O get() precisa ser chamado antes de qualquer outro elemento do Streamlit
    username_from_cookie = cookie_manager.get('lotomind_user')
    if username_from_cookie:
        user_data = get_user_db(username_from_cookie)
        if user_data:
            st.session_state['logged_user'] = user_data
# --------------------------

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
    if not password.isnumeric(): return False, "A senha deve ser numérica."
    
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

def reset_password_db(username, email, new_password):
    user = get_user_db(username)
    if user and user.get('email') == email:
        if not new_password.isnumeric(): return False, "A nova senha deve ser numérica."
        try:
            supabase_client.table("users").update({"password": new_password}).eq("username", username).execute()
            return True, "Senha alterada com sucesso!"
        except Exception as e: return False, f"Erro: {e}"
    return False, "Usuário ou Email incorretos."
# -------------------------------------------------

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

# --- SIDEBAR & LOGIN ---

# Sidebar (Menu Lateral)
with st.sidebar:
    # Tenta achar o logo na pasta atual ou na anterior
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    elif os.path.exists("../logo.png"):
        st.image("../logo.png", width=150)
    else:
        st.title("Lotomind")
    
    # --- ÁREA DE LOGIN ---
    st.markdown("### 👤 Sua Conta")
    
    if 'logged_user' not in st.session_state:
        st.session_state['logged_user'] = None

    if supabase_client:
        if st.session_state['logged_user']:
            user = st.session_state['logged_user']
            st.success(f"Olá, {user['username']}!")
            st.caption(f"Email: {user['email']}")
            if st.button("Sair", key="btn_logout"):
                st.session_state['logged_user'] = None
                cookie_manager.delete('lotomind_user')
                st.rerun()
            user_email = user['email'] # Usa o email do cadastro para vincular os palpites
        else:
            tab_login, tab_cad, tab_rec = st.tabs(["Login", "Cadastro", "Ajuda"])
            
            with tab_login:
                l_user = st.text_input("Usuário", key="l_u")
                l_pass = st.text_input("Senha (Numérica)", type="password", key="l_p")
                permanecer_logado = st.checkbox("Permanecer logado", key="chk_persist")
                if st.button("Entrar", key="btn_login", type="primary"):
                    u = login_user_db(l_user, l_pass)
                    if u:
                        st.session_state['logged_user'] = u
                        if permanecer_logado:
                            # Salva o cookie por 30 dias
                            cookie_manager.set('lotomind_user', u['username'], expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        st.rerun()
                    else: st.error("Dados incorretos.")
            
            with tab_cad:
                c_user = st.text_input("Criar Usuário", key="c_u")
                c_email = st.text_input("Seu Email", key="c_e")
                c_pass = st.text_input("Senha (Numérica)", type="password", key="c_p")
                if st.button("Cadastrar", key="btn_cad"):
                    ok, msg = register_user_db(c_user, c_email, c_pass)
                    if ok: st.success(msg)
                    else: st.error(msg)
            
            with tab_rec:
                st.caption("Recuperar Acesso:")
                r_user = st.text_input("Usuário", key="r_u")
                r_email = st.text_input("Email", key="r_e")
                r_pass = st.text_input("Nova Senha", type="password", key="r_p")
                if st.button("Alterar Senha", key="btn_reset"):
                    ok, msg = reset_password_db(r_user, r_email, r_pass)
                    if ok: st.success(msg)
                    else: st.error(msg)
            
            user_email = None
    else:
        st.error("Supabase não configurado. Usando modo Offline (Local).")
        user_email = None
    # ---------------------
    
    def on_menu_change():
        st.session_state.menu_changed = True

    menu = st.radio(
        "Navegação", 
        ["Início", "Meus Palpites", "Estatísticas"],
        key="menu_selection",
        on_change=on_menu_change
    )
    
    st.markdown("---")
    if st.button("🔄 Forçar Atualização"):
        with st.spinner("Buscando dados na Caixa..."):
            novos = buscar_dados_api()
            if novos:
                st.session_state['dados'] = novos
                st.success("Dados atualizados!")
            else:
                st.error("Erro ao conectar.")

dados = st.session_state['dados']
ultimo_resultado = dados[0] if dados else None

# --- LÓGICA PARA FECHAR SIDEBAR ---
if st.session_state.get("menu_changed", False):
    st.session_state.menu_changed = False
    st.components.v1.html(
        """
        <script>
            const streamlitDoc = window.parent.document;
            const sidebar = streamlitDoc.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                const closeButton = sidebar.querySelector('button[kind="secondary"]');
                if (closeButton) {
                    closeButton.click();
                }
            }
        </script>
        """,
        height=0,
    )

# --- TELA: INÍCIO ---
if menu == "Início":
    st.title("LotoMind 🍀")
    
    if ultimo_resultado:
        # --- SEÇÃO 1: PRÓXIMO CONCURSO ---
        st.subheader("🎯 Próximo Concurso")
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)

            prox_concurso = ultimo_resultado.get('proximoConcurso')
            c1.metric("Concurso", prox_concurso if prox_concurso else "Aguardando")

            prox_data = ultimo_resultado.get('dataProximoConcurso')
            c2.metric("Data", prox_data if prox_data else "Aguardando")
            
            valor_estimado = ultimo_resultado.get('valorEstimadoProximoConcurso', 0)
            c3.metric("Prêmio Estimado", f"R$ {valor_estimado:,.2f}")

    # --- SEÇÃO 2: GERADOR DE PALPITES ---
    st.divider()
    st.subheader("Gerador de Jogos")

    if st.button("🎲 GERAR NOVO PALPITE", type="primary", use_container_width=True):
        if dados and ultimo_resultado:
            jogo, confianca, msg = gerar_palpite_logica(dados, ultimo_resultado)
            st.session_state['palpite_atual'] = jogo
            st.session_state['msg_palpite'] = msg
            st.session_state['confianca_atual'] = confianca
        else:
            st.error("Não foi possível carregar os dados para gerar um palpite.")

    if st.session_state['palpite_atual']:
        jogo = st.session_state['palpite_atual']
        
        st.markdown(f"<h2 style='text-align: center; color: #4b0082;'>{' '.join([f'{n:02d}' for n in jogo])}</h2>", unsafe_allow_html=True)
        st.info(st.session_state['msg_palpite'])

        col_a, col_b = st.columns(2)
        if col_a.button("💾 Salvar Palpite"):
            if ultimo_resultado:
                novo = {
                    "concurso": ultimo_resultado.get('proximoConcurso', 'N/A'),
                    "data": ultimo_resultado.get('dataProximoConcurso', 'S/D'),
                    "numeros": jogo,
                    "confianca": st.session_state.get('confianca_atual', 0)
                }
                if salvar_novo_palpite(novo, user_email):
                    st.toast("Palpite salvo com sucesso!", icon="✅")

        if ultimo_resultado:
            nums_str = " ".join([f"{n:02d}" for n in jogo])
            texto_wpp = f"🍀 Sugestão Lotomind\nConcurso: {ultimo_resultado.get('proximoConcurso', 'N/A')}\nNúmeros: {nums_str}"
            link_wpp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_wpp)}"
            col_b.link_button("📱 Compartilhar WhatsApp", link_wpp)

    # --- SEÇÃO 3: ÚLTIMO SORTEIO ---
    if ultimo_resultado:
        st.divider()
        st.subheader("Último Sorteio Realizado")
        with st.container(border=True):
            premiacao_15 = ultimo_resultado.get('premiacoes', [{}])[0]
            ganhadores = premiacao_15.get('ganhadores') # Pode ser None
            valor_premio = premiacao_15.get('valorPremio', 0)

            # Layout com 3 colunas para melhor visualização
            c1, c2, c3 = st.columns(3)

            c1.metric("Concurso", f"{ultimo_resultado.get('concurso', 'N/A')}")
            c1.caption(f"Data: {ultimo_resultado.get('data', 'N/A')}")
            
            c2.metric("Ganhadores (15 pts)", f"{ganhadores}" if ganhadores is not None else "N/A")
            c3.metric("Prêmio Total", f"R$ {valor_premio:,.2f}")
            
            st.write("**Dezenas Sorteadas:**")
            dezenas = ultimo_resultado.get('dezenas') or ultimo_resultado.get('listaDezenas')
            if dezenas:
                html_bolas_list = []
                for i, d in enumerate(dezenas):
                    html_bolas_list.append(f"<span style='display:inline-block; text-align:center; background-color:#4b0082; color:white; padding: 6px 0; width: 36px; height: 36px; line-height: 24px; border-radius:50%; margin:3px; font-weight:bold; font-size: 14px;'>{d}</span>")
                    if (i + 1) % 5 == 0 and (i + 1) < len(dezenas):
                        html_bolas_list.append("<br>")
                
                html_bolas = "".join(html_bolas_list)
                st.markdown(f"<div style='text-align: center;'>{html_bolas}</div>", unsafe_allow_html=True)

# --- TELA: MEUS PALPITES ---
elif menu == "Meus Palpites":
    st.title("Histórico de Palpites")
    palpites = carregar_palpites(user_email)

    if not palpites:
        st.info("Nenhum palpite salvo nesta conta.")
    else:
        # Botão de limpar tudo desativado na nuvem por segurança, ou implemente delete all
        if st.button("🔄 Atualizar Lista"):
            st.rerun()
        # --- CÁLCULO DAS ESTATÍSTICAS ---
        lista_acertos = []
        contagem_faixas = Counter()

        if dados:
            for p in palpites:
                for sorteio in dados:
                    if str(sorteio['concurso']) == str(p.get('concurso')):
                        sorteados = [int(x) for x in (sorteio.get('dezenas') or sorteio.get('listaDezenas'))]
                        acertos = len(set(p['numeros']) & set(sorteados))
                        lista_acertos.append(acertos)
                        contagem_faixas.update([acertos])
                        break
        
        # --- EXIBIÇÃO DAS ESTATÍSTICAS ---
        st.subheader("📊 Desempenho dos Palpites")
        with st.container(border=True):
            if not lista_acertos:
                st.warning("Nenhum palpite conferido ainda. Aguardando novos sorteios.")
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Palpites Salvos", f"{len(palpites)}")
                col2.metric("Média Acertos", f"{sum(lista_acertos) / len(lista_acertos):.2f}")
                col3.metric("Mín. Acertos", f"{min(lista_acertos)}")
                col4.metric("Máx. Acertos", f"{max(lista_acertos)}")

                st.divider()
                
                st.write("**Resumo de Pontuações (Jogos Conferidos):**")
                
                abaixo_9 = sum(contagem_faixas[i] for i in range(10))
                
                c1, c2 = st.columns(2)
                c1.markdown(f"""
                - **15 acertos:** `{contagem_faixas[15]}`
                - **14 acertos:** `{contagem_faixas[14]}`
                - **13 acertos:** `{contagem_faixas[13]}`
                - **12 acertos:** `{contagem_faixas[12]}`
                """)
                c2.markdown(f"""
                - **11 acertos:** `{contagem_faixas[11]}`
                - **10 acertos:** `{contagem_faixas[10]}`
                - **9 ou menos:** `{abaixo_9}`
                """)

        st.divider()

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

        # --- LISTA DE PALPITES INDIVIDUAIS ---
        st.subheader("Seus Jogos Salvos")
        # Se vier do banco, pode não ser uma lista simples, garantimos a iteração
        for i, p in enumerate(palpites):
            acertos = 0
            status = "Aguardando..."
            cor_status = "grey"
            confianca_salva = p.get('confianca', 'N/A')
            p_id = p.get('id') # ID do Supabase
            
            if dados:
                for sorteio in dados:
                    if str(sorteio['concurso']) == str(p.get('concurso')):
                        sorteados = [int(x) for x in (sorteio.get('dezenas') or sorteio.get('listaDezenas'))]
                        acertos = len(set(p['numeros']) & set(sorteados))
                        status = f"{acertos} Acertos"
                        cor_status = "green" if acertos >= 11 else "red"
                        break
            
            col_exp, col_del = st.columns([0.9, 0.1])

            with col_exp.expander(f"Concurso {p['concurso']} | {status} | Confiança: {confianca_salva}%"):
                st.write(f"**Seus Números:** {', '.join([f'{n:02d}' for n in p['numeros']])}")
                if status != "Aguardando...":
                    st.markdown(f"Resultado: :{cor_status}[{status}]")
            
            if col_del.button("🗑️", key=f"del_{i}", help="Excluir este palpite"):
                if excluir_palpite(p_id, user_email, index_local=i):
                    st.rerun()

# --- TELA: ESTATÍSTICAS ---
elif menu == "Estatísticas":
    st.title("Estatísticas (Últimos 60)")
    if not dados:
        st.warning("Sem dados carregados.")
    else:
        ult_60 = dados[:60]
        contagem = Counter()
        for s in ult_60:
            contagem.update([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Mais Sorteados")
            df_top = [{"Dezena": f"{n:02d}", "Vezes": c} for n, c in contagem.most_common(10)]
            st.dataframe(df_top, hide_index=True, use_container_width=True)
        with c2:
            st.subheader("❄️ Menos Sorteados")
            df_bot = [{"Dezena": f"{n:02d}", "Vezes": c} for n, c in contagem.most_common()[-6:]]
            st.dataframe(df_bot, hide_index=True, use_container_width=True)

        st.divider()

        # Cálculos de Atraso e Sequência
        atrasados = []
        sequencias = []

        for n in range(1, 26):
            # Atraso (Quantos sorteios faz que não sai)
            curr_atraso = 0
            for s in dados:
                nums = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]
                if n not in nums: curr_atraso += 1
                else: break
            if curr_atraso >= 3:
                atrasados.append({"Dezena": f"{n:02d}", "Atraso": f"{curr_atraso} jogos"})

            # Sequência (Quantos sorteios seguidos está saindo)
            curr_seq = 0
            for s in dados:
                nums = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]
                if n in nums: curr_seq += 1
                else: break
            if curr_seq >= 4:
                sequencias.append({"Dezena": f"{n:02d}", "Sequência": f"{curr_seq} seguidos"})

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("🐢 Mais Atrasados")
            st.dataframe(atrasados if atrasados else [{"Info": "Nenhum atraso >= 3"}], hide_index=True, use_container_width=True)
        
        with c4:
            st.subheader("⚡ Em Sequência")
            st.dataframe(sequencias if sequencias else [{"Info": "Nenhuma sequência >= 4"}], hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("📜 Histórico (Últimos 60)")
        df_hist = [{"Concurso": s['concurso'], "Data": s['data'], "Dezenas": str(sorted([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])).replace('[','').replace(']','')} for s in ult_60]
        st.dataframe(df_hist, hide_index=True, use_container_width=True)

# Rodapé
st.markdown("---")
st.caption("Developed by Rodrigo Carielo | Lotomind Web Version")

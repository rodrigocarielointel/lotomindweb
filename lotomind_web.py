import streamlit as st
import random
import requests
import json
import os
import urllib.parse
from collections import Counter

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

def carregar_palpites():
    if os.path.exists(ARQUIVO_PALPITES):
        try:
            with open(ARQUIVO_PALPITES, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_palpites(palpites):
    with open(ARQUIVO_PALPITES, "w") as f:
        json.dump(palpites, f, indent=4)

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
        return None, "Dados insuficientes para gerar palpite."

    ult_60 = historico[:60]
    ult_5 = historico[:5]
    ult_3 = historico[:3]
    
    dezenas_ultimo = [int(n) for n in (ultimo_resultado.get('dezenas') or ultimo_resultado.get('listaDezenas'))]

    # Frequência
    contagem = Counter()
    for s in ult_60:
        contagem.update([int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))])
    
    top_10 = [n for n, c in contagem.most_common(10)]
    bottom_6 = [n for n, c in contagem.most_common()[-6:]]

    # Flow (Números quentes para excluir)
    excluir_flow = []
    for n in range(1, 26):
        count_seq = 0
        for s in ult_5:
            res_sorteio = [int(x) for x in (s.get('dezenas') or s.get('listaDezenas'))]
            if n in res_sorteio: count_seq += 1
            else: break 
        if count_seq >= 4: excluir_flow.append(n)

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

        pares = len([n for n in jogo if n % 2 == 0])
        impares = 15 - pares
        if not ((impares == 8 and pares == 7) or (impares == 7 and pares == 8)): continue

        if not all(n in jogo for n in obrigatorios_atraso): continue

        # Regras Flexíveis
        t_ok = 5 <= len([n for n in jogo if n in top_10]) <= 7
        b_ok = 3 <= len([n for n in jogo if n in bottom_6]) <= 4
        f_ok = not any(n in jogo for n in excluir_flow)

        regras_extras = [t_ok, b_ok, f_ok]
        acertos_regras = regras_extras.count(True)

        if acertos_regras == 3 or tentativas > 4500:
            confianca = 100 if acertos_regras == 3 else int(70 + (acertos_regras * 10))
            motivos = []
            if not t_ok: motivos.append("Top10 fora")
            if not b_ok: motivos.append("Bottom6 fora")
            if not f_ok: motivos.append("Contém Flow")
            
            msg = "Todas as métricas atendidas!" if not motivos else f"Ajuste: {', '.join(motivos)}"
            return jogo, f"Confiança: {confianca}% | {msg}"

    return jogo, "Gerado por exaustão (Confiança Baixa)"

# --- INTERFACE DO APP WEB ---

# Inicialização de Estado (Memória do App)
if 'dados' not in st.session_state:
    st.session_state['dados'] = carregar_dados()
if 'palpite_atual' not in st.session_state:
    st.session_state['palpite_atual'] = None
if 'msg_palpite' not in st.session_state:
    st.session_state['msg_palpite'] = ""

# Sidebar (Menu Lateral)
with st.sidebar:
    # Tenta achar o logo na pasta atual ou na anterior
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    elif os.path.exists("../logo.png"):
        st.image("../logo.png", width=150)
    else:
        st.title("Lotomind")
    
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
    st.title("Lotofácil Master 🍀")
    
    if ultimo_resultado:
        # Card de Informações do Último Sorteio
        with st.container(border=True):
            c1, c2 = st.columns(2)
            c1.metric("Último Concurso", f"{ultimo_resultado['concurso']}")
            c1.caption(f"Data: {ultimo_resultado['data']}")
            
            valor = ultimo_resultado.get('valorEstimadoProximoConcurso', 0)
            c2.metric("Prêmio Estimado", f"R$ {valor:,.2f}")
            c2.caption(f"Próx: {ultimo_resultado['proximoConcurso']}")
            
            dezenas = ultimo_resultado.get('dezenas') or ultimo_resultado.get('listaDezenas')
            st.write("**Dezenas Sorteadas:**")
            # Exibe bolinhas coloridas com quebra de linha a cada 5
            html_bolas_list = []
            for i, d in enumerate(dezenas):
                html_bolas_list.append(f"<span style='display:inline-block; text-align:center; background-color:#4b0082; color:white; padding: 6px 0; width: 36px; height: 36px; line-height: 24px; border-radius:50%; margin:3px; font-weight:bold; font-size: 14px;'>{d}</span>")
                if (i + 1) % 5 == 0 and (i + 1) < len(dezenas):
                    html_bolas_list.append("<br>")
            
            html_bolas = "".join(html_bolas_list)
            st.markdown(f"<div style='text-align: center;'>{html_bolas}</div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("Gerador de Jogos")

    if st.button("🎲 GERAR NOVO PALPITE", type="primary", use_container_width=True):
        jogo, msg = gerar_palpite_logica(dados, ultimo_resultado)
        st.session_state['palpite_atual'] = jogo
        st.session_state['msg_palpite'] = msg

    if st.session_state['palpite_atual']:
        jogo = st.session_state['palpite_atual']
        
        # Exibe o jogo gerado grande
        st.markdown(f"<h2 style='text-align: center; color: #4b0082;'>{' '.join([f'{n:02d}' for n in jogo])}</h2>", unsafe_allow_html=True)
        st.info(st.session_state['msg_palpite'])

        col_a, col_b = st.columns(2)
        if col_a.button("💾 Salvar Palpite"):
            palpites = carregar_palpites()
            novo = {
                "concurso": ultimo_resultado['proximoConcurso'],
                "data": ultimo_resultado['dataProximoSorteio'],
                "numeros": jogo
            }
            palpites.append(novo)
            salvar_palpites(palpites)
            st.toast("Palpite salvo com sucesso!", icon="✅")

        # Botão WhatsApp
        nums_str = " ".join([f"{n:02d}" for n in jogo])
        texto_wpp = f"🍀 Sugestão Lotomind\nConcurso: {ultimo_resultado['proximoConcurso']}\nNúmeros: {nums_str}"
        link_wpp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_wpp)}"
        col_b.link_button("📱 Compartilhar WhatsApp", link_wpp)

# --- TELA: MEUS PALPITES ---
elif menu == "Meus Palpites":
    st.title("Histórico de Palpites")
    palpites = carregar_palpites()

    if not palpites:
        st.info("Você ainda não salvou nenhum palpite.")
    else:
        if st.button("Limpar Histórico", type="secondary"):
            salvar_palpites([])
            st.rerun()
        
        for p in reversed(palpites):
            acertos = 0
            status = "Aguardando..."
            cor_status = "grey"
            
            if dados:
                for sorteio in dados:
                    if str(sorteio['concurso']) == str(p['concurso']):
                        sorteados = [int(x) for x in (sorteio.get('dezenas') or sorteio.get('listaDezenas'))]
                        acertos = len(set(p['numeros']) & set(sorteados))
                        status = f"{acertos} Acertos"
                        cor_status = "green" if acertos >= 11 else "red"
                        break
            
            with st.expander(f"Concurso {p['concurso']} | {status}"):
                st.write(f"**Seus Números:** {', '.join([f'{n:02d}' for n in p['numeros']])}")
                if status != "Aguardando...":
                    st.markdown(f"Resultado: :{cor_status}[{status}]")

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

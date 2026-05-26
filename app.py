import streamlit as st
import pandas as pd

st.set_page_config(page_title="Caderno de Questões", layout="centered")

# --- 1. INICIALIZAÇÃO DE ESTADOS (MEMÓRIA) ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'acertos' not in st.session_state: st.session_state.acertos = 0
if 'erros' not in st.session_state: st.session_state.erros = 0
if 'regras_simulado' not in st.session_state: st.session_state.regras_simulado = []
if 'df_ativo' not in st.session_state: st.session_state.df_ativo = pd.DataFrame()
if 'respostas_dadas' not in st.session_state: st.session_state.respostas_dadas = {}

# --- 2. CARREGAMENTO BLINDADO CONTRA ERROS ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("questoes.csv", sep=";", encoding='utf-8')
    except:
        try:
            df = pd.read_csv("questoes.csv", sep=";", encoding='latin1')
        except:
            return pd.DataFrame() # Retorna vazio se der erro fatal
    
    # Isso impede o 'KeyError' garantindo que as colunas existam mesmo se o CSV falhar
    colunas_esperadas = ['ID', 'Disciplina', 'Assunto', 'Assertiva', 'Gabarito', 'Comentario']
    for col in colunas_esperadas:
        if col not in df.columns:
            df[col] = "Sem informação"
    return df

df_base = carregar_dados()
if df_base.empty:
    st.error("Arquivo questoes.csv não encontrado ou vazio. Verifique a pasta.")
    st.stop()

# --- 3. LÓGICA DE AÇÕES ---
def adicionar_regra(disciplina, assunto, qtd):
    st.session_state.regras_simulado.append({'Disciplina': disciplina, 'Assunto': assunto, 'Qtd': qtd})

def limpar_regras():
    st.session_state.regras_simulado = []
    st.session_state.df_ativo = pd.DataFrame()
    resetar_progresso()

def resetar_progresso():
    st.session_state.indice = 0
    st.session_state.acertos = 0
    st.session_state.erros = 0
    st.session_state.respostas_dadas = {}

def gerar_prova():
    if not st.session_state.regras_simulado: return
    frames = []
    for r in st.session_state.regras_simulado:
        filtro = df_base[(df_base['Disciplina'] == r['Disciplina']) & (df_base['Assunto'] == r['Assunto'])]
        qtd_real = min(r['Qtd'], len(filtro))
        if qtd_real > 0:
            frames.append(filtro.sample(n=qtd_real))
    
    if frames:
        st.session_state.df_ativo = pd.concat(frames).sample(frac=1).reset_index(drop=True)
        resetar_progresso()

def responder(escolha, gabarito):
    idx = st.session_state.indice
    st.session_state.respostas_dadas[idx] = escolha
    if escolha == gabarito:
        st.session_state.acertos += 1
    else:
        st.session_state.erros += 1

def mudar_questao(delta):
    st.session_state.indice += delta

# --- 4. BARRA LATERAL (FILTROS E DESEMPENHO) ---
st.sidebar.header("Montar Simulado")
disc_selecionada = st.sidebar.selectbox("1. Disciplina", df_base['Disciplina'].unique())
assuntos_disp = df_base[df_base['Disciplina'] == disc_selecionada]['Assunto'].unique()
assunto_selecionado = st.sidebar.selectbox("2. Assunto", assuntos_disp)

qtd_max = len(df_base[(df_base['Disciplina'] == disc_selecionada) & (df_base['Assunto'] == assunto_selecionado)])
qtd_desejada = st.sidebar.number_input(f"3. Qtd (Máx: {qtd_max})", min_value=1, max_value=qtd_max if qtd_max>0 else 1)

if st.sidebar.button("➕ Incluir", disabled=(qtd_max == 0)):
    adicionar_regra(disc_selecionada, assunto_selecionado, qtd_desejada)

if st.session_state.regras_simulado:
    st.sidebar.divider()
    st.sidebar.markdown("**Prova atual:**")
    for r in st.session_state.regras_simulado:
        st.sidebar.caption(f"• {r['Assunto']} ({r['Qtd']}q)")
    
    c1, c2 = st.sidebar.columns(2)
    c1.button("Gerar Prova", type="primary", on_click=gerar_prova, use_container_width=True)
    c2.button("Limpar", on_click=limpar_regras, use_container_width=True)

st.sidebar.divider()
st.sidebar.header("Desempenho")
c_acerto, c_erro = st.sidebar.columns(2)
c_acerto.metric("Acertos ✅", st.session_state.acertos)
c_erro.metric("Erros ❌", st.session_state.erros)

# --- 5. ÁREA PRINCIPAL DA PROVA ---
df_prova = st.session_state.df_ativo

if df_prova.empty:
    st.info("👈 Monte seu simulado no menu lateral e clique em 'Gerar Prova'.")
    st.stop()

# Barra de Navegação (Anterior / Próxima)
col_nav_esq, col_nav_meio, col_nav_dir = st.columns([1, 2, 1])
with col_nav_esq:
    st.button("⬅ Anterior", on_click=mudar_questao, args=(-1,), disabled=(st.session_state.indice == 0), use_container_width=True)
with col_nav_meio:
    st.markdown(f"<h4 style='text-align: center;'>Questão {st.session_state.indice + 1} de {len(df_prova)}</h4>", unsafe_allow_html=True)
with col_nav_dir:
    st.button("Próxima ➡", on_click=mudar_questao, args=(1,), disabled=(st.session_state.indice == len(df_prova) - 1), use_container_width=True)

st.divider()

# Dados da Questão
idx_atual = st.session_state.indice
questao = df_prova.iloc[idx_atual]
gabarito_real = str(questao['Gabarito']).strip().upper()
ja_respondida = idx_atual in st.session_state.respostas_dadas

# Enunciado
st.caption(f"{questao['Disciplina']} ➔ {questao['Assunto']} | ID Original: {questao['ID']}")
st.write(f"**{questao['Assertiva']}**")

# Botões de Julgamento
col1, col2 = st.columns(2)
with col1:
    st.button("CERTO", key=f"c_{idx_atual}", on_click=responder, args=("C", gabarito_real), disabled=ja_respondida, use_container_width=True)
with col2:
    st.button("ERRADO", key=f"e_{idx_atual}", on_click=responder, args=("E", gabarito_real), disabled=ja_respondida, use_container_width=True)

# Feedback Visual (Aparece apenas após responder)
if ja_respondida:
    escolha_feita = st.session_state.respostas_dadas[idx_atual]
    st.divider()
    
    if escolha_feita == gabarito_real:
        st.success("✅ Resposta Correta!")
    else:
        st.error(f"❌ Resposta Incorreta. Você marcou '{escolha_feita}' e o gabarito é '{gabarito_real}'.")
    
    st.info(f"**Comentário:** {questao['Comentario']}")
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Caderno de Questões", layout="centered")

# ==========================================
# ⚙️ MOTOR DE PROPORÇÕES (SEU EDITAL AQUI)
# ==========================================
PROPORCOES_INSS = {
    "Direito Previdenciário": {
        "Beneficiários": 15,
        "Regime de Previdência Complementar": 5,
        "Benefícios em Espécie": 25,
        "Custeio": 15,
        "Salário de Benefício": 10
    },
    "Língua Portuguesa": {
        "Interpretação de Textos (Compreensão)": 8,
        "Crase": 2,
        "Sintaxe": 5
    },
    "Direito Administrativo": {
        "Licitações": 3,
        "Atos Administrativos": 2,
        "Organização Administrativa": 2,
        "Processo Administrativo (Lei n° 9.784/1999)": 2
    },
    "Direito Constitucional": {
        "Direitos e Garantias Fundamentais": 4
    }
}

# --- 1. INICIALIZAÇÃO DE ESTADOS ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'acertos' not in st.session_state: st.session_state.acertos = 0
if 'erros' not in st.session_state: st.session_state.erros = 0
if 'regras_simulado' not in st.session_state: st.session_state.regras_simulado = []
if 'df_ativo' not in st.session_state: st.session_state.df_ativo = pd.DataFrame()
if 'respostas_dadas' not in st.session_state: st.session_state.respostas_dadas = {}

# --- 2. CARREGAMENTO BLINDADO ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("questoes.csv", sep=";", encoding='utf-8')
    except:
        try:
            df = pd.read_csv("questoes.csv", sep=";", encoding='latin1')
        except:
            return pd.DataFrame()
    
    colunas_esperadas = ['ID', 'Disciplina', 'Assunto', 'Assertiva', 'Gabarito', 'Comentario']
    for col in colunas_esperadas:
        if col not in df.columns: df[col] = "Sem informação"
        
    # CRIA COLUNAS "FANTASMAS" PARA BUSCA À PROVA DE ERROS (Tudo minúsculo, sem espaços extras)
    df['Disc_pad'] = df['Disciplina'].astype(str).str.strip().str.lower()
    df['Ass_pad'] = df['Assunto'].astype(str).str.strip().str.lower()
    
    return df

df_base = carregar_dados()
if df_base.empty:
    st.error("Arquivo questoes.csv não encontrado ou vazio.")
    st.stop()

# --- 3. LÓGICA DE GERAÇÃO INTELIGENTE ---
def resetar_progresso():
    st.session_state.indice = 0
    st.session_state.acertos = 0
    st.session_state.erros = 0
    st.session_state.respostas_dadas = {}

def gerar_bateria(prova, modo, disc, ass, qtd_desejada):
    frames = []
    
    # ROTA 1: SIMULADO INSS
    if prova == "INSS" and modo == "Simulado":
        for d, assuntos_dict in PROPORCOES_INSS.items():
            d_pad = str(d).strip().lower()
            for a, peso in assuntos_dict.items():
                a_pad = str(a).strip().lower()
                filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                qtd_real = min(peso, len(filtro))
                if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
                
    # ROTA 2: QUESTÕES INSS PROPORCIONAIS
    elif prova == "INSS" and modo == "Questões":
        if disc == "Todas":
            total_peso_edital = sum(sum(a.values()) for a in PROPORCOES_INSS.values())
            fator = qtd_desejada / total_peso_edital if total_peso_edital > 0 else 0
            
            for d, assuntos_dict in PROPORCOES_INSS.items():
                d_pad = str(d).strip().lower()
                for a, peso in assuntos_dict.items():
                    a_pad = str(a).strip().lower()
                    qtd_calc = round(peso * fator)
                    filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                    qtd_real = min(qtd_calc, len(filtro))
                    if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
                    
        elif ass == "Todos":
            d_pad = str(disc).strip().lower()
            if disc in PROPORCOES_INSS:
                total_peso_disc = sum(PROPORCOES_INSS[disc].values())
                fator = qtd_desejada / total_peso_disc if total_peso_disc > 0 else 0
                for a, peso in PROPORCOES_INSS[disc].items():
                    a_pad = str(a).strip().lower()
                    qtd_calc = round(peso * fator)
                    filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                    qtd_real = min(qtd_calc, len(filtro))
                    if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
            else:
                filtro = df_base[df_base['Disc_pad'] == d_pad]
                qtd_real = min(qtd_desejada, len(filtro))
                if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
        else:
            d_pad = str(disc).strip().lower()
            a_pad = str(ass).strip().lower()
            filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
            qtd_real = min(qtd_desejada, len(filtro))
            if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))

    # ROTA 3: MODO LIVRE
    else: 
        if not st.session_state.regras_simulado: return
        for r in st.session_state.regras_simulado:
            d_pad = str(r['Disciplina']).strip().lower()
            a_pad = str(r['Assunto']).strip().lower()
            filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
            qtd_real = min(r['Qtd'], len(filtro))
            if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))

    # Junta, embaralha e inicia
    if frames:
        prova_final = pd.concat(frames).sample(frac=1).reset_index(drop=True)
        st.session_state.df_ativo = prova_final
        resetar_progresso()
        
        # Alerta de Limite do Banco de Dados
        if len(prova_final) < qtd_desejada and modo == "Questões" and prova == "INSS":
            st.sidebar.warning(f"⚠️ Você pediu {qtd_desejada} questões, mas o sistema só encontrou {len(prova_final)} que correspondem aos assuntos do Edital do INSS no seu banco de dados.")
    else:
        st.sidebar.error("Nenhuma questão encontrada para este filtro com base no edital do INSS cadastrado.")

def responder(escolha, gabarito):
    idx = st.session_state.indice
    st.session_state.respostas_dadas[idx] = escolha
    if escolha == gabarito:
        st.session_state.acertos += 1
    else:
        st.session_state.erros += 1

def mudar_questao(delta):
    st.session_state.indice += delta

def limpar_dados():
    st.session_state.regras_simulado = []
    st.session_state.df_ativo = pd.DataFrame()
    resetar_progresso()

# --- 4. BARRA LATERAL (FILTROS) ---
st.sidebar.header("Configurar Bateria")

prova_sel = st.sidebar.selectbox("1. Prova", ["", "INSS"])
modo_sel = st.sidebar.selectbox("2. Modo", ["Questões", "Simulado"])

travar_filtros = (prova_sel == "INSS" and modo_sel == "Simulado")

disc_disp = ["Todas"] + list(df_base['Disciplina'].unique())
disc_sel = st.sidebar.selectbox("3. Disciplina", disc_disp, disabled=travar_filtros)

if disc_sel == "Todas":
    ass_disp = ["Todos"]
else:
    ass_disp = ["Todos"] + list(df_base[df_base['Disciplina'] == disc_sel]['Assunto'].unique())
    
ass_sel = st.sidebar.selectbox("4. Assunto", ass_disp, disabled=travar_filtros)

qtd_sel = st.sidebar.number_input("5. Qtd", min_value=1, value=150, disabled=travar_filtros)

if prova_sel == "INSS":
    if st.sidebar.button(f"🚀 Gerar {modo_sel} INSS", type="primary", use_container_width=True):
        gerar_bateria(prova_sel, modo_sel, disc_sel, ass_sel, qtd_sel)
else:
    st.sidebar.caption("Modo Manual: Inclua os assuntos para montar a prova com assuntos fora da proporção.")
    if st.sidebar.button("➕ Incluir no Carrinho"):
        st.session_state.regras_simulado.append({'Disciplina': disc_sel, 'Assunto': ass_sel, 'Qtd': qtd_sel})
    
    if st.session_state.regras_simulado:
        for r in st.session_state.regras_simulado:
            st.sidebar.text(f"• {r['Assunto']} ({r['Qtd']}q)")
        if st.sidebar.button("Gerar Prova Manual", type="primary", use_container_width=True):
            gerar_bateria(prova_sel, modo_sel, None, None, None)

if st.sidebar.button("Limpar Tela", use_container_width=True):
    limpar_dados()

st.sidebar.divider()
st.sidebar.header("Desempenho")
c_acerto, c_erro = st.sidebar.columns(2)
c_acerto.metric("Acertos ✅", st.session_state.acertos)
c_erro.metric("Erros ❌", st.session_state.erros)

# --- 5. ÁREA PRINCIPAL DA PROVA ---
df_prova = st.session_state.df_ativo

if df_prova.empty:
    st.info("👈 Ajuste os filtros na barra lateral e gere sua bateria de questões. Se quiser resolver suas 150 questões aleatoriamente sem a rigidez da proporção do edital, deixe o filtro 'Prova' em branco e use o Modo Manual.")
    st.stop()

col_nav_esq, col_nav_meio, col_nav_dir = st.columns([1, 2, 1])
with col_nav_esq:
    st.button("⬅ Anterior", on_click=mudar_questao, args=(-1,), disabled=(st.session_state.indice == 0), use_container_width=True)
with col_nav_meio:
    st.markdown(f"<h4 style='text-align: center;'>Questão {st.session_state.indice + 1} de {len(df_prova)}</h4>", unsafe_allow_html=True)
with col_nav_dir:
    st.button("Próxima ➡", on_click=mudar_questao, args=(1,), disabled=(st.session_state.indice == len(df_prova) - 1), use_container_width=True)

st.divider()

idx_atual = st.session_state.indice
questao = df_prova.iloc[idx_atual]
gabarito_real = str(questao['Gabarito']).strip().upper()
ja_respondida = idx_atual in st.session_state.respostas_dadas

st.caption(f"{questao['Disciplina']} ➔ {questao['Assunto']} | ID Original: {questao['ID']}")
st.write(f"**{questao['Assertiva']}**")

col1, col2 = st.columns(2)
with col1:
    st.button("CERTO", key=f"c_{idx_atual}", on_click=responder, args=("C", gabarito_real), disabled=ja_respondida, use_container_width=True)
with col2:
    st.button("ERRADO", key=f"e_{idx_atual}", on_click=responder, args=("E", gabarito_real), disabled=ja_respondida, use_container_width=True)

if ja_respondida:
    escolha_feita = st.session_state.respostas_dadas[idx_atual]
    st.divider()
    if escolha_feita == gabarito_real:
        st.success("✅ Resposta Correta!")
    else:
        st.error(f"❌ Resposta Incorreta. O gabarito é '{gabarito_real}'.")
    st.info(f"**Comentário:** {questao['Comentario']}")

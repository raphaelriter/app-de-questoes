import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Caderno de Questões", layout="centered")

# ==========================================
# ⚙️ MOTOR DE PROPORÇÕES (PESOS RELATIVOS)
# ==========================================
# O sistema calcula a distribuição sozinho com base nesses números. 
# Não se preocupe em "fechar a conta", ele usa regras de proporção (Regra de 3) 
# baseada na quantidade total de questões que você pedir no filtro.
PROPORCOES_INSS = {
    "Direito Previdenciário": {
        "Princípios e Objetivos da Seguridade Social": 4.55,
        "Financiamento da Seguridade Social": 4.55,
        "Saúde, Previdência Social e Assistência Social": 6.82,
        "Origem e Evolução Legislativa da Seguridade Social": 0.76,
        "Legislação Previdenciária (Fontes, Aplicação, Hierarquia etc.)": 3.79,
        "Empregado (RGPS)": 1.52,
        "Empregado Doméstico (RGPS)": 0.76,
        "Contribuinte Individual (RGPS)": 0.76,
        "Segurado Especial (RGPS)": 1.52,
        "Segurado Facultativo (RGPS)": 1.52,
        "Da Manutenção e da Perda da Qualidade de Segurado": 3.03,
        "Tópicos Mesclados sobre Segurados (RGPS)": 1.52,
        "Dos Dependentes (RGPS)": 1.52,
        "Conceito de Empresa e Empregador Doméstico": 3.03,
        "Carência": 0.76,
        "Do Cálculo do Valor do Benefício": 2.27,
        "Das Aposentadorias por Tempo de Contribuição e por Idade do Segurado com Deficiência": 3.79,
        "Do Salário-Maternidade": 0.76,
        "Da Pensão por Morte": 1.52,
        "Seguro Desemprego, FAT e Abono Salarial": 3.79,
        "Do Reconhecimento da Filiação": 3.79,
        "Da Contagem Recíproca de Tempo de Serviço": 5.30,
        "Da Habilitação e Reabilitação de Profissionais e do Serviço Social": 2.27,
        "Das Disposições Diversas e Transitórias Relativas às Prestações (Prescrição, Decadência e Outros)": 6.06,
        "Do Salário-de-Contribuição": 6.06,
        "Da Arrecadação e Recolhimento das Contribuições (Prescrição, Decadência e Outros)": 3.03,
        "Receitas das Contribuições Sociais": 2.27,
        "Receitas de Outras Fontes": 0.76,
        "Recursos das Decisões Administrativas": 3.03,
        "Regime Próprio de Previdência Social na Constituição Federal": 0.76,
        "Dos Princípios e das Diretrizes (arts. 4º e 5º da Lei nº 8.742/93)": 0.76,
        "Da Organização e da Gestão (arts. 6º a 19 da Lei nº 8.742/93)": 0.76,
        "Dos Benefícios (arts. 20 a 22 da Lei nº 8.742/93)": 3.79,
        "Dos Serviços, Programas de Assistência Social e Enfrentamento da Pobreza (arts. 23 a 26-H da Lei nº 8.742/93)": 1.52,
        "Decreto nº 6.214/2007 - Regulamento do Benefício de Prestação Continuada (BPC)": 0.76,
        "Lei nº 7.070/1982 - Pensão Especial para Portadores da Síndrome de Talidomida": 1.52,
        "Lei nº 7.986/1989 - Pensão Especial aos Seringueiros": 1.52,
        "Lei nº 8.059/1990 - Pensão Especial devida aos Ex-Combatentes da Segunda Guerra Mundial": 1.52,
        "Lei nº 9.422/1996 - Pensão Especial às Vítimas de Hemodiálise de Caruaru": 0.76,
        "Lei nº 9.425/1996 - Pensão Especial às Vítimas do Acidente Nuclear Ocorrido em Goiânia (CÉSIO 137)": 0.76,
        "Lei nº 10.559/2002 - Aposentadoria e Pensão Excepcional ao Anistiado Político": 1.52,
        "Lei nº 10.779/2003 - Seguro Desemprego ao Pescador Artesanal (Seguro Defeso)": 0.76,
        "Lei nº 11.520/2007 - Pensão Especial às Pessoas Atingidas pela Hanseníase": 0.76,
        "Lei nº 13.985/2020 - Pensão Especial Destinada a Crianças com Síndrome Congênita do Zika Vírus": 1.52
    },
    "Língua Portuguesa": {
        "Interpretação de Textos": 8.0,
        "Crase": 2.0,
        "Sintaxe": 5.0
    },
    "Direito Administrativo": {
        "Licitações": 3.0,
        "Atos Administrativos": 2.0,
        "Organização Administrativa": 2.0,
        "Processo Administrativo (Lei n° 9.784/1999)": 2.0
    },
    "Direito Constitucional": {
        "Direitos e Garantias Fundamentais": 4.0
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
        
    df['Disc_pad'] = df['Disciplina'].astype(str).str.strip().str.lower()
    df['Ass_pad'] = df['Assunto'].astype(str).str.strip().str.lower()
    return df

df_base = carregar_dados()
if df_base.empty:
    st.error("Arquivo questoes.csv não encontrado ou vazio.")
    st.stop()

# --- 3. LÓGICA DE GERAÇÃO INTELIGENTE (MATEMÁTICA ADAPTATIVA) ---
def resetar_progresso():
    st.session_state.indice = 0
    st.session_state.acertos = 0
    st.session_state.erros = 0
    st.session_state.respostas_dadas = {}

def gerar_bateria(prova, modo, disc, ass, qtd_desejada):
    frames = []
    peso_total_edital = sum(sum(a.values()) for a in PROPORCOES_INSS.values())
    
    # ROTA 1: SIMULADO INSS (Calcula cota global de cada disciplina e distribui pelos assuntos)
    if prova == "INSS" and modo == "Simulado":
        for d, assuntos_dict in PROPORCOES_INSS.items():
            d_pad = str(d).strip().lower()
            peso_disciplina = sum(assuntos_dict.values())
            qtd_disciplina = (peso_disciplina / peso_total_edital) * qtd_desejada if peso_total_edital > 0 else 0
            
            for a, peso in assuntos_dict.items():
                a_pad = str(a).strip().lower()
                qtd_calc = round((peso / peso_disciplina) * qtd_disciplina) if peso_disciplina > 0 else 0
                
                filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                qtd_real = min(qtd_calc, len(filtro))
                if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
                
    # ROTA 2: QUESTÕES INSS PROPORCIONAIS
    elif prova == "INSS" and modo == "Questões":
        if disc == "Todas":
            for d, assuntos_dict in PROPORCOES_INSS.items():
                d_pad = str(d).strip().lower()
                peso_disciplina = sum(assuntos_dict.values())
                qtd_disciplina = (peso_disciplina / peso_total_edital) * qtd_desejada if peso_total_edital > 0 else 0
                
                for a, peso in assuntos_dict.items():
                    a_pad = str(a).strip().lower()
                    qtd_calc = round((peso / peso_disciplina) * qtd_disciplina) if peso_disciplina > 0 else 0
                    
                    filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                    qtd_real = min(qtd_calc, len(filtro))
                    if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
                    
        elif ass == "Todos":
            d_pad = str(disc).strip().lower()
            if disc in PROPORCOES_INSS:
                peso_disciplina = sum(PROPORCOES_INSS[disc].values())
                for a, peso in PROPORCOES_INSS[disc].items():
                    a_pad = str(a).strip().lower()
                    qtd_calc = round((peso / peso_disciplina) * qtd_desejada) if peso_disciplina > 0 else 0
                    
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

    # ROTA 3: MODO LIVRE (CORINGAS)
    else: 
        if not st.session_state.regras_simulado: return
        for r in st.session_state.regras_simulado:
            d_pad = str(r['Disciplina']).strip().lower()
            a_pad = str(r['Assunto']).strip().lower()
            
            if d_pad == "todas":
                filtro = df_base.copy()
            elif a_pad == "todos":
                filtro = df_base[df_base['Disc_pad'] == d_pad]
            else:
                filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                
            qtd_real = min(r['Qtd'], len(filtro))
            if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))

    # Junta, embaralha e inicia
    if frames:
        prova_final = pd.concat(frames).sample(frac=1).reset_index(drop=True)
        st.session_state.df_ativo = prova_final
        resetar_progresso()
        
        if len(prova_final) < qtd_desejada and modo == "Questões" and prova == "INSS":
            st.sidebar.warning(f"⚠️ Solicitadas {qtd_desejada} questões, mas só encontrei {len(prova_final)} em banco mapeadas no Edital INSS.")
    else:
        st.sidebar.error("Nenhuma questão encontrada no banco para estes critérios.")

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

# Agora bloqueia APENAS a seleção de matéria/assunto no simulado. 
# A quantidade de questões fica livre para você definir o tamanho do simulado.
travar_disc_ass = (prova_sel == "INSS" and modo_sel == "Simulado")

disc_disp = ["Todas"] + list(df_base['Disciplina'].unique())
disc_sel = st.sidebar.selectbox("3. Disciplina", disc_disp, disabled=travar_disc_ass)

if disc_sel == "Todas":
    ass_disp = ["Todos"]
else:
    ass_disp = ["Todos"] + list(df_base[df_base['Disciplina'] == disc_sel]['Assunto'].unique())
    
ass_sel = st.sidebar.selectbox("4. Assunto", ass_disp, disabled=travar_disc_ass)

qtd_sel = st.sidebar.number_input("5. Qtd", min_value=1, value=120)

if prova_sel == "INSS":
    if st.sidebar.button(f"🚀 Gerar {modo_sel} INSS", type="primary", use_container_width=True):
        gerar_bateria(prova_sel, modo_sel, disc_sel, ass_sel, qtd_sel)
else:
    st.sidebar.caption("Modo Manual: Construa a prova bloco a bloco.")
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
    st.info("👈 Ajuste os filtros na barra lateral. Se não quiser as proporções do edital INSS, deixe 'Prova' em branco e use o Modo Manual.")
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

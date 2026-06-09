import streamlit as st
import pandas as pd
import unicodedata
import re
import math
import csv

st.set_page_config(page_title="Caderno de Questões", layout="centered")

# ==========================================
# ⚙️ FUNÇÕES DE ESTERILIZAÇÃO E MATEMÁTICA
# ==========================================
def padronizar(texto):
    if pd.isna(texto): return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z0-9]', '', texto)
    return texto

def distribuir_vagas_exatas(dicionario_pesos, vagas_totais):
    """
    Algoritmo de Maior Resto (Hamilton): Garante que a soma das vagas 
    seja estritamente igual à quantidade solicitada, sem inflação de arredondamento.
    """
    soma_pesos = sum(dicionario_pesos.values())
    if soma_pesos == 0 or vagas_totais <= 0:
        return {k: 0 for k in dicionario_pesos}
    
    # 1. Calcula a cota exata (com decimais) para cada item
    cotas_exatas = {k: (v / soma_pesos) * vagas_totais for k, v in dicionario_pesos.items()}
    
    # 2. Garante a parte inteira (piso) para cada um
    alocacao = {k: math.floor(v) for k, v in cotas_exatas.items()}
    
    # 3. Calcula quantas vagas sobraram devido ao corte dos decimais
    vagas_restantes = int(vagas_totais - sum(alocacao.values()))
    
    # 4. Ordena os itens pelos maiores restos decimais e distribui as sobras
    restos = {k: cotas_exatas[k] - alocacao[k] for k in cotas_exatas}
    ordenados_por_resto = sorted(restos.keys(), key=lambda x: restos[x], reverse=True)
    
    for i in range(vagas_restantes):
        if i < len(ordenados_por_resto):
            alocacao[ordenados_por_resto[i]] += 1
            
    return alocacao

# ==========================================
# ⚙️ MOTOR DE PROPORÇÕES (APENAS PREVIDENCIÁRIO)
# ==========================================
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
    }
}

# --- 1. INICIALIZAÇÃO DE ESTADOS ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'acertos' not in st.session_state: st.session_state.acertos = 0
if 'erros' not in st.session_state: st.session_state.erros = 0
if 'regras_simulado' not in st.session_state: st.session_state.regras_simulado = []
if 'df_ativo' not in st.session_state: st.session_state.df_ativo = pd.DataFrame()
if 'respostas_dadas' not in st.session_state: st.session_state.respostas_dadas = {}

# --- 2. CARREGAMENTO BLINDADO CONTRA ERROS DE TEXTO E ASPAS ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("questoes.csv", sep=";", encoding='utf-8', on_bad_lines='skip', quoting=csv.QUOTE_NONE)
    except:
        try:
            df = pd.read_csv("questoes.csv", sep=";", encoding='latin1', on_bad_lines='skip', quoting=csv.QUOTE_NONE)
        except:
            return pd.DataFrame()
    
    colunas_esperadas = ['ID', 'Disciplina', 'Assunto', 'Assertiva', 'Gabarito', 'Comentario']
    for col in colunas_esperadas:
        if col not in df.columns: df[col] = "Sem informação"
        
    df['Disc_pad'] = df['Disciplina'].apply(padronizar)
    df['Ass_pad'] = df['Assunto'].apply(padronizar)
    return df

df_base = carregar_dados()
if df_base.empty:
    st.error("Arquivo questoes.csv não encontrado, vazio ou com erro crítico de estrutura.")
    st.stop()

# --- 3. LÓGICA DE GERAÇÃO INTELIGENTE (COTA EXATA) ---
def resetar_progresso():
    st.session_state.indice = 0
    st.session_state.acertos = 0
    st.session_state.erros = 0
    st.session_state.respostas_dadas = {}

def gerar_bateria(prova, modo, disc, ass, qtd_desejada):
    frames = []
    
    # ROTA 1: SIMULADO INSS
    if prova == "INSS" and modo == "Simulado":
        pesos_disciplinas = {d: sum(assuntos.values()) for d, assuntos in PROPORCOES_INSS.items()}
        vagas_disciplinas = distribuir_vagas_exatas(pesos_disciplinas, qtd_desejada)
        
        for d, assuntos_dict in PROPORCOES_INSS.items():
            d_pad = padronizar(d)
            vagas_d = vagas_disciplinas[d]
            vagas_assuntos = distribuir_vagas_exatas(assuntos_dict, vagas_d)
            
            for a, qtd_calc in vagas_assuntos.items():
                if qtd_calc > 0:
                    a_pad = padronizar(a)
                    filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                    qtd_real = min(qtd_calc, len(filtro))
                    if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
                
    # ROTA 2: QUESTÕES INSS PROPORCIONAIS
    elif prova == "INSS" and modo == "Questões":
        if disc == "Todas":
            pesos_disciplinas = {d: sum(assuntos.values()) for d, assuntos in PROPORCOES_INSS.items()}
            vagas_disciplinas = distribuir_vagas_exatas(pesos_disciplinas, qtd_desejada)
            
            for d, assuntos_dict in PROPORCOES_INSS.items():
                d_pad = padronizar(d)
                vagas_d = vagas_disciplinas[d]
                vagas_assuntos = distribuir_vagas_exatas(assuntos_dict, vagas_d)
                
                for a, qtd_calc in vagas_assuntos.items():
                    if qtd_calc > 0:
                        a_pad = padronizar(a)
                        filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                        qtd_real = min(qtd_calc, len(filtro))
                        if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
                        
        elif ass == "Todos":
            d_pad = padronizar(disc)
            if disc in PROPORCOES_INSS:
                vagas_assuntos = distribuir_vagas_exatas(PROPORCOES_INSS[disc], qtd_desejada)
                for a, qtd_calc in vagas_assuntos.items():
                    if qtd_calc > 0:
                        a_pad = padronizar(a)
                        filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                        qtd_real = min(qtd_calc, len(filtro))
                        if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
            else:
                filtro = df_base[df_base['Disc_pad'] == d_pad]
                qtd_real = min(qtd_desejada, len(filtro))
                if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))
        else:
            d_pad = padronizar(disc)
            a_pad = padronizar(ass)
            filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
            qtd_real = min(qtd_desejada, len(filtro))
            if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))

    # ROTA 3: MODO LIVRE
    else: 
        if not st.session_state.regras_simulado: return
        for r in st.session_state.regras_simulado:
            d_pad = padronizar(r['Disciplina'])
            a_pad = padronizar(r['Assunto'])
            
            if d_pad == "todas":
                filtro = df_base.copy()
            elif a_pad == "todos":
                filtro = df_base[df_base['Disc_pad'] == d_pad]
            else:
                filtro = df_base[(df_base['Disc_pad'] == d_pad) & (df_base['Ass_pad'] == a_pad)]
                
            qtd_real = min(r['Qtd'], len(filtro))
            if qtd_real > 0: frames.append(filtro.sample(n=qtd_real))

    if frames:
        prova_final = pd.concat(frames).sample(frac=1).reset_index(drop=True)
        st.session_state.df_ativo = prova_final
        resetar_progresso()
        
        if len(prova_final) < qtd_desejada and modo == "Questões" and prova == "INSS":
            st.sidebar.warning(f"⚠️ Solicitadas {qtd_desejada} questões, mas só encontrei {len(prova_final)} mapeadas no banco que atendem à regra.")
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

# --- 4. BARRA LATERAL ---
st.sidebar.header("Configurar Bateria")

with st.sidebar.expander("🛠️ Diagnóstico do Banco"):
    st.caption("Verifique como os nomes foram salvos no seu CSV. Corrija divergências no arquivo.")
    resumo_banco = df_base.groupby(['Disciplina', 'Assunto']).size().reset_index(name='Qtd Cadastrada')
    st.dataframe(resumo_banco, use_container_width=True, hide_index=True)

with st.sidebar.expander("📊 Questões do Teste (Raio-X)"):
    st.caption("Estrutura exata da prova gerada:")
    if st.session_state.df_ativo.empty:
        st.info("Nenhum teste gerado.")
    else:
        resumo_teste = st.session_state.df_ativo.groupby(['Disciplina', 'Assunto']).size().reset_index(name='Qtd no Teste')
        st.dataframe(resumo_teste, use_container_width=True, hide_index=True)
        st.markdown(f"**Total alocado:** {len(st.session_state.df_ativo)} vagas preenchidas")

prova_sel = st.sidebar.selectbox("1. Prova", ["", "INSS"])
modo_sel = st.sidebar.selectbox("2. Modo", ["Questões", "Simulado"])

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
    st.info("👈 Ajuste os filtros na barra lateral para iniciar.")
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

import streamlit as st
import pandas as pd
import unicodedata
import re
import math
import csv
import json

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
    soma_pesos = sum(dicionario_pesos.values())
    if soma_pesos == 0 or vagas_totais <= 0:
        return {k: 0 for k in dicionario_pesos}
    
    cotas_exatas = {k: (v / soma_pesos) * vagas_totais for k, v in dicionario_pesos.items()}
    alocacao = {k: math.floor(v) for k, v in cotas_exatas.items()}
    vagas_restantes = int(vagas_totais - sum(alocacao.values()))
    
    restos = {k: cotas_exatas[k] - alocacao[k] for k in cotas_exatas}
    ordenados_por_resto = sorted(restos.keys(), key=lambda x: restos[x], reverse=True)
    
    for i in range(vagas_restantes):
        if i < len(ordenados_por_resto):
            alocacao[ordenados_por_resto[i]] += 1
            
    return alocacao

def extrair_questoes_com_repescagem(df_fonte, dicionario_cotas, d_pad):
    frames = []
    deficit = 0
    pool_reserva = []
    
    for a, qtd_calc in dicionario_cotas.items():
        if qtd_calc > 0:
            a_pad = padronizar(a)
            filtro = df_fonte[(df_fonte['Disc_pad'] == d_pad) & (df_fonte['Ass_pad'] == a_pad)]
            
            qtd_real = min(qtd_calc, len(filtro))
            if qtd_real > 0:
                selecionadas = filtro.sample(n=qtd_real)
                frames.append(selecionadas)
                
                nao_selecionadas = filtro.drop(selecionadas.index)
                if not nao_selecionadas.empty:
                    pool_reserva.append(nao_selecionadas)
            
            deficit += (qtd_calc - qtd_real)
            
    if deficit > 0 and pool_reserva:
        df_reserva = pd.concat(pool_reserva)
        qtd_repescagem = min(deficit, len(df_reserva))
        if qtd_repescagem > 0:
            frames.append(df_reserva.sample(n=qtd_repescagem))
            
    return frames

# ==========================================
# ⚙️ MOTOR DE PROPORÇÕES (APENAS PREVIDENCIÁRIO)
# ==========================================
PROPORCOES_INSS = {
   "Direito Previdenciário": {
        "Saúde, Previdência Social e Assistência Social": 9.0,
        "Do Reconhecimento da Filiação": 8.0,
        "Das Disposições Diversas e Transitórias Relativas às Prestações": 8.0,
        "Da Contagem Recíproca de Tempo de Serviço": 7.0,
        "Recursos das Decisões Administrativas": 6.0,
        "Financiamento da Seguridade Social": 6.0,
        "Do Salário-de-Contribuição": 6.0,
        "Legislação Previdenciária (Fontes, Aplicação, Hierarquia etc.)": 5.0,
        "Seguro Desemprego, FAT e Abono Salarial": 5.0,
        "Das Aposentadorias por Tempo de Contribuição e por Idade do Segurado com Deficiência": 5.0,
        "Conceito de Empresa e Empregador Doméstico": 4.0,
        "Dos Serviços, Programas de Assistência Social e Enfrentamento da Pobreza": 4.0,
        "Dos Dependentes (RGPS)": 4.0,
        "Princípios e Objetivos da Seguridade Social": 4.0,
        "Tópicos Mesclados sobre Segurados (RGPS)": 4.0,
        "Segurado Facultativo (RGPS)": 4.0,
        "Da Manutenção e da Perda da Qualidade de Segurado": 4.0,
        "Da Arrecadação e Recolhimento das Contribuições": 4.0,
        "Do Cálculo do Valor do Benefício": 3.0,
        "Da Habilitação e Reabilitação de Profissionais e do Serviço Social": 3.0,
        "Lei nº 13.985/2020 - Pensão Especial (Zika Vírus)": 2.0,
        "Segurado Especial (RGPS)": 2.0,
        "Origem e Evolução Legislativa da Seguridade Social": 4.0,
        "Lei nº 9.425/1996 - Pensão Especial (CÉSIO 137)": 2.0,
        "Lei nº 9.422/1996 - Pensão Especial (Hemodiálise)": 2.0,
        "Sonegação de Contribuição Previdenciária (art. 337-A do CP)": 2.0,
        "Lei nº 8.059/1990 - Pensão Especial (Ex-Combatentes)": 2.0,
        "Lei nº 7.070/1982 - Pensão Especial (Talidomida)": 2.0,
        "Lei nº 10.559/2002 - Aposentadoria (Anistiado Político)": 2.0,
        "Lei nº 11.520/2007 - Pensão Especial (Hanseníase)": 2.0,
        "Lei nº 10.779/2003 - Seguro Desemprego (Pescador)": 2.0,
        "Emenda Constitucional nº 103/2019 (Reforma da Previdência)": 0,
        "Dos Princípios e das Diretrizes (LOAS)": 2.0,
        "Dos Benefícios (LOAS)": 2.0,
        "Da Pensão por Morte": 2.0,
        "Da Apropriação Indébita (arts. 168 a 170 do CP)": 2.0,
        "Empregado Doméstico (RGPS)": 1.0,
        "Do Salário-Maternidade": 1.0,
        "Regime Próprio de Previdência Social na Constituição Federal": 1.0,
        "Decreto nº 6.214/2007 - BPC": 1.0,
        "Da Organização e da Gestão (LOAS)": 1.0,
        "Contribuinte Individual (RGPS)": 1.0,
        "Carência": 1.0,
    }
}

# --- 1. INICIALIZAÇÃO DE ESTADOS ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'acertos' not in st.session_state: st.session_state.acertos = 0
if 'erros' not in st.session_state: st.session_state.erros = 0
if 'regras_simulado' not in st.session_state: st.session_state.regras_simulado = []
if 'df_ativo' not in st.session_state: st.session_state.df_ativo = pd.DataFrame()
if 'respostas_dadas' not in st.session_state: st.session_state.respostas_dadas = {}
if 'tamanho_fonte' not in st.session_state: st.session_state.tamanho_fonte = 18  # INOVAÇÃO 1: Controle de Zoom

# --- 2. CARREGAMENTO BLINDADO (MODO INTELIGENTE) ---
@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        df = pd.read_csv("questoes.csv", sep=";", encoding='utf-8', on_bad_lines='skip', quoting=csv.QUOTE_NONE)
    except:
        try:
            df = pd.read_csv("questoes.csv", sep=";", encoding='latin1', on_bad_lines='skip', quoting=csv.QUOTE_NONE)
        except:
            return pd.DataFrame()
    
    # MAPEAMENTO INTELIGENTE DE COLUNAS
    mapa_colunas = {}
    for col in df.columns:
        c_clean = padronizar(col)
        if 'id' in c_clean: mapa_colunas[col] = 'ID'
        elif 'disciplina' in c_clean: mapa_colunas[col] = 'Disciplina'
        elif 'assunto' in c_clean: mapa_colunas[col] = 'Assunto'
        elif 'assertiva' in c_clean: mapa_colunas[col] = 'Assertiva'
        elif 'gabarito' in c_clean: mapa_colunas[col] = 'Gabarito'
        elif 'comentario' in c_clean: mapa_colunas[col] = 'Comentario'
        
    df = df.rename(columns=mapa_colunas)
    
    colunas_esperadas = ['ID', 'Disciplina', 'Assunto', 'Assertiva', 'Gabarito', 'Comentario']
    for col in colunas_esperadas:
        if col not in df.columns: df[col] = "Sem informação"
        
    # LIMPEZA DE GABARITO
    df['Gabarito'] = df['Gabarito'].astype(str).str.replace('"', '').str.replace("'", "").str.strip().str.upper()
    df['Gabarito'] = df['Gabarito'].apply(lambda x: 'C' if x.startswith('C') else ('E' if x.startswith('E') else x))
    
    # LIMPEZA DE COMENTÁRIO
    df['Comentario'] = df['Comentario'].astype(str).str.replace(r'^"|"$', '', regex=True).replace('Sem informação', '')
    
    df['Disc_pad'] = df['Disciplina'].apply(padronizar)
    df['Ass_pad'] = df['Assunto'].apply(padronizar)
    return df

df_base = carregar_dados()
if df_base.empty:
    st.error("Arquivo questoes.csv não encontrado, vazio ou com erro crítico de estrutura.")
    st.stop()

# --- 3. LÓGICA DE GERAÇÃO INTELIGENTE ---
def resetar_progresso():
    st.session_state.indice = 0
    st.session_state.acertos = 0
    st.session_state.erros = 0
    st.session_state.respostas_dadas = {}

def gerar_bateria(prova, modo, disc, ass, qtd_desejada):
    frames = []
    
    if prova == "INSS" and modo == "Simulado":
        pesos_disciplinas = {d: sum(assuntos.values()) for d, assuntos in PROPORCOES_INSS.items()}
        vagas_disciplinas = distribuir_vagas_exatas(pesos_disciplinas, qtd_desejada)
        
        for d, assuntos_dict in PROPORCOES_INSS.items():
            d_pad = padronizar(d)
            vagas_d = vagas_disciplinas[d]
            vagas_assuntos = distribuir_vagas_exatas(assuntos_dict, vagas_d)
            
            frames_d = extrair_questoes_com_repescagem(df_base, vagas_assuntos, d_pad)
            frames.extend(frames_d)
                
    elif prova == "INSS" and modo == "Questões":
        if disc == "Todas":
            pesos_disciplinas = {d: sum(assuntos.values()) for d, assuntos in PROPORCOES_INSS.items()}
            vagas_disciplinas = distribuir_vagas_exatas(pesos_disciplinas, qtd_desejada)
            
            for d, assuntos_dict in PROPORCOES_INSS.items():
                d_pad = padronizar(d)
                vagas_d = vagas_disciplinas[d]
                vagas_assuntos = distribuir_vagas_exatas(assuntos_dict, vagas_d)
                
                frames_d = extrair_questoes_com_repescagem(df_base, vagas_assuntos, d_pad)
                frames.extend(frames_d)
                        
        elif ass == "Todos":
            d_pad = padronizar(disc)
            if disc in PROPORCOES_INSS:
                vagas_assuntos = distribuir_vagas_exatas(PROPORCOES_INSS[disc], qtd_desejada)
                frames_d = extrair_questoes_com_repescagem(df_base, vagas_assuntos, d_pad)
                frames.extend(frames_d)
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
            st.sidebar.warning(f"⚠️ Atenção: Você pediu {qtd_desejada} questões, mas a disciplina só possui {len(prova_final)} cadastradas no total do banco.")
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
    st.caption("Verifique as questões ativas no CSV.")
    resumo_banco = df_base.groupby(['Disciplina', 'Assunto']).size().reset_index(name='Qtd Cadastrada')
    st.dataframe(resumo_banco, use_container_width=True, hide_index=True)

with st.sidebar.expander("📊 Questões do Teste (Raio-X)"):
    st.caption("Estrutura da prova gerada:")
    if st.session_state.df_ativo.empty:
        st.info("Nenhum teste gerado.")
    else:
        resumo_teste = st.session_state.df_ativo.groupby(['Disciplina', 'Assunto']).size().reset_index(name='Qtd no Teste')
        st.dataframe(resumo_teste, use_container_width=True, hide_index=True)
        st.markdown(f"**Total alocado:** {len(st.session_state.df_ativo)} questões")

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
qtd_sel = st.sidebar.number_input("5. Qtd", min_value=1, value=100)

if prova_sel == "INSS":
    if st.sidebar.button(f"🚀 Gerar {modo_sel} INSS", type="primary", use_container_width=True):
        gerar_bateria(prova_sel, modo_sel, disc_sel, ass_sel, qtd_sel)
else:
    st.sidebar.caption("Modo Manual: Construa a prova bloco a bloco.")
    if st.sidebar.button("➕ Selecionar Assunto"):
        st.session_state.regras_simulado.append({'Disciplina': disc_sel, 'Assunto': ass_sel, 'Qtd': qtd_sel})
    
    if st.session_state.regras_simulado:
        for r in st.session_state.regras_simulado:
            st.sidebar.text(f"• {r['Assunto']} ({r['Qtd']}q)")
        if st.sidebar.button("Gerar Prova Manual", type="primary", use_container_width=True):
            gerar_bateria(prova_sel, modo_sel, None, None, None)

if st.sidebar.button("Limpar Tela", use_container_width=True):
    limpar_dados()

# INOVAÇÃO 3: Totalizador no painel
st.sidebar.divider()
st.sidebar.header("Desempenho")
c_acerto, c_erro, c_total = st.sidebar.columns(3)
c_acerto.metric("Acertos ✅", st.session_state.acertos)
c_erro.metric("Erros ❌", st.session_state.erros)
c_total.metric("Total 🎯", st.session_state.acertos + st.session_state.erros)

# --- SISTEMA DE SALVAMENTO E RECUPERAÇÃO ---
st.sidebar.divider()
st.sidebar.header("💾 Salvar / Carregar Progresso")

if not st.session_state.df_ativo.empty:
    estado_atual = {
        'indice': st.session_state.indice,
        'acertos': st.session_state.acertos,
        'erros': st.session_state.erros,
        'respostas_dadas': {str(k): v for k, v in st.session_state.respostas_dadas.items()},
        'df_ativo': st.session_state.df_ativo.to_dict(orient='records'),
        'regras_simulado': st.session_state.regras_simulado
    }
    
    json_string = json.dumps(estado_atual, ensure_ascii=False)
    
    st.sidebar.download_button(
        label="⬇️ Baixar Progresso Atual",
        data=json_string,
        file_name="progresso_simulado.json",
        mime="application/json",
        use_container_width=True
    )
else:
    st.sidebar.caption("Gere uma bateria de questões para habilitar o salvamento.")

st.sidebar.divider()

arquivo_upload = st.sidebar.file_uploader("📂 Restaurar sessão anterior", type=["json"])

if arquivo_upload is not None:
    if st.sidebar.button("Recarregar Progresso", type="primary", use_container_width=True):
        dados = json.load(arquivo_upload)
        
        st.session_state.indice = dados.get('indice', 0)
        st.session_state.acertos = dados.get('acertos', 0)
        st.session_state.erros = dados.get('erros', 0)
        st.session_state.respostas_dadas = {int(k): v for k, v in dados.get('respostas_dadas', {}).items()}
        st.session_state.df_ativo = pd.DataFrame(dados.get('df_ativo', []))
        st.session_state.regras_simulado = dados.get('regras_simulado', [])
        
        st.rerun()

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

# INOVAÇÃO 1: Botões de Zoom alinhados com o cabeçalho da questão
col_cabecalho, col_menos, col_mais = st.columns([8, 1, 1])
with col_cabecalho:
    st.caption(f"{questao['Disciplina']} ➔ {questao['Assunto']} | ID Original: {questao['ID']}")
with col_menos:
    if st.button("A-", use_container_width=True):
        st.session_state.tamanho_fonte = max(12, st.session_state.tamanho_fonte - 2)
        st.rerun()
with col_mais:
    if st.button("A+", use_container_width=True):
        st.session_state.tamanho_fonte = min(40, st.session_state.tamanho_fonte + 2)
        st.rerun()

# Injeta a formatação de fonte dinâmica
st.markdown(
    f"<div style='font-size: {st.session_state.tamanho_fonte}px; font-weight: bold; margin-bottom: 20px; line-height: 1.5;'>"
    f"{questao['Assertiva']}"
    f"</div>", 
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)
with col1:
    st.button("CERTO", key=f"c_{idx_atual}", on_click=responder, args=("C", gabarito_real), disabled=ja_respondida, use_container_width=True)
with col2:
    st.button("ERRADO", key=f"e_{idx_atual}", on_click=responder, args=("E", gabarito_real), disabled=ja_respondida, use_container_width=True)

if ja_respondida:
    escolha_feita = st.session_state.respostas_dadas[idx_atual]
    st.divider()
    
    # INOVAÇÃO 2: Gabarito revelado em ambas as situações
    if escolha_feita == gabarito_real:
        st.success(f"✅ Resposta Correta! O gabarito é '{gabarito_real}'.")
    else:
        st.error(f"❌ Resposta Incorreta. O gabarito é '{gabarito_real}'.")
    
    comentario_exibir = str(questao['Comentario']).strip()
    if comentario_exibir and comentario_exibir != 'nan':
        st.info(f"**Comentário:** {comentario_exibir}")

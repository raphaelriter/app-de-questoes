import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Caderno de Questões", layout="centered")

# --- INICIALIZAÇÃO DE ESTADOS (MEMÓRIA DO APP) ---
for key in ['indice', 'acertos', 'erros']:
    if key not in st.session_state:
        st.session_state[key] = 0

for key in ['respondido', 'escolha']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'respondido' else None

# Novos estados para gerenciar a montagem do simulado
if 'regras_simulado' not in st.session_state:
    st.session_state.regras_simulado = [] # Guarda os filtros que você incluir
if 'df_ativo' not in st.session_state:
    st.session_state.df_ativo = pd.DataFrame() # Guarda a prova gerada

# --- CARREGAMENTO DE DADOS ---
try:
    df_base = pd.read_csv("questoes.csv", sep=";", encoding='utf-8')
except FileNotFoundError:
    st.error("Arquivo questoes.csv não encontrado na pasta.")
    st.stop()
except UnicodeDecodeError:
    df_base = pd.read_csv("questoes.csv", sep=";", encoding='latin1')

# --- FUNÇÕES DE LÓGICA ---
def responder(resposta, gabarito_correto):
    st.session_state.respondido = True
    st.session_state.escolha = resposta
    if resposta == gabarito_correto:
        st.session_state.acertos += 1
    else:
        st.session_state.erros += 1

def proxima_questao():
    st.session_state.indice += 1
    st.session_state.respondido = False
    st.session_state.escolha = None

def adicionar_regra(disciplina, assunto, qtd):
    st.session_state.regras_simulado.append({
        'Disciplina': disciplina,
        'Assunto': assunto,
        'Qtd': qtd
    })

def limpar_regras():
    st.session_state.regras_simulado = []
    st.session_state.df_ativo = pd.DataFrame()

def gerar_prova():
    if not st.session_state.regras_simulado:
        return
    
    frames_questoes = []
    # Busca aleatoriamente no banco o número de questões pedidas para cada regra
    for regra in st.session_state.regras_simulado:
        filtro = df_base[(df_base['Disciplina'] == regra['Disciplina']) & (df_base['Assunto'] == regra['Assunto'])]
        qtd_real = min(regra['Qtd'], len(filtro)) # Trava de segurança para não pedir mais do que existe
        
        if qtd_real > 0:
            amostra = filtro.sample(n=qtd_real) # Puxa questões aleatórias
            frames_questoes.append(amostra)
    
    if frames_questoes:
        # Junta todas as amostras e embaralha a prova (frac=1)
        prova_final = pd.concat(frames_questoes).sample(frac=1).reset_index(drop=True)
        st.session_state.df_ativo = prova_final
        
        # Zera contadores para o novo simulado
        st.session_state.indice = 0
        st.session_state.acertos = 0
        st.session_state.erros = 0
        st.session_state.respondido = False
        st.session_state.escolha = None

# --- BARRA LATERAL: CONSTRUTOR DE SIMULADO ---
st.sidebar.header("Montar Simulado")

# 1. Filtro em Cascata (Disciplina puxa o Assunto)
disciplinas_disp = df_base['Disciplina'].dropna().unique().tolist()
disc_selecionada = st.sidebar.selectbox("1. Disciplina", disciplinas_disp)

assuntos_disp = df_base[df_base['Disciplina'] == disc_selecionada]['Assunto'].dropna().unique().tolist()
assunto_selecionado = st.sidebar.selectbox("2. Assunto", assuntos_disp)

# 2. O sistema calcula quantas questões você tem daquele assunto no banco
qtd_max = len(df_base[(df_base['Disciplina'] == disc_selecionada) & (df_base['Assunto'] == assunto_selecionado)])
qtd_desejada = st.sidebar.number_input(f"3. Quantidade (Máx disponível: {qtd_max})", min_value=1, max_value=qtd_max if qtd_max > 0 else 1, step=1)

# Botão de incluir bloqueia se não houver questões
if st.sidebar.button("➕ Incluir no Simulado", disabled=(qtd_max == 0)):
    adicionar_regra(disc_selecionada, assunto_selecionado, qtd_desejada)

# Exibe a "Cesta" de questões sendo montada
if st.session_state.regras_simulado:
    st.sidebar.divider()
    st.sidebar.markdown("**Estrutura da Prova:**")
    total_q = 0
    for r in st.session_state.regras_simulado:
        st.sidebar.caption(f"• {r['Assunto']} ({r['Qtd']} q)")
        total_q += r['Qtd']
    
    st.sidebar.markdown(f"**Total: {total_q} questões**")
    
    col_g, col_l = st.sidebar.columns(2)
    col_g.button("Gerar Prova", type="primary", on_click=gerar_prova, use_container_width=True)
    col_l.button("Limpar", on_click=limpar_regras, use_container_width=True)

st.sidebar.divider()

# --- BARRA LATERAL: DESEMPENHO ---
st.sidebar.header("Desempenho Atual")
total_resolvidas = st.session_state.acertos + st.session_state.erros
col_a, col_e = st.sidebar.columns(2)
col_a.metric("Acertos ✅", st.session_state.acertos)
col_e.metric("Erros ❌", st.session_state.erros)
st.sidebar.metric("Total Resolvidas", total_resolvidas)

# --- TELA PRINCIPAL (RENDERIZAÇÃO DA PROVA) ---
df_prova = st.session_state.df_ativo

# Estado 1: Nenhuma prova gerada
if df_prova.empty:
    st.info("👈 Use o menu lateral para selecionar as disciplinas, assuntos e quantidades. Depois, clique em 'Gerar Prova'.")
    st.stop()

# Estado 2: Prova finalizada
if st.session_state.indice >= len(df_prova):
    st.success("🎉 Simulado concluído!")
    st.write(f"**Resultado Final:** {st.session_state.acertos} Acertos | {st.session_state.erros} Erros")
    if st.button("Montar Novo Simulado", type="primary"):
        limpar_regras()
        st.rerun()
    st.stop()

# Estado 3: Resolvendo questões
questao_atual = df_prova.iloc[st.session_state.indice]
gabarito_real = str(questao_atual['Gabarito']).strip().upper()

st.subheader(f"Questão {st.session_state.indice + 1} de {len(df_prova)}")
st.caption(f"{questao_atual['Disciplina']} ➔ {questao_atual['Assunto']} | ID Original: {questao_atual['ID']}")
st.write(f"**{questao_atual['Assertiva']}**")

col1, col2 = st.columns(2)
with col1:
    st.button("CERTO", key=f"c_{st.session_state.indice}", on_click=responder, args=("C", gabarito_real), disabled=st.session_state.respondido, use_container_width=True)
with col2:
    st.button("ERRADO", key=f"e_{st.session_state.indice}", on_click=responder, args=("E", gabarito_real), disabled=st.session_state.respondido, use_container_width=True)

if st.session_state.respondido:
    st.divider()
    if st.session_state.escolha == gabarito_real:
        st.success("✅ Resposta Correta!")
    else:
        st.error(f"❌ Resposta Incorreta. O gabarito é {gabarito_real}.")

    st.info(f"**Comentário:** {questao_atual['Comentario']}")
    st.button("Próxima Questão ➔", on_click=proxima_questao, type="primary")
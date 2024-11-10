import streamlit as st
import bcrypt
import json
import os
import requests
import pandas as pd
from datetime import datetime

# Configurações iniciais
if 'login_status' not in st.session_state:
    st.session_state.login_status = False

if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# Estados da edição
if 'editing' not in st.session_state:
    st.session_state.editing = False
if 'editing_book' not in st.session_state:
    st.session_state.editing_book = None

# Constantes
USERS_FILE = 'users.json'
API_URL = "http://localhost:8080"

# Funções de autenticação
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    default_users = {
        "admin": {
            "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
            "role": "admin",
            "name": "Administrador"
        },
        "user": {
            "password": bcrypt.hashpw("user123".encode(), bcrypt.gensalt()).decode(),
            "role": "user",
            "name": "Usuário"
        }
    }
    save_users(default_users)
    return default_users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def login(username, password):
    users = load_users()
    if username in users:
        if bcrypt.checkpw(password.encode(), users[username]['password'].encode()):
            st.session_state.login_status = True
            st.session_state.user_info = {
                'username': username,
                'role': users[username]['role'],
                'name': users[username]['name']
            }
            return True
    return False

def register(username, password, name, role="user"):
    users = load_users()
    if username in users:
        return False, "Usuário já existe"
    
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = {
        "password": hashed_pw,
        "role": role,
        "name": name
    }
    save_users(users)
    return True, "Usuário registrado com sucesso"

# Páginas de autenticação
def login_page():
    st.title("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            if login(username, password):
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

    if st.button("Criar nova conta"):
        st.session_state.page = "register"
        st.rerun()

def register_page():
    st.title("📝 Novo Cadastro")
    
    with st.form("register_form"):
        name = st.text_input("Nome Completo")
        username = st.text_input("Nome de Usuário")
        password = st.text_input("Senha", type="password")
        password_confirm = st.text_input("Confirmar Senha", type="password")
        
        submit = st.form_submit_button("Cadastrar")
        
        if submit:
            if not all([username, password, name]):
                st.error("Todos os campos são obrigatórios")
            elif password != password_confirm:
                st.error("As senhas não coincidem")
            else:
                success, message = register(username, password, name)
                if success:
                    st.success(message)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)
    
    if st.button("Voltar para login"):
        st.session_state.page = "login"
        st.rerun()

def editar_livro(livro):
    st.subheader(f"📝 Editar Livro: {livro['Título']}")
    
    with st.form(key=f"edit_form_{livro['ID']}", clear_on_submit=False):
        novo_titulo = st.text_input("Título*", value=livro['Título'])
        novo_autor = st.text_input("Autor*", value=livro['Autor'])
        
        col1, col2 = st.columns(2)
        with col1:
            generos = ["Romance", "Ficção Científica", "Fantasia", 
                      "Técnico", "Biografia", "História",
                      "Autoajuda", "Infantil", "Outro"]
            novo_genero = st.selectbox(
                "Gênero",
                options=generos,
                index=generos.index(livro['Gênero']) if livro['Gênero'] in generos else 0
            )
        
        with col2:
            categorias = ["Livro Físico", "E-book", "Audiobook",
                         "Revista", "Artigo", "Outro"]
            nova_categoria = st.selectbox(
                "Categoria",
                options=categorias,
                index=categorias.index(livro['Categoria']) if livro['Categoria'] in categorias else 0
            )
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Salvar Alterações")
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar")
        
        if submitted:
            if not novo_titulo or not novo_autor:
                st.error("❌ Título e autor são campos obrigatórios!")
                return False
            
            dados_atualizados = {
                "titulo": novo_titulo,
                "autor": novo_autor,
                "genero": novo_genero,
                "categoria": nova_categoria
            }
            
            try:
                response = requests.put(
                    f"{API_URL}/livros/{livro['ID']}",
                    json=dados_atualizados
                )
                
                if response.status_code == 200:
                    st.success("✅ Livro atualizado com sucesso!")
                    return True
                else:
                    st.error(f"❌ Erro ao atualizar livro: {response.text}")
                    return False
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
                return False
        
        if cancelar:
            return True
    
    return False

def adicionar_livro():
    st.header("➕ Adicionar Novo Livro")
    
    with st.form(key="form_livro", clear_on_submit=True):
        st.subheader("Informações do Livro")
        
        titulo = st.text_input("Título do Livro*")
        autor = st.text_input("Nome do Autor*")
        
        col1, col2 = st.columns(2)
        with col1:
            genero = st.selectbox("Gênero", [
                "Romance", "Ficção Científica", "Fantasia", 
                "Técnico", "Biografia", "História",
                "Autoajuda", "Infantil", "Outro"
            ])
        
        with col2:
            categoria = st.selectbox("Categoria", [
                "Livro Físico", "E-book", "Audiobook",
                "Revista", "Artigo", "Outro"
            ])
        
        submitted = st.form_submit_button("📚 Cadastrar Livro")
        
        if submitted:
            if not titulo or not autor:
                st.error("❌ Título e autor são campos obrigatórios!")
                return
            
            novo_livro = {
                "titulo": titulo,
                "autor": autor,
                "genero": genero,
                "categoria": categoria
            }
            
            try:
                response = requests.post(f"{API_URL}/livros", json=novo_livro)
                if response.status_code == 201:
                    st.success("✅ Livro cadastrado com sucesso!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Erro ao cadastrar livro: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Erro de conexão com o servidor!")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")

def listar_livros():
    st.header("📚 Biblioteca Digital")
    
    try:
        response = requests.get(f"{API_URL}/livros")
        if response.status_code == 200:
            livros = response.json()
            if not livros:
                st.info("📢 Nenhum livro cadastrado ainda.")
                return
            
            df = pd.DataFrame(livros)
            df.columns = ['ID', 'Título', 'Autor', 'Gênero', 'Categoria']
            
            # Filtros
            with st.expander("🔍 Filtros de Busca", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    busca = st.text_input("🔎 Buscar por título ou autor")
                
                with col2:
                    generos = st.multiselect(
                        "Filtrar por Gênero",
                        options=sorted(df['Gênero'].unique())
                    )
                
                with col3:
                    categorias = st.multiselect(
                        "Filtrar por Categoria",
                        options=sorted(df['Categoria'].unique())
                    )
                
                # Aplicar filtros
                df_filtrado = df.copy()
                if busca:
                    mask = (
                        df_filtrado['Título'].str.contains(busca, case=False) |
                        df_filtrado['Autor'].str.contains(busca, case=False)
                    )
                    df_filtrado = df_filtrado[mask]
                if generos:
                    df_filtrado = df_filtrado[df_filtrado['Gênero'].isin(generos)]
                if categorias:
                    df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias)]
                
                # Métricas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Livros", len(df))
                with col2:
                    st.metric("Livros Filtrados", len(df_filtrado))
                with col3:
                    percentual = (len(df_filtrado) / len(df) * 100) if len(df) > 0 else 0
                    st.metric("Percentual", f"{percentual:.1f}%")
            
            # Tabela principal
            st.dataframe(
                df_filtrado,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", help="Identificador único"),
                    "Título": st.column_config.TextColumn("Título", help="Título do livro", width="large"),
                    "Autor": st.column_config.TextColumn("Autor", help="Nome do autor"),
                    "Gênero": st.column_config.TextColumn("Gênero", help="Gênero literário"),
                    "Categoria": st.column_config.TextColumn("Categoria", help="Tipo do livro")
                },
                hide_index=True,
            )
            
            # Gerenciamento (apenas para admin)
            if st.session_state.user_info['role'] == 'admin':
                st.markdown("---")
                st.subheader("🛠️ Gerenciar Livros")
                
                livro_selecionado = st.selectbox(
                    "Selecione um livro para gerenciar:",
                    options=df_filtrado.to_dict('records'),
                    format_func=lambda x: f"{x['Título']} - {x['Autor']}"
                )
                
                if livro_selecionado:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📝 Editar"):
                            st.session_state.editing = True
                            st.session_state.editing_book = livro_selecionado
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️ Excluir"):
                            st.warning(f"🚨 Tem certeza que deseja excluir '{livro_selecionado['Título']}'?")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Sim, excluir"):
                                    try:
                                        response = requests.delete(f"{API_URL}/livros/{livro_selecionado['ID']}")
                                        if response.status_code == 204:
                                            st.success("✅ Livro excluído com sucesso!")
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao excluir livro!")
                                    except Exception as e:
                                        st.error(f"❌ Erro: {str(e)}")
                            with col2:
                                if st.button("❌ Não, cancelar"):
                                    st.rerun()
                
                # Mostrar formulário de edição se estiver editando
                if st.session_state.get('editing', False) and st.session_state.get('editing_book'):
                    if editar_livro(st.session_state.editing_book):
                        st.session_state.editing = False
                        st.session_state.editing_book = None
                        st.rerun()
                    
    except requests.exceptions.ConnectionError:
        st.error("❌ Erro de conexão com o servidor!")
    except Exception as e:
        st.error(f"❌ Erro ao carregar livros: {str(e)}")

@st.cache_data(ttl=300)
def load_dashboard_data():
    try:
        response = requests.get(f"{API_URL}/livros")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def dashboard():
    st.header("📊 Dashboard")
    
    try:
        df = load_dashboard_data()
        if df.empty:
            st.info("📢 Nenhum dado disponível para análise.")
            return
        
        df.columns = ['ID', 'Título', 'Autor', 'Gênero', 'Categoria']
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Livros", len(df))
        with col2:
            st.metric("Autores Únicos", df['Autor'].nunique())
        with col3:
            st.metric("Gêneros", df['Gênero'].nunique())
        with col4:
            st.metric("Categorias", df['Categoria'].nunique())
        
        st.markdown("---")
        
        # Análises por gênero e categoria
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Distribuição por Gênero")
            generos_count = df['Gênero'].value_counts()
            st.bar_chart(generos_count)
            
            st.markdown("### Detalhamento por Gênero")
            generos_df = pd.DataFrame({
                'Gênero': generos_count.index,
                'Quantidade': generos_count.values,
                'Percentual': (generos_count.values / len(df) * 100).round(1)
            })
            generos_df['Percentual'] = generos_df['Percentual'].apply(lambda x: f"{x}%")
            st.dataframe(generos_df, hide_index=True)
        
        with col2:
            st.subheader("📊 Distribuição por Categoria")
            categorias_count = df['Categoria'].value_counts()
            st.bar_chart(categorias_count)
            
            st.markdown("### Detalhamento por Categoria")
            categorias_df = pd.DataFrame({
                'Categoria': categorias_count.index,
                'Quantidade': categorias_count.values,
                'Percentual': (categorias_count.values / len(df) * 100).round(1)
            })
            categorias_df['Percentual'] = categorias_df['Percentual'].apply(lambda x: f"{x}%")
            st.dataframe(categorias_df, hide_index=True)
        
        st.markdown("---")
        
        # Análise de autores
        st.subheader("👥 Análise de Autores")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Top 10 Autores")
            top_autores = df['Autor'].value_counts().head(10)
            st.bar_chart(top_autores)
            
            top_autores_df = pd.DataFrame({
                'Autor': top_autores.index,
                'Quantidade': top_autores.values,
                'Percentual': (top_autores.values / len(df) * 100).round(1)
            })
            top_autores_df['Percentual'] = top_autores_df['Percentual'].apply(lambda x: f"{x}%")
            st.dataframe(top_autores_df, hide_index=True)
        
        with col2:
            st.markdown("### Distribuição de Livros por Autor")
            livros_por_autor = df['Autor'].value_counts()
            distribuicao_df = pd.DataFrame({
                'Categoria': [
                    'Autores com 1 livro',
                    'Autores com 2-5 livros',
                    'Autores com mais de 5 livros'
                ],
                'Quantidade': [
                    (livros_por_autor == 1).sum(),
                    ((livros_por_autor >= 2) & (livros_por_autor <= 5)).sum(),
                    (livros_por_autor > 5).sum()
                ]
            })
            st.dataframe(distribuicao_df, hide_index=True)
        
        # Exportação de dados
        st.markdown("---")
        st.subheader("📥 Exportar Dados")
        
        col1, col2 = st.columns(2)
        with col1:
            # CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📄 Baixar CSV",
                data=csv,
                file_name=f'biblioteca_dados_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv'
            )
        
        with col2:
            # Excel
            buffer = pd.ExcelWriter(f'biblioteca_dados_{datetime.now().strftime("%Y%m%d")}.xlsx', 
                                  engine='xlsxwriter')
            df.to_excel(buffer, index=False, sheet_name='Dados')
            buffer.save()
            
            with open(buffer.name, 'rb') as f:
                excel_data = f.read()
            
            st.download_button(
                "📊 Baixar Excel",
                data=excel_data,
                file_name=f'biblioteca_dados_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mime='application/vnd.ms-excel'
            )
            
    except Exception as e:
        st.error(f"❌ Erro ao gerar dashboard: {str(e)}")

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Biblioteca Digital",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inicialização de estados
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    
    # Verificar arquivo de usuários
    if not os.path.exists(USERS_FILE):
        users = load_users()
        save_users(users)
    
    # Fluxo principal
    if not st.session_state.login_status:
        if st.session_state.page == "login":
            login_page()
        elif st.session_state.page == "register":
            register_page()
    else:
        # Menu lateral
        with st.sidebar:
            st.title("📚 Biblioteca Digital")
            st.write(f"Bem-vindo, {st.session_state.user_info['name']}!")
            st.write(f"Função: {st.session_state.user_info['role']}")
            st.markdown("---")
            
            # Menu dinâmico baseado na função
            menu_options = ["📖 Listar Livros", "📊 Dashboard"]
            if st.session_state.user_info['role'] == "admin":
                menu_options.insert(1, "➕ Adicionar Livro")
            
            menu = st.radio("Menu", menu_options)
            
            st.markdown("---")
            if st.button("🚪 Sair"):
                st.session_state.login_status = False
                st.session_state.user_info = None
                st.session_state.editing = False
                st.session_state.editing_book = None
                st.rerun()
        
        # Conteúdo principal
        if menu == "📖 Listar Livros":
            listar_livros()
        elif menu == "➕ Adicionar Livro" and st.session_state.user_info['role'] == "admin":
            adicionar_livro()
        elif menu == "📊 Dashboard":
            dashboard()

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime
import json

# Cargar las credenciales desde el archivo secrets.toml
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="probate-streamlit")
dbNames = db.collection("movies")

# Carga todos los registros de Firestore, usaré cache para eficientar mi app
@st.cache_data(ttl=900)  # cache por 15 min (esto lo podemos cambiar segun requiramos)
def load_dataset():
    all_docs = dbNames.stream()
    all_data = [doc.to_dict() for doc in all_docs]
    return pd.DataFrame(all_data)
df_base = load_dataset()

#Encabezado
st.header("Netflix App")

#Agregar en el sidebar opción a mostrar todas las peliculas
agree = st.sidebar.checkbox("Mostrar todos los filmes")
if agree:
    st.dataframe(df_base)

#Función para cargar por título
def load_by_title(title):
  query = dbNames.where("name","==",title)
  docs = list(query.stream())
  return docs[0] if docs else None

#Buscar película
st.sidebar.subheader("Título de la película:")
title_search = st.sidebar.text_input("Ingrese filme")
btn_search = st.sidebar.button("Buscar")

if btn_search and title_search:
    results = df_base[df_base["name"].str.contains(title_search, case=False, na=False)]
    st.sidebar.write(f"{len(results)} filme(s) encontrado(s):")
    st.dataframe(results)

st.sidebar.markdown("____")

#Buscar películas por director
st.sidebar.subheader("Filtrar por director")

# Cargar nombres únicos de directores desde el DataFrame base
directores = df_base["director"].dropna().unique().tolist()
selected_director = st.sidebar.selectbox("Seleccione director", [""] + sorted(directores))

# Botón para filtrar por director
btn_filtrar = st.sidebar.button("Filtrar director")

if btn_filtrar and selected_director:
    filtered_df = df_base[df_base["director"] == selected_director]
    st.write(f"{len(filtered_df)} filme(s) encontrados del director: {selected_director}")
    st.dataframe(filtered_df)

st.sidebar.markdown("____")

# Formulario para registrar nueva película
st.sidebar.subheader("Registrar nueva película")

with st.sidebar.form("formulario_completo"):
    name = st.text_input("Título de la película") 
    director = st.text_input("Director")
    writer = st.text_input("Escritor")
    star = st.text_input("Protagonista")
    company = st.text_input("Compañía Productora")
    country = st.text_input("País")
    genre = st.text_input("Género")
    rating = st.text_input("Clasificación")
    released = st.date_input("Fecha de estreno (dd/mm/yy)", value=datetime.today())
    year = st.number_input("Año", min_value=1900, max_value=2100, step=1)
    runtime = st.number_input("Duración (min)", min_value=1)
    score = st.number_input("Puntuación IMDb", min_value=0.0, max_value=10.0, step=0.1)
    votes = st.number_input("Número de votos", min_value=0)
    budget = st.number_input("Presupuesto (USD)", min_value=0)
    gross = st.number_input("Recaudación (USD)", min_value=0)
    
    submit_button = st.form_submit_button("Insertar filme")

#  Lógica post-formulario
if submit_button:
    campos = [name, director, writer, star, company, country, genre, rating,
              released, year, runtime, score, votes, budget, gross]
    
    if all(campos):
        # Normalizamos el título de la película para que podamos validar que no se ingrese una película registrada previamente
        id_movie = name.strip().lower().replace(" ", "_")

        # Verificar si ya existe ese título
        existente = load_by_title(name)

        # Armamos el diccionario limpio
        movie_data = {
            "name": name,
            "director": director,
            "writer": writer,
            "star": star,
            "company": company,
            "country": country,
            "genre": genre,
            "rating": rating,
            "released": str(released),  # Los datos de firesbase están con string
            "year": int(year),
            "runtime": int(runtime),
            "score": float(score),
            "votes": int(votes),
            "budget": int(budget),
            "gross": int(gross)
        }


        if existente:
            st.warning(f"⚠️ El filme '{name}' ya existe. No se insertó duplicado. Por favor revisar la información")
        else:
            doc_ref = db.collection("movies").document(id_movie)
            doc_ref.set(movie_data)
            st.success(f"Filme '{name}' insertado correctamente con ID '{id_movie}'.")
    else:
        st.warning("😱 Por favor, completa todos los campos antes de insertar.")

# Clear cache button
st.sidebar.markdown("____") 
if st.sidebar.button("Limpiar todo"):
    st.cache_data.clear()
    st.rerun()

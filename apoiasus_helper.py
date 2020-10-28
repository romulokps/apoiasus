import pandas as pd
import unidecode
import streamlit as st
import numpy as np
from geopy.distance import geodesic

def normalize_city_name(df, column):
    df[column] = df[column].str.lower().str.replace("-"," ")
    df[column] = df[column].apply(lambda x : unidecode.unidecode(x))
    return df

@st.cache
def get_data():
    url ='https://sgtes.unasus.gov.br/apoiasus/login/listadevagas.asp'
    apoiasus_data = pd.read_html(url)[0] # Returns DataFrame of all tables on page
    apoiasus_data = normalize_city_name(apoiasus_data, "Município")

    cidades = pd.read_csv('https://github.com/romulokps/apoiasus/raw/master/populacaoBR2.csv',dtype={"ibgeID": str}, index_col=0)
    cidades = normalize_city_name(cidades, "cidade")

    df = pd.merge(apoiasus_data, cidades, left_on = ['UF','Município'], right_on = ['estado','cidade'], how="left")

    df.loc[81, ["ibgeID", "cidade", "estado", "pop"]] = cidades.loc[2341]

    lat_long = pd.read_csv("https://github.com/kelvins/Municipios-Brasileiros/raw/main/csv/municipios.csv", dtype={"codigo_ibge": str})
    lat_long.drop(columns = ["nome", "capital", "codigo_uf"], inplace = True)

    df = pd.merge(df, lat_long, left_on=["ibgeID"], right_on=["codigo_ibge"], how="inner")
    df.drop(columns = ["codigo_ibge", "cidade", "estado", "pop"], inplace=True)

    search_df = pd.merge(cidades, lat_long, left_on="ibgeID", right_on="codigo_ibge").drop(columns = ["pop", "codigo_ibge"])

    return df, search_df

def calc_distances(df, chosen_city):
    distances = {}
    chosen_city_coordinates = chosen_city[0][-2:] # pega as coordenadas da cidade escolhida
    for i in range(len(df)):
        ibge_id = df.loc[i]["ibgeID"] # usa o IBGE ID como chave no dicionário pra facilitar o merge depois
        city_coordinates = df.loc[i][-2:].values
        distances[ibge_id] = geodesic(city_coordinates, chosen_city_coordinates).km
    return distances

data, search_df = get_data()

st.title("Helper Brasil Conta Comigo")
st.sidebar.title("Filtros")
st.markdown("Essa é uma aplicação em desenvolvimento com o intuito de ajudar você a achar a cidade mais próxima com vagas no programa Brasil Conta Comigo. Aqui os dados estão sempre atualizados com os do [ApoiASUS](https://sgtes.unasus.gov.br/apoiasus/login/listadevagas.asp)")
st.sidebar.markdown("Aqui você pode filtrar melhor a distância máxima de sua cidade e sua profissão de interesse")

st.sidebar.title("Configurações")

# Pegando a distância aproximada entre as cidades
city = st.sidebar.text_input('Digite o nome da sua cidade')
state = st.sidebar.text_input('Digite a sigla de seu estado')

if city and state:
    city = city.lower()
    city = unidecode.unidecode(city)

    # retriving data from the chosen city
    res = search_df.loc[(search_df["estado"].str.lower() == state.lower()) & (search_df["cidade"] == city)].values


    # getting distance from each city to the city the user chose
    dists = calc_distances(data, res)
    dists_dataframe = pd.DataFrame(dists, index=[0]).T.reset_index()
    dists_dataframe.columns = ["ibgeID", "distancia"]

    # merging distances
    data = pd.merge(data, dists_dataframe, left_on = "ibgeID", right_on="ibgeID")

    # sorting values by distance
    data = data.sort_values(by="distancia")

# Escolhendo a profissão
select = st.sidebar.selectbox('Escolha a profissão de interesse', ["Medicina", "Enfermagem", "Farmácia", "Fisioterapia"])
data = data.loc[data[select] > 0]

# Escolhendo a distancia máxima
if city and state:
    chosen_dist = st.sidebar.slider("Selecione a distância máxima", int(data.distancia.min()), int(data.distancia.max()), 200)
    if chosen_dist:
        data = data.loc[data.distancia <= chosen_dist]

# longitude , latitude
st.title("Mapa com resultados")
st.map(data)

# Mostrando o dataframe
if st.sidebar.checkbox("Mostrar resultados"):
	st.title("Tabela com resultados")
	st.write(data[["UF", "Município", select, "ibgeID", "distancia"]])

st.title("Autores")
st.image(["imgs/Itamar.png", "imgs/Romulo.jpg"], caption=["Itamar Rocha, estudante de Engenharia da computação - UFPB", "Rômulo Kunrath, estudante de Medicina - UFPB"], width=300)

st.title("Contato")
st.markdown("Itamar : [linkedin](https://www.linkedin.com/in/itamarrocha/) , [Github](https://github.com/ItamarRocha/)")
st.markdown("Rômulo : [Email](mailto:romulokps@gmail.com) , [Github](https://github.com/romulokps)")
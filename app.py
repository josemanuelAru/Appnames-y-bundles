import io
import time
import urllib.parse
import pandas as pd
import requests
import streamlit as st

# Intentar importar el scraper de Google Play
try:
  from google_play_scraper import search
  HAS_PLAY_SCRAPER = True
except ImportError:
  HAS_PLAY_SCRAPER = False

st.set_page_config(
    page_title='App ID & Bundle Extractor', page_icon='📱', layout='wide'
)

st.title('📱 Extractor de Bundle ID & App ID (iOS & Android)')
st.write(
    'Obtén los identificadores oficiales de la **App Store (iOS)** y **Google'
    ' Play (Android)** escribiendo los nombres a mano o subiendo un archivo'
    ' CSV.'
)


# --- FUNCIONES DE BÚSQUEDA ---
def get_ios_info(app_name, country='US'):
  """Busca en la API oficial de iTunes."""
  clean_name = app_name.split('.com')[0] if '.com' in app_name else app_name
  encoded_name = urllib.parse.quote(clean_name)
  url = f'https://itunes.apple.com/search?term={encoded_name}&entity=software&country={country}&limit=1'

  try:
    response = requests.get(url, timeout=4)
    if response.status_code == 200:
      data = response.json()
      if data.get('resultCount', 0) > 0:
        res = data['results'][0]
        return res.get('bundleId', 'N/A'), str(res.get('trackId', 'N/A'))
  except Exception:
    pass
  return 'N/A', 'N/A'


def get_android_info(app_name, country='us'):
  """Busca en Google Play Store."""
  if not HAS_PLAY_SCRAPER:
    return 'Librería no instalada', 'Librería no instalada'

  clean_name = app_name.split('.com')[0] if '.com' in app_name else app_name
  try:
    results = search(clean_name, n_hits=1, lang='en', country=country)
    if results:
      app_pkg = results[0].get('appId', 'N/A')
      return app_pkg, app_pkg  # En Android Bundle ID y App ID son el mismo
  except Exception:
    pass
  return 'N/A', 'N/A'


def process_app_list(app_list, country_code):
  """Procesa una lista de nombres y muestra progreso."""
  results = []
  total = len(app_list)

  progress_bar = st.progress(0)
  status_text = st.empty()

  start_time = time.time()

  for idx, name in enumerate(app_list):
    name_clean = name.strip()
    if not name_clean:
      continue

    status_text.text(f'Buscando ({idx + 1}/{total}): {name_clean}')

    ios_bundle, ios_id = get_ios_info(name_clean, country=country_code)
    android_pkg, _ = get_android_info(name_clean, country=country_code.lower())

    results.append({
        'App Name': name_clean,
        'iOS Bundle ID': ios_bundle,
        'iOS App ID': ios_id,
        'Android Bundle / App ID': android_pkg,
    })

    progress_bar.progress((idx + 1) / total)
    time.sleep(0.05)

  status_text.success(
      f'¡Completado en {round(time.time() - start_time, 1)} segundos!'
  )
  return pd.DataFrame(results)


# --- CONFIGURACIÓN EN LA BARRA LATERAL ---
st.sidebar.header('⚙️ Configuración')
country_code = st.sidebar.text_input('Código de País (US, ES, FR, etc.):', 'US')

# --- MODO DE ENTRADA DE DATOS ---
tab1, tab2 = st.tabs(
    ['✍️ Escribir Lista a Mano', '📁 Subir Archivo CSV / Excel']
)

# OPCIÓN 1: Entrada manual por texto
with tab1:
  st.subheader('Introduce una lista de nombres (uno por línea):')
  default_text = """Block Blast
Vita Mahjong
Wordscapes
Spotify
TikTok"""
  user_text = st.text_area(
      'Nombres de las aplicaciones:', value=default_text, height=200
  )

  if st.button('🚀 Buscar Identificadores (Manual)'):
    app_names = [line for line in user_text.split('\n') if line.strip()]
    if app_names:
      df_results = process_app_list(app_names, country_code)
      st.dataframe(df_results, use_container_width=True)

      # Preparar descarga
      csv = df_results.to_csv(index=False).encode('utf-8')
      st.download_button(
          '📥 Descargar Resultados en CSV',
          data=csv,
          file_name='Apps_Identificadores.csv',
          mime='text/csv',
      )
    else:
      st.warning('Escribe al menos un nombre de aplicación.')

# OPCIÓN 2: Subir archivo
with tab2:
  skip_rows = st.number_input(
      'Filas a saltar en el CSV (metadatos):',
      min_value=0,
      max_value=20,
      value=8,
  )
  uploaded_file = st.file_uploader('Sube tu archivo CSV', type=['csv'])

  if uploaded_file is not None:
    try:
      df_upload = pd.read_csv(uploaded_file, skiprows=skip_rows)
      if 'App Name' in df_upload.columns:
        st.write(
            f'Vista previa del archivo ({len(df_upload)} aplicaciones'
            ' encontradas):'
        )
        st.dataframe(df_upload.head(3), use_container_width=True)

        if st.button('🚀 Procesar CSV Completo'):
          app_names = df_upload['App Name'].dropna().tolist()
          df_results = process_app_list(app_names, country_code)

          st.dataframe(df_results.head(10), use_container_width=True)

          csv = df_results.to_csv(index=False).encode('utf-8')
          st.download_button(
              '📥 Descargar CSV Enriquecido',
              data=csv,
              file_name='CSV_Apps_Enriquecido.csv',
              mime='text/csv',
          )
      else:
        st.error("El archivo no tiene una columna llamada 'App Name'.")
    except Exception as e:
      st.error(f'Error al leer el archivo: {e}')

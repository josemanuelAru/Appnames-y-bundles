import io
import time
import urllib.parse
import pandas as pd
import requests
import streamlit as st

# Intentar cargar la librería de Android
try:
  from google_play_scraper import search

  HAS_PLAY_SCRAPER = True
except ImportError:
  HAS_PLAY_SCRAPER = False

st.set_page_config(
    page_title='App ID & Bundle Extractor', page_icon='📱', layout='centered'
)

st.title('📱 Extractor de Bundle ID & App ID')
st.write(
    'Selecciona el sistema operativo, introduce las aplicaciones y obtén sus'
    ' identificadores.'
)


# --- FUNCIONES DE BÚSQUEDA ---
def get_ios_info(app_name):
  """Busca en la API de Apple (US por defecto)."""
  clean_name = app_name.split('.com')[0] if '.com' in app_name else app_name
  encoded_name = urllib.parse.quote(clean_name)
  url = f'https://itunes.apple.com/search?term={encoded_name}&entity=software&limit=1'

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


def get_android_info(app_name):
  """Busca en Google Play Store."""
  if not HAS_PLAY_SCRAPER:
    return 'Librería no instalada', 'Librería no instalada'

  clean_name = app_name.split('.com')[0] if '.com' in app_name else app_name
  try:
    results = search(clean_name, n_hits=1, lang='en', country='us')
    if results:
      app_pkg = results[0].get('appId', 'N/A')
      return app_pkg, app_pkg
  except Exception:
    pass
  return 'N/A', 'N/A'


def process_app_list(app_list, target_os):
  """Procesa la lista según el OS seleccionado."""
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

    row_data = {'App Name': name_clean}

    # Búsqueda condicional según la selección del usuario
    if target_os in ['iOS', 'Ambos']:
      ios_bundle, ios_id = get_ios_info(name_clean)
      # Cambio de nombre de la columna aquí
      row_data['iOS Bundle ID (ID para android)'] = ios_bundle
      row_data['iOS App ID'] = ios_id

    if target_os in ['Android', 'Ambos']:
      android_pkg, _ = get_android_info(name_clean)
      row_data['Android Bundle / App ID'] = android_pkg

    results.append(row_data)

    progress_bar.progress((idx + 1) / total)
    time.sleep(0.04)

  status_text.success(
      f'¡Completado en {round(time.time() - start_time, 1)} segundos!'
  )
  return pd.DataFrame(results)


# --- SELECTOR DE SISTEMA OPERATIVO ---
selected_os = st.radio(
    '1. Selecciona el Sistema Operativo:',
    options=['iOS', 'Android', 'Ambos'],
    horizontal=True,
)

# Advertencia si falta la librería de Android y se ha seleccionado Android
if selected_os in ['Android', 'Ambos'] and not HAS_PLAY_SCRAPER:
  st.warning(
      '⚠️ La librería `google-play-scraper` no está instalada. Ejecuta `pip'
      ' install google-play-scraper` en tu terminal o añádela a'
      ' `requirements.txt`.'
  )

st.write('---')

# --- ENTRADA DE DATOS ---
tab1, tab2 = st.tabs(
    ['✍️ Escribir Lista a Mano', '📁 Subir Archivo CSV / Excel']
)

# TAB 1: Entrada manual
with tab1:
  default_text = """Block Blast
Vita Mahjong
Wordscapes
Spotify
TikTok"""
  user_text = st.text_area(
      '2. Nombres de las aplicaciones (uno por línea):',
      value=default_text,
      height=180,
  )

  if st.button('🚀 Buscar Identificadores'):
    app_names = [line for line in user_text.split('\n') if line.strip()]
    if app_names:
      df_results = process_app_list(app_names, selected_os)
      st.dataframe(df_results, use_container_width=True)

      csv = df_results.to_csv(index=False).encode('utf-8')
      st.download_button(
          '📥 Descargar CSV',
          data=csv,
          file_name='Apps_Identificadores.csv',
          mime='text/csv',
      )
    else:
      st.warning('Escribe al menos un nombre.')

# TAB 2: Subida de CSV
with tab2:
  uploaded_file = st.file_uploader('2. Sube tu archivo CSV', type=['csv'])

  if uploaded_file is not None:
    try:
      # Leer CSV intentando detectar automáticamente encabezados
      df_upload = pd.read_csv(uploaded_file)

      # Si 'App Name' no está en la primera fila, buscar en las siguientes
      if 'App Name' not in df_upload.columns:
        # Intentar saltar hasta 8 filas por si es un reporte con metadatos
        for skip in range(1, 10):
          uploaded_file.seek(0)
          temp_df = pd.read_csv(uploaded_file, skiprows=skip)
          if 'App Name' in temp_df.columns:
            df_upload = temp_df
            break

      if 'App Name' in df_upload.columns:
        st.write(f'Apps encontradas en el archivo: **{len(df_upload)}**')

        if st.button('🚀 Procesar CSV'):
          app_names = df_upload['App Name'].dropna().tolist()
          df_results = process_app_list(app_names, selected_os)

          st.dataframe(df_results, use_container_width=True)

          csv = df_results.to_csv(index=False).encode('utf-8')
          st.download_button(
              '📥 Descargar CSV Enriquecido',
              data=csv,
              file_name='CSV_Apps_Enriquecido.csv',
              mime='text/csv',
          )
      else:
        st.error("No se encontró la columna 'App Name' en el CSV.")
    except Exception as e:
      st.error(f'Error al leer el archivo: {e}')

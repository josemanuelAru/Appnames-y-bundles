import io
import os
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
    page_title='App ID & Bundle Extractor', page_icon='📱', layout='wide'
)

st.title('📱 Extractor de Bundle ID & App ID')
st.write(
    'Busca identificadores de aplicaciones manualmente o extrae los datos '
    'directamente desde tu Biblioteca de Apps.'
)

# --- FUNCIONES DE BÚSQUEDA ---
def get_ios_info(app_name, country_code='US'):
  """Busca en la API de Apple y añade 'id' al inicio del iOS App ID."""
  clean_name = app_name.split('.com')[0] if '.com' in app_name else app_name
  encoded_name = urllib.parse.quote(clean_name)
  url = f'https://itunes.apple.com/search?term={encoded_name}&entity=software&country={country_code}&limit=1'

  try:
    response = requests.get(url, timeout=4)
    if response.status_code == 200:
      data = response.json()
      if data.get('resultCount', 0) > 0:
        res = data['results'][0]
        track_id = res.get('trackId')
        # Formatear añadiendo 'id' al inicio
        ios_id = f"id{track_id}" if track_id else "N/A"
        return res.get('bundleId', 'N/A'), ios_id
  except Exception:
    pass
  return 'N/A', 'N/A'


def get_android_info(app_name, country_code='us'):
  """Busca en Google Play Store."""
  if not HAS_PLAY_SCRAPER:
    return 'Librería no instalada'

  clean_name = app_name.split('.com')[0] if '.com' in app_name else app_name
  try:
    results = search(clean_name, n_hits=1, lang='en', country=country_code.lower())
    if results:
      return results[0].get('appId', 'N/A')
  except Exception:
    pass
  return 'N/A'


def process_app_list(df_apps, target_os='Ambos', country_code='US'):
  """Procesa una lista de apps (DataFrame) y busca sus identificadores."""
  results = []
  total = len(df_apps)

  progress_bar = st.progress(0)
  status_text = st.empty()
  start_time = time.time()

  for idx, row in df_apps.iterrows():
    name_clean = str(row['App Name']).strip()
    
    # Mantener el tráfico si viene del CSV
    auctions = row.get('Auctions', None)
    
    status_text.text(f'Buscando ({idx + 1}/{total}): {name_clean}')

    row_data = {'App Name': name_clean}
    if auctions is not None:
        row_data['Auctions (Tráfico)'] = auctions

    # Búsqueda según el OS seleccionado
    if target_os in ['iOS', 'Ambos']:
      ios_bundle, ios_id = get_ios_info(name_clean, country_code)
      row_data['Android App ID'] = ios_bundle  # Bundle ID de iOS
      row_data['iOS App ID'] = ios_id          # Ahora con 'id' delante (ej. id306310789)

    if target_os in ['Android', 'Ambos']:
      android_pkg = get_android_info(name_clean, country_code)
      row_data['Android Bundle / App ID'] = android_pkg

    results.append(row_data)

    progress_bar.progress((idx + 1) / total)
    time.sleep(0.04)

  status_text.success(
      f'¡Completado en {round(time.time() - start_time, 1)} segundos!'
  )
  return pd.DataFrame(results)


# --- ADVERTENCIA LIBRERÍA ANDROID ---
if not HAS_PLAY_SCRAPER:
  st.warning(
      '⚠️ La librería `google-play-scraper` no está instalada. Ejecuta `pip '
      'install google-play-scraper` o añádela a tu `requirements.txt`.'
  )

st.write('---')

# --- PESTAÑAS DE LA APP ---
tab1, tab2 = st.tabs(["✍️ Búsqueda Manual", "📁 Biblioteca de Apps"])

# ==========================================
# PESTAÑA 1: BÚSQUEDA MANUAL
# ==========================================
with tab1:
  st.subheader("Búsqueda Manual de Identificadores")
  
  manual_os = st.selectbox('Sistema Operativo:', ['iOS', 'Android', 'Ambos'], key='manual_os')
      
  default_text = "Block Blast\nVita Mahjong\nWordscapes\nSpotify"
  user_text = st.text_area('Nombres de las aplicaciones (uno por línea):', value=default_text, height=180)

  if st.button('🚀 Buscar Identificadores'):
    app_names = [line for line in user_text.split('\n') if line.strip()]
    if app_names:
      df_manual = pd.DataFrame({'App Name': app_names})
      df_results = process_app_list(df_manual, manual_os, 'US')
      
      st.dataframe(df_results, use_container_width=True)
      csv = df_results.to_csv(index=False).encode('utf-8')
      st.download_button('📥 Descargar CSV', data=csv, file_name='Apps_Manual.csv', mime='text/csv')
    else:
      st.warning('Escribe al menos un nombre.')


# ==========================================
# PESTAÑA 2: BIBLIOTECA DE APPS (FILTRO POR PAÍS Y OS)
# ==========================================
with tab2:
  st.subheader("Extraer Top Apps por País y Sistema Operativo")
  
  data_dir = 'data'
  files_in_dir = []
  if os.path.exists(data_dir):
      files_in_dir = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

  if not files_in_dir:
      st.info("📂 No se han encontrado archivos CSV en la carpeta `data/`.")
  else:
      # Analizar los archivos existentes para extraer países y OSs disponibles
      available_countries = set()
      available_os = set()

      for filename in files_in_dir:
          name_no_ext = filename.replace('.csv', '')
          if '-' in name_no_ext:
              parts = name_no_ext.split('-', 1)
              available_countries.add(parts[0].upper())
              available_os.add(parts[1])
          else:
              available_countries.add(name_no_ext.upper())

      col1_b, col2_b = st.columns(2)
      with col1_b:
          selected_country = st.selectbox(
              '1. Selecciona el País:', 
              options=sorted(list(available_countries)) if available_countries else ['US']
          )
      with col2_b:
          selected_os = st.selectbox(
              '2. Selecciona el Sistema Operativo:', 
              options=sorted(list(available_os)) if available_os else ['iOS', 'Android']
          )

      # Construir el nombre del archivo esperado (ej. "US-iOS.csv")
      target_filename = f"{selected_country}-{selected_os}.csv"
      
      # Buscar el archivo de forma insensible a mayúsculas/minúsculas
      actual_filename = None
      for f in files_in_dir:
          if f.lower() == target_filename.lower():
              actual_filename = f
              break

      if not actual_filename:
          st.warning(f"⚠️ No existe el archivo `{target_filename}` en la carpeta `data/`.")
      else:
          file_path = os.path.join(data_dir, actual_filename)
          
          try:
              # Detectar en qué línea empieza "App Name" para saltar cabeceras
              skip_idx = 0
              with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                  for i, line in enumerate(f):
                      if line.startswith('App Name'):
                          skip_idx = i
                          break

              df_file = pd.read_csv(file_path, skiprows=skip_idx)

              if 'App Name' in df_file.columns:
                  # Ordenar por tráfico (Auctions)
                  if 'Auctions' in df_file.columns:
                      df_file['Auctions'] = pd.to_numeric(df_file['Auctions'], errors='coerce')
                      df_file = df_file.sort_values(by='Auctions', ascending=False).dropna(subset=['App Name'])

                  total_apps = len(df_file)

                  top_limit = st.slider(
                      '3. ¿Cuántas aplicaciones del Top quieres procesar?',
                      min_value=5, 
                      max_value=min(500, total_apps) if total_apps > 0 else 100, 
                      value=min(30, total_apps), 
                      step=5
                  )

                  df_top = df_file.head(top_limit).copy()

                  st.write(f"**Vista previa de las Top {top_limit} apps (de {total_apps} totales en {actual_filename}):**")
                  preview_cols = ['App Name', 'Auctions'] if 'Auctions' in df_top.columns else ['App Name']
                  st.dataframe(df_top[preview_cols], use_container_width=True)

                  if st.button(f'🚀 Obtener Identificadores para el Top {top_limit}'):
                      df_results = process_app_list(
                          df_top, 
                          target_os=selected_os, 
                          country_code=selected_country
                      )

                      st.subheader('Resultados:')
                      st.dataframe(df_results, use_container_width=True)

                      csv = df_results.to_csv(index=False).encode('utf-8')
                      st.download_button(
                          '📥 Descargar Tabla Final en CSV',
                          data=csv,
                          file_name=f'Top_{top_limit}_{selected_country}_{selected_os}.csv',
                          mime='text/csv'
                      )
              else:
                  st.error(f"No se encontró la columna 'App Name' en `{actual_filename}`.")

          except Exception as e:
              st.error(f"Error al procesar el archivo `{actual_filename}`: {e}")

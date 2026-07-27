import io
import time
import urllib.parse
import pandas as pd
import requests
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title='Enriquecedor de Apps (iTunes API)',
    page_icon='📲',
    layout='centered',
)

st.title('📲 Enriquecedor de App Names')
st.write(
    'Sube tu archivo CSV con nombres de aplicaciones para obtener sus **Bundle'
    ' IDs** e **iOS App IDs** automáticamente mediante la API de iTunes.'
)


# Función para consultar la API de Apple
def fetch_app_info(app_name, country='US'):
  clean_name = app_name.split('.com')[0] if '.com' in app_name else app_name
  encoded_name = urllib.parse.quote(clean_name)
  url = f'https://itunes.apple.com/search?term={encoded_name}&entity=software&country={country}&limit=1'

  try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      data = response.json()
      if data.get('resultCount', 0) > 0:
        res = data['results'][0]
        return res.get('bundleId', 'N/A'), str(res.get('trackId', 'N/A'))
  except Exception:
    pass
  return 'N/A', 'N/A'


# 1. Configuración del País en la barra lateral
st.sidebar.header('⚙️ Configuración')
country_code = st.sidebar.text_input(
    'Código de País para iTunes (ej: US, ES, FR):', 'US'
)
skip_rows = st.sidebar.number_input(
    'Filas a saltar en el CSV (encabezados/metadatos):',
    min_value=0,
    max_value=20,
    value=8,
)

# 2. Componente para subir el archivo CSV
uploaded_file = st.file_uploader('Sube tu archivo CSV', type=['csv'])

if uploaded_file is not None:
  try:
    # Cargar el CSV subido por el usuario
    df = pd.read_csv(uploaded_file, skiprows=skip_rows)

    st.success(f' Archivo cargado correctamente: **{len(df)} filas** encontradas.')

    # Verificar si existe la columna App Name
    if 'App Name' not in df.columns:
      st.error(
          "El CSV no contiene una columna llamada exactas mente '**App Name**'."
          ' Por favor revisa las filas a saltar en la barra lateral.'
      )
      st.write('Columnas detectadas:', list(df.columns))
    else:
      # Mostrar vista previa
      st.subheader('Vista previa de los datos:')
      st.dataframe(df.head(5), use_container_width=True)

      # Botón para iniciar el proceso
      if st.button('🚀 Procesar y obtener Bundle IDs'):
        bundle_ids = []
        app_ids = []

        total_rows = len(df)

        # Crear barra de progreso e indicadores visuales
        progress_bar = st.progress(0)
        status_text = st.empty()

        start_time = time.time()

        for idx, row in df.iterrows():
          app_name = str(row['App Name'])
          bundle_id, app_id = fetch_app_info(app_name, country=country_code)

          bundle_ids.append(bundle_id)
          app_ids.append(app_id)

          # Actualizar barra de progreso cada fila
          current_progress = (idx + 1) / total_rows
          progress_bar.progress(current_progress)
          status_text.text(
              f'Procesando app {idx + 1} de {total_rows}: {app_name}'
          )

          # Pequeña pausa para evitar bloqueos por rate-limit
          time.sleep(0.03)

        # Asignar nuevas columnas
        df['Bundle ID'] = bundle_ids
        df['iOS App ID'] = app_ids

        status_text.success(
            f'¡Proceso completado en {round(time.time() - start_time, 1)}'
            ' segundos!'
        )

        # Mostrar resultado final
        st.subheader('Resultados enriquecidos:')
        st.dataframe(
            df[['App Name', 'Bundle ID', 'iOS App ID']].head(10),
            use_container_width=True,
        )

        # Convertir dataframe a CSV en memoria para la descarga
        output = io.BytesIO()
        df.to_csv(output, index=False)
        processed_data = output.getvalue()

        # Botón de descarga
        st.download_button(
            label='📥 Descargar CSV Enriquecido',
            data=processed_data,
            file_name='Apps_Enriquecidas.csv',
            mime='text/csv',
        )

  except Exception as e:
    st.error(f'Error al leer el archivo CSV: {e}')

import pandas as pd
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title='Mi Primera App en Streamlit',
    page_icon='🚀',
    layout='wide',
)

# 2. Título y descripción
st.title('🚀 Mi Primera Aplicación Web con Streamlit')
st.write(
    '¡Hola! Esta aplicación está alojada gratuitamente en Streamlit Cloud'
    ' mediante GitHub.'
)

# 3. Barra lateral (Sidebar)
st.sidebar.header('⚙️ Configuración')
nombre_usuario = st.sidebar.text_input('¿Cómo te llamas?', 'Visitante')
categoria = st.sidebar.selectbox(
    'Selecciona una categoría:', ['Opción A', 'Opción B', 'Opción C']
)

# 4. Mensaje personalizado
st.success(f'¡Bienvenido/a, **{nombre_usuario}**!')

# 5. Sección de métricas interactivas
st.subheader('📊 Panel de Métricas')
col1, col2, col3 = st.columns(3)
col1.metric(label='Usuarios Activos', value='1,234', delta='12%')
col2.metric(label='Ventas del Mes', value='$12,450', delta='-3%')
col3.metric(label='Categoría Seleccionada', value=categoria)

# 6. Datos de ejemplo y gráfico
st.subheader('📈 Datos de Ejemplo')

data = {
    'Mes': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo'],
    'Ventas': [10, 25, 18, 40, 32],
    'Clientes': [5, 12, 10, 20, 18],
}
df = pd.DataFrame(data)

# Mostrar tabla y gráfico en dos columnas
col_tabla, col_grafico = st.columns([1, 2])

with col_tabla:
  st.write('**Tabla de Datos:**')
  st.dataframe(df, use_container_width=True)

with col_grafico:
  st.write('**Gráfico de Tendencia:**')
  st.line_chart(df.set_index('Mes'))

# 7. Botón interactivo
if st.button('🎉 ¡Haz clic aquí para una sorpresa!'):
  st.balloons()

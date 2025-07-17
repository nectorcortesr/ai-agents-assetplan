import streamlit as st
import requests
import json
import os

# Configuración de la página
st.set_page_config(page_title="Assetplan Agent", page_icon="🏠", layout="wide")

# Título y descripción
st.title("🏠 Assetplan Agent")
st.markdown("Consulta propiedades disponibles en Assetplan.cl y revisa cambios de precios.")

# URL de la API (puede ser configurada por variable de entorno)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Función para consultar la API
def query_api(endpoint, payload=None):
    try:
        if endpoint == "/ask" and payload:
            response = requests.post(f"{API_URL}{endpoint}", json=payload)
        else:
            response = requests.get(f"{API_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Error al conectar con la API: {str(e)}"}

# Sección para hacer preguntas
st.header("Hacer una pregunta")
query = st.text_input("Ingresa tu consulta (ej. 'Departamentos de 2 dormitorios en Providencia bajo 3 000 UF')")
if st.button("Enviar consulta"):
    if query:
        with st.spinner("Procesando..."):
            result = query_api("/ask", {"query": query})
            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader("Respuesta")
                st.write(result["answer"])
                st.subheader("Fuentes")
                for i, url in enumerate(result.get("urls", []), 1):
                    st.markdown(f"[{i}] [Ver propiedad]({url})")
                st.write(f"**Confianza**: {result.get('confidence', 'N/A')}")
    else:
        st.warning("Por favor, ingresa una consulta.")

# Sección para ver cambios de precios
st.header("Cambios de precios")
if st.button("Ver últimos cambios"):
    with st.spinner("Cargando cambios..."):
        result = query_api("/changes")
        if "error" in result:
            st.error(result["error"])
        else:
            changes = result.get("changes", [])
            if not changes:
                st.info(result.get("message", "No se encontraron cambios."))
            else:
                st.subheader("Cambios detectados")
                for change in changes:
                    st.markdown(f"""
                    - **Propiedad**: {change['title']} ({change['location']})
                    - **URL**: [Ver propiedad]({change['url']})
                    - **Cambio**: Precio anterior: {change['old_price']} → Nuevo precio: {change['new_price']}
                    - **Fecha**: {change['timestamp']}
                    """)
                st.write(f"**Total**: {result.get('message', 'N/A')}")

# Nota al pie
st.markdown("---")
st.markdown("Desarrollado con ❤️ por Nector Cortés. Datos obtenidos de assetplan.cl.")

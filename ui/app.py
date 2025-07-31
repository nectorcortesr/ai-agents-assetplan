import streamlit as st
import requests
import os

st.set_page_config(page_title="SQM Agente", page_icon="🤖", layout="wide")

# 🎯 Encabezado fijo que no se pierde en el scroll
st.markdown("""
<div style="
    position: fixed;
    top: 60px;
    left: 50%;
    transform: translateX(-50%);
    width: 95%;
    background-color: #0e1117;
    padding: 15px 10px;
    border-bottom: 2px solid #444;
    text-align: center;
    z-index: 999;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    border-radius: 0 0 10px 10px;
">
    <h2 style="color: white; margin: 0; font-size: 40px;">🤖 Agente SQM</h2>
    <p style="color: white; font-weight: bold; margin: 5px 0 0 0; font-size: 20px;">
        Consulta sobre el Manual NPT3 Coya Sur
    </p>
</div>

<!-- Espaciador para compensar el header fijo -->
<div style="height: 120px;"></div>
""", unsafe_allow_html=True)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Inicializa historial si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Contenedor para el historial
chat_placeholder = st.container()
# Contenedor para la interacción actual
response_placeholder = st.container()

# Mostrar historial (hasta antes de la nueva consulta)
with chat_placeholder:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

# Entrada del usuario
user_input = st.chat_input("Escribe tu consulta aquí...")

if user_input:
    # Agrega mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Mostrar inmediatamente la nueva pregunta en el historial
    with chat_placeholder:
        st.chat_message("user").write(user_input)
    
    # Construye historial anterior (solo preguntas, sin la nueva)
    history = [m["content"] for m in st.session_state.messages if m["role"] == "user"][:-1]

    # Usar el contenedor de respuesta para el spinner y la respuesta
    with response_placeholder:
        with st.spinner("Consultando..."):
            try:
                response = requests.post(f"{API_URL}/ask", json={"query": user_input, "history": history})
                response.raise_for_status()
                answer = response.json().get("answer", "Sin respuesta.")
            except Exception as e:
                answer = f"⚠️ Error al consultar la API: {str(e)}"

        # Agrega y muestra respuesta del asistente
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)
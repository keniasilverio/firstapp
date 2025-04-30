import streamlit as st

st.title("Meu Primeiro App com Streamlit 🎉")

st.write("Olá! this is your first project did with Helianthus.🌻")

nome = st.text_input("whats the name of your project?")

if nome:
    st.write(f"Olá, {nome}! So lets start... 🌻")

if st.button("click here"):
    st.write("Você clicou no botão! 🚀")

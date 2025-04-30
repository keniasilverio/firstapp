import streamlit as st

st.title("Meu Primeiro App com Streamlit 🎉")

st.write("Olá! Este é um app simples feito com Streamlit.")

nome = st.text_input("Qual o seu nome?")

if nome:
    st.write(f"Olá, {nome}! Seja bem-vinda ao seu primeiro app. 🌻")

if st.button("Clique aqui"):
    st.write("Você clicou no botão! 🚀")

"""Valida Streamlit. Nao e um RAG e nao consulta documentos."""
import streamlit as st

st.set_page_config(page_title='Laboratorio RAG local', page_icon='📚')
st.title('Laboratorio didatico: RAG local')
st.info('Interface de verificacao: o mecanismo RAG sera implementado nas proximas aulas.')
pergunta = st.text_input('Escreva uma pergunta de exemplo:', 'O que e recuperacao de informacao?')
if st.button('Verificar interface'):
    st.success(f'Interface pronta. Pergunta recebida: {pergunta}')

import streamlit as st

def home_screen():
    st.header("Home Page")

    col1,col2=st.columns(2)

    with col1:
            if st.button("Teacher Portal"):
                st.session_state['login_type']='teacher'
                st.rerun()
    with col2:
            if st.button("student portal"):
                  st.session_state['login_type']='student'
                  st.rerun()
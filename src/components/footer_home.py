import streamlit as st

def footer_home():

    st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-top:8px">
            <p style='text-align:center; color:#E0E3FF'>Made with ❤️ by Shubh</p>
        </div>   
                
                """, unsafe_allow_html=True)
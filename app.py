import streamlit as st
import requests
import random
import string
import re
import json

class MailTM:
    def __init__(self):
        self.base = "https://api.mail.tm"
        self.session = requests.Session()
        self.token = None
        self.address = None
        self.password = self._gen_password()
        self._register_account()

    def _gen_username(self):
        return "ceci" + ''.join(random.choices(string.digits, k=4))

    def _gen_password(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    def _get_domain(self):
        r = self.session.get(self.base + "/domains")
        return r.json()["hydra:member"][0]["domain"]

    def _register_account(self):
        domain = self._get_domain()
        username = self._gen_username()
        self.address = f"{username}@{domain}"
        self.session.post(self.base + "/accounts", json={"address": self.address, "password": self.password})
        r = self.session.post(self.base + "/token", json={"address": self.address, "password": self.password})
        self.token = r.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def get_email(self):
        return self.address

    def get_messages(self):
        r = self.session.get(self.base + "/messages")
        return r.json().get("hydra:member", [])

    def read_message(self, msg_id):
        r = self.session.get(self.base + f"/messages/{msg_id}")
        return r.json()

def limpiar_html(html):
    return re.sub('<[^<]+?>', '', html)

st.set_page_config(page_title="Correos Ceci", layout="centered")
st.title("Correos fáciles para Ceci")

if "mailtm" not in st.session_state:
    st.session_state.mailtm = MailTM()

if st.button("Crear nuevo correo"):
    st.session_state.mailtm = MailTM()

correo = st.session_state.mailtm.get_email()
st.success(f"Correo actual: **{correo}**")

if st.button("Revisar bandeja de entrada"):
    msgs = st.session_state.mailtm.get_messages()
    if not msgs:
        st.info("No hay mensajes nuevos.")
    for msg in msgs:
        st.markdown(f"**De:** {msg['from']['address']}")
        st.markdown(f"**Asunto:** {msg['subject']}")
        if st.button(f"Leer mensaje ID: {msg['id']}", key=msg['id']):
            try:
                contenido = st.session_state.mailtm.read_message(msg["id"])
                texto = contenido.get("text", "")
                html = contenido.get("html", "")
                intro = contenido.get("intro", "")

                if texto:
                    st.text_area("Mensaje (texto)", texto, height=200)
                elif html:
                    limpio = limpiar_html(html)
                    st.text_area("Mensaje (HTML limpio)", limpio.strip(), height=300)
                elif intro:
                    st.text_area("Mensaje (intro)", intro.strip(), height=150)
                else:
                    st.warning("Mensaje vacío. Mostrando JSON completo:")
                    st.code(json.dumps(contenido, indent=2))

            except Exception as e:
                st.error(f"Error al leer el mensaje: {e}")

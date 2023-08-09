import streamlit as st
import tarfile
import os
import subprocess
import yaml

UPLOAD_FOLDER = 'upload'
EXTRACT_FOLDER = 'extract'
SUMMARY_FOLDER = 'summary'

if 'hotsos_text' not in st.session_state:
        st.session_state['hotsos_text'] = ""

if 'hotgpt_text' not in st.session_state:
        st.session_state['hotgpt_text'] = ""

st.set_page_config(page_title="HotGPT demo", page_icon=":robot:", layout="wide")

def button_hotsos():
    summary_file = st.session_state['summary_file']
    with open(summary_file, 'r') as file:
        result = yaml.safe_load(file)
        output = str(result['kernel']['potential-issues']['KernelErrors']).lstrip('[\'').rstrip('\']').split('LLM PROMPT')[0]
        st.session_state['hotsos_text'] = output

def button_hotgpt():
    summary_file = st.session_state['summary_file']
    with open(summary_file, 'r') as file:
        result = yaml.safe_load(file)
        prompt = str(result['kernel']['potential-issues']['KernelErrors']).lstrip('[\'').rstrip('\']').split('LLM PROMPT')[1]
        st.session_state['hotgpt_text'] = prompt

col1, col2, col3 = st.columns((3,3,3))
with col1:
    uploaded_file = st.file_uploader(label="Upload sosreport", type="tar.xz")
    if uploaded_file is not None:
        sosreport_name, ext = os.path.splitext(uploaded_file.name)
        sosreport_name, ext = os.path.splitext(sosreport_name)
        sosreport_path = UPLOAD_FOLDER + '/' + uploaded_file.name
        extract_path = EXTRACT_FOLDER + '/' + sosreport_name
        summary_path = SUMMARY_FOLDER + '/' + sosreport_name
        summary_file = summary_path + '/' + sosreport_name + '.summary.yaml'

        st.session_state['sosreport_name'] = sosreport_name
        st.session_state['sosreport_path'] = sosreport_path
        st.session_state['extract_path'] = extract_path
        st.session_state['summary_path'] = summary_path
        st.session_state['summary_file'] = summary_file

        if not os.path.exists(UPLOAD_FOLDER):
            os.mkdir(UPLOAD_FOLDER)
        if not os.path.exists(EXTRACT_FOLDER):
            os.mkdir(EXTRACT_FOLDER)
        if not os.path.exists(SUMMARY_FOLDER):
            os.mkdir(SUMMARY_FOLDER)

        if not os.path.exists(sosreport_path):
            with open(sosreport_path, "wb") as f:
                f.write(uploaded_file.getvalue())

        if not os.path.exists(extract_path):
            tar = tarfile.open(sosreport_path, "r:xz")
            tar.extractall(EXTRACT_FOLDER)

        if not os.path.exists(summary_file):
            subprocess.call("hotsos --kernel --short -s --output-path " + summary_path + " " + extract_path, shell=True)

st.write("")
st.write("")
st.button('Ask HotSOS', on_click = button_hotsos)
hotsos_text = st.text_area("", key = 'hotsos_text')

st.write("")
st.write("")
st.write("")
st.write("")
st.button('Ask HotGPT', on_click = button_hotgpt)
hotgpt_text = st.text_area("", key = 'hotgpt_text')
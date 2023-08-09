import streamlit as st
import tarfile
import os
import subprocess
import yaml
from keys import OPENAI_API_KEY
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.2, max_tokens=2000)
KERNEL_TEMPLATE = """You are a kernel expert. Given the kernel calltraces, your job is to go through the calltraces and explain every line in detail
and then analyze the calltraces, list steps how to debug and possible solutions in bullet format.
        Calltraces: {text}
        Answer:
"""

UPLOAD_FOLDER = 'upload'
EXTRACT_FOLDER = 'extract'
SUMMARY_FOLDER = 'summary'

if 'output_text' not in st.session_state:
        st.session_state['output_text'] = ""

st.set_page_config(page_title="HotGPT demo", page_icon=":robot:", layout="wide")

def button_hotsos():
    summary_file = st.session_state['summary_file']
    with open(summary_file, 'r') as file:
        result = yaml.safe_load(file)
        output = str(result['kernel']['potential-issues']['KernelErrors']).lstrip('[\'').rstrip('\']').split('LLM_PROMPT')[0]
        st.session_state['output_text'] = output

def button_hotgpt():
    summary_file = st.session_state['summary_file']
    with open(summary_file, 'r') as file:
        result = yaml.safe_load(file)
        calltrace = str(result['kernel']['potential-issues']['KernelErrors']).lstrip('[\'').rstrip('\']').split('LLM_PROMPT')[1].rstrip('(origin=kernel.auto_scenario_check)')
        st.session_state['output_text'] = 'thinking...'
        prompt_template = PromptTemplate(input_variables=["text"], template=KERNEL_TEMPLATE)
        answer_chain = LLMChain(llm=llm, prompt=prompt_template)
        answer = answer_chain.run(calltrace)
        st.session_state['output_text'] = answer


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
                print('upload sosreport')
                f.write(uploaded_file.getvalue())

        if not os.path.exists(extract_path):
            print('extract sosreport')
            tar = tarfile.open(sosreport_path, "r:xz")
            tar.extractall(EXTRACT_FOLDER)

        if not os.path.exists(summary_file):
            print('run hotsos')
            subprocess.call("hotsos --kernel --short -s --output-path " + summary_path + " " + extract_path, shell=True)

btn1, btn2, btn3 = st.columns((3,3,8))
with btn1:
    st.button('Ask HotSOS', on_click = button_hotsos)

with btn2:
    st.button('Ask HotGPT', on_click = button_hotgpt)

st.text_area("", height = 500, key = 'output_text')

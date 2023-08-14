import streamlit as st
import tarfile
import os
import subprocess
import yaml
import time
from keys import OPENAI_API_KEY
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.5, max_tokens=2000)
KERNEL_TEMPLATE = """You are a kernel expert. Given the kernel calltraces, your job is to go through the calltraces, print each calltrace in bullet format and add a detail explanation in different words to the tail of each calltrace
and then analyze the calltraces and list possible debug steps, and then list all possible solutions in bullet format.
        Calltraces: {text}
        Answer:
"""

UPLOAD_FOLDER = 'upload'
EXTRACT_FOLDER = 'extract'
SUMMARY_FOLDER = 'summary'

if 'result_text' not in st.session_state:
        st.session_state['result_text'] = ""
if 'log_text' not in st.session_state:
        st.session_state['log_text'] = ""

st.set_page_config(page_title="HotGPT demo", page_icon=":robot:", layout="wide")

def button_hotsos():
    summary_file = st.session_state['summary_file']
    with open(summary_file, 'r') as file:
        result = yaml.safe_load(file)
        output = str(result['kernel']['potential-issues']['KernelErrors']).lstrip('[\'').rstrip('\']').split('LLM_PROMPT')[0]
        calltrace = str(result['kernel']['potential-issues']['KernelErrors']).lstrip('[\'').rstrip('\']').split('LLM_PROMPT')[1].rstrip('(origin=kernel.auto_scenario_check)')
        calltrace = calltrace.replace('\\n', '\n')
        st.session_state['result_text'] = output
        st.session_state['log_text'] = calltrace

def button_hotgpt():
    summary_file = st.session_state['summary_file']
    llm_file = summary_file + '.txt'
    if not os.path.exists(llm_file):
        with open(summary_file, 'r') as file:
            result = yaml.safe_load(file)
            calltrace = str(result['kernel']['potential-issues']['KernelErrors']).lstrip('[\'').rstrip('\']').split('LLM_PROMPT')[1].rstrip('(origin=kernel.auto_scenario_check)')
            calltrace = calltrace.replace('\\n', '\n')
            prompt_template = PromptTemplate(input_variables=["text"], template=KERNEL_TEMPLATE)
            answer_chain = LLMChain(llm=llm, prompt=prompt_template)
            answer = answer_chain.run(calltrace)
            st.session_state['result_text'] = answer
            st.session_state['log_text'] = calltrace
            with open(llm_file, 'w') as sfile:
                sfile.write(answer)
    else:
        with open(llm_file, 'r') as lfile:
            answer = lfile.read()
            st.session_state['result_text'] = answer

col1, col2, col3 = st.columns((3,1,5))
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
            st.session_state['status_text'] = 'done'

btn1, btn2, btn3 = st.columns((3,3,8))
with btn1:
    st.button('Ask HotSOS', on_click = button_hotsos)
with btn2:
    st.button('Ask LLM', on_click = button_hotgpt)

result1, result2 = st.columns((3,4))
with result1:
    st.text_area("Error logs found in uploaded sosreport", label_visibility = "visible", height = 500, key = 'log_text')
with result2:
    st.text_area("Analysis ouput", label_visibility = "visible", height = 500, key = 'result_text')

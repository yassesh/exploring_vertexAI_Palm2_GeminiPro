# !pip install --upgrade google-cloud-aiplatform
# !pip install langchain
# !pip install -U langchain-google-vertexai
import sys
if "google.colab" in sys.modules:
    from google.colab import auth as google_auth
    google_auth.authenticate_user()

from google.cloud import aiplatform
print(f"Vertex AI SDK version: {aiplatform.__version__}")

# Initialize Vertex AI SDK
import vertexai

from pydantic import BaseModel, root_validator
from typing import Any, Mapping, Optional, List, Dict
from langchain.llms.base import LLM
# from langchain.llms import VertexAI
from langchain_google_vertexai import VertexAI
from langchain.prompts import PromptTemplate

PROJECT_ID = "vertex-project-406219"  # @param {type:"string"}

LOCATION = "us-central1"  # @param {type:"string"}

vertexai.init(project=PROJECT_ID, location=LOCATION)

# Standard LLM completion model
llm = VertexAI(
    model_name="text-bison@001",
    max_output_tokens=256,
    temperature=0.1,
    top_p=0.8,
    top_k=40,
    verbose=True,
)

import os
import json
import requests

endpoint = 'https://hn.algolia.com/api/v1/search_by_date'
thread_id = '38490811'
url = f'{endpoint}?tags=comment,story_{thread_id}'

response_raw = requests.get(url)
response = json.loads(response_raw.text)

posts = []
for hit in response['hits']:
    if hit['parent_id'] == hit['story_id']:
        post = {'created_at': hit['created_at'], 'author': hit['author'], 'description': hit['comment_text']}
        posts.append(post)


description = posts[0]['description']

fields = """
    - Company
    - Goal
    - Positions
    - Locations
    - Job Type: Full time or part time
    - Remote (Full, Partial, from specific timezone)
    - Compensation
    - Experience
    - Website URL
    - Job offer URLs
    - Emails
    - Visa
"""


template = """
You will be provided with a Job description enclosed between ####.
The job description is taken from 'Ask HN: Who is Hiring?' and may contain HTML tags.

Extract from it the following key points (use null if needed):{fields}

If you encouter any concealed email address then decipher.
Format the output as a valid JSON object.

####
{description}
####
"""

import re
results = []
for post in posts:
  description = post['description']

  prompt = PromptTemplate.from_template(template)

  chain = prompt | llm
  raw_result = chain.invoke({"fields": fields, "description": description})
  result = re.sub(r"\n", '', raw_result)
  results.append(result)

# print(results)

json_docs = []
for doc in results:
    json_docs.append(json.loads(doc))

# print(json.dumps(json_docs, indent=2))



import streamlit as st

for job in json_docs:

  # Company name and goal as header
  st.markdown(f"## {job['Company']} - {job['Goal']}")  

  # Position and location
  col1, col2 = st.columns(2)
  col1.markdown(f"**Position:** {job['Positions']}")
  col2.markdown(f"**Location:** {job['Locations']}")

  # Other key details
  col3, col4 = st.columns(2)
  col3.markdown(f"**Job Type:** {job['Job Type']}")
  col4.markdown(f"**Remote:** {job['Remote']}")
  col5, col6 = st.columns(2)
  col5.markdown(f"**Compensation:** {job['Compensation']}")
  col6.markdown(f"**Experience:** {job['Experience']}")
  col7, col8 = st.columns(2)
  col7.markdown(f"**Job Listings:** {job['Job offer URLs']}")
  col8.markdown(f"**Email Contacts::** {job['Emails']}")

  # Divider  
  st.markdown("---")
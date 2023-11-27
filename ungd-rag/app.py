import logging

import streamlit as st
from langchain.chains import RetrievalQA
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient

# see what langchain is doing
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("langchain")

embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
llm = OpenAI()
client = QdrantClient("localhost", port=6333)

db = Qdrant(client, collection_name="speech_parts", embeddings=embeddings_model)


# schema
metadata_field_info = [
    AttributeInfo(
        name="country",
        description="The country of the speaker",
        type="string",
    ),
    AttributeInfo(
        name="iso_code",
        description="The ISO country code of the country of the speaker",
        type="string",
    ),
    AttributeInfo(
        name="post",
        description="The position of the speaker",
        type="string",
    ),
    AttributeInfo(name="session", description="The session number", type="float"),
    AttributeInfo(name="speaker", description="The name of the speaker", type="string"),
    AttributeInfo(name="year", description="The year of the speech", type="float"),
]
document_content_description = (
    "A snippet of a speech given at the United Nations General Debate"
)

retriever = SelfQueryRetriever.from_llm(
    llm,
    db,
    document_content_description,
    metadata_field_info,
    chain_kwargs={"allowed_operators": ["and", "or", "not"]},
    verbose=True,
)


prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Cite the year and country of the speaker in your response.

{context}

Question: {question}
Helpful Answer:"""
document_prompt = PromptTemplate.from_template(
    "Representative from {country} speaking in {year}\n{page_content}"
)
prompt = PromptTemplate.from_template(prompt_template)
qa = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"document_prompt": document_prompt, "prompt": prompt},
)


st.title("UNGD Explorer")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question..."):
    # Display user message in chat message container
    st.chat_message("user").write(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    llm_response = qa(prompt)
    response = llm_response["result"].strip()
    source_docs = llm_response["source_documents"]
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.write(response)
    for source_doc in source_docs:
        with st.expander("Source document"):
            for k, v in source_doc.metadata.items():
                st.markdown(f"**{k}**: {v}")
            st.write(source_doc.page_content)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

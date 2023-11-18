import asyncio

import pandas as pd
import typer
import yaml
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema.document import Document
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient
from yaml import SafeLoader

params = yaml.load(open("config.yaml"), Loader=SafeLoader)


async def _index_documents(
    data_file: str, collection_name: str, client_uri: str
) -> QdrantClient:
    """Index documents into Qdrant

    Args:
        subset: Indicate whether to load a subset of the data for testing.

    Returns:
        DB client object
    """
    df = pd.read_csv(data_file).fillna("")
    documents = []
    for _, row in df.iterrows():
        row = row.to_dict()
        documents.append(Document(page_content=row.pop("text"), metadata=row))
    embeddings_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return await Qdrant.afrom_documents(
        documents,
        embeddings_model,
        collection_name=collection_name,
        location=client_uri,
    )


def main(subset: bool = True):
    """Index data for search

    Args:
        subset: Indicate whether to load a subset of the data for testing.
    """
    suffix = "_subset" if subset else ""
    fn = params["data"][f"processed{suffix}"]
    collection_name = params["qdrant"][f"collection_name{suffix}"]
    asyncio.run(_index_documents(fn, collection_name, params["qdrant"]["uri"]))


if __name__ == "__main__":
    typer.run(main)

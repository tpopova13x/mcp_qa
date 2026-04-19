import os
import chromadb


def _get_client_and_collection_name():
    host = os.environ["CHROMA_HOST"]
    port = int(os.environ["CHROMA_PORT"])
    collection_name = os.environ["COLLECTION_NAME"]
    client = chromadb.HttpClient(host=host, port=port)
    return client, collection_name


def clear_chroma_collection():
    """Delete the ChromaDB collection if it exists."""
    client, collection_name = _get_client_and_collection_name()
    try:
        client.delete_collection(name=collection_name)
        print(f"Deleted ChromaDB collection '{collection_name}'.")
    except chromadb.errors.NotFoundError:
        print(f"ChromaDB collection '{collection_name}' does not exist, nothing to delete.")


def upsert_to_chroma(documents, ids, metadatas):
    """Upsert documents into a ChromaDB collection."""
    if not documents:
        print("No documents to ingest.")
        return

    client, collection_name = _get_client_and_collection_name()
    collection = client.get_or_create_collection(name=collection_name)
    collection.upsert(documents=documents, ids=ids, metadatas=metadatas)
    print(f"Ingested {len(documents)} documents into '{collection_name}' collection.")

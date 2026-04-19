import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_HOST = os.environ["CHROMA_HOST"]
CHROMA_PORT = int(os.environ["CHROMA_PORT"])
COLLECTION_NAME = "internal_docs"


def query(question: str, n_results: int = 2):
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = client.get_collection(name=COLLECTION_NAME)

    results = collection.query(query_texts=[question], n_results=n_results)

    print(f"\nQuestion: {question}\n")
    for i, (doc, meta, distance) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
    ):
        print(f"--- Result {i + 1} (source: {meta['source']}, distance: {distance:.4f}) ---")
        print(doc)
        print()


def main():
    print("Ask questions about the internal documentation. Type 'quit' to exit.\n")
    while True:
        question = input("Your question: ").strip()
        if not question or question.lower() in ("quit", "exit", "q"):
            break
        query(question)


if __name__ == "__main__":
    main()

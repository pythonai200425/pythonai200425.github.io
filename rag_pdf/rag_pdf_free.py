import gradio as gr
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import pipeline

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GENERATION_MODEL = "google/flan-t5-base"

vectorstore = None
generation_pipeline = None


def get_generation_pipeline():
    global generation_pipeline
    if generation_pipeline is None:
        generation_pipeline = pipeline(
            "text2text-generation",
            model=GENERATION_MODEL,
            tokenizer=GENERATION_MODEL,
        )
    return generation_pipeline


def load_and_index(pdf_path: str):
    """Load a PDF, chunk it, embed it, and return a retriever."""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    print(f"Loaded {len(pages)} pages from {pdf_path}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(pages)
    print(f"Split into {len(chunks)} chunks")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    store = Chroma.from_documents(chunks, embedding=embeddings)
    return store.as_retriever(search_kwargs={"k": 4})


def build_prompt(question: str, docs, history):
    context_parts = []
    for idx, doc in enumerate(docs, start=1):
        page = doc.metadata.get("page")
        page_text = f"page {page + 1}" if isinstance(page, int) else "unknown page"
        context_parts.append(f"[{idx} | {page_text}]\n{doc.page_content}")

    recent_history = history[-6:] if history else []
    history_lines = []
    for msg in recent_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_lines.append(f"{role}: {content}")

    context_text = "\n\n".join(context_parts) if context_parts else "No context found."
    history_text = "\n".join(history_lines) if history_lines else "No prior chat history."

    return (
        "Answer the question using only the context below. "
        "If the answer is not present, say you do not know.\n\n"
        f"Chat history:\n{history_text}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )


def upload_pdf(pdf_file):
    """Called when user uploads a PDF."""
    global vectorstore

    if pdf_file is None:
        return "No file uploaded.", []

    retriever = load_and_index(pdf_file.name)
    vectorstore = retriever
    return "PDF indexed. Ask questions now.", []


def ask_question(question, history):
    """Called when user sends a message."""
    history = history or []

    if not question:
        return history

    if vectorstore is None:
        return history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": "Please upload a PDF first."},
        ]

    docs = vectorstore.invoke(question)
    prompt = build_prompt(question, docs, history)

    generator = get_generation_pipeline()
    result = generator(prompt, max_new_tokens=220, do_sample=False)
    answer = result[0]["generated_text"].strip()

    pages = sorted(
        {
            doc.metadata.get("page")
            for doc in docs
            if isinstance(doc.metadata.get("page"), int)
        }
    )
    if pages:
        answer += "\n\nSources: pages " + ", ".join(str(page + 1) for page in pages)

    return history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]


with gr.Blocks(title="Chat with Your PDF (Free)") as demo:
    gr.Markdown("## Chat with Your PDF (Free, local)\nUpload a PDF and ask questions.")

    with gr.Row():
        pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
        status = gr.Textbox(label="Status", interactive=False)

    chatbot = gr.Chatbot(label="Conversation", height=400)
    question_input = gr.Textbox(placeholder="Ask a question about your PDF...", label="Question")

    pdf_input.change(fn=upload_pdf, inputs=pdf_input, outputs=[status, chatbot])
    question_input.submit(fn=ask_question, inputs=[question_input, chatbot], outputs=chatbot)


if __name__ == "__main__":
    demo.launch()

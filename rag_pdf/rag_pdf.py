# rag_app.py — complete working app
import os
import gradio as gr
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from dotenv import load_dotenv

load_dotenv()

def load_and_index(pdf_path: str):
    """Load a PDF, chunk it, embed it, return a retriever."""

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set. Add it to the project's .env file.")

    # Step 1: Load PDF pages
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    print(f"Loaded {len(pages)} pages from {pdf_path}")

    # Step 2: Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(pages)
    print(f"Split into {len(chunks)} chunks")

    # Step 3: Embed and store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(chunks, embedding=embeddings)

    # Step 4: Return retriever
    return vectorstore.as_retriever(search_kwargs={"k": 4})

def build_chain(retriever):
    """Wrap retriever in a conversational RAG chain."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        verbose=False
    )
    return chain

# Global state
chain = None

def upload_pdf(pdf_file):
    """Called when user uploads a PDF."""
    global chain
    if pdf_file is None:
        return "No file uploaded.", []

    retriever = load_and_index(pdf_file.name)
    chain = build_chain(retriever)
    return "✅ PDF indexed! Ask me anything about it.", []

def ask_question(question, history):
    """Called when user sends a message."""
    global chain
    history = history or []

    if chain is None:
        return history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": "Please upload a PDF first."},
        ]

    result = chain.invoke({"question": question})
    answer = result["answer"]

    # Append sources
    sources = result.get("source_documents", [])
    if sources:
        pages = set(doc.metadata.get("page", "?") for doc in sources)
        answer += f"\n\n_Sources: pages {', '.join(str(p+1) for p in sorted(pages))}_"

    return history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]

# Build the UI
with gr.Blocks(title="Chat with Your PDF") as demo:
    gr.Markdown("## 📄 Chat with Your PDF\nUpload a PDF, then ask questions about it.")

    with gr.Row():
        pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
        status = gr.Textbox(label="Status", interactive=False)

    chatbot = gr.Chatbot(label="Conversation", height=400)
    question_input = gr.Textbox(placeholder="Ask a question about your PDF...", label="Question")

    pdf_input.change(fn=upload_pdf, inputs=pdf_input, outputs=[status, chatbot])

    question_input.submit(
        fn=ask_question,
        inputs=[question_input, chatbot],
        outputs=chatbot
    )

    gr.Examples(
        examples=[
            ["What is this document about?"],
            ["Summarize the main points."],
            ["What does it say about pricing?"],
        ],
        inputs=question_input
    )

if __name__ == "__main__":
    demo.launch()
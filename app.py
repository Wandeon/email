
import streamlit as st
import pandas as pd
import tempfile
import mailbox
import requests
import math
from langdetect import detect

# Hugging Face Inference API settings for Mistral 7B Instruct
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
headers = {"Authorization": "Bearer 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"}

# Chat-style prompt template with language support
def create_chat_payload(user_text, language="English"):
    prompt = (
        f"[INST] You are an intelligent assistant analyzing professional email messages written in {language}.\n"
        "Extract and organize relevant information clearly, focusing on:\n"
        "1. Topics Identified\n"
        "2. People and Roles\n"
        "3. Companies and Customers Mentioned\n"
        "4. Conversation Threads (Grouped by Topic)\n"
        "5. Action Items\n"
        "6. Pending or Follow-Up Items\n"
        "7. Deadlines and Time-sensitive Info\n"
        "\n"
        "Group emails logically. Provide concise and structured summaries.\n"
        "Here are the emails:\n"
        f"{user_text} [/INST]"
    )
    return {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.3
        }
    }

# Summarize text using Hugging Face model
def summarize_text(text, language="English"):
    payload = create_chat_payload(text, language)
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        return f"Error: {response.text}"

# Extract emails from .mbox with UTF-8 support
def read_emails_from_mbox(file_path):
    mbox = mailbox.mbox(file_path)
    emails = []
    for message in mbox:
        subject = message['subject'] or "(No subject)"
        try:
            body = message.get_payload(decode=True)
            if body:
                try:
                    body = body.decode('utf-8', errors='ignore')
                except:
                    body = str(body)
            else:
                body = "(No content)"
        except:
            body = "(Unreadable content)"
        emails.append(f"Subject: {subject}\n{body}")
    return emails

# Streamlit app
st.title("📧 Email Summarizer (MBOX Format) with Mistral 7B")
uploaded_file = st.file_uploader("Upload a .mbox file", type=["mbox"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as tmp:
        tmp.write(uploaded_file.getvalue())
        file_path = tmp.name

    emails = read_emails_from_mbox(file_path)
    st.success(f"Loaded {len(emails)} emails")

    if emails:
        batch_size = 20
        num_batches = math.ceil(len(emails) / batch_size)
        partial_summaries = []

        with st.spinner("Analyzing emails in batches..."):
            for i in range(num_batches):
                batch = emails[i*batch_size:(i+1)*batch_size]
                batch_text = "\n\n".join(batch)
                if len(batch_text.strip()) < 100:
                    continue
                try:
                    lang = detect(batch_text)
                except:
                    lang = "en"
                language = "Croatian" if lang == "hr" else "English"
                summary = summarize_text(batch_text, language)
                partial_summaries.append(summary)

        # Final summarization
        if partial_summaries:
            full_summary_input = "\n\n".join(partial_summaries)
            language = "Croatian" if detect(full_summary_input) == "hr" else "English"

            with st.spinner("Generating final full summary..."):
                final_summary = summarize_text(full_summary_input, language)

            st.markdown("### Final Summary")
            st.write(final_summary)

            if st.button("Save Summary"):
                with open("summaries.csv", "a", encoding="utf-8") as f:
                    f.write(f"{uploaded_file.name}|{final_summary}\n")
                st.success("Summary saved to summaries.csv")
        else:
            st.warning("No meaningful content found in the uploaded emails.")

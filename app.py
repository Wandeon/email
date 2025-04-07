
import streamlit as st
import pandas as pd
import tempfile
import mailbox
import requests

# Hugging Face Inference API settings
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": "Bearer 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"}

# Function to call Hugging Face API for summarization
def summarize_text(text):
    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]['summary_text']
    else:
        return f"Error: {response.text}"

# Read .mbox file and extract email bodies
def read_emails_from_mbox(file_path):
    mbox = mailbox.mbox(file_path)
    emails = []
    for message in mbox:
        subject = message['subject'] or "(No subject)"
        body = message.get_payload(decode=True)
        if body:
            try:
                body = body.decode()
            except:
                body = str(body)
        else:
            body = "(No content)"
        emails.append(f"Subject: {subject}\n{body}")
    return emails

# Streamlit UI
st.title("📧 Email Summarizer (MBOX Format)")
uploaded_file = st.file_uploader("Upload a .mbox file", type=["mbox"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as tmp:
        tmp.write(uploaded_file.getvalue())
        file_path = tmp.name

    emails = read_emails_from_mbox(file_path)
    st.success(f"Loaded {len(emails)} emails")

    if emails:
        # Limit the content to a manageable size for summarization
        full_text = "\n\n".join(emails[:5])  # summarizing first 5 emails
        st.subheader("📝 Summary")
        with st.spinner("Summarizing..."):
            summary = summarize_text(full_text)
        st.write(summary)

        # Optionally save
        if st.button("💾 Save Summary"):
            with open("summaries.csv", "a", encoding="utf-8") as f:
                f.write(f"{uploaded_file.name}|{summary}\n")
            st.success("Summary saved to summaries.csv")

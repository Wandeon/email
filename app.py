
import streamlit as st
import pandas as pd
import tempfile
import mailbox
import requests
import math

# Hugging Face Inference API settings
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": "Bearer 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"}

# Improved prompt template
PROMPT_TEMPLATE = '''
You are an advanced assistant specialized in analyzing professional email inboxes across various industries.

Your task is to review a batch of email messages and organize the information in a clear, useful, and structured way. These messages may relate to various clients, projects, tasks, teams, or internal discussions.

Your output should include the following sections:

1. 📚 Topics Identified
2. 👥 People and Roles
3. 🏢 Companies and Customers Mentioned
4. 📨 Conversation Threads (Grouped by Topic)
5. ✅ Action Items
6. ⏳ Pending or Follow-Up Items
7. 🗓️ Deadlines and Time-sensitive Info

Be concise but informative. Maintain structure so the information is easy to navigate.

Here are the emails to analyze:
{text}
'''

# Function to call Hugging Face API for summarization
def summarize_text(text):
    payload = {
        "inputs": PROMPT_TEMPLATE.replace("{text}", text)
    }
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
        st.subheader("📝 Summary")
        batch_size = 20
        num_batches = math.ceil(len(emails) / batch_size)
        chunks = []

        with st.spinner("Preprocessing emails in chunks..."):
            for i in range(num_batches):
                batch = emails[i*batch_size:(i+1)*batch_size]
                full_text = "\n\n".join(batch)
                chunks.append(full_text)

        all_text_combined = "\n\n".join(chunks)

        with st.spinner("Generating full summary..."):
            final_summary = summarize_text(all_text_combined)

        st.markdown("### 📦 Final Summary")
        st.write(final_summary)

        if st.button("💾 Save Summary"):
            with open("summaries.csv", "a", encoding="utf-8") as f:
                f.write(f"{uploaded_file.name}|{final_summary}\n")
            st.success("Summary saved to summaries.csv")

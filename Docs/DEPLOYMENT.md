# Deployment Guide - Streamlit Community Cloud

This guide explains how to deploy the Antigravity Recommender for free using Streamlit's cloud hosting.

## 1. Prerequisites
- A GitHub account.
- The project pushed to a GitHub repository.
- A **Groq API Key**.

## 2. Connect to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click **New app**.
3. Select your repository, the **main** branch, and set the **Main file path** to:
   `backend/streamlit_app.py`
4. Click **Advanced settings...**.

## 3. Configure Secrets (CRITICAL)
Streamlit Cloud does not read your local `.env` file. You must add your API key manually in the **Secrets** section of the deployment dashboard:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

## 4. Deploy
1. Click **Deploy**.
2. Streamlit will install the dependencies from `backend/requirements.txt` and start the server.
3. Your app will be live at a URL like `https://antigravity-zomato.streamlit.app`.

## 5. Local Testing
To test the Streamlit app on your machine:
```bash
pip install -r backend/requirements.txt
streamlit run backend/streamlit_app.py
```

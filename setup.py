from setuptools import setup, find_packages

setup(
    name="antigravity",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.111.0",
        "uvicorn[standard]==0.29.0",
        "python-dotenv==1.0.1",
        "groq==1.1.2",
        "pandas==2.2.2",
        "httpx[http2]==0.28.1",
        "streamlit==1.40.0",
    ],
    python_requires=">=3.11",
)

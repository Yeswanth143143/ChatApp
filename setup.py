from setuptools import setup, find_packages

setup(
    name="Chat Application",
    author="Yeswanth Chowdary",
    version="0.0.1",
    author_email="bgotti@hawk.iit.edu",
    install_requires=["openai","langchain","streamlit","python_dotenv","PyPDF2","langchain-openai","langchain-community", "azure-cosmos","azure-identity"],
    packages=find_packages()
)
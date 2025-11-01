"""
Simple test endpoint to verify Vercel Python works
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Vercel Python FastAPI is working!", "message": "This is a test endpoint"}

@app.get("/test")
def test():
    return {"test": "success"}

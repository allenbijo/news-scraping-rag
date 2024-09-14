import os
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple
import uvicorn
import random
import time
from datetime import datetime
# import redis
from vectorsaving import vectorize_papers, get_vectors
from fetch_news import get_news_links, load_news
from langchain_community.vectorstores import FAISS

# Redis setup
# redis_client = redis.Redis(host='redis', port=6379, db=0)

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


def get_db():
	db = get_vectors()
	ret = db.as_retriever(search_kwargs={"k": 5})


@app.get("/health")
async def health_check():
	return {"status": "healthy", "message": f"API is active"}


@app.get("/search")
async def search(
		vectors: FAISS = Depends(get_vectors),
		text: str = Query(..., title="Search query"),
		top_k: int = Query(4, title="Number of results to fetch"),
		threshold: float = Query(0.8, title="Similarity score threshold")
):
	if not text:
		raise HTTPException(status_code=400, detail="Search query cannot be empty")

	if top_k < 1:
		raise HTTPException(status_code=400, detail="top_k must be at least 1")

	if threshold < 0 or threshold > 1:
		raise HTTPException(status_code=400, detail="Threshold must be between 0 and 1")

	results = vectors.similarity_search_with_score(query=text, k=top_k)

	filtered_results = [(result, float(score)) for result, score in results if score >= threshold]

	return filtered_results


async def scrape_news():
	links = get_news_links()
	news = load_news(links)
	vectorize_papers(news)


@app.on_event("startup")
async def startup_event():
	asyncio.create_task(scrape_news())
	# pass


if __name__ == "__main__":
	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
	# http://127.0.0.1:8000/search?text=infosys&top_k=5&threshold=0.5

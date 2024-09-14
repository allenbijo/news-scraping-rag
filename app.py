import os
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import aioredis
from functools import lru_cache
import json
from pydantic import BaseModel
from typing import List, Tuple
import uvicorn
import time
from datetime import datetime
from langchain_community.vectorstores import FAISS
from vectorsaving import vectorize_papers, get_vectors
from fetch_news import get_news_links, load_news

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Redis setup
redis_client = aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
CACHE_EXPIRATION = 60 * 60 * 24  # 24 hours


@lru_cache()
def get_db():
	return get_vectors()


@app.on_event("startup")
async def startup_event():
	asyncio.create_task(scrape_news())


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

	# Check if results are in cache
	cache_key = f"search:{text}:{top_k}:{threshold}"
	cached_results = await redis_client.get(cache_key)

	if cached_results:
		return json.loads(cached_results)

	results = vectors.similarity_search_with_score(query=text, k=top_k)

	filtered_results = [(result.page_content, float(score)) for result, score in results if score >= threshold]

	# Serialize the results in a JSON-friendly format
	serializable_results = [
		{"content": content, "score": score}
		for content, score in filtered_results
	]

	# Cache the results
	await redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(serializable_results))

	return filtered_results


async def scrape_news():
	links = get_news_links()
	news = load_news(links)
	vectorize_papers(news)


if __name__ == "__main__":
	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
# http://127.0.0.1:8000/search?text=infosys&top_k=5&threshold=0.5

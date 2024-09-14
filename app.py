import os
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import aioredis
from functools import lru_cache
import json
import uvicorn
import time
from datetime import datetime
from langchain_community.vectorstores import FAISS
from vectorsaving import vectorize_papers, get_vectors
from fetch_news import get_news_links, load_news
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_logger")

# Configure FastAPI
app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Configure Redis
redis_client = aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
CACHE_EXPIRATION = 60 * 60 * 24  # 24 hours
USER_REQUEST_LIMIT = 5  # Maximum 5 requests per user


@lru_cache()
def get_db():
	return get_vectors()


# Scrape news on startup
@app.on_event("startup")
async def startup_event():
	asyncio.create_task(scrape_news())


# Health check endpoint
@app.get("/health")
async def health_check():
	return {"status": "healthy", "message": f"API is active"}


# Search endpoint
@app.get("/search")
async def search(
		vectors: FAISS = Depends(get_vectors),
		text: str = Query(..., title="Search query"),
		top_k: int = Query(4, title="Number of results to fetch"),
		threshold: float = Query(0.8, title="Similarity score threshold"),
		user_id: str = Query(..., title="User ID")

):
	# Start tracking time
	start_time = time.time()

	# Input validation
	if not text:
		raise HTTPException(status_code=400, detail="Search query cannot be empty")

	if top_k < 1:
		raise HTTPException(status_code=400, detail="top_k must be at least 1")

	if threshold < 0 or threshold > 1:
		raise HTTPException(status_code=400, detail="Threshold must be between 0 and 1")

	# Rate limiting check
	user_key = f"user:{user_id}:requests"
	request_count = await redis_client.get(user_key)

	if request_count is None:
		await redis_client.set(user_key, 1, ex=60 * 60 * 24)  # 24 hours expiration
	elif int(request_count) >= USER_REQUEST_LIMIT:
		raise HTTPException(status_code=429, detail="Rate limit exceeded. You can make only 5 requests per day.")
	else:
		await redis_client.incr(user_key)

	# Check if results are in cache
	cache_key = f"search:{text}:{top_k}:{threshold}"
	cached_results = await redis_client.get(cache_key)

	if cached_results:
		return json.loads(cached_results)

	results = vectors.similarity_search_with_score(query=text, k=top_k)

	filtered_results = sorted([(result, float(score)) for result, score in results if score >= threshold], key=lambda x: x[1], reverse=True)

	# Serialize the results in a JSON-friendly format
	serializable_results = [
		{"result": json.dumps(vars(result)), "score": score}
		for result, score in filtered_results
	]

	# Cache the results
	await redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(serializable_results))

	# Log inference time
	inference_time = time.time() - start_time
	logger.info(f"Inference Time: {inference_time:.4f} seconds for User: {user_id} with Query: '{text}'")

	# Return results and add inference time to the response
	return {
		"results": filtered_results,
		"inference_time": inference_time
	}


async def scrape_news():
	links = get_news_links()
	news = load_news(links)
	vectorize_papers(news)


if __name__ == "__main__":
	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
	# http://127.0.0.1:8000/search?text=infosys&top_k=5&threshold=0.5

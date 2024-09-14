# Backend API for RAG with News Scraping and FAISS

This project implements a backend API using Python and FastAPI, with FAISS for vector data storage and efficient similarity search. It includes features such as rate limiting, background news scraping, and vector-based article search.

## Features

- Basic API endpoint with rate limiting
- Background news scraping from Times Of India
- Vector-based article search using FAISS
- Docker containerization

## Setup and Running

1. Make sure you have Docker and Docker Compose installed on your system.
2. Clone this repository.
3. Navigate to the project directory.
4. Run the following command to start the services:

   ```
   docker-compose up --build
   ```

5. The API will be available at `http://localhost:8000`.

## API Endpoints

- `/health`: GET request to check if the API is active.
    - returns: `{"status": "healthy", "message": f"API is active"}`
- `/search`: GET request to search for similar articles based on a query string.
  - query parameters:
    - `text`: The search query string.
    - `top_k`: The maximum number of results to return.
    - `threshold`: The minimum similarity score for results.
    - `user_id`: The user ID for rate limiting.
    - returns: A list of articles similar to the query string.

## Vector Search

This project uses FAISS (Facebook AI Similarity Search) for efficient similarity search of articles. Article titles are encoded into vector representations using a pre-trained BERT model, and these vectors are indexed in FAISS for fast retrieval.

## Design Decisions

1. **FastAPI**: Chosen for its high performance, easy-to-use async support, and automatic API documentation.
2. **FAISS**: Implemented for efficient similarity search of article vectors.
3. **all-MiniLM-L6-v2**: Used for encoding article titles into vector representations.
4. **Background Scraping**: Implemented as a separate asyncio task to update the news database oon startup.
5. **Docker**: Used for containerization to ensure consistent environments across development and deployment.

<sub>This project was developed as part of the RAG project for Trademarkia by Allen Bijo - 21BAI1266</sub>
# Aurora Member QA System


## 1. Overview 

This project is a simple question answering service built on top of Aurora’s public member messages API. The system takes a natural language question, searches the member messages, and returns the closest match in a clean JSON response. The goal is to keep the design easy to follow, reliable, and simple to maintain.

## 2. Tech Stack

. Python

. FastAPI

. Sentence Transformers

. Embedding based similarity search

. In memory vector index

. Uvicorn

. Render for deployment

The setup stays intentionally lightweight to keep the code easy to understand and run without extra infrastructure.


## 3. Project Structure

. main.py contains the FastAPI application and exposes the /ask endpoint

. qa.py handles embeddings and vector search

. services/messages.py fetches member messages from Aurora’s API

. extractors/extractors.py cleans and normalizes message text

. requirements.txt lists all dependencies

The system runs entirely in memory which keeps it fast and easy to deploy.

## 4. Architecture

Aurora API  
    ↓
    
Message Fetcher  
    ↓
    
Extractor for text cleaning  
    ↓
    
Embedding Model  
    ↓
    
In Memory Index  
    ↑
    
User Question through FastAPI /ask  
    ↓
    
Similarity Search  
    ↓
    
Best Match Returned as JSON


## 5. How the System Works

. The service downloads all public member messages from Aurora’s API.

. Text is cleaned and normalized.

. Each message is converted into an embedding vector.

. The user sends a question to the /ask endpoint.

. The question is embedded and compared to all message vectors.

. The closest match is returned as JSON.

. If nothing is relevant, the response is:

“The information is not available in the member messages.”


## 6. API Specification

Endpoint:
GET /ask?question=Your+Question+Here

Example:
GET `http://localhost:8000/ask?question=When%20is%20Fatima%20planning%20her%20trip%20to%20London%3F`

Sample Response:

{
  "answer": "Member: Fatima El Tahir | Timestamp: 2025-03-27T06:01:58Z | Message: Looking to connect with a reputable antiques dealer in London."
}




## 7. Running Locally

Install dependencies:
`pip install -r requirements.txt`

Start the service:
`uvicorn aurora_app.main:app --reload`

Swagger UI:
`http://127.0.0.1:8000/docs`

## 8. Performance Notes

. The system handles a few thousand messages in memory without any issues.

. Typical response times stay under half a second on Render.

. A compact embedding model is used for fast processing.


## 9. Design Decisions

. Embeddings provide better matching accuracy for natural language questions.

. FastAPI keeps the routing clean and adds automatic documentation.

. An in memory index avoids extra infrastructure.

. TF IDF and keyword based scoring were considered but did not perform as well for open ended questions.



## 10. Future Enhancements

. Add caching to avoid fetching data repeatedly.

. Move embeddings into a vector database such as FAISS for larger datasets.

. Add hybrid scoring that blends embeddings and keywords.

. Add logging and monitoring for production use.

. Introduce batch endpoints for multiple questions.


## 11. Limitations

The system is designed for small to medium datasets and works best with short messages. It does not handle very large collections of documents, and it does not use hybrid retrieval or a vector database at this stage. It is built for clarity and ease of review rather than full scale production.


## 12. Deployment

This service can run on platforms such as Render, Railway, Fly.io, and AWS Lightsail.

The current live deployment is available below.


## 13. Live API Endpoint 

Base URL:
https://aurora-member-qa-i99g.onrender.com/ask?question=

Direct Test Samples:

- Fatima travel example

https://aurora-member-qa-i99g.onrender.com/ask?question=When+is+Fatima+planning+her+trip+to+London%3F

- Yoga trainer example

https://aurora-member-qa-i99g.onrender.com/ask?question=Who+needs+a+Yoga+trainer+in+Dubai%3F

- Antiques dealer example

https://aurora-member-qa-i99g.onrender.com/ask?question=Who+is+looking+for+an+antiques+dealer%3F

- Business networking example

https://aurora-member-qa-i99g.onrender.com/ask?question=Who+is+looking+to+connect+with+other+founders%3F

Sample Response:

{
  "answer": "Member: Fatima El-Tahir | Timestamp: 2025-03-27T06:01:58Z | Message: Looking to connect with a reputable antiques dealer in London."
}


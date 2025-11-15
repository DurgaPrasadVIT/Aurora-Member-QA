# Aurora Member QA System


## 1. Overview 

This document describes a lightweight question answering service built on top of Aurora’s public member messages API. The system receives a natural-language question, searches all available
member messages, and returns the best matching entry in a clean JSON response. The design is intentionally simple, predictable, and transparent, aligning with Aurora’s assignment expectations.


## 2. Project Structure

The system follows a minimal modular structure:

• main.py – Hosts the FastAPI application and exposes the `/ask` endpoint.

• qa.py – Handles embeddings, vector comparison, and message retrieval. 

• services/messages.py – Fetches public member messages from Aurora’s API. 

• extractors/extractors.py – Normalizes and cleans message text. 

All dependencies are listed in requirements.txt. The system operates entirely in memory for
speed and simplicity.


## 3. How the System Works

1. The service downloads all public member messages from Aurora’s API.
2. Text is cleaned and standardized.
3. Each message is converted into an embedding vector.
4. A user asks a question via the `/ask` endpoint.
5. The question is embedded and compared to all stored vectors.
6. The closest match is returned as JSON.
If no meaningful match exists, the response is:
“The information is not available in the member messages.”


## 4. API Specification

Endpoint:
GET /ask?question=Your+Question+Here

Example:
GET `http://localhost:8000/ask?question=When%20is%20Fatima%20planning%20her%20trip%20to%20London%3F`

Sample Response:

{
  "answer": "Member: Fatima El Tahir | Timestamp: 2025-03-27T06:01:58Z | Message: Looking to connect with a reputable antiques dealer in London."
}




## 5. Running Locally

Install dependencies:
`pip install -r requirements.txt`

Start the service:
`uvicorn aurora_app.main:app --reload`

Swagger UI:
`http://127.0.0.1:8000/docs`


## 6. Design Decisions


• Embeddings: Provide flexible matching for differently worded questions.

• FastAPI: Offers clean routing and automatic documentation.

• In memory index: Ideal for small datasets, avoids infrastructure overhead.

• Alternate approaches considered: TF-IDF, lightweight RAG, rule based matching.

Embeddings demonstrated the best balance of accuracy, simplicity, and maintainability.



## 7. Data Notes

During analysis of the public dataset:

• Some names are similar and require clean normalization.

• Message length varies.

• A few timestamps and structures differ slightly.

• Normalization ensures consistent embedding quality.

All processed messages go through the extractor before storage.



## 8. Deployment-Ready Design

This service can be deployed to:

• Render

• Railway

• Fly.io

• AWS Lightsail

After deployment, the public URL can replace the local endpoint in the README.



## 9. Future Enhancements

• Add caching to avoid refetching data.

• Move embeddings into a vector DB like FAISS for scalability.

• Improve ranking using hybrid search (embeddings + keyword scoring).

• Add structured logging for debugging and monitoring.



## 10. Summary

This system offers:

• A clear and reliable /ask interface

• A simple architecture that Aurora reviewers can understand quickly

• Clean embeddings-based matching

• A maintainable foundation ready for scaling

The project is focused, predictable, and aligned with the take-home assignment requirements.


## 11. Live API Endpoint & Examples Links

Base URL:
https://aurora-member-qa-i99g.onrender.com/ask?question=


Direct Test Samples:

• Fatima travel example

https://aurora-member-qa-i99g.onrender.com/ask?question=When+is+Fatima+planning+her+trip+to+London%3F

• Yoga trainer example

https://aurora-member-qa-i99g.onrender.com/ask?question=Who+needs+a+Yoga+trainer+in+Dubai%3F

• Antiques dealer example

https://aurora-member-qa-i99g.onrender.com/ask?question=Who+is+looking+for+an+antiques+dealer%3F

• Business networking example

https://aurora-member-qa-i99g.onrender.com/ask?question=Who+is+looking+to+connect+with+other+founders%3F

Sample Response:

{
  "answer": "Member: Fatima El-Tahir | Timestamp: 2025-03-27T06:01:58Z | Message: Looking to connect with a reputable antiques dealer in London."
}


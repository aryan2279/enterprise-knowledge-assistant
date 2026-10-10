\# Enterprise Knowledge Assistant (RAG)



An AI-powered knowledge assistant that allows authenticated users to upload documents and ask questions about their content. The system retrieves relevant document chunks and generates answers using Google Gemini, with source references.



\## Features



\- User registration and JWT-based login

\- PDF, TXT, and DOCX document uploads

\- Text extraction and chunking

\- Semantic search using sentence embeddings

\- Vector storage and retrieval with Qdrant

\- AI-generated answers using Google Gemini

\- Source references for answers

\- User-specific document access



\## Tech Stack



\- \*\*Backend:\*\* Python, FastAPI

\- \*\*Authentication:\*\* JWT

\- \*\*Database:\*\* PostgreSQL

\- \*\*Vector Database:\*\* Qdrant

\- \*\*Embeddings:\*\* Sentence Transformers

\- \*\*LLM:\*\* Google Gemini

\- \*\*Deployment:\*\* Docker Compose



\## How It Works



1\. A user logs in and uploads a document.

2\. The backend extracts the document text and splits it into chunks.

3\. The chunks are converted into embeddings and stored in Qdrant.

4\. A user submits a question.

5\. The system retrieves relevant chunks belonging to that user.

6\. Gemini generates an answer using the retrieved context and provides source references.



\## Setup



\### Prerequisites



\- Docker Desktop

\- Google Gemini API key



\### Installation



1\. Clone the repository:



&#x20;  ```bash

&#x20;  git clone YOUR\_GITHUB\_REPOSITORY\_URL

&#x20;  cd enterprises--rag

&#x20;  ```



2\. Create a `.env` file in the project root using the environment variables required by the application. Configure your PostgreSQL connection, Gemini API key, and model name. Never commit real credentials.



3\. Start the application:



&#x20;  ```bash

&#x20;  docker compose up -d --build

&#x20;  ```



4\. Open the API documentation:



&#x20;  http://localhost:8000/docs



\## Main API Endpoints



| Method | Endpoint | Purpose |

|---|---|---|

| POST | `/api/auth/register` | Register a user |

| POST | `/api/auth/login` | Log in |

| GET | `/api/auth/me` | Get current user |

| POST | `/api/documents/upload` | Upload a document |

| GET | `/api/documents/` | List accessible documents |

| POST | `/api/search/` | Ask a question |



\## Security



\- Protected endpoints require JWT authentication.

\- Document retrieval is restricted to the authenticated user's documents.

\- Answers should be based on retrieved document context.

\- API keys and passwords must be kept out of source control.



\## Future Improvements



\- A React frontend

\- Conversation history

\- Improved retrieval evaluation

\- Automated tests and CI/CD



\## Author



Aryan Dev


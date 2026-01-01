# Dalilk - AI Car Assistant

An intelligent AI-powered car recommendation system for the Egyptian market, built with FastAPI and advanced RAG (Retrieval-Augmented Generation) technology.

##  Features

- **Smart Car Recommendations**: AI-powered suggestions based on user preferences
- **Natural Language Processing**: Understands Arabic and English queries
- **Vector Database Search**: Fast and accurate car information retrieval
- **Multi-LLM Support**: Compatible with Cohere, Groq, OpenAI, and HuggingFace
- **Session Management**: Maintains conversation context for better recommendations
- **RESTful API**: Easy integration with web and mobile applications

## 📋 Requirements

- Python 3.9 or later
- MongoDB (for data storage)
- Qdrant (for vector database)

## 🚀 Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd Ai
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate  # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirments.txt
```

### 4. Setup environment variables
```bash
cp src/.env.example src/.env
```

Edit `src/.env` and add your API keys:
- `COHERE_API_KEY` - Your Cohere API key
- `GROQ_API_KEY` - Your Groq API key (optional)
- `OPENAI_API_KEY` - Your OpenAI API key (optional)
- `DATABASE_URL` - MongoDB connection string
- `VECTOR_DB_PATH` - Qdrant database path

## 🏃 Running the Server

### Development Mode
```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Using the start script
```bash
cd src
./start_server.sh
```

### Troubleshooting: "Address already in use"
```bash
# Find the process using port 8000
lsof -i :8000

# Kill the process (replace <PID> with actual process ID)
kill -9 <PID>
```

## 📡 API Endpoints

### Data Management
- **Upload File**: `POST /api/v1/data/upload`
- **Process File**: `POST /api/v1/data/process`

### NLP & Search
- **Push to Vector DB**: `POST /api/v1/nlp/index/push`
- **Get Index Info**: `GET /api/v1/nlp/index/info`
- **Search**: `POST /api/v1/nlp/index/search`
- **Chat**: `POST /api/v1/nlp/index/chat`

## 🏗️ Project Structure

```
Ai/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── routes/              # API endpoints
│   │   ├── data.py          # Data upload/processing
│   │   └── nlp.py           # NLP and chat endpoints
│   ├── controlles/          # Business logic
│   │   ├── NLPController.py # NLP operations
│   │   └── ProcessControlles.py # Data processing
│   ├── stores/              # External services
│   │   ├── llm/             # LLM providers
│   │   └── Vector_db/       # Vector database
│   ├── models/              # Database models
│   ├── helper/              # Utility functions
│   └── assets/              # Data files
├── requirments.txt          # Python dependencies
└── README.md                # This file
```

## 🔧 Configuration

The system supports multiple LLM backends:
- **Cohere** (default for embeddings and generation)
- **Groq** (fast inference)
- **OpenAI** (GPT models)
- **HuggingFace** (local models)

Configure in `.env`:
```env
GENERATION_BACKEND=cohere
EMBEDDING_BACKEND=cohere
VECTOR_DB_BACKEND=qdrant
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is part of a graduation project.

## 👥 Team

Developed by the Dalilk AI team for the Egyptian car market.

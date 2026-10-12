# Wellora 🌿

> **AI Companion for Wellness and Lifestyle — Voice-Enabled**

Wellora is an intelligent health and wellness assistant that tracks nutrition, manages meals, and provides personalized health guidance using voice and text interactions.

---

## 🚀 Features

- **Voice & Chat Assistant**: Conversational agent with speech input and TTS feedback.
- **Intelligent Food Classifier & Calorie Tracking**: Recognizes meals, portions, calculates calories and macronutrients, and flags nutritional insights.
- **Interactive Wellness Dashboard**: Track calories, macros, hydration, and logs across daily timelines.
- **Extensive Food Database**: Built-in support for nutritional reference databases.
- **FastAPI Backend + React Vite Frontend**: Modern, responsive stack designed for speed and simplicity.

---

## 🛠️ Project Structure

```
wellora/
├── backend/
│   ├── agents/          # LangChain / LangGraph agents & tools
│   ├── core/            # Core configuration & utilities
│   ├── data/            # Nutritional datasets & CSVs
│   ├── routers/         # FastAPI API routes (chat, dashboard, users)
│   ├── database.py      # SQLAlchemy database configuration
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic data schemas
│   ├── requirements.txt # Python dependencies
│   └── main.py          # FastAPI application entry point
├── frontend/
│   ├── src/             # React application source code
│   ├── public/          # Static assets
│   ├── package.json     # Node dependencies & scripts
│   └── vite.config.js   # Vite configuration
└── README.md
```

---

## ⚡ Getting Started

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend development server
uvicorn main:app --reload --port 8000
```

The API documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run frontend development server
npm run dev
```

The application will be running at `http://localhost:5173`.

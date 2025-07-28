# 🚀 AI News Aggregator - Quick Start Guide

## Prerequisites Checklist

Before running the app, you need:

- [ ] **Supabase Account** (free tier works)
- [ ] **Google Gemini API Key** (free tier available)
- [ ] **Python 3.11+** installed
- [ ] **Git** installed

---

## 📋 Step-by-Step Setup

### 1. **Get Supabase Credentials** 

1. Go to [supabase.com](https://supabase.com) → Sign up (free)
2. Create a new project
3. Go to **Settings** → **API**
4. Copy these values:
   - **Project URL** (like `https://xyz.supabase.co`)
   - **Anon/Public Key** (starts with `eyJhbGciOi...`)

### 2. **Set Up Database Schema**

1. In your Supabase dashboard → **SQL Editor**
2. Copy and paste the entire contents of `migrations/001_initial_schema.sql`
3. Click **Run** to create the database tables

### 3. **Get Google Gemini API Key**

1. Go to [Google AI Studio](https://ai.google.dev/aistudio)
2. Click **Get API Key** → **Create API key**
3. Copy your API key (starts with `AIza...`)

### 4. **Configure Environment**

```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your actual credentials
# Replace the placeholder values:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_actual_anon_key
GEMINI_API_KEY=your_actual_gemini_key
```

### 5. **Install & Test**

```bash
# Activate virtual environment
source venv_linux/bin/activate

# Install dependencies (if not already done)
pip install -r requirements.txt

# Test your setup
python test_setup.py
```

### 6. **Start the Server**

```bash
# Start the FastAPI server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. **Test the API**

Open your browser and visit:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🧪 Testing the Application

### API Endpoints to Test:

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Trigger Article Fetch**
   ```bash
   curl -X POST http://localhost:8000/webhook/fetch \
     -H "Content-Type: application/json" \
     -d '{"sources": ["arxiv"]}'
   ```

3. **List Articles**
   ```bash
   curl "http://localhost:8000/articles?limit=5"
   ```

4. **Get Statistics**
   ```bash
   curl http://localhost:8000/stats
   ```

### Expected Behavior:

- **First Run**: No articles yet, but API should respond
- **After Fetch**: Articles start appearing from ArXiv
- **AI Analysis**: Articles get relevance scores 0-100
- **Deduplication**: Similar articles marked as duplicates

---

## 🔧 Troubleshooting

### Common Issues:

**"GOOGLE_API_KEY not found"**
- Check your `.env` file has the correct Gemini API key
- Make sure there are no spaces around the `=` sign

**"Database connection failed"**
- Verify your Supabase URL and key in `.env`
- Make sure you ran the database migration SQL

**"No articles found"**
- This is normal on first run
- Trigger a fetch: `POST /webhook/fetch`
- Check `/stats` endpoint to see fetch status

**"Module not found"**
- Make sure you're in the virtual environment: `source venv_linux/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

---

## 📊 Understanding the Data Flow

1. **Fetch** → Background task collects articles from ArXiv/HackerNews/RSS
2. **Analyze** → AI scores each article for AI/ML relevance (0-100)
3. **Embed** → Generate vector embeddings for similarity search
4. **Dedupe** → Compare embeddings to find duplicates (85% threshold)
5. **Store** → Save unique articles to Supabase with vectors
6. **Serve** → API returns processed articles with metadata

---

## 🎯 Quick Demo Commands

```bash
# 1. Start the server
python -m uvicorn src.main:app --reload

# 2. In another terminal, trigger article fetching
curl -X POST http://localhost:8000/webhook/fetch \
  -H "Content-Type: application/json" \
  -d '{"sources": ["arxiv", "hackernews"]}'

# 3. Wait 30-60 seconds, then check results
curl "http://localhost:8000/articles?limit=10&min_relevance_score=60"

# 4. Check system stats
curl http://localhost:8000/stats
```

---

## 🚀 Next Steps

Once everything is working:

1. **Set up RSS feeds** in the fetcher configuration
2. **Customize AI prompts** in `src/agents/prompts.py`
3. **Adjust similarity threshold** in configuration
4. **Set up scheduled fetching** for automation
5. **Build a frontend** using the API endpoints

For detailed API documentation, visit http://localhost:8000/docs when the server is running.
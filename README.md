# WhatsApp AI Bookmarks

Modern, AI-powered bookmark management system integrated with WhatsApp.

## Features

- 🤖 AI-powered search and organization using X.AI Grok
- 📱 WhatsApp integration for easy bookmark saving
- 🔍 Advanced semantic search capabilities
- 🏷️ Automatic tagging and categorization
- 📊 Content analysis and summarization
- 🌐 Multi-language support
- ⚡ Fast vector-based search using FAISS

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI/ML**: X.AI Grok, SentenceTransformers, FAISS
- **Infrastructure**: Vercel, PostgreSQL (Vercel Storage)
- **Integration**: Twilio (WhatsApp)

## Development

1. Clone the repository
```bash
git clone https://github.com/yourusername/whatsapp-ai-bookmarks.git
cd whatsapp-ai-bookmarks
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run development server
```bash
uvicorn app.main:app --reload
```

## Environment Variables

Required environment variables:
- `XAI_API_KEY`: X.AI Grok API key
- `TWILIO_ACCOUNT_SID`: Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Twilio Auth Token
- `TWILIO_PHONE_NUMBER`: WhatsApp phone number
- `DATABASE_URL`: PostgreSQL connection URL

## API Endpoints

- `POST /api/bookmarks`: Save a new bookmark
- `GET /api/bookmarks`: List all bookmarks
- `POST /api/search`: Search bookmarks
- `POST /api/whatsapp/webhook`: WhatsApp webhook endpoint

## Deployment

The application is configured for deployment on Vercel:

1. Connect your GitHub repository to Vercel
2. Configure environment variables in Vercel dashboard
3. Deploy!

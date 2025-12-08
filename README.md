# Cocktail Recipe Library

Extract cocktail recipes from screenshots using AI (Claude Vision) and organize them in a searchable library.

## Features

- **AI Recipe Extraction** - Upload a screenshot and Claude Vision extracts ingredients, instructions, and metadata
- **Smart Categorization** - Recipes are automatically categorized by template (Sour, Old Fashioned, Martini, etc.), spirit, glassware, and serving style
- **Mobile Friendly** - PWA support for easy access from your phone
- **Multiple Upload Methods** - Drag & drop, paste from clipboard, URL, or file picker

## Tech Stack

- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **Frontend**: Next.js 14 + Tailwind CSS
- **AI**: Anthropic Claude Vision API

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Run
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Deploy to Railway

See [DEPLOY.md](./DEPLOY.md) for detailed instructions.

Quick deploy:
1. Push to GitHub
2. Connect repo to Railway
3. Add environment variables:
   - Backend: `ANTHROPIC_API_KEY`
   - Frontend: `NEXT_PUBLIC_API_URL`

## License

MIT

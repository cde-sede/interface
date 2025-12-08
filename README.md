# Flask + React + Vite + TypeScript

A barebone fullstack application with Flask backend serving React frontend static files.

## Project Structure

```
.
├── backend/          # Flask backend
│   ├── app.py
│   ├── requirements.txt
│   └── static/       # Built frontend files (generated)
└── frontend/         # React + Vite + TypeScript frontend
    ├── src/
    ├── vite.config.ts
    └── package.json
```

## Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Development Mode

Run both servers separately for development with hot reload:

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then open your browser to `http://localhost:5173`. The Vite dev server will proxy API requests to the Flask backend at `http://localhost:5000`.

## Production Mode

Build the frontend and serve it from Flask:

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Run the Flask server:
   ```bash
   cd backend
   python app.py
   ```

Then open your browser to `http://localhost:5000`. Flask will serve both the API endpoints and the static frontend files.

## Available API Endpoints

- `GET /api/health` - Health check endpoint
- `GET /api/hello` - Returns a hello message

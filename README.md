# DocForge

Simple MVP web app for converting Word documents, images, and text to PDF.

## Project Structure

```text
DocForge/
  frontend/  Next.js + Tailwind CSS app
  backend/   FastAPI conversion API
```

## Requirements

- Node.js 20+
- Python 3.11+
- LibreOffice installed and available as `soffice` for Word to PDF conversion

If LibreOffice is not on PATH, set:

```powershell
$env:LIBREOFFICE_PATH="C:\Program Files\LibreOffice\program\soffice.exe"
```

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API endpoints:

- `POST /api/word-to-pdf`
- `POST /api/image-to-pdf`
- `POST /api/text-to-pdf`

## Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

The frontend expects the backend at `http://localhost:8000`. To use a different API URL, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deploy

DocForge has two parts:

- Frontend: deploy `frontend/` to Vercel as a Next.js app.
- Backend: deploy `backend/` to Render as a Docker web service.

Backend environment variables:

```env
FRONTEND_ORIGINS=https://your-frontend-domain.vercel.app
```

Frontend environment variables:

```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.onrender.com
```

For Render, the repository includes `render.yaml` and `backend/Dockerfile`.
The Docker image installs LibreOffice Writer for Word to PDF conversion.

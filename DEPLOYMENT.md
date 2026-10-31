# Deploying INFRANOX to Vercel

INFRANOX is configured for deployment on **Vercel** with zero configuration required.

## 1. Quick Deploy Frontend on Vercel

1. Push your repository to **GitHub**:
   ```bash
   git init
   git add .
   git commit -m "feat: infranox production react frontend"
   git remote add origin https://github.com/<your-username>/infranox.git
   git push -u origin main
   ```

2. Go to **[vercel.com](https://vercel.com)**:
   - Click **Add New Project**.
   - Import your GitHub repository.
   - Vercel will automatically detect `vercel.json` in the root:
     - **Build Command:** `cd frontend && npm install && npm run build`
     - **Output Directory:** `frontend/dist`
   - Click **Deploy**.

3. In Vercel Project Settings &rarr; **Environment Variables**, add:
   ```env
   VITE_API_BASE_URL=https://your-infranox-backend-api.com
   ```
   *(If deploying backend separately on Render, Railway, Fly.io, or AWS).*

---

## 2. Deploying the Python FastAPI Backend

The backend runs `server.py` using **Uvicorn / FastAPI**:
- Deploy on **Railway**, **Render**, or **Fly.io**:
  - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
  - **Environment Variables:**
    - `SARVAM_API_KEY`: *(Optional)* Your Sarvam AI API subscription key from [sarvam.ai](https://www.sarvam.ai).
- The FastAPI backend includes CORS enabled for all origins, allowing your Vercel frontend domain to connect seamlessly.

---

## 3. Local Development

- **FastAPI Backend & Production App:** `http://localhost:8000`
- **Vite React Dev Server (HMR):** `http://localhost:5173`
- **Swagger API Docs:** `http://localhost:8000/docs`


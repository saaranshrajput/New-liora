# Liora

Liora is a FastAPI-based solar recommendation application with static frontend pages.

## Project layout

- `frontend/pages/` contains the HTML pages.
- `frontend/css/` contains the stylesheets.
- `frontend/js/` contains the browser scripts.
- `app/` contains the FastAPI backend, database code, schemas, and utilities.
- Deployment files such as `Procfile`, `Dockerfile`, and `requirements.txt` remain at the project root.

## Deployment

This repo is set up for permanent hosting with a provider like Render, Railway, or Heroku.

### Recommended deploy flow

1. Push the repo to GitHub.
2. Connect the GitHub repository to your host.
3. Use `uvicorn app.main:app --host 0.0.0.0 --port $PORT` or the provided `Procfile`.
4. Ensure the host builds from `requirements.txt` and uses `runtime.txt`.

## Deploying to Render

1. In Render, create a new Web Service.
2. Connect to the GitHub repo: `saaranshrajput/New-liora`.
3. Set the branch to `master`.
4. Use build command:

```bash
pip install -r requirements.txt
```

5. Use start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. Set `Health Check Path` to `/api`.

7. Optionally add a `DATABASE_URL` environment variable if you provision a Postgres database; otherwise the app uses `sqlite:///./liora.db` by default.
8. Set `PUBLIC_URL` or `ALLOWED_ORIGINS` to your live frontend origin if the API and frontend are hosted on different domains (for example, `https://liora.example.com`). When omitted, the app still allows local development origins.

## Production notes

- The app currently uses SQLite at `liora.db`.
- For a more reliable production deployment, switch to PostgreSQL or MySQL.
- Do not commit `venv/` or `.env` to GitHub.

### AI chatbot setup

The chatbot uses an OpenAI-compatible chat API. Keep the key on the server and set it as an environment variable:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

Optional settings are `OPENAI_MODEL` (defaults to `gpt-4o-mini`) and `OPENAI_API_URL` (defaults to OpenAI's chat completions endpoint). Configure the same variables in your hosting provider before publishing. The browser never receives the API key.

### Contact form setup

The Contact us form sends messages through Resend. Set `RESEND_API_KEY` on the server before publishing. You can optionally set `CONTACT_FROM_EMAIL` to a verified Resend sender address; otherwise the development sender is used.

## Making changes after publishing

Yes — you can make changes after publishing.

1. Update your code locally.
2. Commit changes to git.
3. Push to GitHub.
4. Your hosting provider can auto-deploy or redeploy from the updated branch.

## Local startup

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

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

The chatbot uses an OpenAI-compatible chat API. Keep the key on the server. For local development, the app loads a project-root `.env` file (without overriding environment variables already set by the host):

```powershell
OPENAI_API_KEY=your-api-key
```

Optional settings are `OPENAI_MODEL` (defaults to `gpt-4o-mini`) and `OPENAI_API_URL` (defaults to `https://api.openai.com/v1/chat/completions`). Set these as environment variables in your hosting provider before publishing. The browser never receives the API key.

### Contact form setup

The Contact us form sends messages through Resend. All three variables are required: `RESEND_API_KEY`, `CONTACT_FROM_EMAIL`, and `CONTACT_TO_EMAIL`. Set `CONTACT_FROM_EMAIL` to a sender on a domain verified with Resend and `CONTACT_TO_EMAIL` to the inbox that should receive contact messages. Resend's `onboarding@resend.dev` sender is restricted to testing and may only send to the Resend account's verified email; use a verified domain for production delivery.

### Account recovery and social sign-in

Password recovery sends a single-use link that expires after 30 minutes. It uses the same Resend integration as the contact form, so configure `RESEND_API_KEY` and a verified `CONTACT_FROM_EMAIL` in Render. Set `PUBLIC_URL` to the service's public HTTPS URL (for example, `https://liora.example.com`) so reset links point to the correct site.

Google and Apple sign-in are enabled only when their client IDs are configured:

- `GOOGLE_CLIENT_ID`: a Google OAuth web client ID. Add the Render site origin to its authorized JavaScript origins.
- `APPLE_CLIENT_ID`: the Apple Services ID. Configure the website domain and the `/login-page` return URL in Apple Developer.

The client IDs are public identifiers, not private keys. Do not add provider secrets to frontend code.

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

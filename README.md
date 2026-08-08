# Liora

Liora is a FastAPI-based solar recommendation application with static frontend pages.

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

## Production notes

- The app currently uses SQLite at `liora.db`.
- For a more reliable production deployment, switch to PostgreSQL or MySQL.
- Do not commit `venv/` or `.env` to GitHub.

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

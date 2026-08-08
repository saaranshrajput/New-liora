# Liora

Liora is a FastAPI-based solar recommendation application with static frontend pages.

## Deployment

This repo is set up for permanent hosting with a provider like Render, Railway, or Heroku.

### Recommended deploy flow

1. Push the repo to GitHub.
2. Connect the GitHub repository to your host.
3. Use `uvicorn app.main:app --host 0.0.0.0 --port $PORT` or the provided `Procfile`.
4. Ensure the host builds from `requirements.txt` and uses `runtime.txt`.

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

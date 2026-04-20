# Admin Portal

React + TypeScript admin portal for UGDatabase.

## Local development

1. Install dependencies:

```bash
npm install
```

2. Start dev server:

```bash
npm run dev
```

3. Required local env vars (for example in `.env.local`):

```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_GCS_CLIENT_ID=<web-client-id>.apps.googleusercontent.com
```

## Cloud Run deployment

Use the deploy script from the repo root or from this folder.

Required environment variables:
- `VITE_API_URL` (must include `/api/v1`)
- `VITE_GCS_CLIENT_ID` (Google OAuth Web client ID)

Example:

```bash
VITE_API_URL=https://backend-<hash>-<region>.run.app/api/v1 \
VITE_GCS_CLIENT_ID=<web-client-id>.apps.googleusercontent.com \
./scripts/deploy-cloud-run.sh
```

Optional overrides:
- `PROJECT_ID` (default `ultrasound-guidance`)
- `REGION` (default `us-east1`)
- `SERVICE_NAME` (default `admin-portal`)
- `ALLOW_UNAUTHENTICATED` (`true` by default)

## Google OAuth checklist

If Google sign-in shows "doesn't comply with Google's OAuth 2.0 policy":

1. Open Google Cloud Console > APIs & Services > Credentials.
2. Open the OAuth 2.0 Web client used by `VITE_GCS_CLIENT_ID`.
3. Add origins under **Authorized JavaScript origins**:
   - deployed Cloud Run URL, for example `https://admin-portal-<hash>-<region>.run.app`
   - `http://localhost:5173` for local development
4. If OAuth consent is in Testing mode, add your account to **OAuth consent screen > Test users**.

## Backend CORS requirement

The backend must allow the admin portal origin in `ALLOWED_ORIGINS`.
Use backend deploy with:

```bash
ADMIN_PORTAL_ORIGIN=https://admin-portal-<hash>-<region>.run.app ./scripts/deploy-cloud-run.sh
```

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GCS_CLIENT_ID: string
  readonly VITE_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

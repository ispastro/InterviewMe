export const config = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  WS_BASE_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  JWT_STORAGE_KEY: 'interviewme_token',
  REFRESH_TOKEN_KEY: 'interviewme_refresh_token',
} as const;
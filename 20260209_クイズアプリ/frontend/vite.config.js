import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      // WebSocket（バックエンドも /api/ws を持つのでパス書き換えなし）
      '/api/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
      // API 呼び出し（バックエンドが /api/ プレフィックスを持つのでそのまま転送）
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // アップロード画像（バックエンドが /uploads のまま配信）
      '/uploads': 'http://localhost:8000',
    },
  },
})

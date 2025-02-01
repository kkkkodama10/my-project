import express from 'express';
import cors from 'cors';

const app = express();
const PORT = 3000;  // フロントエンドのサーバーポート

// CORSの有効化（必要に応じて変更）
app.use(cors());

// 静的ファイルの提供 (OpenAPIで生成したフロントエンドコード)
app.use(express.static('dist'));

// サーバー起動
app.listen(PORT, () => {
    console.log(`Frontend running at http://localhost:${PORT}`);
});

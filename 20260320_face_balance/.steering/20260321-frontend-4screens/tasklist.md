# タスクリスト: フロントエンド4画面

## フェーズ1: 基盤セットアップ

- [x] `main.tsx` を QueryClient + BrowserRouter で更新
- [x] `api/client.ts` を作成（axios インスタンス + 型定義 + API 関数）

## フェーズ2: 共通コンポーネント

- [x] `components/Layout.tsx` を作成（ナビゲーションバー + Outlet）
- [x] `components/StatusBadge.tsx` を作成（ステータスバッジ）
- [x] `components/Toast.tsx` を作成（エラートースト）

## フェーズ3: PersonListPage

- [x] `pages/PersonListPage.tsx` を作成
  - [x] 人物一覧をカード表示
  - [x] 人物追加フォーム
  - [x] 人物削除ボタン
  - [x] カードクリックで詳細へ遷移

## フェーズ4: PersonDetailPage

- [x] `pages/PersonDetailPage.tsx` を作成
  - [x] 人物名・画像一覧表示
  - [x] ファイルアップロード
  - [x] ステータスバッジ表示
  - [x] error メッセージ表示
  - [x] ポーリング（3秒間隔）
  - [x] 画像削除ボタン
  - [x] 一覧へ戻るリンク

## フェーズ5: ComparePage

- [x] `pages/ComparePage.tsx` を作成
  - [x] ドロップダウン2つで人物選択
  - [x] 「比較する」ボタンでスコア表示
  - [x] キャッシュバッジ表示
  - [x] 比較履歴へのリンク

## フェーズ6: HistoryPage

- [x] `pages/HistoryPage.tsx` を作成
  - [x] 比較結果一覧（日時降順）
  - [x] 人物名・スコア・有効/無効ステータス表示
  - [x] 比較ページへ戻るリンク

## フェーズ7: App.tsx Router 設定

- [x] `App.tsx` を React Router v6 でルーティング設定

## フェーズ8: 動作確認

- [x] npm run build が通ることを確認
- [x] TypeScript エラーがないことを確認（tsc --noEmit）

## フェーズ9: 振り返り

- [x] tasklist.md に振り返り記録

---

## 実装後の振り返り

**実装完了日**: 2026-03-21

**計画と実績の差分**:
- Tailwind CSS の設定ファイル（tailwind.config.ts, postcss.config.js, index.css）の追加が必要だった（計画に含まれていなかった）
- docker-compose.yml の volumes が `./frontend/src:/app/src` のみだったため、設定ファイル追加後にイメージ再ビルドが必要だった
- バックエンドの `ImageListResponse` に `metadata_` フィールドが含まれていなかったため、追加した
- `refetchInterval` の `typeof images` 参照によるTypeScript循環参照エラーを `Image[]` 明示型キャストで解決

**実装検証後の修正**:
- `PersonDetailPage.tsx`: `refetchInterval` コールバックで `typeof images` → `Image[] | undefined` に修正（TS循環参照エラー解消）
- `ComparePage.tsx`: 同一人物 A/B 選択時の送信ガード（`aId === bId`）を追加
- `.eslintrc.cjs` 追加: ESLint 設定ファイルが欠如していたため新規作成
- `backend/app/schemas/image.py`: `ImageListResponse` に `metadata_: dict | None = None` 追加（エラーメッセージ表示に必要）

**学んだこと**:
- docker-compose で src のみマウントしている場合、設定ファイルはイメージ再ビルドが必要
- TanStack Query v5 の `refetchInterval` に関数を渡す場合、戻り値型を `: number | false` と明示的に指定しないと TypeScript の循環参照エラーが発生する
- Tailwind CSS が正しく処理されているかは CSS バンドルサイズで確認可能（0.06 kB → 11.84 kB）

**次回への改善提案**:
- `docker-compose.yml` のフロントエンドボリュームマウントを `./frontend:/app` + `node_modules` の anonymous volume 方式に変更すると、設定ファイル変更時の再ビルドが不要になる
- テスト基盤（Vitest + React Testing Library）の整備
- `Layout.tsx` のアクティブ判定を `useMatch` に変更し、サブパス（`/persons/:id`）でも「人物一覧」がアクティブになるよう改善

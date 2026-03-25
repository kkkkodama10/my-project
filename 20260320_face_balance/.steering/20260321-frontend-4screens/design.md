# 設計: フロントエンド4画面

## ディレクトリ構成

```
frontend/src/
├── api/
│   └── client.ts          # axios インスタンス + 各 API 関数
├── components/
│   ├── Layout.tsx          # ナビゲーションバー + Outlet
│   ├── StatusBadge.tsx     # 画像ステータスバッジ
│   └── Toast.tsx           # エラートースト（シンプル実装）
├── pages/
│   ├── PersonListPage.tsx  # / 人物一覧
│   ├── PersonDetailPage.tsx # /persons/:id 人物詳細
│   ├── ComparePage.tsx     # /compare 比較
│   └── HistoryPage.tsx     # /history 比較履歴
├── App.tsx                 # Router 設定
└── main.tsx                # エントリポイント（QueryClient + BrowserRouter）
```

## API クライアント設計（api/client.ts）

```typescript
// 型定義
type Person = { id: string; name: string; image_count: number; created_at: string }
type Image  = { id: string; person_id: string; status: string; thumbnail_path: string | null; created_at: string; metadata_?: { error?: string } }
type ComparisonResult = { score: number; is_cached: boolean }
type ComparisonItem   = { id: string; person_a_id: string; person_b_id: string; score: number; is_valid: boolean; created_at: string }

// API 関数
createPerson(name: string): Promise<Person>
listPersons(): Promise<Person[]>
deletePerson(id: string): Promise<void>
listImages(personId: string): Promise<Image[]>
uploadImage(personId: string, file: File): Promise<void>
deleteImage(imageId: string): Promise<void>
comparePersons(aId: string, bId: string): Promise<ComparisonResult>
listComparisons(): Promise<ComparisonItem[]>
```

## TanStack Query キー設計

| キー | 用途 |
|------|------|
| `['persons']` | 人物一覧 |
| `['images', personId]` | 人物の画像一覧（ポーリング対象） |
| `['comparisons']` | 比較履歴一覧 |

## ポーリング設計

画像一覧クエリで `analyzed` でないステータスの画像が1枚でもある場合:
`refetchInterval: 3000` を動的に設定してポーリングを継続する。

```typescript
const hasProcessing = images.some(img => !['analyzed', 'error'].includes(img.status))
useQuery({ ..., refetchInterval: hasProcessing ? 3000 : false })
```

## エラーハンドリング

- axios インスタンスにレスポンスインターセプターを設定
- `detail` フィールドを取り出してトースト表示
- Toast はシンプルな固定位置 div（右上）で実装
- グローバル状態不要 → `useState` でコンポーネント内管理

## スタイル方針

- Tailwind CSS のユーティリティクラスのみ使用
- カラーパレット: グレー系（bg-gray-50/100/800）+ アクセント blue-500/600
- ステータスバッジカラー:
  - `analyzed` → green
  - `error` → red
  - `validating`/`analyzing` → yellow（アニメーション付き）
  - `uploaded` → gray

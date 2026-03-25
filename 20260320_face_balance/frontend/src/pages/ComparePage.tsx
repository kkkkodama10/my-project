import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  listPersons,
  comparePersons,
  type ComparisonResult,
  type FeatureBreakdownItem,
} from '../api/client'
import Toast from '../components/Toast'

const CATEGORY_ORDER = ['距離', '角度', '比率'] as const

function groupByCategory(items: FeatureBreakdownItem[]) {
  const groups: Record<string, FeatureBreakdownItem[]> = {}
  for (const cat of CATEGORY_ORDER) {
    groups[cat] = items.filter((item) => item.category === cat)
  }
  return groups
}

function similarityColor(similarity: number): string {
  if (similarity >= 90) return 'bg-green-500'
  if (similarity >= 70) return 'bg-blue-500'
  if (similarity >= 50) return 'bg-yellow-500'
  return 'bg-red-400'
}

export default function ComparePage() {
  const [aId, setAId] = useState('')
  const [bId, setBId] = useState('')
  const [result, setResult] = useState<ComparisonResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isBreakdownOpen, setIsBreakdownOpen] = useState(false)

  const handleError = useCallback((e: unknown) => {
    setError(e instanceof Error ? e.message : String(e))
  }, [])

  const { data: persons = [], isLoading } = useQuery({
    queryKey: ['persons'],
    queryFn: listPersons,
  })

  const compareMutation = useMutation({
    mutationFn: () => comparePersons(aId, bId),
    onSuccess: (data) => {
      setResult(data)
      setIsBreakdownOpen(false)
    },
    onError: handleError,
  })

  const handleCompare = (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    compareMutation.mutate()
  }

  return (
    <>
      {error && <Toast message={error} onClose={() => setError(null)} />}

      <h1 className="text-2xl font-bold text-gray-800 mb-6">顔比較</h1>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <form onSubmit={handleCompare} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm max-w-md">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              人物 A
            </label>
            <select
              value={aId}
              onChange={(e) => setAId(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">選択してください</option>
              {persons.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              人物 B
            </label>
            <select
              value={bId}
              onChange={(e) => setBId(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">選択してください</option>
              {persons.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={!aId || !bId || aId === bId || compareMutation.isPending}
            className="w-full bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white py-2 rounded font-medium text-sm"
          >
            {compareMutation.isPending ? '比較中...' : '比較する'}
          </button>

          {/* 結果表示 */}
          {result && (
            <div className="mt-6 p-4 bg-gray-50 rounded border border-gray-200">
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <span className="text-3xl font-bold text-blue-600">
                    {result.score.toFixed(1)}%
                  </span>
                  {result.is_cached && (
                    <span className="bg-gray-200 text-gray-600 text-xs px-2 py-0.5 rounded">
                      キャッシュ
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500">類似度スコア</p>
              </div>

              {/* ブレークダウン表示 */}
              {result.breakdown && result.breakdown.length > 0 && (
                <div className="mt-4">
                  <button
                    type="button"
                    onClick={() => setIsBreakdownOpen(!isBreakdownOpen)}
                    className="text-sm text-blue-500 hover:text-blue-700 font-medium"
                  >
                    {isBreakdownOpen ? '▾ 詳細を閉じる' : '▸ 詳細を見る'}
                  </button>

                  {isBreakdownOpen && (
                    <div className="mt-3 space-y-4">
                      <p className="text-xs text-gray-400">
                        総合スコアはAIが算出。詳細は顔のパーツごとの比較です。
                      </p>
                      {Object.entries(groupByCategory(result.breakdown)).map(
                        ([category, items]) =>
                          items.length > 0 && (
                            <div key={category}>
                              <h3 className="text-xs font-semibold text-gray-500 mb-2">
                                {category}
                              </h3>
                              <div className="space-y-2">
                                {items.map((item) => (
                                  <div key={item.key}>
                                    <div className="flex justify-between text-xs mb-0.5">
                                      <span className="text-gray-700">{item.label}</span>
                                      <span className="text-gray-500 font-medium">
                                        {item.similarity.toFixed(1)}%
                                      </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                                      <div
                                        className={`h-1.5 rounded-full ${similarityColor(item.similarity)}`}
                                        style={{ width: `${Math.min(item.similarity, 100)}%` }}
                                      />
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ),
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </form>
      )}

      <div className="mt-6">
        <Link to="/history" className="text-sm text-blue-500 hover:underline">
          比較履歴を見る →
        </Link>
      </div>
    </>
  )
}

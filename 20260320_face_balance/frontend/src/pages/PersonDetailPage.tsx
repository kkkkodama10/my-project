import { useState, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listPersons, listImages, uploadImage, deleteImage, type Image } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import Toast from '../components/Toast'

export default function PersonDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleError = useCallback((e: unknown) => {
    setError(e instanceof Error ? e.message : String(e))
  }, [])

  const { data: persons = [] } = useQuery({
    queryKey: ['persons'],
    queryFn: listPersons,
  })
  const person = persons.find((p) => p.id === id)

  const { data: images = [], isLoading } = useQuery({
    queryKey: ['images', id],
    queryFn: () => listImages(id!),
    enabled: !!id,
    refetchInterval: (query): number | false => {
      const data = query.state.data as Image[] | undefined
      if (!data) return false
      const hasProcessing = data.some(
        (img: Image) => !['analyzed', 'error'].includes(img.status),
      )
      return hasProcessing ? 3000 : false
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadImage(id!, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images', id] })
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      if (fileInputRef.current) fileInputRef.current.value = ''
    },
    onError: handleError,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteImage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images', id] })
      queryClient.invalidateQueries({ queryKey: ['persons'] })
    },
    onError: handleError,
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadMutation.mutate(file)
  }

  return (
    <>
      {error && <Toast message={error} onClose={() => setError(null)} />}

      <div className="mb-6">
        <Link to="/" className="text-sm text-blue-500 hover:underline">
          ← 一覧へ戻る
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        {person?.name ?? '人物詳細'}
      </h1>

      {/* アップロードエリア */}
      <div className="mb-8 flex items-center gap-3">
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadMutation.isPending}
          className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-medium"
        >
          {uploadMutation.isPending ? 'アップロード中...' : '画像を追加'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
        />
        <span className="text-xs text-gray-400">JPEG / PNG 対応</span>
      </div>

      {/* 画像一覧 */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : images.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-12">
          画像が登録されていません
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {images.map((image) => (
            <div
              key={image.id}
              className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm flex gap-4 items-start"
            >
              {/* サムネイル */}
              {image.thumbnail_path ? (
                <img
                  src={image.thumbnail_path}
                  alt="thumbnail"
                  className="w-20 h-20 object-cover rounded border border-gray-100 flex-shrink-0"
                />
              ) : (
                <div className="w-20 h-20 bg-gray-100 rounded flex items-center justify-center flex-shrink-0">
                  <span className="text-gray-400 text-xs">No image</span>
                </div>
              )}

              {/* 情報 */}
              <div className="flex-1 min-w-0">
                <StatusBadge status={image.status} />
                {image.status === 'error' && image.metadata_?.error && (
                  <p className="text-xs text-red-600 mt-1 break-words">
                    {image.metadata_.error}
                  </p>
                )}
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(image.created_at).toLocaleString('ja-JP')}
                </p>
                <div className="flex items-center gap-3 mt-2">
                  <button
                    onClick={() => deleteMutation.mutate(image.id)}
                    disabled={deleteMutation.isPending}
                    className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
                  >
                    削除
                  </button>
                  {image.status === 'analyzed' && (
                    <a
                      href={`/api/images/${image.id}/landmarks`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-500 hover:underline"
                    >
                      ランドマーク確認
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

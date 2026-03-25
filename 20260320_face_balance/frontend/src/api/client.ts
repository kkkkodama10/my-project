import axios from 'axios'

// --- 型定義 ---

export type Person = {
  id: string
  name: string
  image_count: number
  created_at: string
}

export type Image = {
  id: string
  person_id: string
  status: string
  thumbnail_path: string | null
  created_at: string
  metadata_?: { error?: string }
}

export type FeatureBreakdownItem = {
  key: string
  label: string
  category: string
  similarity: number
  value_a: number
  value_b: number
}

export type ComparisonResult = {
  score: number
  is_cached: boolean
  breakdown: FeatureBreakdownItem[] | null
}

export type ComparisonItem = {
  id: string
  person_a_id: string
  person_b_id: string
  score: number
  is_valid: boolean
  created_at: string
}

// --- axios インスタンス ---

export const apiClient = axios.create({
  baseURL: '/api',
})

// エラーレスポンスのインターセプター（detail フィールド抽出用）
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const detail =
      error?.response?.data?.detail ?? error?.message ?? 'エラーが発生しました'
    const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    return Promise.reject(new Error(message))
  },
)

// --- API 関数 ---

export async function createPerson(name: string): Promise<Person> {
  const res = await apiClient.post<Person>('/persons', { name })
  return res.data
}

export async function listPersons(): Promise<Person[]> {
  const res = await apiClient.get<Person[]>('/persons')
  return res.data
}

export async function deletePerson(id: string): Promise<void> {
  await apiClient.delete(`/persons/${id}`)
}

export async function listImages(personId: string): Promise<Image[]> {
  const res = await apiClient.get<Image[]>(`/persons/${personId}/images`)
  return res.data
}

export async function uploadImage(personId: string, file: File): Promise<void> {
  const form = new FormData()
  form.append('file', file)
  await apiClient.post(`/persons/${personId}/images`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export async function deleteImage(imageId: string): Promise<void> {
  await apiClient.delete(`/images/${imageId}`)
}

export async function comparePersons(
  aId: string,
  bId: string,
): Promise<ComparisonResult> {
  const res = await apiClient.post<ComparisonResult>(
    `/persons/${aId}/compare/${bId}`,
  )
  return res.data
}

export async function listComparisons(): Promise<ComparisonItem[]> {
  const res = await apiClient.get<ComparisonItem[]>('/comparisons')
  return res.data
}

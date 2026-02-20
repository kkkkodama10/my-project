/**
 * fetch ラッパー — credentials:include を固定
 * FormData の場合は Content-Type を自動設定に任せる
 */
async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData
  const headers = isFormData
    ? {}
    : { 'Content-Type': 'application/json' }

  const res = await fetch(path, {
    credentials: 'include',
    headers: { ...headers, ...(options.headers || {}) },
    ...options,
  })
  return res
}

export function get(path) {
  return request(path, { method: 'GET' })
}

export function post(path, body) {
  return request(path, {
    method: 'POST',
    body: body !== undefined ? (body instanceof FormData ? body : JSON.stringify(body)) : undefined,
  })
}

export function put(path, body) {
  return request(path, {
    method: 'PUT',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

export function del(path) {
  return request(path, { method: 'DELETE' })
}

export default { get, post, put, del }

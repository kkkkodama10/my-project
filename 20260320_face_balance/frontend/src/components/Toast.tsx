import { useEffect } from 'react'

type Props = {
  message: string
  onClose: () => void
}

export default function Toast({ message, onClose }: Props) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm bg-red-600 text-white px-4 py-3 rounded shadow-lg flex items-start gap-3">
      <span className="flex-1 text-sm">{message}</span>
      <button
        onClick={onClose}
        className="text-white opacity-70 hover:opacity-100 text-lg leading-none"
      >
        ×
      </button>
    </div>
  )
}

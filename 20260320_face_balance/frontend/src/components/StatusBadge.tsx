type Props = {
  status: string
}

const statusConfig: Record<string, { label: string; className: string }> = {
  analyzed: {
    label: '解析済み',
    className: 'bg-green-100 text-green-800',
  },
  error: {
    label: 'エラー',
    className: 'bg-red-100 text-red-800',
  },
  analyzing: {
    label: '解析中',
    className: 'bg-yellow-100 text-yellow-800 animate-pulse',
  },
  validating: {
    label: '検証中',
    className: 'bg-yellow-100 text-yellow-800 animate-pulse',
  },
  uploaded: {
    label: 'アップロード済み',
    className: 'bg-gray-100 text-gray-700',
  },
}

export default function StatusBadge({ status }: Props) {
  const config = statusConfig[status] ?? {
    label: status,
    className: 'bg-gray-100 text-gray-700',
  }

  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}

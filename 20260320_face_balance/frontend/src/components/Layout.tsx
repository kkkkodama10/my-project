import { Link, Outlet, useLocation } from 'react-router-dom'

const navItems = [
  { to: '/', label: '人物一覧' },
  { to: '/compare', label: '比較する' },
  { to: '/history', label: '比較履歴' },
]

export default function Layout() {
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6">
        <span className="font-bold text-gray-800 text-lg mr-4">FaceGraph</span>
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={`text-sm font-medium ${
              pathname === item.to
                ? 'text-blue-600 border-b-2 border-blue-600 pb-0.5'
                : 'text-gray-600 hover:text-blue-500'
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <main className="max-w-4xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}

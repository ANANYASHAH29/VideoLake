import { useEffect, useState } from 'react'

export default function Stats({ api }) {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch(`${api}/api/dashboard/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => setStats({}))
  }, [api])

  if (!stats) return <p>Loading stats...</p>

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Object.entries(stats).map(([key, value]) => (
        <div key={key} className="p-4 bg-white rounded shadow">
          <div className="text-sm text-gray-500 capitalize">{key.replace(/_/g, ' ')}</div>
          <div className="text-xl font-semibold">
            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
          </div>
        </div>
      ))}
    </div>
  )
}

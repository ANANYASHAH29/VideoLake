import { useEffect, useState } from 'react'

export default function DuplicateClusters({ api }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch(`${api}/api/dashboard/clusters`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ clusters: 0, cluster_sizes: {} }))
  }, [api])

  if (!data) return <p>Loading clusters...</p>

  const sizes = data.cluster_sizes || {}
  const entries = Object.entries(sizes)
    .sort((a, b) => Number(b[1]) - Number(a[1]))
    .slice(0, 40)

  return (
    <div>
      <p className="text-lg font-semibold mb-2">Total clusters: {data.clusters}</p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {entries.map(([cid, count]) => (
          <div key={cid} className="p-2 bg-white rounded shadow text-sm">
            cluster {cid}: {count}
          </div>
        ))}
      </div>
    </div>
  )
}

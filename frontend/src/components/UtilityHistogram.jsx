import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

export default function UtilityHistogram({ api }) {
  const [data, setData] = useState([])

  useEffect(() => {
    fetch(`${api}/api/dashboard/histogram`)
      .then((r) => r.json())
      .then((d) => {
        const points = d.bins
          .slice(0, -1)
          .map((bin, i) => ({ bin: bin.toFixed(2), count: d.counts[i] || 0 }))
        setData(points)
      })
      .catch(() => setData([]))
  }, [api])

  return (
    <div className="h-80 bg-white p-4 rounded shadow">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="bin" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#0f172a" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

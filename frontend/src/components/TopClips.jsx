import { useEffect, useState } from 'react'

export default function TopClips({ api }) {
  const [clips, setClips] = useState([])

  useEffect(() => {
    fetch(`${api}/api/dashboard/topclips?limit=20`)
      .then((r) => r.json())
      .then(setClips)
      .catch(() => setClips([]))
  }, [api])

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm bg-white rounded shadow">
        <thead>
          <tr className="bg-slate-100">
            <th className="p-2 text-left">ID</th>
            <th className="p-2 text-left">Video</th>
            <th className="p-2 text-left">Start</th>
            <th className="p-2 text-left">End</th>
            <th className="p-2 text-left">Utility</th>
            <th className="p-2 text-left">Selected</th>
          </tr>
        </thead>
        <tbody>
          {clips.map((c) => (
            <tr key={c.id} className="border-b">
              <td className="p-2">{c.id}</td>
              <td className="p-2">{c.video_id}</td>
              <td className="p-2">{(c.start_sec || 0).toFixed(1)}</td>
              <td className="p-2">{(c.end_sec || 0).toFixed(1)}</td>
              <td className="p-2">{(c.utility || 0).toFixed(3)}</td>
              <td className="p-2">{c.selected ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

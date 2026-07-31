import { useState } from 'react'

export default function ResearchResults({ api }) {
  const [videoId, setVideoId] = useState('')
  const [compression, setCompression] = useState(0.5)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function runEvaluation() {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch(`${api}/api/research/evaluate/${videoId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ compression }),
      })
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setResult({ error: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 items-center">
        <input
          type="number"
          value={videoId}
          onChange={(e) => setVideoId(e.target.value)}
          placeholder="Video ID"
          className="border p-2 rounded"
        />
        <input
          type="number"
          step="0.05"
          min="0"
          max="0.95"
          value={compression}
          onChange={(e) => setCompression(parseFloat(e.target.value))}
          className="border p-2 rounded"
        />
        <button
          onClick={runEvaluation}
          disabled={loading || !videoId}
          className="px-4 py-2 bg-slate-900 text-white rounded disabled:opacity-50"
        >
          {loading ? 'Running...' : 'Evaluate'}
        </button>
      </div>

      {result?.error && <p className="text-red-600">{result.error}</p>}

      {result?.baselines && (
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(result.baselines).map(([name, metrics]) => (
            <div key={name} className="bg-white p-4 rounded shadow">
              <h3 className="font-bold capitalize mb-2">
                {name.replace(/_/g, ' ')}
              </h3>
              <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                {JSON.stringify(metrics, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

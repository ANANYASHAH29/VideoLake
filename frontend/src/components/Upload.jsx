import { useState } from 'react'

export default function Upload({ api }) {
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`${api}/api/ingestion/upload`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      setMessage(`Uploaded ${data.filename} (id=${data.video_id}, status=${data.status})`)
    } catch (err) {
      setMessage(`Error: ${err.message}`)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <input
        type="file"
        accept="video/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="block w-full"
      />
      <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
        Upload
      </button>
      {message && <p className="text-sm text-gray-700">{message}</p>}
    </form>
  )
}

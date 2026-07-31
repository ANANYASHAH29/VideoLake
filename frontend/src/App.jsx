import { useState } from 'react'
import Upload from './components/Upload'
import Stats from './components/Stats'
import UtilityHistogram from './components/UtilityHistogram'
import DuplicateClusters from './components/DuplicateClusters'
import TopClips from './components/TopClips'
import ResearchResults from './components/ResearchResults'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const tabs = ['Upload', 'Stats', 'Histogram', 'Clusters', 'Top Clips', 'Research']

export default function App() {
  const [active, setActive] = useState('Upload')

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800">
      <header className="bg-slate-900 text-white p-4 shadow">
        <h1 className="text-2xl font-bold">LakeVideo Dashboard</h1>
        <p className="text-sm text-slate-300">
          Curate hour-scale videos for foundation model training
        </p>
      </header>
      <nav className="flex gap-2 p-4 bg-white shadow-sm overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setActive(t)}
            className={`px-4 py-2 rounded whitespace-nowrap ${
              active === t ? 'bg-slate-900 text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {t}
          </button>
        ))}
      </nav>
      <main className="p-4">
        {active === 'Upload' && <Upload api={API} />}
        {active === 'Stats' && <Stats api={API} />}
        {active === 'Histogram' && <UtilityHistogram api={API} />}
        {active === 'Clusters' && <DuplicateClusters api={API} />}
        {active === 'Top Clips' && <TopClips api={API} />}
        {active === 'Research' && <ResearchResults api={API} />}
      </main>
    </div>
  )
}

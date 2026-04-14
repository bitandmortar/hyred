import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload,
  FileText,
  Briefcase,
  Zap,
  Activity,
  Server,
  Database,
  CheckCircle,
  AlertCircle,
  Download,
  Trash2,
  Cpu,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'

// ─── Config ──────────────────────────────────────────────────────────────────
const DEFAULT_PROFILE_NAME = import.meta.env.VITE_DEFAULT_PROFILE_NAME || ''
const DEFAULT_PROFILE_TITLE = import.meta.env.VITE_DEFAULT_PROFILE_TITLE || ''

// ─── Types ───────────────────────────────────────────────────────────────────

interface Document {
  name: string
  uploaded_at: string
  file_type: string
  size: number
}

interface AnalysisResult {
  name: string
  title: string
  top_skills: string[]
  experience_years: number
  achievements: string[]
  gaps: string[]
  strengths: string[]
  ats_score: number
}

interface SystemStatus {
  llm_model: string
  model_status: string
  document_count: number
  rag_status: string
}

type AppView = 'landing' | 'generating' | 'results'

// ─── Constants ───────────────────────────────────────────────────────────────

const API_BASE = '/api/hyred'

// ─── Components ──────────────────────────────────────────────────────────────

function BauhausHeader({ status }: { status: SystemStatus | null }) {
  return (
    <header className="shrink-0 w-full h-16 bg-[#fafaf3] border-b border-[#dadad4] flex justify-between items-center px-10">
        <div className="flex items-center gap-8">
            <span className="text-2xl font-black tracking-tighter text-[#b60020]">HYRED</span>
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-neutral-400">NEURAL_RESUME_ENGINE // V3_MIGRATION</span>
        </div>
        <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
                <div className={`w-2 h-2 ${status?.model_status === 'ready' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-[10px] font-black uppercase tracking-widest text-neutral-900">
                    {status?.llm_model || 'OFFLINE'}
                </span>
            </div>
            <span className="text-[10px] font-mono font-bold text-neutral-400 uppercase">
                {status?.document_count || 0} DOCUMENTS
            </span>
        </div>
    </header>
  )
}

export default function App() {
  const [view, setView] = useState<AppView>('landing')
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [generatedResume, setGeneratedResume] = useState('')
  const [generatedCoverLetter, setGeneratedCoverLetter] = useState('')
  const [generationStatus, setGenerationStatus] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [jobDescription, setJobDescription] = useState('')
  const [profileName, setProfileName] = useState(DEFAULT_PROFILE_NAME)
  const [profileTitle, setProfileTitle] = useState(DEFAULT_PROFILE_TITLE)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const triggerAnalysis = async (docName: string) => {
    setAnalyzing(docName)
    try {
      const res = await fetch(`${API_BASE}/documents/${docName}/analyze`)
      if (!res.ok) throw new Error('Analysis failed')
      const data = await res.json()
      setAnalysis(data)
      setView('results')
    } catch (e) {
      setError(`Failed to analyze ${docName}`)
    } finally {
      setAnalyzing(null)
    }
  }

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`)
      const data = await res.json()
      setStatus({
        llm_model: data.llm.model,
        model_status: data.ok ? 'ready' : 'error',
        document_count: data.rag.indexed_files,
        rag_status: 'ok'
      })
    } catch (e) {
      setError('Backend connection failed')
    }
  }

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`)
      const data = await res.json()
      // Map API fields to UI Document type
      const docs = data.files.map((f: any) => ({
        name: f.name,
        uploaded_at: '2026-04-08', // Logic for real date could be added
        file_type: f.file_type,
        size: f.size_kb * 1024
      }))
      setDocuments(docs)
    } catch (e) {
      console.error('Failed to fetch documents')
    }
  }

  useEffect(() => {
    fetchStatus()
    fetchDocuments()
  }, [])

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        body: formData
      })
      if (res.ok) {
        await fetchDocuments()
        await fetchStatus()
      } else {
        const data = await res.json()
        setError(data.detail || 'Upload failed')
      }
    } catch (e) {
      setError('Network error during upload')
    } finally {
      setUploading(false)
    }
  }

  const handleGenerate = async () => {
    if (!jobDescription) return
    setIsGenerating(true)
    setGeneratedResume('')
    setGeneratedCoverLetter('')
    setGenerationStatus('Initiating Neural Sequence...')
    setView('results')

    try {
      const response = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: jobDescription,
          profile_name: profileName,
          profile_title: profileTitle
        })
      })

      if (!response.body) throw new Error('No response body')
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let resumeAcc = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        
        const chunks = decoder.decode(value).split('\n').filter(Boolean)
        for (const chunk of chunks) {
          try {
            const data = json_parse_safe(chunk)
            if (data.type === 'status') {
              setGenerationStatus(data.message)
            } else if (data.type === 'chunk') {
              resumeAcc += data.text
              setGeneratedResume(resumeAcc)
            } else if (data.type === 'done') {
              setGeneratedResume(data.resume)
              setGeneratedCoverLetter(data.cover_letter)
              setGenerationStatus(null)
            } else if (data.type === 'error') {
              setError(data.message)
            }
          } catch (e) { /* partial chunk */ }
        }
      }
    } catch (e) {
      setError('Generation failed')
    } finally {
      setIsGenerating(false)
    }
  }

  const json_parse_safe = (str: string) => {
    try { return JSON.parse(str) } catch (e) { return {} }
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#fafaf3]">
      <BauhausHeader status={status} />
      
      <div className="flex-1 bauhaus-grid p-[2px] overflow-hidden">
        {/* Repository Sidebar (Col 1-3) */}
        <aside className="col-span-3 bg-[#eeeee8] flex flex-col p-10 overflow-y-auto no-scrollbar">
            <h2 className="text-[10px] font-black tracking-[0.2em] text-[#b60020] uppercase mb-10 pb-4 border-b border-[#dadad4]">Repository</h2>
            
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              className="hidden" 
              accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
            />

            <div 
              onClick={() => fileInputRef.current?.click()}
              className={`mb-10 p-8 border-2 border-dashed border-[#dadad4] bg-white flex flex-col items-center text-center cursor-pointer hover:border-[#b60020] transition-all ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
            >
                {uploading ? (
                  <Activity size={32} className="mb-4 text-[#b60020] animate-pulse" />
                ) : (
                  <Upload size={32} className="mb-4 text-neutral-300" />
                )}
                <span className="text-[10px] font-black uppercase tracking-widest text-neutral-400">
                  {uploading ? 'UPLOADING...' : 'Drop PDF / DOCX / TEXT / MD'}
                </span>
            </div>

            <div className="space-y-2">
                {documents.map(doc => (
                    <div 
                      key={doc.name} 
                      onClick={() => triggerAnalysis(doc.name)}
                      className={`p-4 bg-white border border-[#dadad4] hover:border-[#1d54c7] transition-all cursor-pointer group ${analyzing === doc.name ? 'border-[#b60020]' : ''}`}
                    >
                        <div className="flex items-center gap-3">
                            <FileText size={14} className="text-neutral-300 group-hover:text-[#1d54c7]" />
                            <div className="text-[11px] font-black uppercase truncate flex-1">{doc.name}</div>
                        </div>
                        <div className="mt-2 flex justify-between items-center text-[9px] font-mono text-neutral-400 font-bold uppercase">
                            <span>{(doc.size/1024).toFixed(1)} KB</span>
                            <span className="text-[#1d54c7] group-hover:underline">
                              {analyzing === doc.name ? 'ANALYZING...' : 'Analyze'}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </aside>

        {/* Generator Workspace (Col 4-8) */}
        {/* Generator Workspace (Col 4-8) */}
        <main className="col-span-5 bg-white flex flex-col overflow-hidden">
            <header className="h-14 border-b border-[#dadad4] flex px-8 justify-between items-center bg-[#fafaf3] shrink-0">
                <div className="flex gap-10">
                    <button className={`h-14 flex items-center font-black text-[10px] uppercase tracking-widest transition-all ${view !== 'results' ? 'text-[#b60020] border-b-2 border-[#b60020]' : 'text-neutral-400 hover:text-black'}`} onClick={() => setView('landing')}>Job Spec</button>
                    {(analysis || generatedResume) && (
                      <button className={`h-14 flex items-center font-black text-[10px] uppercase tracking-widest transition-all ${view === 'results' ? 'text-[#b60020] border-b-2 border-[#b60020]' : 'text-neutral-400 hover:text-black'}`} onClick={() => setView('results')}>Neural Result {isGenerating && '...'}</button>
                    )}
                </div>
            </header>

            <div className="flex-1 p-0 relative overflow-y-auto">
                {view !== 'results' ? (
                  <div className="w-full h-full flex flex-col">
                      <div className="flex gap-4 p-4 border-b border-neutral-200">
                          <input
                              className="flex-1 p-3 font-bold text-[12px] border border-neutral-200 outline-none focus:border-[#b60020] placeholder:text-neutral-300"
                              placeholder="YOUR NAME"
                              value={profileName}
                              onChange={(e) => setProfileName(e.target.value)}
                          />
                          <input
                              className="flex-1 p-3 font-bold text-[12px] border border-neutral-200 outline-none focus:border-[#b60020] placeholder:text-neutral-300"
                              placeholder="YOUR TITLE / ROLE"
                              value={profileTitle}
                              onChange={(e) => setProfileTitle(e.target.value)}
                          />
                      </div>
                      <textarea
                          className="flex-1 w-full p-10 font-bold text-[13px] leading-relaxed border-none outline-none resize-none placeholder:text-neutral-200"
                          placeholder="PASTE TARGET JOB DESCRIPTION // NEURAL ALIGNMENT..."
                          value={jobDescription}
                          onChange={(e) => setJobDescription(e.target.value)}
                      />
                  </div>
                ) : (
                  <div className="p-10 prose prose-slate max-w-none prose-sm">
                    {generatedResume ? (
                      <>
                        <ReactMarkdown>{generatedResume}</ReactMarkdown>
                        {generatedCoverLetter && (
                          <>
                            <hr className="my-10 border-[#dadad4]" />
                            <h2 className="text-[10px] font-black uppercase tracking-widest text-neutral-400 mb-6">Generated Cover Letter</h2>
                            <ReactMarkdown>{generatedCoverLetter}</ReactMarkdown>
                          </>
                        )}
                      </>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full opacity-30 py-20">
                         <Activity className="w-12 h-12 mb-4 animate-pulse" />
                         <span className="text-[10px] font-black uppercase tracking-widest">Awaiting Induction...</span>
                      </div>
                    )}
                  </div>
                )}
            </div>

            <footer className="shrink-0 h-28 p-8 border-t border-[#dadad4] bg-[#eeeee8] flex gap-4">
                <button 
                  onClick={handleGenerate}
                  disabled={!jobDescription || isGenerating}
                  className="flex-1 bg-[#b60020] text-white font-black text-[12px] uppercase tracking-[0.2em] hover:bg-neutral-900 transition-colors disabled:opacity-50 flex items-center justify-center gap-4" 
                >
                  {isGenerating ? (
                    <>
                      <Activity size={16} className="animate-pulse" />
                      <span>{generationStatus || 'SYNTHESIZING...'}</span>
                    </>
                  ) : (
                    <>
                      <Zap size={16} />
                      <span>GENERATE RESUME</span>
                    </>
                  )}
                </button>
                <button className="bg-white border border-[#dadad4] px-8 font-black text-[10px] uppercase tracking-widest hover:bg-[#dadad4]">Save Prefs</button>
            </footer>
        </main>


        {/* Intelligence Ledger (Col 9-12) */}
        <section className="col-span-4 bg-[#eeeee8] border-l border-[#dadad4] flex flex-col overflow-hidden">
            <header className="h-14 px-8 border-b border-[#dadad4] bg-white flex justify-between items-center shrink-0">
                <h2 className="text-[10px] font-black tracking-[0.2em] text-[#1d54c7] uppercase">Intelligence Ledger</h2>
            </header>
            
            <div className="flex-1 overflow-y-auto no-scrollbar">
                {view !== 'results' ? (
                    <div className="p-10 opacity-10 flex flex-col items-center justify-center h-full text-center">
                         <Activity className="w-16 h-16 mb-4 text-[#1d54c7]" />
                         <p className="text-[11px] font-black tracking-[0.5em] uppercase">Awaiting Induction</p>
                    </div>
                ) : analysis && (
                    <div className="p-10 space-y-10">
                        <div>
                          <h3 className="text-[10px] font-black uppercase text-neutral-400 mb-4 tracking-widest">Neural Map</h3>
                          <div className="p-6 bg-white border border-[#dadad4] space-y-4">
                             <div className="flex justify-between items-end">
                                <div>
                                   <div className="text-xl font-black uppercase">{analysis.name}</div>
                                   <div className="text-xs font-bold text-[#1d54c7] uppercase">{analysis.title}</div>
                                </div>
                                <div className="text-right">
                                   <div className="text-[24px] font-black">{analysis.ats_score}%</div>
                                   <div className="text-[8px] font-black uppercase tracking-widest text-[#b60020]">ATS Aligned</div>
                                </div>
                             </div>
                             
                             <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[#fafaf3]">
                                <div>
                                   <div className="text-[8px] font-black uppercase text-neutral-400 mb-2">Capabilities</div>
                                   <div className="flex flex-wrap gap-1">
                                      {analysis.top_skills.map(s => <span key={s} className="px-1.5 py-0.5 bg-[#fafaf3] border border-[#dadad4] text-[8px] font-black uppercase">{s}</span>)}
                                   </div>
                                </div>
                                <div>
                                   <div className="text-[8px] font-black uppercase text-neutral-400 mb-2">Tenure</div>
                                   <div className="text-lg font-black">{analysis.experience_years}YRS</div>
                                </div>
                             </div>
                          </div>
                        </div>

                        <div>
                           <h3 className="text-[10px] font-black uppercase text-neutral-400 mb-4 tracking-widest">Strength Vectors</h3>
                           <div className="space-y-2">
                              {analysis.strengths.map((s, i) => (
                                 <div key={i} className="flex gap-4 items-start">
                                    <div className="w-1 h-5 bg-[#00ff88] shrink-0 mt-1"></div>
                                    <div className="text-[11px] font-bold leading-tight">{s}</div>
                                 </div>
                              ))}
                           </div>
                        </div>

                        <div>
                           <h3 className="text-[10px] font-black uppercase text-neutral-400 mb-4 tracking-widest">Strategic Gaps</h3>
                           <div className="space-y-2">
                              {analysis.gaps.map((g, i) => (
                                 <div key={i} className="flex gap-4 items-start">
                                    <div className="w-1 h-5 bg-[#ff4444] shrink-0 mt-1"></div>
                                    <div className="text-[11px] font-bold leading-tight">{g}</div>
                                 </div>
                              ))}
                           </div>
                        </div>
                    </div>
                )}
            </div>

            <footer className="p-6 bg-white border-t border-[#dadad4] flex justify-between items-center text-[8px] font-black uppercase text-neutral-300 tracking-widest">
                 <span>HYRED // NEURAL_ENGINE</span>
                 <span>2026_MASTER</span>
            </footer>
        </section>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-10 right-10 bg-[#1a1c19] text-white p-4 font-black text-[10px] uppercase tracking-widest z-50 flex items-center gap-4"
          >
            <AlertCircle size={14} className="text-[#b60020]" />
            {error}
            <button onClick={() => setError(null)} className="ml-4 opacity-50 hover:opacity-100">✕</button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}


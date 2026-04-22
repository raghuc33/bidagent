import { useState, useCallback } from 'react'
import { connectPipeline } from '../services/api'

const PHASE_LABELS = {
    A: 'Evidence Analysis',
    B: 'Draft & Squeeze',
    B_draft: 'Draft Generation',
    C: 'Tone Styling',
    D: 'Quality Scoring',
}

export default function usePipeline() {
    const [phases, setPhases] = useState([])
    const [isRunning, setIsRunning] = useState(false)
    const [result, setResult] = useState(null)

    const runPipeline = useCallback((sectionTitle, sectionDescription, docId, sessionId, sectionId) => {
        setIsRunning(true)
        setResult(null)
        setPhases([
            { id: 'A', label: 'Evidence Analysis', status: 'pending' },
            { id: 'B', label: 'Draft & Squeeze', status: 'pending' },
            { id: 'C', label: 'Tone Styling', status: 'pending' },
            { id: 'D', label: 'Quality Scoring', status: 'pending' },
        ])

        connectPipeline(sectionTitle, sectionDescription, docId, sessionId, sectionId, (event) => {
            if (event.phase === 'complete') {
                setIsRunning(false)
                setResult(event)
                return
            }

            if (event.phase === 'error') {
                setIsRunning(false)
                setResult({ error: event.error })
                return
            }

            // Skip B_draft sub-phase for UI simplicity
            if (event.phase === 'B_draft') return

            setPhases(prev => prev.map(p => {
                if (p.id === event.phase) {
                    return { ...p, status: event.status, result: event.result, label: event.label || PHASE_LABELS[event.phase] || p.label }
                }
                return p
            }))
        })
    }, [])

    return { phases, isRunning, result, runPipeline }
}

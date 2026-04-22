function PipelineProgress({ phases }) {
    return (
        <div className="space-y-3">
            {phases.map((phase) => (
                <div key={phase.id} className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                        phase.status === 'done' ? 'bg-green-500 text-white'
                        : phase.status === 'running' ? 'bg-blue-500 text-white animate-pulse'
                        : 'bg-gray-200 text-gray-400'
                    }`}>
                        {phase.status === 'done' ? '✓' : phase.status === 'running' ? '...' : phase.id}
                    </div>
                    <div className={`text-sm ${phase.status === 'running' ? 'font-medium text-blue-600' : phase.status === 'done' ? 'text-gray-700' : 'text-gray-400'}`}>
                        {phase.label}
                        {phase.status === 'done' && phase.result?.score !== undefined && (
                            <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                                Score: {phase.result.score}/100
                            </span>
                        )}
                        {phase.status === 'done' && phase.result?.word_count !== undefined && (
                            <span className="ml-2 text-xs text-gray-500">
                                ({phase.result.word_count} words)
                            </span>
                        )}
                    </div>
                </div>
            ))}
        </div>
    )
}

export default PipelineProgress

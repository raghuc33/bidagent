function SelectionToolbar({ position, onAddToChat, onRegenerate, onImprove }) {
    if (!position) return null

    return (
        <div
            data-selection-toolbar
            className="fixed z-50 flex items-center gap-0.5 bg-gray-900 text-white rounded-lg shadow-lg px-1 py-1"
            style={{ top: position.top - 40, left: position.left }}
            onMouseDown={(e) => e.preventDefault()}
        >
            <button
                onClick={onAddToChat}
                className="px-2.5 py-1 text-xs hover:bg-gray-700 rounded transition-colors"
            >
                Add to chat
            </button>
            <div className="w-px h-4 bg-gray-600" />
            <button
                onClick={onRegenerate}
                className="px-2.5 py-1 text-xs hover:bg-gray-700 rounded transition-colors"
            >
                Rewrite
            </button>
            <div className="w-px h-4 bg-gray-600" />
            <button
                onClick={onImprove}
                className="px-2.5 py-1 text-xs hover:bg-gray-700 rounded transition-colors"
            >
                Improve
            </button>
        </div>
    )
}

export default SelectionToolbar

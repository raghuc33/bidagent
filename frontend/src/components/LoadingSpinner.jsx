function LoadingSpinner({ size = 'md', className = '' }) {
    const sizes = {
        sm: 'w-5 h-5 border-2',
        md: 'w-8 h-8 border-3',
        lg: 'w-12 h-12 border-4',
    }

    return (
        <div
            className={`${sizes[size]} border-gray-200 border-t-blue-500 rounded-full animate-spin ${className}`}
            role="status"
            aria-label="Loading"
        />
    )
}

export default LoadingSpinner

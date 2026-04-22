import { Component } from 'react'

class ErrorBoundary extends Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="max-w-lg mx-auto mt-20 p-8 text-center">
                    <h2 className="text-xl font-semibold text-red-600 mb-4">Something went wrong</h2>
                    <p className="text-gray-600 mb-6">{this.state.error?.message || 'An unexpected error occurred.'}</p>
                    <button
                        onClick={() => this.setState({ hasError: false, error: null })}
                        className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                    >
                        Try again
                    </button>
                </div>
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary

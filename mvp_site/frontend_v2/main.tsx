import React from 'react'
import ReactDOM from 'react-dom/client'
import AppWithRouter from './src/AppWithRouter'
import ErrorBoundary from './src/components/ErrorBoundary'
import './src/styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AppWithRouter />
    </ErrorBoundary>
  </React.StrictMode>,
)

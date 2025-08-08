import { useMemo } from 'react'

/**
 * Custom hook to detect if the application is running in test mode
 * @returns boolean indicating if test_mode=true is present in URL parameters
 */
export function useTestMode(): boolean {
  return useMemo(() => {
    return new URLSearchParams(window.location.search).get('test_mode') === 'true'
  }, [])
}
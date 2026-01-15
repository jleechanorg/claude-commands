/**
 * Utility function to convert system warnings from API response to StoryEntry format.
 * 
 * This centralizes the logic for handling system warnings to avoid code duplication
 * across GamePlayView and GameView components.
 * 
 * @param systemWarnings - Array of warning strings from API response (may be undefined/null)
 * @returns Array of StoryEntry objects representing system warnings, or empty array if none
 */
export function createSystemWarningEntries(
  systemWarnings: string[] | undefined | null
): Array<{
  id: string;
  type: 'system';
  content: string;
  timestamp: string;
  author: 'system';
}> {
  if (!Array.isArray(systemWarnings) || systemWarnings.length === 0) {
    return [];
  }

  return [
    {
      id: `warnings-${Date.now()}`,
      type: 'system',
      content: `⚠️ System warnings:\n${systemWarnings.map(w => `- ${String(w)}`).join('\n')}`,
      timestamp: new Date().toISOString(),
      author: 'system'
    }
  ];
}

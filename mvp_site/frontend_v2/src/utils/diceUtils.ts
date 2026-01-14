/**
 * Utility functions for dice roll formatting and display in the UI.
 */

export interface DiceRoll {
  type?: string;
  result?: number;
  modifier?: number;
  total?: number;
  reason?: string;
}

/**
 * Formats a single dice roll (string or object) into a human-readable string.
 * Supports legacy string format and the preferred object format.
 */
export function formatDiceRoll(roll: string | DiceRoll | unknown): string {
  if (typeof roll === 'string') {
    // Legacy string format - return as-is
    return roll;
  } else if (typeof roll === 'object' && roll !== null) {
    // Object format - format nicely
    const r = roll as DiceRoll;
    const type = r.type || 'Roll';

    // Result handling
    const result = r.result !== undefined && r.result !== null ? r.result : '';

    // Modifier handling (Copilot fix: handle negative values correctly)
    let modifierStr = '';
    if (r.modifier !== undefined && r.modifier !== null && r.modifier !== 0) {
      const modNumber = Number(r.modifier);
      if (!Number.isNaN(modNumber)) {
        if (modNumber > 0) {
          modifierStr = ` + ${modNumber}`;
        } else {
          // Negative modifier: Math.abs removes the minus, then we add " - "
          modifierStr = ` - ${Math.abs(modNumber)}`;
        }
      } else {
        // Fallback for non-numeric modifiers
        modifierStr = ` + ${r.modifier}`;
      }
    }

    const total = r.total !== undefined && r.total !== null ? r.total : (r.result ?? '');
    const reason = r.reason ? ` (${r.reason})` : '';

    return `${type}: ${result}${modifierStr} = ${total}${reason}`;
  } else {
    // Fallback for unexpected formats
    return String(roll);
  }
}

/**
 * Formats an array of dice rolls into a comma-separated string.
 * Useful for system messages.
 */
export function formatDiceRolls(rolls: (string | DiceRoll | unknown)[]): string {
  if (!Array.isArray(rolls)) return '';
  return rolls.map(formatDiceRoll).join(', ');
}

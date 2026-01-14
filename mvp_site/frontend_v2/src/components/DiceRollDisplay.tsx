import React from 'react'
import { formatDiceRoll, DiceRoll } from '../utils/diceUtils'

interface DiceRollDisplayProps {
    dice_rolls?: (string | DiceRoll | unknown)[]
    className?: string
}

/**
 * Reusable component for displaying dice rolls with consistent styling and dark mode support.
 */
export const DiceRollDisplay: React.FC<DiceRollDisplayProps> = ({ dice_rolls, className = "" }) => {
    if (!dice_rolls || !Array.isArray(dice_rolls) || dice_rolls.length === 0) {
        return null
    }

    return (
        <div className={`mt-2 p-2 bg-purple-50 dark:bg-purple-950/30 rounded border border-purple-200 dark:border-purple-800 ${className}`}>
            <p className="text-xs font-semibold text-purple-700 dark:text-purple-300 mb-1">🎲 Dice Rolls:</p>
            <div className="text-xs text-purple-600 dark:text-purple-400 space-y-1">
                {dice_rolls.map((roll, idx) => (
                    <div key={idx}>{formatDiceRoll(roll)}</div>
                ))}
            </div>
        </div>
    )
}

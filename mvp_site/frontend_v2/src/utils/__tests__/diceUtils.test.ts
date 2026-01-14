import { describe, it, expect } from 'vitest';
import { formatDiceRoll, formatDiceRolls, DiceRoll } from '../diceUtils';

describe('diceUtils', () => {
    describe('formatDiceRoll', () => {
        it('should format legacy string rolls correctly', () => {
            expect(formatDiceRoll('Natural 20!')).toBe('Natural 20!');
            expect(formatDiceRoll('1d20 + 5')).toBe('1d20 + 5');
        });

        it('should format object rolls with result and total', () => {
            const roll: DiceRoll = {
                type: 'Attack',
                result: 15,
                modifier: 5,
                total: 20,
                reason: 'Longsword'
            };
            expect(formatDiceRoll(roll)).toBe('Attack: 15 + 5 = 20 (Longsword)');
        });

        it('should format object rolls with negative modifiers correctly', () => {
            const roll: DiceRoll = {
                type: 'Damage',
                result: 10,
                modifier: -2,
                total: 8
            };
            expect(formatDiceRoll(roll)).toBe('Damage: 10 - 2 = 8');
        });

        it('should handle missing modifier', () => {
            const roll: DiceRoll = {
                type: 'Damage',
                result: 8,
                total: 8
            };
            expect(formatDiceRoll(roll)).toBe('Damage: 8 = 8');
        });

        it('should handle missing total by falling back to result', () => {
            const roll: DiceRoll = {
                type: 'Skill Check',
                result: 12
            };
            expect(formatDiceRoll(roll)).toBe('Skill Check: 12 = 12');
        });

        it('should handle missing type with default "Roll"', () => {
            const roll: DiceRoll = {
                result: 10,
                total: 10
            };
            expect(formatDiceRoll(roll)).toBe('Roll: 10 = 10');
        });

        it('should handle null or undefined results safely', () => {
            expect(formatDiceRoll({ type: 'Test' })).toBe('Test:  = ');
            expect(formatDiceRoll({})).toBe('Roll:  = ');
        });

        it('should handle non-string non-object inputs by converting to string', () => {
            expect(formatDiceRoll(123)).toBe('123');
            expect(formatDiceRoll(true)).toBe('true');
        });
    });

    describe('formatDiceRolls', () => {
        it('should format an array of mixed rolls', () => {
            const rolls = [
                'Natural 20!',
                { type: 'Damage', result: 5, total: 5 },
                { type: 'Save', result: 10, modifier: 2, total: 12, reason: 'Fire' }
            ];
            const expected = 'Natural 20!, Damage: 5 = 5, Save: 10 + 2 = 12 (Fire)';
            expect(formatDiceRolls(rolls)).toBe(expected);
        });

        it('should return an empty string for non-array input', () => {
            // @ts-ignore - testing runtime safety for invalid inputs
            expect(formatDiceRolls(null)).toBe('');
            // @ts-ignore - testing runtime safety for invalid inputs
            expect(formatDiceRolls(undefined)).toBe('');
        });

        it('should return an empty string for empty array', () => {
            expect(formatDiceRolls([])).toBe('');
        });
    });
});

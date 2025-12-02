/**
 * Campaign validation utilities for Frontend v2
 * Centralizes validation logic to prevent duplication
 */

export interface CampaignLengthValidationResult {
  isValid: boolean;
  errorMessage?: string;
  totalLength: number;
  characterLength: number;
  settingLength: number;
  descriptionLength: number;
}

// Backend combines fields with " | " separator and prefixes each value with its field label
const SAFE_USER_INPUT_LIMIT = 950000; // 950k chars (1M limit - safety buffer for backend processing)
const SEPARATOR_LENGTH = 3; // " | " between fields
const CHARACTER_PREFIX_LENGTH = 11; // "Character: "
const SETTING_PREFIX_LENGTH = 9; // "Setting: "
const DESCRIPTION_PREFIX_LENGTH = 13; // "Description: "

/**
 * Validates combined length of campaign character, setting, and description fields
 *
 * Backend combines these fields with " | " separators and adds entity tracking data.
 * This validation ensures the total doesn't exceed backend's 1M character limit.
 *
 * @param character - Character description
 * @param setting - Setting description
 * @param description - Campaign description
 * @returns Validation result with details
 */
export function validateCampaignCombinedLength(
  character?: string,
  setting?: string,
  description?: string
): CampaignLengthValidationResult {
  const normalizedCharacter = character?.trim() ?? "";
  const normalizedSetting = setting?.trim() ?? "";
  const normalizedDescription = description?.trim() ?? "";

  const characterLength = normalizedCharacter.length;
  const settingLength = normalizedSetting.length;
  const descriptionLength = normalizedDescription.length;

  // Calculate prefix and separator overhead based on non-empty fields
  const nonEmptyFieldCount = [characterLength, settingLength, descriptionLength].filter(
    (len) => len > 0
  ).length;
  const separatorCount = Math.max(0, nonEmptyFieldCount - 1);
  const characterPrefix = characterLength > 0 ? CHARACTER_PREFIX_LENGTH : 0;
  const settingPrefix = settingLength > 0 ? SETTING_PREFIX_LENGTH : 0;
  const descriptionPrefix = descriptionLength > 0 ? DESCRIPTION_PREFIX_LENGTH : 0;

  const totalCombinedLength =
    characterLength +
    settingLength +
    descriptionLength +
    characterPrefix +
    settingPrefix +
    descriptionPrefix +
    SEPARATOR_LENGTH * separatorCount;

  if (totalCombinedLength > SAFE_USER_INPUT_LIMIT) {
    return {
      isValid: false,
      errorMessage:
        `Total campaign input is too long (${totalCombinedLength.toLocaleString()} characters). ` +
        `Maximum combined length for character, setting, and description is ${SAFE_USER_INPUT_LIMIT.toLocaleString()} characters. ` +
        `Current lengths: character=${characterLength.toLocaleString()}, setting=${settingLength.toLocaleString()}, description=${descriptionLength.toLocaleString()}. ` +
        `Please reduce the length of one or more fields.`,
      totalLength: totalCombinedLength,
      characterLength,
      settingLength,
      descriptionLength,
    };
  }

  return {
    isValid: true,
    totalLength: totalCombinedLength,
    characterLength,
    settingLength,
    descriptionLength,
  };
}

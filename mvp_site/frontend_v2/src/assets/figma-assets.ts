// Figma asset mappings
// These map Figma asset IDs to actual image files

// Background images
export const backgroundImage1 = '/image_reference/twin_dragon.png' // Dragon background image
export const backgroundImage2 = '/image_reference/twin_dragon.png' // Dragon background image
export const heroImage = '/image_reference/twin_dragon.png' // Dragon background image

// Export a mapping object for dynamic usage
export const figmaAssets = {
  '7388009b8bbea20b44923143edf5bb1c4c93e240': backgroundImage1,
  '11638f062b57e33399d25c2ad25dfa18dc0824c3': backgroundImage2,
  'ecab425a7edc8f80fb8ff5feaec1011c3fd50550': heroImage,
} as const

// Helper function to get asset by ID
export function getFigmaAsset(id: string): string {
  return figmaAssets[id as keyof typeof figmaAssets] || '/image_reference/twin_dragon.png'
}

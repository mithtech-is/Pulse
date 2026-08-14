import { reactive } from 'vue'

// Global command-palette (Cmd+K) state, so it can be triggered from anywhere.
export const paletteState = reactive({ open: false })

export function openPalette() { paletteState.open = true }
export function closePalette() { paletteState.open = false }
export function togglePalette() { paletteState.open = !paletteState.open }

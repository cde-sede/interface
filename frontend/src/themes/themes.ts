/**
 * Theme Definitions
 *
 * To add a new theme:
 * 1. Create a new Theme object with a unique id
 * 2. Set displayName and description for the UI
 * 3. Choose 4-5 representative colors for previewColors (shown in theme picker)
 * 4. Define all color properties in the colors object
 * 5. Add the theme to the themes array export
 *
 * The theme will automatically appear in the theme picker.
 */

import type { Theme } from './types';

// Default theme - matches the current design aesthetic
const defaultTheme: Theme = {
  id: 'default',
  name: 'default',
  displayName: 'Default',
  description: 'Clean professional design with dark blue accents',
  previewColors: ['#0f172a', '#f8fafc', '#0f172a', '#10b981'],
  colors: {
    // Header
    headerBg: '#0f172a',
    headerText: '#ffffff',
    headerTextMuted: 'rgba(255, 255, 255, 0.7)',
    headerBorder: '#1e293b',

    // Sidebar
    sidebarBg: '#f8fafc',
    sidebarBorder: '#e2e8f0',
    sidebarHeading: '#64748b',
    sidebarItemText: '#475569',
    sidebarItemTextHover: '#0f172a',
    sidebarItemBgHover: '#e2e8f0',
    sidebarItemBgActive: '#0f172a',
    sidebarItemTextActive: '#ffffff',

    // Main content
    mainBg: '#ffffff',
    mainText: '#0f172a',
    mainTextMuted: '#475569',
    mainBorder: '#e2e8f0',

    // Cards and containers
    cardBg: '#f8fafc',
    cardBorder: '#e2e8f0',
    cardBorderHover: '#cbd5e1',

    // Buttons
    buttonPrimaryBg: '#0f172a',
    buttonPrimaryText: '#ffffff',
    buttonPrimaryBgHover: '#1e293b',
    buttonPrimaryBgActive: '#334155',

    // Inputs
    inputBg: '#ffffff',
    inputBorder: '#cbd5e1',
    inputBorderHover: '#94a3b8',
    inputBorderFocus: '#0f172a',
    inputText: '#0f172a',
    inputFocusRing: 'rgba(15, 23, 42, 0.05)',
    inputAccent: '#0f172a',

    // HTTP Method badges
    methodGetBg: '#dcfce7',
    methodGetText: '#166534',
    methodPostBg: '#dbeafe',
    methodPostText: '#1e40af',
    methodPutBg: '#fef3c7',
    methodPutText: '#92400e',
    methodPatchBg: '#e9d5ff',
    methodPatchText: '#6b21a8',
    methodDeleteBg: '#fee2e2',
    methodDeleteText: '#991b1b',

    // Parameter badges
    badgePathBg: '#dbeafe',
    badgePathText: '#1e40af',
    badgeQueryBg: '#fef3c7',
    badgeQueryText: '#92400e',
    badgeBodyBg: '#e0e7ff',
    badgeBodyText: '#3730a3',
    badgeHeaderBg: '#fce7f3',
    badgeHeaderText: '#9f1239',

    // Terminal/Response
    terminalBg: '#0f172a',
    terminalText: '#10b981',
    terminalBorder: '#1e293b',
    terminalHeading: '#94a3b8',
    terminalOverlayBg: 'rgba(15, 23, 42, 0.7)',

    // Scrollbar
    scrollbarThumb: '#cbd5e1',
    scrollbarThumbHover: '#94a3b8',

    // Code blocks
    codeBg: '#f8fafc',
    codeText: '#334155',
    codeBorder: '#e2e8f0',

    // States
    requiredText: '#dc2626',
    emptyStateText: '#94a3b8',
  },
};

// Dark theme - full dark mode
const darkTheme: Theme = {
  id: 'dark',
  name: 'dark',
  displayName: 'Dark',
  description: 'Easy on the eyes with dark backgrounds',
  previewColors: ['#0a0e1a', '#1e293b', '#475569', '#10b981'],
  colors: {
    // Header
    headerBg: '#0a0e1a',
    headerText: '#e2e8f0',
    headerTextMuted: 'rgba(226, 232, 240, 0.7)',
    headerBorder: '#1e293b',

    // Sidebar
    sidebarBg: '#0f172a',
    sidebarBorder: '#1e293b',
    sidebarHeading: '#94a3b8',
    sidebarItemText: '#cbd5e1',
    sidebarItemTextHover: '#f1f5f9',
    sidebarItemBgHover: '#1e293b',
    sidebarItemBgActive: '#334155',
    sidebarItemTextActive: '#ffffff',

    // Main content
    mainBg: '#0f172a',
    mainText: '#e2e8f0',
    mainTextMuted: '#cbd5e1',
    mainBorder: '#1e293b',

    // Cards and containers
    cardBg: '#1e293b',
    cardBorder: '#334155',
    cardBorderHover: '#475569',

    // Buttons
    buttonPrimaryBg: '#3b82f6',
    buttonPrimaryText: '#ffffff',
    buttonPrimaryBgHover: '#2563eb',
    buttonPrimaryBgActive: '#1d4ed8',

    // Inputs
    inputBg: '#1e293b',
    inputBorder: '#334155',
    inputBorderHover: '#475569',
    inputBorderFocus: '#3b82f6',
    inputText: '#e2e8f0',
    inputFocusRing: 'rgba(59, 130, 246, 0.2)',
    inputAccent: '#3b82f6',

    // HTTP Method badges
    methodGetBg: 'rgba(16, 185, 129, 0.2)',
    methodGetText: '#34d399',
    methodPostBg: 'rgba(59, 130, 246, 0.2)',
    methodPostText: '#60a5fa',
    methodPutBg: 'rgba(251, 191, 36, 0.2)',
    methodPutText: '#fbbf24',
    methodPatchBg: 'rgba(168, 85, 247, 0.2)',
    methodPatchText: '#c084fc',
    methodDeleteBg: 'rgba(239, 68, 68, 0.2)',
    methodDeleteText: '#f87171',

    // Parameter badges
    badgePathBg: 'rgba(59, 130, 246, 0.2)',
    badgePathText: '#60a5fa',
    badgeQueryBg: 'rgba(251, 191, 36, 0.2)',
    badgeQueryText: '#fbbf24',
    badgeBodyBg: 'rgba(99, 102, 241, 0.2)',
    badgeBodyText: '#818cf8',
    badgeHeaderBg: 'rgba(236, 72, 153, 0.2)',
    badgeHeaderText: '#f9a8d4',

    // Terminal/Response
    terminalBg: '#0a0e1a',
    terminalText: '#10b981',
    terminalBorder: '#1e293b',
    terminalHeading: '#94a3b8',
    terminalOverlayBg: 'rgba(10, 14, 26, 0.7)',

    // Scrollbar
    scrollbarThumb: '#334155',
    scrollbarThumbHover: '#475569',

    // Code blocks
    codeBg: '#1e293b',
    codeText: '#cbd5e1',
    codeBorder: '#334155',

    // States
    requiredText: '#f87171',
    emptyStateText: '#64748b',
  },
};

// Light theme - clean and bright
const lightTheme: Theme = {
  id: 'light',
  name: 'light',
  displayName: 'Light',
  description: 'Bright and clean interface',
  previewColors: ['#ffffff', '#f1f5f9', '#3b82f6', '#0ea5e9'],
  colors: {
    // Header
    headerBg: '#3b82f6',
    headerText: '#ffffff',
    headerTextMuted: 'rgba(255, 255, 255, 0.8)',
    headerBorder: '#2563eb',

    // Sidebar
    sidebarBg: '#f8fafc',
    sidebarBorder: '#e2e8f0',
    sidebarHeading: '#64748b',
    sidebarItemText: '#475569',
    sidebarItemTextHover: '#1e293b',
    sidebarItemBgHover: '#e2e8f0',
    sidebarItemBgActive: '#3b82f6',
    sidebarItemTextActive: '#ffffff',

    // Main content
    mainBg: '#ffffff',
    mainText: '#0f172a',
    mainTextMuted: '#475569',
    mainBorder: '#e2e8f0',

    // Cards and containers
    cardBg: '#f8fafc',
    cardBorder: '#e2e8f0',
    cardBorderHover: '#cbd5e1',

    // Buttons
    buttonPrimaryBg: '#3b82f6',
    buttonPrimaryText: '#ffffff',
    buttonPrimaryBgHover: '#2563eb',
    buttonPrimaryBgActive: '#1d4ed8',

    // Inputs
    inputBg: '#ffffff',
    inputBorder: '#cbd5e1',
    inputBorderHover: '#94a3b8',
    inputBorderFocus: '#3b82f6',
    inputText: '#0f172a',
    inputFocusRing: 'rgba(59, 130, 246, 0.1)',
    inputAccent: '#3b82f6',

    // HTTP Method badges
    methodGetBg: '#dcfce7',
    methodGetText: '#166534',
    methodPostBg: '#dbeafe',
    methodPostText: '#1e40af',
    methodPutBg: '#fef3c7',
    methodPutText: '#92400e',
    methodPatchBg: '#e9d5ff',
    methodPatchText: '#6b21a8',
    methodDeleteBg: '#fee2e2',
    methodDeleteText: '#991b1b',

    // Parameter badges
    badgePathBg: '#dbeafe',
    badgePathText: '#1e40af',
    badgeQueryBg: '#fef3c7',
    badgeQueryText: '#92400e',
    badgeBodyBg: '#e0e7ff',
    badgeBodyText: '#3730a3',
    badgeHeaderBg: '#fce7f3',
    badgeHeaderText: '#9f1239',

    // Terminal/Response
    terminalBg: '#0f172a',
    terminalText: '#10b981',
    terminalBorder: '#1e293b',
    terminalHeading: '#94a3b8',
    terminalOverlayBg: 'rgba(15, 23, 42, 0.7)',

    // Scrollbar
    scrollbarThumb: '#cbd5e1',
    scrollbarThumbHover: '#94a3b8',

    // Code blocks
    codeBg: '#f8fafc',
    codeText: '#334155',
    codeBorder: '#e2e8f0',

    // States
    requiredText: '#dc2626',
    emptyStateText: '#94a3b8',
  },
};

// Ocean Blue theme - professional blue tones
const oceanBlueTheme: Theme = {
  id: 'ocean-blue',
  name: 'ocean-blue',
  displayName: 'Ocean Blue',
  description: 'Professional blue-tinted theme',
  previewColors: ['#0369a1', '#0284c7', '#38bdf8', '#bae6fd'],
  colors: {
    // Header
    headerBg: '#0369a1',
    headerText: '#ffffff',
    headerTextMuted: 'rgba(255, 255, 255, 0.8)',
    headerBorder: '#075985',

    // Sidebar
    sidebarBg: '#f0f9ff',
    sidebarBorder: '#bae6fd',
    sidebarHeading: '#0369a1',
    sidebarItemText: '#075985',
    sidebarItemTextHover: '#0c4a6e',
    sidebarItemBgHover: '#e0f2fe',
    sidebarItemBgActive: '#0284c7',
    sidebarItemTextActive: '#ffffff',

    // Main content
    mainBg: '#ffffff',
    mainText: '#0c4a6e',
    mainTextMuted: '#075985',
    mainBorder: '#bae6fd',

    // Cards and containers
    cardBg: '#f0f9ff',
    cardBorder: '#bae6fd',
    cardBorderHover: '#7dd3fc',

    // Buttons
    buttonPrimaryBg: '#0284c7',
    buttonPrimaryText: '#ffffff',
    buttonPrimaryBgHover: '#0369a1',
    buttonPrimaryBgActive: '#075985',

    // Inputs
    inputBg: '#ffffff',
    inputBorder: '#7dd3fc',
    inputBorderHover: '#38bdf8',
    inputBorderFocus: '#0284c7',
    inputText: '#0c4a6e',
    inputFocusRing: 'rgba(2, 132, 199, 0.1)',
    inputAccent: '#0284c7',

    // HTTP Method badges
    methodGetBg: '#dcfce7',
    methodGetText: '#166534',
    methodPostBg: '#bfdbfe',
    methodPostText: '#1e40af',
    methodPutBg: '#fef3c7',
    methodPutText: '#92400e',
    methodPatchBg: '#ddd6fe',
    methodPatchText: '#6b21a8',
    methodDeleteBg: '#fee2e2',
    methodDeleteText: '#991b1b',

    // Parameter badges
    badgePathBg: '#bfdbfe',
    badgePathText: '#1e40af',
    badgeQueryBg: '#fef3c7',
    badgeQueryText: '#92400e',
    badgeBodyBg: '#ddd6fe',
    badgeBodyText: '#5b21b6',
    badgeHeaderBg: '#fce7f3',
    badgeHeaderText: '#9f1239',

    // Terminal/Response
    terminalBg: '#0c4a6e',
    terminalText: '#34d399',
    terminalBorder: '#075985',
    terminalHeading: '#7dd3fc',
    terminalOverlayBg: 'rgba(12, 74, 110, 0.7)',

    // Scrollbar
    scrollbarThumb: '#7dd3fc',
    scrollbarThumbHover: '#38bdf8',

    // Code blocks
    codeBg: '#f0f9ff',
    codeText: '#075985',
    codeBorder: '#bae6fd',

    // States
    requiredText: '#dc2626',
    emptyStateText: '#0369a1',
  },
};

// Purple Night theme - deep purple and violet
const purpleNightTheme: Theme = {
  id: 'purple-night',
  name: 'purple-night',
  displayName: 'Purple Night',
  description: 'Deep purple and violet color scheme',
  previewColors: ['#581c87', '#7c3aed', '#a78bfa', '#ddd6fe'],
  colors: {
    // Header
    headerBg: '#581c87',
    headerText: '#ffffff',
    headerTextMuted: 'rgba(255, 255, 255, 0.8)',
    headerBorder: '#6b21a8',

    // Sidebar
    sidebarBg: '#faf5ff',
    sidebarBorder: '#ddd6fe',
    sidebarHeading: '#6b21a8',
    sidebarItemText: '#7c3aed',
    sidebarItemTextHover: '#581c87',
    sidebarItemBgHover: '#ede9fe',
    sidebarItemBgActive: '#7c3aed',
    sidebarItemTextActive: '#ffffff',

    // Main content
    mainBg: '#ffffff',
    mainText: '#3b0764',
    mainTextMuted: '#581c87',
    mainBorder: '#ddd6fe',

    // Cards and containers
    cardBg: '#faf5ff',
    cardBorder: '#ddd6fe',
    cardBorderHover: '#c4b5fd',

    // Buttons
    buttonPrimaryBg: '#7c3aed',
    buttonPrimaryText: '#ffffff',
    buttonPrimaryBgHover: '#6b21a8',
    buttonPrimaryBgActive: '#581c87',

    // Inputs
    inputBg: '#ffffff',
    inputBorder: '#c4b5fd',
    inputBorderHover: '#a78bfa',
    inputBorderFocus: '#7c3aed',
    inputText: '#3b0764',
    inputFocusRing: 'rgba(124, 58, 237, 0.1)',
    inputAccent: '#7c3aed',

    // HTTP Method badges
    methodGetBg: '#dcfce7',
    methodGetText: '#166534',
    methodPostBg: '#dbeafe',
    methodPostText: '#1e40af',
    methodPutBg: '#fef3c7',
    methodPutText: '#92400e',
    methodPatchBg: '#e9d5ff',
    methodPatchText: '#6b21a8',
    methodDeleteBg: '#fee2e2',
    methodDeleteText: '#991b1b',

    // Parameter badges
    badgePathBg: '#dbeafe',
    badgePathText: '#1e40af',
    badgeQueryBg: '#fef3c7',
    badgeQueryText: '#92400e',
    badgeBodyBg: '#e9d5ff',
    badgeBodyText: '#6b21a8',
    badgeHeaderBg: '#fce7f3',
    badgeHeaderText: '#9f1239',

    // Terminal/Response
    terminalBg: '#3b0764',
    terminalText: '#a78bfa',
    terminalBorder: '#581c87',
    terminalHeading: '#c4b5fd',
    terminalOverlayBg: 'rgba(59, 7, 100, 0.7)',

    // Scrollbar
    scrollbarThumb: '#c4b5fd',
    scrollbarThumbHover: '#a78bfa',

    // Code blocks
    codeBg: '#faf5ff',
    codeText: '#581c87',
    codeBorder: '#ddd6fe',

    // States
    requiredText: '#dc2626',
    emptyStateText: '#7c3aed',
  },
};

// Forest Green theme - nature-inspired green tones
const forestGreenTheme: Theme = {
  id: 'forest-green',
  name: 'forest-green',
  displayName: 'Forest Green',
  description: 'Nature-inspired green color scheme',
  previewColors: ['#166534', '#22c55e', '#86efac', '#dcfce7'],
  colors: {
    // Header
    headerBg: '#166534',
    headerText: '#ffffff',
    headerTextMuted: 'rgba(255, 255, 255, 0.8)',
    headerBorder: '#15803d',

    // Sidebar
    sidebarBg: '#f0fdf4',
    sidebarBorder: '#bbf7d0',
    sidebarHeading: '#166534',
    sidebarItemText: '#15803d',
    sidebarItemTextHover: '#14532d',
    sidebarItemBgHover: '#dcfce7',
    sidebarItemBgActive: '#22c55e',
    sidebarItemTextActive: '#ffffff',

    // Main content
    mainBg: '#ffffff',
    mainText: '#14532d',
    mainTextMuted: '#166534',
    mainBorder: '#bbf7d0',

    // Cards and containers
    cardBg: '#f0fdf4',
    cardBorder: '#bbf7d0',
    cardBorderHover: '#86efac',

    // Buttons
    buttonPrimaryBg: '#22c55e',
    buttonPrimaryText: '#ffffff',
    buttonPrimaryBgHover: '#16a34a',
    buttonPrimaryBgActive: '#15803d',

    // Inputs
    inputBg: '#ffffff',
    inputBorder: '#86efac',
    inputBorderHover: '#4ade80',
    inputBorderFocus: '#22c55e',
    inputText: '#14532d',
    inputFocusRing: 'rgba(34, 197, 94, 0.1)',
    inputAccent: '#22c55e',

    // HTTP Method badges
    methodGetBg: '#d1fae5',
    methodGetText: '#065f46',
    methodPostBg: '#dbeafe',
    methodPostText: '#1e40af',
    methodPutBg: '#fef3c7',
    methodPutText: '#92400e',
    methodPatchBg: '#e9d5ff',
    methodPatchText: '#6b21a8',
    methodDeleteBg: '#fee2e2',
    methodDeleteText: '#991b1b',

    // Parameter badges
    badgePathBg: '#dbeafe',
    badgePathText: '#1e40af',
    badgeQueryBg: '#fef3c7',
    badgeQueryText: '#92400e',
    badgeBodyBg: '#e0e7ff',
    badgeBodyText: '#3730a3',
    badgeHeaderBg: '#fce7f3',
    badgeHeaderText: '#9f1239',

    // Terminal/Response
    terminalBg: '#14532d',
    terminalText: '#86efac',
    terminalBorder: '#166534',
    terminalHeading: '#bbf7d0',
    terminalOverlayBg: 'rgba(20, 83, 45, 0.7)',

    // Scrollbar
    scrollbarThumb: '#86efac',
    scrollbarThumbHover: '#4ade80',

    // Code blocks
    codeBg: '#f0fdf4',
    codeText: '#166534',
    codeBorder: '#bbf7d0',

    // States
    requiredText: '#dc2626',
    emptyStateText: '#22c55e',
  },
};

// Kurokula theme - based on terminal color scheme
const kurokulaTheme: Theme = {
  id: 'kurokula',
  name: 'kurokula',
  displayName: 'Kurokula',
  description: 'Dark theme with warm brown and teal accents',
  previewColors: ['#141515', '#78b3a9', '#e1b917', '#e0cfc2'],
  colors: {
    // Header
    headerBg: '#141515',
    headerText: '#e0cfc2',
    headerTextMuted: 'rgba(224, 207, 194, 0.7)',
    headerBorder: '#333333',

    // Sidebar
    sidebarBg: '#1a1b1b',
    sidebarBorder: '#333333',
    sidebarHeading: '#78b3a9',
    sidebarItemText: '#e0cfc2',
    sidebarItemTextHover: '#ffffff',
    sidebarItemBgHover: '#333333',
    sidebarItemBgActive: '#5c91dd',
    sidebarItemTextActive: '#ffffff',

    // Main content
    mainBg: '#141515',
    mainText: '#e0cfc2',
    mainTextMuted: '#867268',
    mainBorder: '#333333',

    // Cards and containers
    cardBg: '#1a1b1b',
    cardBorder: '#333333',
    cardBorderHover: '#515151',

    // Buttons
    buttonPrimaryBg: '#5c91dd',
    buttonPrimaryText: '#ffffff',
    buttonPrimaryBgHover: '#90dbff',
    buttonPrimaryBgActive: '#78b3a9',

    // Inputs
    inputBg: '#1a1b1b',
    inputBorder: '#515151',
    inputBorderHover: '#78b3a9',
    inputBorderFocus: '#5c91dd',
    inputText: '#e0cfc2',
    inputFocusRing: 'rgba(92, 145, 221, 0.2)',
    inputAccent: '#5c91dd',

    // HTTP Method badges
    methodGetBg: 'rgba(120, 179, 169, 0.2)',
    methodGetText: '#afffa5',
    methodPostBg: 'rgba(92, 145, 221, 0.2)',
    methodPostText: '#90dbff',
    methodPutBg: 'rgba(225, 185, 23, 0.2)',
    methodPutText: '#fff700',
    methodPatchBg: 'rgba(139, 121, 166, 0.2)',
    methodPatchText: '#ad93ff',
    methodDeleteBg: 'rgba(195, 90, 82, 0.2)',
    methodDeleteText: '#ffc34c',

    // Parameter badges
    badgePathBg: 'rgba(92, 145, 221, 0.2)',
    badgePathText: '#90dbff',
    badgeQueryBg: 'rgba(225, 185, 23, 0.2)',
    badgeQueryText: '#fff700',
    badgeBodyBg: 'rgba(139, 121, 166, 0.2)',
    badgeBodyText: '#ad93ff',
    badgeHeaderBg: 'rgba(134, 114, 104, 0.2)',
    badgeHeaderText: '#ffcdb6',

    // Terminal/Response
    terminalBg: '#0a0a0a',
    terminalText: '#afffa5',
    terminalBorder: '#333333',
    terminalHeading: '#78b3a9',
    terminalOverlayBg: 'rgba(20, 21, 21, 0.7)',

    // Scrollbar
    scrollbarThumb: '#515151',
    scrollbarThumbHover: '#867268',

    // Code blocks
    codeBg: '#1a1b1b',
    codeText: '#e0cfc2',
    codeBorder: '#333333',

    // States
    requiredText: '#ffc34c',
    emptyStateText: '#867268',
  },
};

// Auto theme - system preference (placeholder, resolved in ThemeContext)
const autoTheme: Theme = {
  id: 'auto',
  name: 'auto',
  displayName: 'Auto',
  description: 'Follow system dark/light mode preference',
  previewColors: ['#0f172a', '#f8fafc', '#3b82f6', '#10b981'],
  colors: defaultTheme.colors, // Fallback, will be resolved dynamically
};

// Export all themes
export const themes: Theme[] = [
  defaultTheme,
  darkTheme,
  lightTheme,
  oceanBlueTheme,
  purpleNightTheme,
  forestGreenTheme,
  kurokulaTheme,
  autoTheme,
];

// Helper to get theme by ID
export const getThemeById = (id: string): Theme | undefined => {
  return themes.find((theme) => theme.id === id);
};

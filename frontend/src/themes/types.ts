/**
 * Theme system type definitions
 *
 * This file defines the structure for themes in the application.
 * All colors should be valid CSS color values (hex, rgb, hsl, etc.)
 */

export type ThemeId = 'default' | 'dark' | 'light' | 'ocean-blue' | 'purple-night' | 'forest-green' | 'kurokula' | 'auto';

export interface ThemeColors {
  // Header
  headerBg: string;
  headerText: string;
  headerTextMuted: string;
  headerBorder: string;

  // Sidebar
  sidebarBg: string;
  sidebarBorder: string;
  sidebarHeading: string;
  sidebarItemText: string;
  sidebarItemTextHover: string;
  sidebarItemBgHover: string;
  sidebarItemBgActive: string;
  sidebarItemTextActive: string;

  // Main content
  mainBg: string;
  mainText: string;
  mainTextMuted: string;
  mainBorder: string;

  // Cards and containers
  cardBg: string;
  cardBorder: string;
  cardBorderHover: string;

  // Buttons
  buttonPrimaryBg: string;
  buttonPrimaryText: string;
  buttonPrimaryBgHover: string;
  buttonPrimaryBgActive: string;

  // Inputs
  inputBg: string;
  inputBorder: string;
  inputBorderHover: string;
  inputBorderFocus: string;
  inputText: string;
  inputFocusRing: string;
  inputAccent: string;

  // HTTP Method badges
  methodGetBg: string;
  methodGetText: string;
  methodPostBg: string;
  methodPostText: string;
  methodPutBg: string;
  methodPutText: string;
  methodPatchBg: string;
  methodPatchText: string;
  methodDeleteBg: string;
  methodDeleteText: string;

  // Parameter badges
  badgePathBg: string;
  badgePathText: string;
  badgeQueryBg: string;
  badgeQueryText: string;
  badgeBodyBg: string;
  badgeBodyText: string;
  badgeHeaderBg: string;
  badgeHeaderText: string;

  // Terminal/Response
  terminalBg: string;
  terminalText: string;
  terminalBorder: string;
  terminalHeading: string;
  terminalOverlayBg: string;

  // Scrollbar
  scrollbarThumb: string;
  scrollbarThumbHover: string;

  // Code blocks
  codeBg: string;
  codeText: string;
  codeBorder: string;

  // States
  requiredText: string;
  emptyStateText: string;
}

export interface Theme {
  id: ThemeId;
  name: string;
  displayName: string;
  description: string;
  previewColors: string[]; // 4-5 representative colors for visual preview
  colors: ThemeColors;
}

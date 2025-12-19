/**
 * Theme Context
 *
 * Provides theme state management throughout the application.
 * Handles localStorage persistence, system preference detection,
 * and CSS variable injection.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { Theme, ThemeId, ThemeColors } from '../themes/types';
import { themes, getThemeById } from '../themes/themes';

interface ThemeContextValue {
	currentThemeId: ThemeId;
	currentTheme: Theme;
	effectiveTheme: Theme; // Resolves 'auto' to actual theme
	themes: Theme[];
	setTheme: (themeId: ThemeId) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = 'app-theme';

/**
 * Get the system's dark/light mode preference
 */
const getSystemPreference = (): 'light' | 'dark' => {
	if (typeof window === 'undefined') return 'light';
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

/**
 * Apply theme colors as CSS variables to :root
 */
const applyThemeVariables = (colors: ThemeColors): void => {
	const root = document.documentElement;

	// Header
	root.style.setProperty('--theme-header-bg', colors.headerBg);
	root.style.setProperty('--theme-header-text', colors.headerText);
	root.style.setProperty('--theme-header-text-muted', colors.headerTextMuted);
	root.style.setProperty('--theme-header-border', colors.headerBorder);

	// Sidebar
	root.style.setProperty('--theme-sidebar-bg', colors.sidebarBg);
	root.style.setProperty('--theme-sidebar-border', colors.sidebarBorder);
	root.style.setProperty('--theme-sidebar-heading', colors.sidebarHeading);
	root.style.setProperty('--theme-sidebar-item-text', colors.sidebarItemText);
	root.style.setProperty('--theme-sidebar-item-text-hover', colors.sidebarItemTextHover);
	root.style.setProperty('--theme-sidebar-item-bg-hover', colors.sidebarItemBgHover);
	root.style.setProperty('--theme-sidebar-item-bg-active', colors.sidebarItemBgActive);
	root.style.setProperty('--theme-sidebar-item-text-active', colors.sidebarItemTextActive);

	// Main content
	root.style.setProperty('--theme-main-bg', colors.mainBg);
	root.style.setProperty('--theme-main-text', colors.mainText);
	root.style.setProperty('--theme-main-text-muted', colors.mainTextMuted);
	root.style.setProperty('--theme-main-border', colors.mainBorder);

	// Cards
	root.style.setProperty('--theme-card-bg', colors.cardBg);
	root.style.setProperty('--theme-card-border', colors.cardBorder);
	root.style.setProperty('--theme-card-border-hover', colors.cardBorderHover);

	// Buttons
	root.style.setProperty('--theme-button-primary-bg', colors.buttonPrimaryBg);
	root.style.setProperty('--theme-button-primary-text', colors.buttonPrimaryText);
	root.style.setProperty('--theme-button-primary-bg-hover', colors.buttonPrimaryBgHover);
	root.style.setProperty('--theme-button-primary-bg-active', colors.buttonPrimaryBgActive);

	// Inputs
	root.style.setProperty('--theme-input-bg', colors.inputBg);
	root.style.setProperty('--theme-input-border', colors.inputBorder);
	root.style.setProperty('--theme-input-border-hover', colors.inputBorderHover);
	root.style.setProperty('--theme-input-border-focus', colors.inputBorderFocus);
	root.style.setProperty('--theme-input-text', colors.inputText);
	root.style.setProperty('--theme-input-focus-ring', colors.inputFocusRing);
	root.style.setProperty('--theme-input-accent', colors.inputAccent);

	// HTTP Method badges
	root.style.setProperty('--theme-method-get-bg', colors.methodGetBg);
	root.style.setProperty('--theme-method-get-text', colors.methodGetText);
	root.style.setProperty('--theme-method-post-bg', colors.methodPostBg);
	root.style.setProperty('--theme-method-post-text', colors.methodPostText);
	root.style.setProperty('--theme-method-put-bg', colors.methodPutBg);
	root.style.setProperty('--theme-method-put-text', colors.methodPutText);
	root.style.setProperty('--theme-method-patch-bg', colors.methodPatchBg);
	root.style.setProperty('--theme-method-patch-text', colors.methodPatchText);
	root.style.setProperty('--theme-method-delete-bg', colors.methodDeleteBg);
	root.style.setProperty('--theme-method-delete-text', colors.methodDeleteText);

	// Parameter badges
	root.style.setProperty('--theme-badge-path-bg', colors.badgePathBg);
	root.style.setProperty('--theme-badge-path-text', colors.badgePathText);
	root.style.setProperty('--theme-badge-query-bg', colors.badgeQueryBg);
	root.style.setProperty('--theme-badge-query-text', colors.badgeQueryText);
	root.style.setProperty('--theme-badge-body-bg', colors.badgeBodyBg);
	root.style.setProperty('--theme-badge-body-text', colors.badgeBodyText);
	root.style.setProperty('--theme-badge-header-bg', colors.badgeHeaderBg);
	root.style.setProperty('--theme-badge-header-text', colors.badgeHeaderText);

	// Terminal/Response
	root.style.setProperty('--theme-terminal-bg', colors.terminalBg);
	root.style.setProperty('--theme-terminal-text', colors.terminalText);
	root.style.setProperty('--theme-terminal-border', colors.terminalBorder);
	root.style.setProperty('--theme-terminal-heading', colors.terminalHeading);
	root.style.setProperty('--theme-terminal-overlay-bg', colors.terminalOverlayBg);

	// Scrollbar
	root.style.setProperty('--theme-scrollbar-thumb', colors.scrollbarThumb);
	root.style.setProperty('--theme-scrollbar-thumb-hover', colors.scrollbarThumbHover);

	// Code blocks
	root.style.setProperty('--theme-code-bg', colors.codeBg);
	root.style.setProperty('--theme-code-text', colors.codeText);
	root.style.setProperty('--theme-code-border', colors.codeBorder);

	// States
	root.style.setProperty('--theme-required-text', colors.requiredText);
	root.style.setProperty('--theme-empty-state-text', colors.emptyStateText);
};

/**
 * Resolve 'auto' theme to actual light/dark theme based on system preference
 */
const resolveAutoTheme = (themeId: ThemeId): Theme => {
	if (themeId !== 'auto') {
		return getThemeById(themeId) || themes[0]; // Fallback to default
	}

	const preference = getSystemPreference();
	const resolvedTheme = getThemeById(preference);
	return resolvedTheme || themes[0];
};

interface ThemeProviderProps {
	children: ReactNode;
}

/**
 * Theme Provider Component
 *
 * Wraps the application and provides theme context to all children.
 * Manages theme state, localStorage persistence, and system preference detection.
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
	// Initialize theme from localStorage or default to 'default'
	const [currentThemeId, setCurrentThemeId] = useState<ThemeId>(() => {
		if (typeof window === 'undefined') return 'default';
		const saved = localStorage.getItem(STORAGE_KEY) as ThemeId | null;
		if (saved && getThemeById(saved)) {
			return saved;
		}
		return 'default';
	});

	const currentTheme = getThemeById(currentThemeId) || themes[0];
	const effectiveTheme = resolveAutoTheme(currentThemeId);

	// Apply theme on mount and when it changes
	useEffect(() => {
		applyThemeVariables(effectiveTheme.colors);
	}, [effectiveTheme]);

	// Listen for system preference changes when in auto mode
	useEffect(() => {
		if (currentThemeId !== 'auto') return;

		const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

		const handleChange = () => {
			const newEffectiveTheme = resolveAutoTheme('auto');
			applyThemeVariables(newEffectiveTheme.colors);
		};

		// Modern browsers
		if (mediaQuery.addEventListener) {
			mediaQuery.addEventListener('change', handleChange);
			return () => mediaQuery.removeEventListener('change', handleChange);
		} else {
			// Fallback for older browsers
			mediaQuery.addListener(handleChange);
			return () => mediaQuery.removeListener(handleChange);
		}
	}, [currentThemeId]);

	const setTheme = (themeId: ThemeId) => {
		if (!getThemeById(themeId) && themeId !== 'auto') {
			console.warn(`Theme '${themeId}' not found, falling back to default`);
			themeId = 'default';
		}

		setCurrentThemeId(themeId);
		localStorage.setItem(STORAGE_KEY, themeId);
	};

	const value: ThemeContextValue = {
		currentThemeId,
		currentTheme,
		effectiveTheme,
		themes,
		setTheme,
	};

	return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

/**
 * Hook to access theme context
 *
 * @example
 * const { currentTheme, setTheme } = useTheme();
 */
export const useTheme = (): ThemeContextValue => {
	const context = useContext(ThemeContext);
	if (!context) {
		throw new Error('useTheme must be used within a ThemeProvider');
	}
	return context;
};

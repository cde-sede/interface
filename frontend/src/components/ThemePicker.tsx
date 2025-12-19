/**
 * Theme Picker Component
 *
 * Visual theme selector with color swatch previews.
 * Displays available themes in a dropdown with color previews.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import './ThemePicker.css';

export const ThemePicker: React.FC = () => {
	const { themes, currentThemeId, setTheme } = useTheme();
	const [isOpen, setIsOpen] = useState(false);
	const dropdownRef = useRef<HTMLDivElement>(null);

	// Close dropdown when clicking outside
	useEffect(() => {
		const handleClickOutside = (event: MouseEvent) => {
			if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
				setIsOpen(false);
			}
		};

		if (isOpen) {
			document.addEventListener('mousedown', handleClickOutside);
		}

		return () => {
			document.removeEventListener('mousedown', handleClickOutside);
		};
	}, [isOpen]);

	// Close dropdown on Escape key
	useEffect(() => {
		const handleEscape = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				setIsOpen(false);
			}
		};

		if (isOpen) {
			document.addEventListener('keydown', handleEscape);
		}

		return () => {
			document.removeEventListener('keydown', handleEscape);
		};
	}, [isOpen]);

	const handleThemeSelect = (themeId: string) => {
		setTheme(themeId as any);
		setIsOpen(false);
	};

	const handleToggle = () => {
		setIsOpen(!isOpen);
	};

	const handleKeyDown = (event: React.KeyboardEvent) => {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleToggle();
		}
	};

	return (
		<div className="theme-picker" ref={dropdownRef}>
			<button
				className="theme-picker-button"
				onClick={handleToggle}
				onKeyDown={handleKeyDown}
				aria-label="Select theme"
				aria-expanded={isOpen}
			>
				<svg
					width="20"
					height="20"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					strokeWidth="2"
					strokeLinecap="round"
					strokeLinejoin="round"
				>
					<circle cx="12" cy="12" r="10" />
					<path d="M12 2a7 7 0 0 0 0 14" />
					<path d="M12 8a7 7 0 0 1 0 14" />
				</svg>
			</button>

			{isOpen && (
				<div className="theme-picker-dropdown">
					<div className="theme-picker-header">
						<span>Select Theme</span>
					</div>
					<div className="theme-list">
						{themes.map((theme) => (
							<button
								key={theme.id}
								className={`theme-option ${currentThemeId === theme.id ? 'active' : ''}`}
								onClick={() => handleThemeSelect(theme.id)}
							>
								<div className="theme-option-info">
									<div className="theme-option-header">
										<span className="theme-option-name">{theme.displayName}</span>
										{currentThemeId === theme.id && (
											<svg
												className="theme-option-check"
												width="16"
												height="16"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												strokeWidth="3"
												strokeLinecap="round"
												strokeLinejoin="round"
											>
												<polyline points="20 6 9 17 4 12" />
											</svg>
										)}
									</div>
									<span className="theme-option-description">{theme.description}</span>
								</div>
								<div className="theme-color-swatches">
									{theme.previewColors.map((color, index) => (
										<span
											key={index}
											className="theme-color-swatch"
											style={{ backgroundColor: color }}
											aria-label={`Color ${index + 1}`}
										/>
									))}
								</div>
							</button>
						))}
					</div>
				</div>
			)}
		</div>
	);
};

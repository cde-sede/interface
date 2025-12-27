/**
 * Modal Component
 *
 * Dialog overlay for displaying content in a modal.
 */

import { useEffect, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Modal.css';

export type ModalSize = 'small' | 'medium' | 'large' | 'fullscreen';

export interface ModalProps extends BaseComponentProps {
	isOpen: boolean;               /** Modal open state */
	onClose: () => void;           /** Close handler */
	title?: string;                /** Modal title */
	children: ReactNode;           /** Modal content */
	size?: ModalSize;              /** Modal size */
	closeOnOverlayClick?: boolean; /** Close when clicking overlay */
	closeOnEscape?: boolean;       /** Close on Escape key */
}

export function Modal({
	isOpen,
	onClose,
	title,
	children,
	size = 'medium',
	closeOnOverlayClick = true,
	closeOnEscape = true,
	className,
	style,
	'data-testid': dataTestId
}: ModalProps) {
	// Handle escape key
	useEffect(() => {
		if (!isOpen || !closeOnEscape) return;

		const handleEscape = (e: KeyboardEvent) => {
			if (e.key === 'Escape') {
				onClose();
			}
		};

		document.addEventListener('keydown', handleEscape);
		return () => document.removeEventListener('keydown', handleEscape);
	}, [isOpen, closeOnEscape, onClose]);

	// Prevent body scroll when modal is open
	useEffect(() => {
		if (isOpen) {
			document.body.style.overflow = 'hidden';
		} else {
			document.body.style.overflow = '';
		}

		return () => {
			document.body.style.overflow = '';
		};
	}, [isOpen]);

	if (!isOpen) return null;

	const handleOverlayClick = (e: React.MouseEvent) => {
		if (closeOnOverlayClick && e.target === e.currentTarget) {
			onClose();
		}
	};

	const modalClassName = cn(
		'lib-modal-content',
		`lib-modal-${size}`,
		className
	);

	return (
		<div
			className="lib-modal-overlay"
			onClick={handleOverlayClick}
			data-testid={dataTestId}
		>
			<div className={modalClassName} style={style}>
				{title && (
					<div className="lib-modal-header">
						<h3>{title}</h3>
						<button
							className="lib-modal-close"
							onClick={onClose}
							aria-label="Close modal"
							type="button"
						>
							×
						</button>
					</div>
				)}
				<div className="lib-modal-body">
					{children}
				</div>
			</div>
		</div>
	);
}

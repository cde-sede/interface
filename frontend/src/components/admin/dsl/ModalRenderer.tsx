/**
 * Modal Renderer
 *
 * Renders modal from DSL definition
 */

import { useEffect, useRef } from 'react';
import type { ModalDefinition, ComponentDefinition } from './types';
import { ActionEngine } from './actionEngine';
import { resolveValue } from './valueResolver';
import StatsCardsRenderer from './StatsCardsRenderer';
import InfoGridRenderer from './InfoGridRenderer';
import CodeBlockRenderer from './CodeBlockRenderer';
import TableRenderer from './TableRenderer';
import ButtonRenderer from './ButtonRenderer';
import FormRenderer from './FormRenderer';
import DividerRenderer from './DividerRenderer';
import BadgeRenderer from './BadgeRenderer';
import ProgressBarRenderer from './ProgressBarRenderer';
import CardRenderer from './CardRenderer';
import AccordionRenderer from './AccordionRenderer';
import ChartRenderer from './ChartRenderer';

interface ModalRendererProps {
	modal: ModalDefinition;
	modalData?: any;
	pageData?: any;
	actionEngine: ActionEngine;
	onClose: () => void;
}

export default function ModalRenderer({
	modal,
	modalData,
	pageData,
	actionEngine,
	onClose
}: ModalRendererProps) {
	const modalRef = useRef<HTMLDivElement>(null);
	const { title: rawTitle, size = 'medium', content, actions, closeOnOverlayClick = true } = modal;

	// Resolve title if it's a ValueRef
	const title = resolveValue(rawTitle, { pageData, data: modalData });

	// Auto-copy key to clipboard if modalData contains a key field
	useEffect(() => {
		if (modalData?.key) {
			navigator.clipboard.writeText(modalData.key).then(() => {
				console.log('API key auto-copied to clipboard');
			}).catch(err => {
					console.error('Failed to auto-copy key:', err);
				});
		}
	}, [modalData?.key]);

	// Handle escape key (only if this is the topmost modal)
	useEffect(() => {
		const handleEscape = (e: KeyboardEvent) => {
			if (e.key === 'Escape') {
				// Check if this modal is the topmost one
				const allModals = document.querySelectorAll('.modal-overlay');
				const thisModal = modalRef.current?.parentElement;
				const topmostModal = allModals[allModals.length - 1];

				// Only close if this is the topmost modal
				if (thisModal === topmostModal) {
					e.stopImmediatePropagation();
					onClose();
				}
			}
		};

		document.addEventListener('keydown', handleEscape);
		return () => document.removeEventListener('keydown', handleEscape);
	}, [onClose]);

	// Handle overlay click
	const handleOverlayClick = (e: React.MouseEvent) => {
		if (closeOnOverlayClick && e.target === e.currentTarget) {
			onClose();
		}
	};

	// Render component
	const renderComponent = (component: ComponentDefinition) => {
		switch (component.type) {
			case 'stats-cards':
				return <StatsCardsRenderer component={component} />;
			case 'info-grid':
				return <InfoGridRenderer component={component} pageData={pageData} modalData={modalData} />;
			case 'code-block':
				return <CodeBlockRenderer component={component} pageData={pageData} modalData={modalData} />;
			case 'table':
				return <TableRenderer component={component} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'button':
				return <ButtonRenderer component={component} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'form':
				return <FormRenderer component={component} pageData={pageData} actionEngine={actionEngine} modalData={modalData} />;
			case 'divider':
				return <DividerRenderer component={component} />;
			case 'badge':
				return <BadgeRenderer component={component} pageData={pageData} modalData={modalData} />;
			case 'progress-bar':
				return <ProgressBarRenderer component={component} pageData={pageData} modalData={modalData} />;
			case 'card':
				return <CardRenderer component={component} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'accordion':
				return <AccordionRenderer component={component} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'chart':
				return <ChartRenderer component={component} pageData={pageData} modalData={modalData} />;
			default:
				return null;
		}
	};

	return (
		<div className="modal-overlay" onClick={handleOverlayClick}>
			<div ref={modalRef} className={`modal-content modal-${size}`}>
				<div className="modal-header">
					<h3>{title}</h3>
					<button className="modal-close" onClick={onClose}>
						×
					</button>
				</div>

				<div className="modal-body">
					{content?.map((component, index) => (
						<div key={index} className="modal-component">
							{renderComponent(component)}
						</div>
					))}
				</div>

				{actions && actions.length > 0 && (
					<div className="modal-actions">
						{actions.map((action, index) => (
							<ButtonRenderer
								key={index}
								component={action}
								pageData={pageData}
								modalData={modalData}
								actionEngine={actionEngine}
							/>
						))}
					</div>
				)}
			</div>
		</div>
	);
}

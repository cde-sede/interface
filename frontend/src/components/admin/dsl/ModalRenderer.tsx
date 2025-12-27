/**
 * Modal Renderer
 *
 * DSL wrapper for the Modal component that handles:
 * - Value resolution from context
 * - Auto-copy key functionality
 * - Rendering DSL content and actions
 */

import { useEffect } from 'react';
import type { ModalDefinition } from './types';
import { ActionEngine } from './actionEngine';
import { resolveValue } from './valueResolver';
import { renderComponent } from '../DSLRenderer';
import ButtonRenderer from './ButtonRenderer';
import { Modal } from '../../library';

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
	const { title: rawTitle, size = 'medium', content, actions, closeOnOverlayClick = true } = modal;

	// Resolve title if it's a ValueRef
	const title = resolveValue(rawTitle, { pageData, data: modalData });

	// Auto-copy key to clipboard if modalData contains a key field
	useEffect(() => {
		if (modalData?.key) {
			navigator.clipboard.writeText(modalData.key).then(() => {
				// console.log('API key auto-copied to clipboard');
			}).catch(err => {
					console.error('Failed to auto-copy key:', err);
				});
		}
	}, [modalData?.key]);

	return (
		<Modal
			title={title}
			isOpen={true}
			onClose={onClose}
			size={size}
			closeOnOverlayClick={closeOnOverlayClick}
		>
			{content?.map((component, index) => (
				<div key={index} className="modal-component">
					{renderComponent(component, pageData, modalData, actionEngine)}
				</div>
			))}

			{actions && actions.length > 0 && (
				<div className="lib-modal-actions">
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
		</Modal>
	);
}

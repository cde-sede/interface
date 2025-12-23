/**
 * DSL Renderer Component
 *
 * Main component that interprets and renders admin page DSL.
 * This component acts as the central orchestrator for DSL-based pages.
 */

import { useState, useCallback } from 'react';
import type { Socket } from 'socket.io-client';
import type {
	PageDSL,
	ComponentDefinition,
	SectionComponent,
	LayoutComponent
} from './dsl/types';
import { ActionEngine, type ActionEngineCallbacks } from './dsl/actionEngine';
import { useSocketEvents } from './hooks/useSocketEvents';
import StatsCardsRenderer from './dsl/StatsCardsRenderer';
import InfoGridRenderer from './dsl/InfoGridRenderer';
import CodeBlockRenderer from './dsl/CodeBlockRenderer';
import TableRenderer from './dsl/TableRenderer';
import ButtonRenderer from './dsl/ButtonRenderer';
import FormRenderer from './dsl/FormRenderer';
import ModalRenderer from './dsl/ModalRenderer';
import ChartRenderer from './dsl/ChartRenderer';
import DividerRenderer from './dsl/DividerRenderer';
import BadgeRenderer from './dsl/BadgeRenderer';
import ProgressBarRenderer from './dsl/ProgressBarRenderer';
import CardRenderer from './dsl/CardRenderer';
import AccordionRenderer from './dsl/AccordionRenderer';
import './dsl/DSLComponents.css';

interface DSLRendererProps {
	dsl: PageDSL;
	socket: Socket | null;
	currentPage: string;
	onShowToast: (message: string, type: 'success' | 'error' | 'info' | 'warning') => void;
	onShowConfirm: (message: string) => Promise<boolean>;
	onNavigate: (page: string) => void;
	onRefresh: () => void;
}

export default function DSLRenderer({
	dsl,
	socket,
	currentPage,
	onShowToast,
	onShowConfirm,
	onNavigate,
	onRefresh
}: DSLRendererProps) {
	const [openModals, setOpenModals] = useState<Set<string>>(new Set());
	const [modalData, setModalData] = useState<Record<string, any>>({});

	// Create action engine callbacks
	const actionCallbacks: ActionEngineCallbacks = {
		showToast: onShowToast,
		showConfirm: onShowConfirm,
		openModal: useCallback((modalId: string, data?: any) => {
			setOpenModals(prev => new Set(prev).add(modalId));
			if (data) {
				setModalData(prev => ({ ...prev, [modalId]: data }));
			}
		}, []),
		closeModal: useCallback((modalId: string) => {
			setOpenModals(prev => {
				const next = new Set(prev);
				next.delete(modalId);
				return next;
			});
			setModalData(prev => {
				const next = { ...prev };
				delete next[modalId];
				return next;
			});
		}, []),
		navigate: onNavigate,
		refresh: onRefresh
	};

	// Create action engine instance
	const actionEngine = new ActionEngine(actionCallbacks);

	// Set up Socket.IO event listeners based on DSL configuration
	useSocketEvents({
		socket,
		realtimeConfig: dsl.realtime,
		currentPage,
		onRefresh,
		onShowToast
	});

	// Render layout
	const renderLayout = (layout: LayoutComponent) => {
		switch (layout.type) {
			case 'vertical':
			case 'horizontal':
				return (
					<div className={`layout-${layout.type} ${layout.className || ''}`}>
						{layout.sections?.map((section, index) => (
							<div key={section.id || index}>
								{renderSection(section)}
							</div>
						))}
					</div>
				);

			case 'grid':
				return (
					<div className={`layout-grid ${layout.className || ''}`}>
						{layout.sections?.map((section, index) => (
							<div key={section.id || index}>
								{renderSection(section)}
							</div>
						))}
					</div>
				);

			case 'tabs':
				// TODO: Implement tabs layout
				return <div>Tabs layout not implemented yet</div>;

			default:
				return null;
		}
	};

	// Render section
	const renderSection = (section: SectionComponent) => {
		return (
			<div className={`content-section ${section.className || ''}`}>
				{section.title && <h3>{section.title}</h3>}
				{section.components.map((component, index) => (
					<div key={index}>
						{renderComponent(component)}
					</div>
				))}
			</div>
		);
	};

	// Render component based on type
	const renderComponent = (component: ComponentDefinition) => {
		switch (component.type) {
			case 'stats-cards':
				return <StatsCardsRenderer component={component} />;

			case 'table':
				return <TableRenderer component={component} pageData={dsl} actionEngine={actionEngine} />;

			case 'info-grid':
				return <InfoGridRenderer component={component} pageData={dsl} />;

			case 'code-block':
				return <CodeBlockRenderer component={component} pageData={dsl} />;

			case 'chart':
				return <ChartRenderer component={component} pageData={dsl} />;

			case 'form':
				return <FormRenderer component={component} pageData={dsl} actionEngine={actionEngine} />;

			case 'button':
				return <ButtonRenderer component={component} pageData={dsl} actionEngine={actionEngine} />;

			case 'alert':
				return (
					<div className={`alert alert-${component.variant}`}>
						{component.message}
					</div>
				);

			case 'empty-state':
				return (
					<div className="empty-state">
						{component.icon && <span className="empty-state-icon">{component.icon}</span>}
						<p className="empty-state-message">{component.message}</p>
						{component.description && (
							<p className="empty-state-description">{component.description}</p>
						)}
					</div>
				);

			case 'divider':
				return <DividerRenderer component={component} />;

			case 'badge':
				return <BadgeRenderer component={component} pageData={dsl} />;

			case 'progress-bar':
				return <ProgressBarRenderer component={component} pageData={dsl} />;

			case 'card':
				return <CardRenderer component={component} pageData={dsl} actionEngine={actionEngine} />;

			case 'accordion':
				return <AccordionRenderer component={component} pageData={dsl} actionEngine={actionEngine} />;

			default:
				console.warn('Unknown component type:', (component as any).type);
				return <div>Unknown component type</div>;
		}
	};

	// Render modals
	const renderModals = () => {
		if (!dsl.modals) return null;

		return Array.from(openModals).map(modalId => {
			const modal = dsl.modals?.[modalId];
			if (!modal) return null;

			const data = modalData[modalId];

			return (
				<ModalRenderer
					key={modalId}
					modal={modal}
					modalData={data}
					pageData={dsl}
					actionEngine={actionEngine}
					onClose={() => actionCallbacks.closeModal(modalId)}
				/>
			);
		});
	};

	return (
		<div className="page-content">
			{/* Page header */}
			<div className="page-header">
				<div>
					<h2>{dsl.title}</h2>
					{dsl.description && <p className="page-description">{dsl.description}</p>}
				</div>
			</div>

			{/* Main content */}
			{renderLayout(dsl.layout)}

			{/* Modals */}
			{renderModals()}
		</div>
	);
}

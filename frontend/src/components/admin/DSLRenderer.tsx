/**
 * DSL Renderer Component
 *
 * Main component that interprets and renders admin page DSL.
 * This component acts as the central orchestrator for DSL-based pages.
 */

import { useState, useCallback, useMemo } from 'react';
import type { Socket } from 'socket.io-client';
import type {
	PageDSL,
	ComponentDefinition,
	RichTextComponent,
	SectionComponent,
	LayoutComponent
} from './dsl/types';
import { ActionEngine, type ActionEngineCallbacks } from './dsl/actionEngine';
import { useSocketEvents } from './hooks/useSocketEvents';
import { usePolling } from './hooks/usePolling';
import StatsCardsRenderer from './dsl/StatsCardsRenderer';
import InfoGridRenderer from './dsl/InfoGridRenderer';
import CodeBlockRenderer from './dsl/CodeBlockRenderer';
import TableRenderer from './dsl/TableRenderer';
import ButtonRenderer from './dsl/ButtonRenderer';
import FormRenderer from './dsl/FormRenderer';
import ModalRenderer from './dsl/ModalRenderer';
import ChartRenderer from './dsl/ChartRenderer';
import DividerRenderer from './dsl/DividerRenderer';
import AlertRenderer from './dsl/AlertRenderer';
import RichTextRenderer from './dsl/RichTextRenderer';
import BadgeRenderer from './dsl/BadgeRenderer';
import ProgressBarRenderer from './dsl/ProgressBarRenderer';
import CardRenderer from './dsl/CardRenderer';
import AccordionRenderer from './dsl/AccordionRenderer';
import PanelRenderer from './dsl/PanelRenderer';
import ImageRenderer from './dsl/ImageRenderer';
import TimelineRenderer from './dsl/TimelineRenderer';
import ListRenderer from './dsl/ListRenderer';
import StepperRenderer from './dsl/StepperRenderer';
import MetricRenderer from './dsl/MetricRenderer';
import AvatarRenderer from './dsl/AvatarRenderer';
import CalloutRenderer from './dsl/CalloutRenderer';
import SpacerRenderer from './dsl/SpacerRenderer';
import TabsRenderer from './dsl/TabsRenderer';
import BreadcrumbsRenderer from './dsl/BreadcrumbsRenderer';
import TooltipRenderer from './dsl/TooltipRenderer';
import ToggleRenderer from './dsl/ToggleRenderer';
import ChipInputRenderer from './dsl/ChipInputRenderer';
import SkeletonRenderer from './dsl/SkeletonRenderer';
import DropdownRenderer from './dsl/DropdownRenderer';
import TreeViewRenderer from './dsl/TreeViewRenderer';
import FileUploadRenderer from './dsl/FileUploadRenderer';
import DatePickerRenderer from './dsl/DatePickerRenderer';
import DataGridRenderer from './dsl/DataGridRenderer';
import CalendarRenderer from './dsl/CalendarRenderer';
import GridRenderer from './dsl/GridRenderer';
import FlexRenderer from './dsl/FlexRenderer';
import ContainerRenderer from './dsl/ContainerRenderer';
import DeferRenderer from './dsl/DeferRenderer';
import DynamicRenderer from './dsl/DynamicRenderer';
import TextInputRenderer from './dsl/TextInputRenderer';
import NumberInputRenderer from './dsl/NumberInputRenderer';
import TextAreaRenderer from './dsl/TextAreaRenderer';
import CheckboxRenderer from './dsl/CheckboxRenderer';
import RadioRenderer from './dsl/RadioRenderer';
import './dsl/DSLComponents.css';

interface DSLRendererProps {
	dsl: PageDSL;
	socket: Socket | null;
	currentPage: string;
	onShowToast: (message: string | RichTextComponent, type: 'success' | 'error' | 'info' | 'warning') => void;
	onShowConfirm: (message: string) => Promise<boolean>;
	onNavigate: (page: string) => void;
	onRefresh: () => void;
}

// Exported render function for use by child components
export function renderComponent(
	component: ComponentDefinition,
	pageData: any,
	_modalData: any,
	actionEngine: ActionEngine
): React.JSX.Element {
	switch (component.type) {
		case 'stats-cards':
			return <StatsCardsRenderer component={component} />;

		case 'table':
			return <TableRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'info-grid':
			return <InfoGridRenderer component={component} pageData={pageData} />;

		case 'code-block':
			return <CodeBlockRenderer component={component} pageData={pageData} />;

		case 'chart':
			return <ChartRenderer component={component} pageData={pageData} />;

		case 'form':
			return <FormRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'button':
			return <ButtonRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'alert':
			return <AlertRenderer component={component} pageData={pageData} modalData={_modalData} />;

		case 'rich-text':
			return <RichTextRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

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
			return <BadgeRenderer component={component} pageData={pageData} />;

		case 'progress-bar':
			return <ProgressBarRenderer component={component} pageData={pageData} />;

		case 'card':
			return <CardRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'accordion':
			return <AccordionRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'image':
			return <ImageRenderer component={component} pageData={pageData} />;

		case 'timeline':
			return <TimelineRenderer component={component} pageData={pageData} />;

		case 'list':
			return <ListRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'stepper':
			return <StepperRenderer component={component} pageData={pageData} />;

		case 'metric':
			return <MetricRenderer component={component} pageData={pageData} />;

		case 'avatar':
			return <AvatarRenderer component={component} pageData={pageData} />;

		case 'callout':
			return <CalloutRenderer component={component} pageData={pageData} />;

		case 'spacer':
			return <SpacerRenderer component={component} />;

		case 'tabs':
			return <TabsRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'breadcrumbs':
			return <BreadcrumbsRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'tooltip':
			return <TooltipRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'toggle':
			return <ToggleRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'chip-input':
			return <ChipInputRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'skeleton':
			return <SkeletonRenderer component={component} pageData={pageData} />;

		case 'dropdown':
			return <DropdownRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'tree-view':
			return <TreeViewRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'file-upload':
			return <FileUploadRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'date-picker':
			return <DatePickerRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'data-grid':
			return <DataGridRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'calendar':
			return <CalendarRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'grid':
			return <GridRenderer component={component} pageData={pageData} actionEngine={actionEngine} />;

		case 'flex':
			return <FlexRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		case 'container':
			return <ContainerRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		case 'defer':
			return <DeferRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		case 'dynamic':
			return <DynamicRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		case 'text-input':
			return <TextInputRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		case 'number-input':
			return <NumberInputRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		case 'textarea':
			return <TextAreaRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		case 'checkbox':
			return <CheckboxRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		case 'radio':
			return <RadioRenderer component={component} pageData={pageData} modalData={_modalData} actionEngine={actionEngine} />;

		default:
			console.warn('Unknown component type:', (component as any).type);
			return <div>Unknown component type</div>;
	}
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
	const [openPanels, setOpenPanels] = useState<Set<string>>(new Set());
	const [minimizedPanels, setMinimizedPanels] = useState<Set<string>>(new Set());
	const [panelData, setPanelData] = useState<Record<string, any>>({});

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
		openPanel: useCallback((panelId: string, data?: any) => {
			setOpenPanels(prev => new Set(prev).add(panelId));
			if (data) {
				setPanelData(prev => ({ ...prev, [panelId]: data }));
			}
			// Initialize default open panels
			if (dsl.panels?.[panelId]?.defaultOpen && !openPanels.has(panelId)) {
				setOpenPanels(prev => new Set(prev).add(panelId));
			}
		}, [dsl.panels, openPanels]),
		closePanel: useCallback((panelId: string) => {
			setOpenPanels(prev => {
				const next = new Set(prev);
				next.delete(panelId);
				return next;
			});
			setPanelData(prev => {
				const next = { ...prev };
				delete next[panelId];
				return next;
			});
		}, []),
		togglePanel: useCallback((panelId: string, data?: any) => {
			setOpenPanels(prev => {
				const next = new Set(prev);
				if (next.has(panelId)) {
					next.delete(panelId);
				} else {
					next.add(panelId);
					if (data) {
						setPanelData(prevData => ({ ...prevData, [panelId]: data }));
					}
				}
				return next;
			});
		}, []),
		navigate: onNavigate,
		refresh: onRefresh
	};

	// Create action engine instance (memoized to persist dataStore across re-renders)
	const actionEngine = useMemo(() => new ActionEngine(actionCallbacks), []);

	// Set up Socket.IO event listeners based on DSL configuration
	useSocketEvents({
		socket,
		realtimeConfig: dsl.realtime,
		currentPage,
		actionEngine,
		onRefresh,
		onShowToast
	});

	// Set up polling based on DSL configuration
	usePolling({
		pollingConfig: dsl.realtime?.polling,
		actionEngine,
		authToken: localStorage.getItem('auth_token')
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
				if (!layout.tabs) return null;
				return (
					<TabsRenderer
						component={{
							type: 'tabs',
							items: layout.tabs.map(tab => ({
								id: tab.id,
								label: tab.label,
								icon: tab.icon,
								content: tab.content.sections?.flatMap(s => s.components) || []
							}))
						}}
						pageData={dsl}
						actionEngine={actionEngine}
					/>
				);

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
						{renderComponentLocal(component)}
					</div>
				))}
			</div>
		);
	};

	// Wrapper function that uses the exported renderComponent
	const renderComponentLocal = (component: ComponentDefinition) => {
		return renderComponent(component, dsl, undefined, actionEngine);
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

	// Render panels
	const renderPanels = () => {
		if (!dsl.panels) return null;

		return Object.entries(dsl.panels).map(([panelId, panel]) => {
			// Check if panel should be open or minimized
			const isOpen = openPanels.has(panelId);
			const isMinimized = minimizedPanels.has(panelId);
			const data = panelData[panelId];

			// Don't render if never opened/minimized and not defaultOpen
			if (!isOpen && !isMinimized && !panel.defaultOpen) return null;

			return (
				<PanelRenderer
					key={panelId}
					panel={panel}
					panelData={data}
					pageData={dsl}
					actionEngine={actionEngine}
					isOpen={isOpen}
					onClose={() => {
						actionCallbacks.closePanel(panelId);
						setMinimizedPanels(prev => {
							const next = new Set(prev);
							next.delete(panelId);
							return next;
						});
					}}
					onOpen={() => {
						actionCallbacks.openPanel(panelId, data);
					}}
					isMinimized={isMinimized}
					onMinimize={(minimized: boolean) => {
						setMinimizedPanels(prev => {
							const next = new Set(prev);
							if (minimized) {
								next.add(panelId);
							} else {
								next.delete(panelId);
							}
							return next;
						});
					}}
				/>
			);
		});
	};

	return (
		<div className="page-content">
			{/* Page header */}
			{ dsl.title || dsl.description ? 
				<div className="page-header">
					<div>
						<h2>{dsl.title}</h2>
						{dsl.description && <p className="page-description">{dsl.description}</p>}
					</div>
				</div>
			: null }

			{/* Main content */}
			{renderLayout(dsl.layout)}

			{/* Modals */}
			{renderModals()}

			{/* Panels */}
			{renderPanels()}
		</div>
	);
}

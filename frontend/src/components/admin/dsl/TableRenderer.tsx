/**
 * Table Renderer
 *
 * DSL adapter for Table library component.
 */

import { startTransition, useState, useEffect, useMemo } from 'react';
import { Table } from '../../library/Table';
import type {
	TableColumn,
	TableRowAction,
	TableHeaderAction,
	TablePagination,
	TableEmptyState
} from '../../library/Table';
import type { TableComponent, ColumnDefinition, RowActionDefinition, TableActionDefinition } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue, resolveComponentData } from './valueResolver';

interface TableRendererProps {
	modalData?: any;
	component: TableComponent;
	pageData?: any;
	actionEngine?: ActionEngine;
}

export default function TableRenderer({ component, pageData, modalData, actionEngine }: TableRendererProps) {
	const { actions, rowActions, emptyState, onRowClick, density, pagination, sortable } = component;

	// Resolve initial data and columns
	const initialData = useMemo(
		() => resolveComponentData(component.data, pageData, modalData) || [],
		[component.data, pageData, modalData]
	);
	const dslColumns: ColumnDefinition[] = resolveComponentData(component.columns, pageData, modalData) || component.columns;

	// Local state for table data (allows adding rows dynamically)
	const [localData, setLocalData] = useState<any[]>(initialData);

	// Sync local data when initial data changes
	useEffect(() => {
		setLocalData(initialData);
	}, [initialData]);

	// Listen for add-rows events
	useEffect(() => {
		if (!component.id) return;

		const handleAddRows = (e: Event) => {
			const customEvent = e as CustomEvent<{ targetId: string; rows: any[] }>;
			if (customEvent.detail.targetId === component.id) {
				setLocalData(prev => [...prev, ...customEvent.detail.rows]);
			}
		};

		window.addEventListener('dsl-add-rows', handleAddRows);
		return () => window.removeEventListener('dsl-add-rows', handleAddRows);
	}, [component.id]);

	const data = localData;

	// Map DSL columns to library columns
	const columns: TableColumn[] = dslColumns.map((col) => ({
		key: col.key,
		label: col.label,
		type: col.type === 'status' ? 'status' : col.type === 'code' ? 'code' : col.type === 'date' ? 'date' : 'text',
		align: col.align,
		width: col.width,
		sortable: col.sortable,
		hidden: col.hidden,
		truncate: col.truncate,
		statusConfig: col.renderer?.type === 'status-badge' && col.renderer.config
			? Object.fromEntries(
				Object.entries(col.renderer.config).map(([key, cfg]) => [
					key,
					{
						label: cfg.label,
						variant: cfg.variant === 'success' ? 'ready' : cfg.variant
					}
				])
			)
			: undefined
	}));

	// Map DSL header actions to library actions
	const headerActions: TableHeaderAction[] | undefined = actions && actionEngine ? actions.map((action: TableActionDefinition) => ({
		id: action.id,
		label: action.label,
		onClick: () => {
			const context = { pageData, data: modalData };
			startTransition(() => {
				if (action.confirmMessage) {
					const message = resolveValue(action.confirmMessage, context);
					actionEngine.executeWithConfirmation(action.action, message, context);
				} else {
					actionEngine.execute(action.action, context);
				}
			});
		}
	})) : undefined;

	// Map DSL row actions to library actions
	const mappedRowActions: TableRowAction[] | undefined = rowActions && actionEngine ? rowActions.map((action: RowActionDefinition) => ({
		id: action.id,
		label: action.label,
		onClick: (row: any) => {
			const context = { row, pageData, data: modalData };
			startTransition(() => {
				if (action.confirmMessage) {
					const message = resolveValue(action.confirmMessage, context);
					actionEngine.executeWithConfirmation(action.action, message, context);
				} else {
					actionEngine.execute(action.action, context);
				}
			});
		}
	})) : undefined;

	// Map DSL row click to library handler
	const handleRowClick = onRowClick && actionEngine ? (row: any) => {
		const context = { row, pageData, data: modalData };

		startTransition(() => {
			switch (onRowClick.action) {
				case 'open-modal':
					const modalId = resolveValue(onRowClick.target, context);
					const params = onRowClick.params
						? Object.fromEntries(
							Object.entries(onRowClick.params).map(([key, val]) => [
								key,
								resolveValue(val, context)
							])
						)
						: undefined;

					actionEngine.execute({
						type: 'open-modal',
						modalId,
						modalData: params
					}, context);
					break;

				case 'navigate':
					actionEngine.execute({
						type: 'navigate',
						page: onRowClick.target
					}, context);
					break;

				case 'api-call':
					actionEngine.execute({
						type: 'api-call',
						endpoint: onRowClick.target
					}, context);
					break;
			}
		});
	} : undefined;

	// Map DSL pagination to library pagination
	const mappedPagination: TablePagination | undefined = pagination ? {
		enabled: pagination.enabled,
		mode: pagination.mode,
		pageSize: pagination.pageSize,
		totalItems: pagination.totalItems ? resolveComponentData(pagination.totalItems, pageData, modalData) : undefined,
		currentPage: pagination.currentPage ? resolveComponentData(pagination.currentPage, pageData, modalData) : undefined,
		onPageChange: pagination.onPageChange && actionEngine ? (newPage: number, pageSize: number) => {
			startTransition(() => {
				const context = {
					pageData,
					data: modalData,
					pagination: {
						pageNumber: newPage,
						pageSize: pageSize
					}
				};
				actionEngine.execute(pagination.onPageChange!, context);
			});
		} : undefined,
		showPageNumbers: pagination.showPageNumbers,
		maxPageButtons: pagination.maxPageButtons,
		showFirstLast: pagination.showFirstLast,
		showPrevNext: pagination.showPrevNext
	} : undefined;

	// Map DSL empty state to library empty state
	const mappedEmptyState: TableEmptyState | undefined = emptyState ? {
		message: emptyState.message,
		description: emptyState.description
	} : undefined;

	const { customStyle, className: rawClassName } = component;
	const className = rawClassName ? resolveValue(rawClassName, { pageData, data: modalData }) : undefined;

	const tableElement = (
		<Table
			data={data || []}
			columns={columns}
			headerActions={headerActions}
			rowActions={mappedRowActions}
			onRowClick={handleRowClick}
			sortable={sortable}
			density={density}
			pagination={mappedPagination}
			emptyState={mappedEmptyState}
			style={customStyle as React.CSSProperties}
			className={className}
		/>
	);

	// Only use ComponentWrapper if we have wrapper-level properties
	const needsWrapper = Boolean(
		actionEngine && (
			component.events?.click ||
			component.events?.hover ||
			component.id ||
			component.ariaLabel ||
			component.ariaDescribedBy
		)
	);

	if (!needsWrapper) {
		return tableElement;
	}

	// Create a component object without customStyle/className to avoid duplication
	const wrapperComponent = {
		...component,
		customStyle: undefined,
		className: undefined
	};

	return (
		<ComponentWrapper
			component={wrapperComponent}
			pageData={pageData}
			modalData={modalData}
			actionEngine={actionEngine}
		>
			{tableElement}
		</ComponentWrapper>
	);
}

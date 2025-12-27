/**
 * Data Grid Renderer
 *
 * DSL adapter for DataGrid library component.
 */

import { startTransition } from 'react';
import { DataGrid } from '../../library/DataGrid';
import type {
	DataGridColumn,
	DataGridRowAction,
	DataGridPagination
} from '../../library/DataGrid';
import type { DataGridComponent, DataGridColumn as DSLDataGridColumn } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface DataGridRendererProps {
	component: DataGridComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function DataGridRenderer({ component, pageData, modalData, actionEngine }: DataGridRendererProps) {
	const {
		data,
		columns,
		editable = false,
		selectable = false,
		rowActions,
		onCellEdit,
		onSelectionChange,
		pagination,
		height,
		virtualized = false
	} = component;

	const resolvedData = resolveValue(data, { pageData, data: modalData });
	const resolvedHeight = height ? resolveValue(height, { pageData, data: modalData }) : 'auto';

	// Map DSL columns to library columns
	const mappedColumns: DataGridColumn[] = columns.map((col: DSLDataGridColumn) => ({
		key: col.key,
		label: col.label,
		width: col.width,
		editable: col.editable,
		type: col.type,
		options: col.options,
		statusConfig: col.renderer?.type === 'status-badge' && col.renderer.config
			? col.renderer.config
			: undefined,
		format: col.format
	}));

	// Map DSL row actions to library actions
	const mappedRowActions: DataGridRowAction[] | undefined = rowActions?.map((action) => ({
		label: action.label,
		icon: action.icon,
		onClick: (row: any, rowIndex: number) => {
			if (actionEngine) {
				startTransition(() => {
					actionEngine.execute(action.action, {
						pageData,
						data: modalData,
						row,
						rowIndex
					});
				});
			}
		}
	}));

	// Map DSL pagination to library pagination
	const mappedPagination: DataGridPagination | undefined = pagination ? {
		pageSize: pagination.pageSize
	} : undefined;

	// Cell edit handler
	const handleCellEdit = onCellEdit && actionEngine ? (row: any, column: string, value: any) => {
		startTransition(() => {
			actionEngine.execute(onCellEdit, {
				pageData,
				data: modalData,
				row,
				column,
				value
			});
		});
	} : undefined;

	// Selection change handler
	const handleSelectionChange = onSelectionChange && actionEngine ? (selectedRows: any[]) => {
		startTransition(() => {
			actionEngine.execute(onSelectionChange, {
				pageData,
				data: modalData,
				selectedRows
			});
		});
	} : undefined;

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const dataGridElement = (
		<DataGrid
			data={resolvedData || []}
			columns={mappedColumns}
			editable={editable}
			selectable={selectable}
			rowActions={mappedRowActions}
			onCellEdit={handleCellEdit}
			onSelectionChange={handleSelectionChange}
			pagination={mappedPagination}
			height={resolvedHeight}
			virtualized={virtualized}
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
		return dataGridElement;
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
			{dataGridElement}
		</ComponentWrapper>
	);
}

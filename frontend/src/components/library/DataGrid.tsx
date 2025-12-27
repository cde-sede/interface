/**
 * DataGrid Component
 *
 * Editable data grid with selection and cell editing.
 */

import { useState, useEffect, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './DataGrid.css';

export type DataGridColumnType = 'text' | 'number' | 'date' | 'boolean' | 'select';
export type DataGridFormatType = 'date' | 'number' | 'currency';

export interface DataGridStatusConfig {
	[key: string]: {
		label: string;
		variant: string;
	};
}

export interface DataGridFormat {
	type: DataGridFormatType;
	options?: any;
}

export interface DataGridColumn {
	key: string;                    /** Column key */
	label: string;                  /** Column header */
	width?: string;                 /** Column width */
	editable?: boolean;             /** Enable cell editing */
	type?: DataGridColumnType;      /** Column type */
	options?: any[];                /** Select options */
	statusConfig?: DataGridStatusConfig; /** Status badge config */
	format?: DataGridFormat;        /** Value formatting */
}

export interface DataGridRowAction {
	label: string;                  /** Action label */
	icon?: string;                  /** Optional icon */
	onClick: (row: any, rowIndex: number) => void; /** Click handler */
}

export interface DataGridPagination {
	pageSize: number;               /** Items per page */
}

export interface DataGridProps extends BaseComponentProps {
	data: any[];                    /** Grid data */
	columns: DataGridColumn[];      /** Column definitions */
	editable?: boolean;             /** Enable editing globally */
	selectable?: boolean;           /** Enable row selection */
	rowActions?: DataGridRowAction[]; /** Row actions */
	onCellEdit?: (row: any, column: string, value: any) => void; /** Cell edit handler */
	onSelectionChange?: (selectedRows: any[]) => void; /** Selection change handler */
	pagination?: DataGridPagination; /** Pagination config */
	height?: string;                /** Container height */
	virtualized?: boolean;          /** Enable virtualization */
}

export function DataGrid({
	data: initialData,
	columns,
	editable = false,
	selectable = false,
	rowActions,
	onCellEdit,
	onSelectionChange,
	pagination,
	height = 'auto',
	virtualized = false,
	className,
	style,
	'data-testid': dataTestId
}: DataGridProps) {
	const [gridData, setGridData] = useState(initialData);
	const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
	const [editingCell, setEditingCell] = useState<{ row: number; col: string } | null>(null);
	const [editValue, setEditValue] = useState<any>('');
	const [currentPage, setCurrentPage] = useState(1);

	useEffect(() => {
		setGridData(initialData);
	}, [initialData]);

	// Pagination
	const pageSize = pagination?.pageSize || 10;
	const totalPages = Math.ceil(gridData.length / pageSize);
	const paginatedData = pagination
		? gridData.slice((currentPage - 1) * pageSize, currentPage * pageSize)
		: gridData;

	const handleCellClick = (rowIndex: number, column: DataGridColumn, value: any) => {
		if (editable && column.editable) {
			setEditingCell({ row: rowIndex, col: column.key });
			setEditValue(value);
		}
	};

	const handleCellEdit = (rowIndex: number, columnKey: string, newValue: any) => {
		const updatedData = [...gridData];
		const actualIndex = pagination ? (currentPage - 1) * pageSize + rowIndex : rowIndex;
		updatedData[actualIndex] = { ...updatedData[actualIndex], [columnKey]: newValue };
		setGridData(updatedData);
		setEditingCell(null);

		onCellEdit?.(updatedData[actualIndex], columnKey, newValue);
	};

	const handleRowSelect = (rowIndex: number) => {
		const newSelection = new Set(selectedRows);
		if (newSelection.has(rowIndex)) {
			newSelection.delete(rowIndex);
		} else {
			newSelection.add(rowIndex);
		}
		setSelectedRows(newSelection);

		const selectedData = Array.from(newSelection).map(idx => gridData[idx]);
		onSelectionChange?.(selectedData);
	};

	const handleSelectAll = () => {
		if (selectedRows.size === gridData.length) {
			setSelectedRows(new Set());
			onSelectionChange?.([]);
		} else {
			const allIndices = new Set(gridData.map((_: any, idx: number) => idx));
			setSelectedRows(allIndices);
			onSelectionChange?.(gridData);
		}
	};

	const renderCell = (row: any, column: DataGridColumn, rowIndex: number): ReactNode => {
		const value = row[column.key];
		const isEditing = editingCell?.row === rowIndex && editingCell?.col === column.key;

		if (isEditing) {
			return (
				<input
					type={column.type || 'text'}
					value={editValue}
					onChange={(e) => setEditValue(e.target.value)}
					onBlur={() => handleCellEdit(rowIndex, column.key, editValue)}
					onKeyDown={(e) => {
						if (e.key === 'Enter') {
							handleCellEdit(rowIndex, column.key, editValue);
						} else if (e.key === 'Escape') {
							setEditingCell(null);
						}
					}}
					className="lib-data-grid-input"
					style={{
						width: '100%',
						boxSizing: 'border-box',
						background: 'transparent',
						padding: '0px 0px',
						margin: '0',
						border: '1px solid var(--theme-input-accent)',
						font: 'inherit'
					}}
					autoFocus
				/>
			);
		}

		// Apply status badge renderer
		if (column.statusConfig) {
			const statusConfig = column.statusConfig[value];
			if (statusConfig) {
				return <span className={`badge badge-${statusConfig.variant}`}>{statusConfig.label}</span>;
			}
		}

		// Apply format if defined
		if (column.format) {
			if (column.format.type === 'date') {
				return new Date(value).toLocaleDateString();
			} else if (column.format.type === 'number') {
				return Number(value).toLocaleString();
			} else if (column.format.type === 'currency') {
				return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
			}
		}

		return value;
	};

	const gridClassName = cn(
		'lib-data-grid',
		virtualized && 'lib-data-grid-virtualized',
		className
	);

	return (
		<div
			className="lib-data-grid-container"
			style={{ height, ...style }}
			data-testid={dataTestId}
		>
			<div className={gridClassName}>
				<table className="lib-data-grid-table" style={{ tableLayout: 'fixed', width: '100%' }}>
					<thead className="lib-data-grid-header">
						<tr>
							{selectable && (
								<th className="lib-data-grid-cell lib-data-grid-select">
									<input
										type="checkbox"
										checked={selectedRows.size === gridData.length && gridData.length > 0}
										onChange={handleSelectAll}
									/>
								</th>
							)}
							{columns.map(column => (
								<th
									key={column.key}
									className="lib-data-grid-cell"
									style={{ width: column.width }}
								>
									{column.label}
								</th>
							))}
							{rowActions && rowActions.length > 0 && (
								<th className="lib-data-grid-cell lib-data-grid-actions">Actions</th>
							)}
						</tr>
					</thead>
					<tbody className="lib-data-grid-body">
						{paginatedData.map((row: any, rowIndex: number) => (
							<tr
								key={rowIndex}
								className={cn(
									'lib-data-grid-row',
									selectedRows.has(rowIndex) && 'lib-data-grid-row-selected'
								)}
							>
								{selectable && (
									<td className="lib-data-grid-cell lib-data-grid-select">
										<input
											type="checkbox"
											checked={selectedRows.has(rowIndex)}
											onChange={() => handleRowSelect(rowIndex)}
										/>
									</td>
								)}
								{columns.map(column => (
									<td
										key={column.key}
										className={cn(
											'lib-data-grid-cell',
											column.editable && 'lib-data-grid-editable'
										)}
										onClick={() => handleCellClick(rowIndex, column, row[column.key])}
									>
										{renderCell(row, column, rowIndex)}
									</td>
								))}
								{rowActions && rowActions.length > 0 && (
									<td className="lib-data-grid-cell lib-data-grid-actions">
										<div className="lib-data-grid-actions-buttons">
											{rowActions.map((action, actionIndex) => (
												<button
													key={actionIndex}
													className="lib-data-grid-action-button"
													onClick={() => action.onClick(row, rowIndex)}
													title={action.label}
												>
													{action.icon || action.label}
												</button>
											))}
										</div>
									</td>
								)}
							</tr>
						))}
					</tbody>
				</table>
			</div>

			{pagination && totalPages > 1 && (
				<div className="lib-data-grid-pagination">
					<button
						className="lib-data-grid-pagination-button"
						onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
						disabled={currentPage === 1}
					>
						Previous
					</button>
					<span className="lib-data-grid-pagination-info">
						Page {currentPage} of {totalPages}
					</span>
					<button
						className="lib-data-grid-pagination-button"
						onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
						disabled={currentPage === totalPages}
					>
						Next
					</button>
				</div>
			)}
		</div>
	);
}

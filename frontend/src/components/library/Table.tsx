/**
 * Table Component
 *
 * Data table with sorting, pagination, and actions.
 */

import { useState, useMemo, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Table.css';

export type TableDensity = 'comfortable' | 'compact' | 'dense';
export type TableColumnType = 'text' | 'status' | 'code' | 'date';
export type TableColumnAlign = 'left' | 'center' | 'right';
export type TablePaginationMode = 'client' | 'server';

export interface TableStatusConfig {
	[key: string]: {
		label: string;
		variant: 'ready' | 'error' | 'warning' | 'info';
	};
}

export interface TableColumn {
	key: string;                     /** Column key (maps to data field) */
	label: string;                   /** Column header label */
	type?: TableColumnType;          /** Column type for rendering */
	align?: TableColumnAlign;        /** Text alignment */
	width?: string;                  /** Column width */
	sortable?: boolean;              /** Enable sorting */
	hidden?: boolean;                /** Hide column */
	truncate?: boolean;              /** Truncate long text */
	statusConfig?: TableStatusConfig; /** Status badge configuration */
}

export interface TableRowAction {
	id: string;                      /** Unique action ID */
	label: string;                   /** Action label */
	onClick: (row: any) => void;     /** Click handler */
	disabled?: (row: any) => boolean; /** Disabled condition */
}

export interface TableHeaderAction {
	id: string;                      /** Unique action ID */
	label: string;                   /** Action label */
	onClick: () => void;             /** Click handler */
	disabled?: boolean;              /** Disabled state */
}

export interface TablePagination {
	enabled: boolean;                /** Enable pagination */
	mode?: TablePaginationMode;      /** Pagination mode */
	pageSize: number;                /** Items per page */
	totalItems?: number;             /** Total items (server mode) */
	currentPage?: number;            /** Current page (server mode) */
	onPageChange?: (page: number, pageSize: number) => void; /** Page change handler */
	showPageNumbers?: boolean;       /** Show page buttons */
	maxPageButtons?: number;         /** Max page buttons to show */
	showFirstLast?: boolean;         /** Show first/last buttons */
	showPrevNext?: boolean;          /** Show prev/next buttons */
}

export interface TableEmptyState {
	message: string;                 /** Empty message */
	description?: string;            /** Optional description */
}

export interface TableProps extends BaseComponentProps {
	data: any[];                     /** Table data */
	columns: TableColumn[];          /** Column definitions */
	headerActions?: TableHeaderAction[]; /** Header actions */
	rowActions?: TableRowAction[];   /** Row actions */
	onRowClick?: (row: any) => void; /** Row click handler */
	sortable?: boolean;              /** Enable sorting globally */
	density?: TableDensity;          /** Table density */
	pagination?: TablePagination;    /** Pagination config */
	emptyState?: TableEmptyState;    /** Empty state config */
}

export function Table({
	data,
	columns,
	headerActions,
	rowActions,
	onRowClick,
	sortable = false,
	density = 'comfortable',
	pagination,
	emptyState,
	className,
	style,
	'data-testid': dataTestId
}: TableProps) {
	// Pagination state (for client-side pagination)
	const [currentPage, setCurrentPage] = useState(1);

	// Sorting state
	const [sortColumn, setSortColumn] = useState<string | null>(null);
	const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

	// Filter visible columns
	const visibleColumns = useMemo(() => {
		return columns.filter(col => !col.hidden);
	}, [columns]);

	// Determine pagination settings
	const paginationEnabled = pagination?.enabled ?? false;
	const pageSize = pagination?.pageSize ?? 20;
	const paginationMode = pagination?.mode ?? 'client';

	// For server-side pagination, use values from props
	const totalItems = paginationMode === 'server'
		? (pagination?.totalItems ?? data.length)
		: data.length;

	const activePage = paginationMode === 'server'
		? (pagination?.currentPage ?? 1)
		: currentPage;

	// Calculate pagination values
	const totalPages = Math.ceil(totalItems / pageSize);

	// Sort and slice data for client-side operations
	const processedData = useMemo(() => {
		let result = data;

		// Apply client-side sorting if enabled and a column is selected
		if (sortColumn && result.length > 0) {
			result = [...result].sort((a, b) => {
				const aVal = a[sortColumn];
				const bVal = b[sortColumn];

				// Handle null/undefined values
				if (aVal == null && bVal == null) return 0;
				if (aVal == null) return 1;
				if (bVal == null) return -1;

				// Compare based on type
				let comparison = 0;
				if (typeof aVal === 'number' && typeof bVal === 'number') {
					comparison = aVal - bVal;
				} else if (typeof aVal === 'string' && typeof bVal === 'string') {
					comparison = aVal.localeCompare(bVal);
				} else if (aVal instanceof Date && bVal instanceof Date) {
					comparison = aVal.getTime() - bVal.getTime();
				} else {
					// Fallback to string comparison
					comparison = String(aVal).localeCompare(String(bVal));
				}

				return sortDirection === 'asc' ? comparison : -comparison;
			});
		}

		// Apply client-side pagination if enabled
		if (paginationEnabled && paginationMode === 'client') {
			const startIndex = (currentPage - 1) * pageSize;
			const endIndex = startIndex + pageSize;
			return result.slice(startIndex, endIndex);
		}

		return result;
	}, [data, sortColumn, sortDirection, paginationEnabled, paginationMode, currentPage, pageSize]);

	const isEmpty = processedData.length === 0;

	// Render cell value based on column type
	const renderCell = (row: any, column: TableColumn): ReactNode => {
		const value = row[column.key];

		// Handle status badge rendering
		if (column.type === 'status' && column.statusConfig) {
			const config = column.statusConfig[String(value)];
			if (config) {
				const variantClass = config.variant === 'ready' ? 'lib-table-status-ready'
					: config.variant === 'error' ? 'lib-table-status-error'
					: config.variant === 'warning' ? 'lib-table-status-warning'
					: 'lib-table-status-info';
				return (
					<span className={cn('lib-table-status-badge', variantClass)}>
						{config.label}
					</span>
				);
			}
			return <span className="lib-table-status-badge">{String(value)}</span>;
		}

		// Handle code type
		if (column.type === 'code') {
			return <code className="lib-table-cell-code">{String(value)}</code>;
		}

		// Handle date type
		if (column.type === 'date') {
			try {
				// Handle different date formats: ISO string, Unix ms, or Unix seconds
				let date: Date;

				if (typeof value === 'string') {
					// ISO format string
					date = new Date(value);
				} else if (typeof value === 'number') {
					// If number is too small, it's likely Unix seconds, convert to ms
					const timestamp = value < 10000000000 ? value * 1000 : value;
					date = new Date(timestamp);
				} else {
					return <span>{String(value)}</span>;
				}

				if (isNaN(date.getTime())) {
					return <span>{String(value)}</span>;
				}

				return <span>{date.toLocaleString()}</span>;
			} catch {
				return <span>{String(value)}</span>;
			}
		}

		// Default: render as text
		return <span>{String(value)}</span>;
	};

	// Handle column sort
	const handleColumnSort = (column: TableColumn) => {
		// Check if this column is sortable
		const isSortable = column.sortable ?? sortable;
		if (!isSortable) return;

		// Toggle sort direction if same column, otherwise default to asc
		if (sortColumn === column.key) {
			setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
		} else {
			setSortColumn(column.key);
			setSortDirection('asc');
		}

		// Reset to first page when sorting changes
		setCurrentPage(1);
	};

	// Handle page change
	const handlePageChange = (newPage: number) => {
		if (newPage < 1 || newPage > totalPages) return;

		if (paginationMode === 'server' && pagination?.onPageChange) {
			// Server-side: call onPageChange handler
			pagination.onPageChange(newPage, pageSize);
		} else {
			// Client-side: update local state
			setCurrentPage(newPage);
		}
	};

	// Generate page numbers to display
	const getPageNumbers = (): (number | string)[] => {
		const maxButtons = pagination?.maxPageButtons ?? 7;
		const pages: (number | string)[] = [];

		if (totalPages <= maxButtons) {
			// Show all pages
			for (let i = 1; i <= totalPages; i++) {
				pages.push(i);
			}
		} else {
			// Show subset with ellipsis
			const sideButtons = Math.floor((maxButtons - 3) / 2);

			if (activePage <= sideButtons + 2) {
				// Near start
				for (let i = 1; i <= maxButtons - 2; i++) {
					pages.push(i);
				}
				pages.push('...');
				pages.push(totalPages);
			} else if (activePage >= totalPages - sideButtons - 1) {
				// Near end
				pages.push(1);
				pages.push('...');
				for (let i = totalPages - maxButtons + 3; i <= totalPages; i++) {
					pages.push(i);
				}
			} else {
				// Middle
				pages.push(1);
				pages.push('...');
				for (let i = activePage - sideButtons; i <= activePage + sideButtons; i++) {
					pages.push(i);
				}
				pages.push('...');
				pages.push(totalPages);
			}
		}

		return pages;
	};

	const tableClassName = cn(
		'lib-table',
		density !== 'comfortable' && `lib-table-${density}`,
		className
	);

	return (
		<div data-testid={dataTestId} style={style}>
			{/* Header actions */}
			{headerActions && headerActions.length > 0 && (
				<div className="lib-table-header-actions">
					{headerActions.map((action) => (
						<button
							key={action.id}
							className="lib-table-action-button"
							onClick={action.onClick}
							disabled={action.disabled}
						>
							{action.label}
						</button>
					))}
				</div>
			)}

			{/* Empty state */}
			{isEmpty && (
				<div className="lib-table-empty-state">
					{emptyState ? (
						<>
							<p className="lib-table-empty-state-message">{emptyState.message}</p>
							{emptyState.description && (
								<p className="lib-table-empty-state-description">{emptyState.description}</p>
							)}
						</>
					) : (
						<p className="lib-table-empty-state-message">No data available</p>
					)}
				</div>
			)}

			{/* Table */}
			{!isEmpty && (
				<div className="lib-table-container">
					<table className={tableClassName}>
						<thead>
							<tr>
								{visibleColumns.map((column) => {
									const isSortable = column.sortable ?? sortable;
									const isActiveSortColumn = sortColumn === column.key;

									return (
										<th
											key={column.key}
											style={{
												width: column.width,
												textAlign: column.align || 'left',
												cursor: isSortable ? 'pointer' : 'default',
												userSelect: 'none'
											}}
											onClick={() => handleColumnSort(column)}
										>
											<div style={{
												display: 'flex',
												alignItems: 'center',
												gap: '0.25rem',
												justifyContent: column.align === 'center' ? 'center'
													: column.align === 'right' ? 'flex-end'
													: 'flex-start'
											}}>
												<span>{column.label}</span>
												{isSortable && (
													<span className="lib-table-sort-indicator">
														<span style={{ opacity: isActiveSortColumn && sortDirection === 'asc' ? 1 : 0.3 }}>▲</span>
														<span style={{ opacity: isActiveSortColumn && sortDirection === 'desc' ? 1 : 0.3 }}>▼</span>
													</span>
												)}
											</div>
										</th>
									);
								})}
								{rowActions && rowActions.length > 0 && <th className="lib-table-actions-cell">Actions</th>}
							</tr>
						</thead>
						<tbody>
							{processedData.map((row: any, index: number) => (
								<tr
									key={index}
									onClick={() => onRowClick?.(row)}
									className={onRowClick ? 'lib-table-row-clickable' : ''}
								>
									{visibleColumns.map((column) => (
										<td
											key={column.key}
											style={{
												textAlign: column.align || 'left',
												...(column.truncate && {
													whiteSpace: 'nowrap',
													overflow: 'hidden',
													textOverflow: 'ellipsis'
												})
											}}
										>
											{renderCell(row, column)}
										</td>
									))}
									{rowActions && rowActions.length > 0 && (
										<td className="lib-table-actions-cell">
											<div className="lib-table-row-actions">
												{rowActions.map((action) => {
													const isDisabled = action.disabled ? action.disabled(row) : false;
													return (
														<button
															key={action.id}
															className="lib-table-action-button"
															onClick={(e) => {
																e.stopPropagation();
																action.onClick(row);
															}}
															disabled={isDisabled}
															title={action.label}
														>
															{action.label}
														</button>
													);
												})}
											</div>
										</td>
									)}
								</tr>
							))}
						</tbody>
					</table>
				</div>
			)}

			{/* Pagination controls */}
			{!isEmpty && paginationEnabled && totalPages > 1 && (
				<div className="lib-table-pagination">
					{/* First button */}
					{(pagination?.showFirstLast ?? true) && (
						<button
							className="lib-table-pagination-button"
							onClick={() => handlePageChange(1)}
							disabled={activePage === 1}
						>
							First
						</button>
					)}

					{/* Previous button */}
					{(pagination?.showPrevNext ?? true) && (
						<button
							className="lib-table-pagination-button"
							onClick={() => handlePageChange(activePage - 1)}
							disabled={activePage === 1}
						>
							Prev
						</button>
					)}

					{/* Page numbers */}
					{(pagination?.showPageNumbers ?? true) && getPageNumbers().map((page, index) => {
						if (page === '...') {
							return (
								<span key={`ellipsis-${index}`} className="lib-table-pagination-ellipsis">
									...
								</span>
							);
						}

						const pageNum = page as number;
						const isActive = pageNum === activePage;

						return (
							<button
								key={pageNum}
								className={cn(
									'lib-table-pagination-button',
									isActive && 'lib-table-pagination-active'
								)}
								onClick={() => handlePageChange(pageNum)}
								disabled={isActive}
							>
								{pageNum}
							</button>
						);
					})}

					{/* Next button */}
					{(pagination?.showPrevNext ?? true) && (
						<button
							className="lib-table-pagination-button"
							onClick={() => handlePageChange(activePage + 1)}
							disabled={activePage === totalPages}
						>
							Next
						</button>
					)}

					{/* Last button */}
					{(pagination?.showFirstLast ?? true) && (
						<button
							className="lib-table-pagination-button"
							onClick={() => handlePageChange(totalPages)}
							disabled={activePage === totalPages}
						>
							Last
						</button>
					)}

					{/* Page info */}
					<span className="lib-table-pagination-info">
						Page {activePage} of {totalPages}
					</span>
				</div>
			)}
		</div>
	);
}

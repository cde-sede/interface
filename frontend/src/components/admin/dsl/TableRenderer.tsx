/**
 * Table Renderer
 *
 * Renders table component from DSL with pagination support
 */

import { useState, useMemo } from 'react';
import type { TableComponent, ColumnDefinition, RowActionDefinition, TableActionDefinition } from './types';
import { resolveValue, resolveComponentData } from './valueResolver';
import { ActionEngine } from './actionEngine';

interface TableRendererProps {
	modalData?: any;
	component: TableComponent;
	pageData?: any;
	actionEngine: ActionEngine;
}

export default function TableRenderer({ component, pageData, modalData, actionEngine }: TableRendererProps) {
	const { actions, rowActions, emptyState, onRowClick, density, pagination } = component;

	// Pagination state (for client-side pagination)
	const [currentPage, setCurrentPage] = useState(1);

	// Resolve data and columns
	const allData = resolveComponentData(component.data, pageData, modalData);
	const columns: ColumnDefinition[] = resolveComponentData(component.columns, pageData, modalData) || component.columns;

	// Determine pagination mode and settings
	const paginationEnabled = pagination?.enabled ?? false;
	const pageSize = pagination?.pageSize ?? 20;
	const paginationMode = pagination?.mode ?? 'client';

	// For server-side pagination, get values from DSL
	const totalItems = paginationMode === 'server'
		? resolveComponentData(pagination?.totalItems, pageData, modalData)
		: allData?.length ?? 0;

	const serverCurrentPage = paginationMode === 'server'
		? resolveComponentData(pagination?.currentPage, pageData, modalData) ?? 1
		: currentPage;

	// Calculate pagination values
	const totalPages = Math.ceil(totalItems / pageSize);
	const activePage = paginationMode === 'server' ? serverCurrentPage : currentPage;

	// Slice data for client-side pagination
	const data = useMemo(() => {
		if (!paginationEnabled || paginationMode === 'server') {
			return allData;
		}

		const startIndex = (currentPage - 1) * pageSize;
		const endIndex = startIndex + pageSize;
		return allData?.slice(startIndex, endIndex);
	}, [allData, paginationEnabled, paginationMode, currentPage, pageSize]);

	const isEmpty = !data || data.length === 0;

	// Render cell value based on column type
	const renderCell = (row: any, column: ColumnDefinition) => {
		const value = row[column.key];

		// Handle status badge rendering
		if (column.type === 'status' && column.renderer?.type === 'status-badge') {
			const config = column.renderer.config?.[String(value)];
			if (config) {
				// Map variants to CSS classes (success -> ready for existing CSS)
				const variantClass = config.variant === 'success' ? 'status-ready' : `status-${config.variant}`;
				return (
					<span className={`status-badge ${variantClass}`}>
						{config.label}
					</span>
				);
			}
			return <span className="status-badge">{String(value)}</span>;
		}

		// Handle code type
		if (column.type === 'code') {
			return <code className="monospace">{String(value)}</code>;
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

	// Handle row click
	const handleRowClick = (row: any) => {
		if (!onRowClick) return;

		const context = { row, pageData, data: modalData };

		switch (onRowClick.action) {
			case 'open-modal':
				// Resolve modal ID and params
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
	};

	// Handle row action
	const handleRowAction = async (row: any, action: RowActionDefinition) => {
		const context = { row, pageData, data: modalData };

		// Handle confirmation
		if (action.confirmMessage) {
			const message = resolveValue(action.confirmMessage, context);
			await actionEngine.executeWithConfirmation(action.action, message, context);
		} else {
			await actionEngine.execute(action.action, context);
		}
	};

	// Handle header action
	const handleHeaderAction = async (action: TableActionDefinition) => {
		const context = { pageData, data: modalData };

		// Handle confirmation
		if (action.confirmMessage) {
			const message = resolveValue(action.confirmMessage, context);
			await actionEngine.executeWithConfirmation(action.action, message, context);
		} else {
			await actionEngine.execute(action.action, context);
		}
	};

	// Handle page change
	const handlePageChange = async (newPage: number) => {
		if (newPage < 1 || newPage > totalPages) return;

		if (paginationMode === 'server' && pagination?.onPageChange) {
			// Server-side: call onPageChange action
			const context = {
				pageData,
				data: modalData, // Include modal data for ValueRef resolution
				pagination: {
					pageNumber: newPage,
					pageSize: pageSize
				}
			};
			await actionEngine.execute(pagination.onPageChange, context);
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
			const sideButtons = Math.floor((maxButtons - 3) / 2); // Reserve 3 for first, last, and current

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

	return (
		<div>
			{/* Header actions */}
			{actions && actions.length > 0 && (
				<div className="table-header-actions" style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
					{actions.map((action) => (
						<button
							key={action.id}
							className="action-button"
							onClick={() => handleHeaderAction(action)}
						>
							{action.label}
						</button>
					))}
				</div>
			)}

			{/* Empty state */}
			{isEmpty && (
				<div>
					{emptyState ? (
						<div className="empty-state">
							<p className="empty-state-message">{emptyState.message}</p>
							{emptyState.description && (
								<p className="empty-state-description">{emptyState.description}</p>
							)}
						</div>
					) : (
							<div className="empty-state">No data available</div>
						)}
				</div>
			)}

			{/* Table */}
			{!isEmpty && (
				<div className="table-container">
					<table className={`data-table ${density ? `table-${density}` : ''}`}>
						<thead>
							<tr>
								{columns.map((column) => (
									<th
										key={column.key}
										style={{
											width: column.width,
											textAlign: column.align || 'left'
										}}
									>
										{column.label}
									</th>
								))}
								{rowActions && rowActions.length > 0 && <th>Actions</th>}
							</tr>
						</thead>
						<tbody>
							{data.map((row: any, index: number) => (
								<tr
									key={index}
									onClick={() => handleRowClick(row)}
									style={{ cursor: onRowClick ? 'pointer' : 'default' }}
								>
									{columns.map((column) => (
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
										<td>
											{rowActions.map((action) => {
												// Check condition if present
												// TODO: Implement full condition evaluation
												return (
													<button
														key={action.id}
														className="table-action-button"
														onClick={(e) => {
															e.stopPropagation();
															handleRowAction(row, action);
														}}
														title={action.label}
													>
														{action.label}
													</button>
												);
											})}
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
				<div className="pagination-controls">
					{/* First button */}
					{(pagination?.showFirstLast ?? true) && (
						<button
							className="pagination-button"
							onClick={() => handlePageChange(1)}
							disabled={activePage === 1}
						>
							First
						</button>
					)}

					{/* Previous button */}
					{(pagination?.showPrevNext ?? true) && (
						<button
							className="pagination-button"
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
								<span key={`ellipsis-${index}`} className="pagination-ellipsis">
									...
								</span>
							);
						}

						const pageNum = page as number;
						const isActive = pageNum === activePage;

						return (
							<button
								key={pageNum}
								className={`pagination-button ${isActive ? 'active' : ''}`}
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
							className="pagination-button"
							onClick={() => handlePageChange(activePage + 1)}
							disabled={activePage === totalPages}
						>
							Next
						</button>
					)}

					{/* Last button */}
					{(pagination?.showFirstLast ?? true) && (
						<button
							className="pagination-button"
							onClick={() => handlePageChange(totalPages)}
							disabled={activePage === totalPages}
						>
							Last
						</button>
					)}

					{/* Page info */}
					<span className="pagination-info">
						Page {activePage} of {totalPages}
					</span>
				</div>
			)}
		</div>
	);
}

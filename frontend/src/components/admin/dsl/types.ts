/**
 * TypeScript types for Admin Panel DSL
 *
 * These types match the backend DSL definitions and provide type safety
 * for the frontend DSL renderer.
 */

// Value Reference Types
export interface ValueRef {
	type: "literal" | "field" | "computed" | "coalesce" | "conditional";
	value?: any;
	path?: string;
	source?: "row" | "form" | "response" | "pageData" | "data" | "pagination";
	template?: string;
	values?: Record<string, ValueRef>;
	// For coalesce: list of values to try in order
	options?: ValueRef[];
	// For conditional: condition, trueValue, falseValue
	condition?: ValueRef;
	trueValue?: ValueRef;
	falseValue?: ValueRef;
}

// Action Types
export interface ActionOnSuccess {
	message?: string;
	action?: ActionDefinition;
}

export interface ActionOnError {
	message?: string;
	action?: ActionDefinition;
}

export interface ActionDefinition {
	type: "api-call" | "open-modal" | "close-modal" | "navigate" | "refresh" | "show-toast";

	// API call config
	endpoint?: string | ValueRef;
	method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
	body?: Record<string, ValueRef | any>;
	headers?: Record<string, string>;

	// Success/error handling
	onSuccess?: ActionOnSuccess;
	onError?: ActionOnError;

	// Modal control
	modalId?: string;
	modalData?: Record<string, ValueRef | any>;

	// Navigation
	page?: string;
	url?: string;

	// Toast control
	message?: string | ValueRef;
	toastType?: "success" | "error" | "info" | "warning";
}

// Component Types

export interface StatusBadgeConfig {
	label: string;
	variant: "success" | "error" | "warning" | "info";
}

export interface ColumnRenderer {
	type: "status-badge" | "date" | "code" | "custom";
	config?: Record<string, StatusBadgeConfig>;
}

export interface ColumnFormat {
	type: "date" | "number" | "currency";
	options?: any;
}

export interface ColumnDefinition {
	key: string;
	label: string;
	type?: "text" | "number" | "date" | "boolean" | "status" | "code";
	sortable?: boolean;
	filterable?: boolean;
	width?: string;
	renderer?: ColumnRenderer;
	format?: ColumnFormat;
	truncate?: boolean;  // Apply text-overflow ellipsis
	align?: "left" | "center" | "right";  // Text alignment
	hidden?: boolean;  // If true, column is not displayed but data is available for actions/refs
}

export interface RowActionDefinition {
	id: string;
	label: string;
	icon?: string;
	confirmMessage?: string | ValueRef;
	action: ActionDefinition;
	condition?: any;
}

export interface TableActionDefinition {
	id: string;
	label: string;
	icon?: string;
	action: ActionDefinition;
	position?: "left" | "right";
	confirmMessage?: string | ValueRef;
}

export interface TablePagination {
	enabled: boolean;
	pageSize: number;

	// Pagination mode
	mode?: "client" | "server"; // Default: "client"

	// Server-side pagination fields
	totalItems?: number | ValueRef; // Total number of items across all pages
	currentPage?: number | ValueRef; // Current page number (1-indexed)
	onPageChange?: ActionDefinition; // Action called when page changes

	// UI configuration
	showPageNumbers?: boolean; // Show page number buttons (default: true)
	maxPageButtons?: number; // Max page buttons to show (default: 7)
	showFirstLast?: boolean; // Show first/last page buttons (default: true)
	showPrevNext?: boolean; // Show previous/next buttons (default: true)
}

export interface EmptyStateComponent {
	type: "empty-state";
	message: string;
	description?: string;
	icon?: string;
	action?: ButtonComponent;
}

export interface TableOnRowClick {
	action: "open-modal" | "navigate" | "api-call";
	target: string;
	params?: Record<string, string | ValueRef>;
}

export interface TableComponent {
	type: "table";
	data: any[] | ValueRef;
	columns: ColumnDefinition[];
	actions?: TableActionDefinition[];
	rowActions?: RowActionDefinition[];
	sortable?: boolean;
	filterable?: boolean;
	pagination?: TablePagination;
	emptyState?: EmptyStateComponent;
	onRowClick?: TableOnRowClick;
	density?: "comfortable" | "compact" | "dense";
}

export interface StatCardTrend {
	direction: "up" | "down";
	value: string;
}

export interface StatCard {
	label: string;
	value: string | number;
	total?: number;
	icon?: string;
	color?: string;
	trend?: StatCardTrend;
}

export interface StatsCardsComponent {
	type: "stats-cards";
	stats: StatCard[];
	columns?: number;
}

export interface InfoGridItem {
	label: string;
	value: string | number | ValueRef;
	type?: "text" | "code" | "status" | "date";
	icon?: string;
	copyable?: boolean;
}

export interface InfoGridComponent {
	type: "info-grid";
	items: InfoGridItem[];
	columns?: number;
}

export interface CodeBlockComponent {
	type: "code-block";
	content: string | object | ValueRef;
	language?: "json" | "javascript" | "python" | "yaml" | "text";
	copyable?: boolean;
	collapsible?: boolean;
}

export interface ChartSeries {
	dataKey: string;
	name: string;
	color?: string;
}

export interface ChartAxis {
	dataKey?: string;
	label?: string;
}

export interface ChartConfig {
	xAxis?: ChartAxis;
	yAxis?: ChartAxis;
	series: ChartSeries[];
	legend?: boolean;
	height?: number;
}

export interface ChartComponent {
	type: "chart";
	chartType: "bar" | "line" | "pie" | "area" | "scatter";
	data: any[] | ValueRef;
	config: ChartConfig;
}

export interface ValidationRule {
	type: "required" | "email" | "min" | "max" | "pattern" | "custom";
	value?: any;
	message?: string;
	validator?: string;
}

export interface FormFieldOption {
	value: any;
	label: string;
	description?: string;
}

export interface FormFieldDefinition {
	name: string;
	label: string;
	type: "text" | "number" | "email" | "password" | "textarea" | "select" |
	"checkbox" | "radio" | "date" | "datetime" | "file";
	required?: boolean;
	defaultValue?: any | ValueRef;
	placeholder?: string | ValueRef;
	helpText?: string | ValueRef;
	validation?: ValidationRule[];
	options?: FormFieldOption[] | ValueRef;
	condition?: any;
	readonly?: boolean;
	// Number input specific
	min?: number;
	max?: number;
	step?: number;
}

export interface FormComponent {
	type: "form";
	fields: FormFieldDefinition[];
	submitAction: ActionDefinition;
	cancelAction?: ActionDefinition;
	layout?: "vertical" | "horizontal" | "grid";
	readonly?: boolean;
}

export interface ButtonComponent {
	type: "button";
	label: string;
	action: ActionDefinition;
	variant?: "primary" | "secondary" | "danger" | "success";
	icon?: string;
	size?: "small" | "medium" | "large";
	disabled?: boolean;
	confirmMessage?: string | ValueRef;
}

export interface AlertComponent {
	type: "alert";
	message: string;
	variant: "info" | "success" | "warning" | "error";
	dismissible?: boolean;
}

export interface DividerComponent {
	type: "divider";
	label?: string;
	orientation?: "horizontal" | "vertical";
	variant?: "solid" | "dashed" | "dotted";
}

export interface BadgeComponent {
	type: "badge";
	label: string | ValueRef;
	variant?: "default" | "success" | "error" | "warning" | "info" | "primary";
	size?: "small" | "medium" | "large";
	icon?: string;
}

export interface ProgressBarComponent {
	type: "progress-bar";
	value: number | ValueRef;
	max?: number;
	label?: string | ValueRef;
	variant?: "default" | "success" | "error" | "warning" | "info";
	showPercentage?: boolean;
	striped?: boolean;
	animated?: boolean;
}

export interface CardComponent {
	type: "card";
	title?: string | ValueRef;
	subtitle?: string | ValueRef;
	content: ComponentDefinition[];
	actions?: ButtonComponent[];
	variant?: "default" | "outlined" | "elevated";
	padding?: "none" | "small" | "medium" | "large";
}

export interface AccordionItem {
	id: string;
	title: string | ValueRef;
	content: ComponentDefinition[];
	defaultExpanded?: boolean;
}

export interface AccordionComponent {
	type: "accordion";
	items: AccordionItem[];
	allowMultiple?: boolean;
	variant?: "default" | "bordered" | "separated";
}

// Component Union Type
export type ComponentDefinition =
| StatsCardsComponent
| TableComponent
| InfoGridComponent
| CodeBlockComponent
| ChartComponent
| FormComponent
| ButtonComponent
| AlertComponent
| EmptyStateComponent
| DividerComponent
| BadgeComponent
| ProgressBarComponent
| CardComponent
| AccordionComponent;

// Layout Types

export interface SectionComponent {
	id?: string;
	title?: string;
	components: ComponentDefinition[];
	collapsible?: boolean;
	defaultCollapsed?: boolean;
	className?: string;
}

export interface TabDefinition {
	id: string;
	label: string;
	icon?: string;
	content: LayoutComponent;
}

export interface LayoutComponent {
	type: "vertical" | "horizontal" | "grid" | "tabs";
	sections?: SectionComponent[];
	tabs?: TabDefinition[];
	gap?: string;
	className?: string;
}

// Modal Types

export interface ModalDefinition {
	title: string;
	size?: "small" | "medium" | "large" | "fullscreen";
	content: ComponentDefinition[];
	actions?: ButtonComponent[];
	closeOnOverlayClick?: boolean;
}

// Real-time Updates

export interface SocketEventHandler {
	event: string;
	handler: "refresh-page" | "update-component" | "show-toast";
	componentId?: string;
	message?: string;
}

export interface PollingConfig {
	interval: number;
	endpoint: string;
	componentId?: string;
}

export interface RealtimeConfig {
	enabled: boolean;
	socketEvents?: SocketEventHandler[];
	polling?: PollingConfig;
}

// Page Types

export interface PageMetadata {
	refreshInterval?: number;
	requiresAuth?: boolean;
	permissions?: string[];
}

export interface PageDSL {
	type: "page";
	title: string;
	description?: string;
	layout: LayoutComponent;
	actions?: ActionDefinition[];
	modals?: Record<string, ModalDefinition>;
	realtime?: RealtimeConfig;
	metadata?: PageMetadata;

	// Page can include data fields directly
	[key: string]: any;
}

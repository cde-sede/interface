/**
 * TypeScript types for Admin Panel DSL
 *
 * These types match the backend DSL definitions and provide type safety
 * for the frontend DSL renderer.
 */

// Value Reference Types
export interface ValueRef {
	type: "literal" | "field" | "computed" | "coalesce" | "conditional" | "transform" | "urlencode";
	value?: any;
	path?: string;
	source?: "row" | "form" | "response" | "pageData" | "data" | "pagination" | "store";
	template?: string;
	values?: Record<string, ValueRef>;
	// For coalesce: list of values to try in order
	options?: ValueRef[];
	// For conditional: condition, trueValue, falseValue
	condition?: ValueRef;
	trueValue?: ValueRef;
	falseValue?: ValueRef;
	// For transform: map/filter operations
	input?: ValueRef | any;
	transform?: string;
	// For urlencode: value to URL encode
	encode?: ValueRef | any;
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
	type: "api-call" | "open-modal" | "close-modal" | "navigate" | "refresh" | "show-toast" | "open-panel" | "close-panel" | "toggle-panel" | "store-data" | "map" | "copy-to-clipboard" | "trigger-dynamic" | "add-rows";

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

	// Panel control
	panelId?: string;
	panelData?: Record<string, ValueRef | any>;

	// Navigation
	page?: string;
	url?: string;

	// Toast control
	message?: string | ValueRef | RichTextComponent;
	toastType?: "success" | "error" | "info" | "warning";

	// Data store
	key?: string | ValueRef;
	value?: any | ValueRef;

	// Map transformation
	input?: any | ValueRef;
	transform?: string;
	output?: string | ValueRef;

	// Clipboard
	copyValue?: string | ValueRef;

	// Dynamic component trigger
	triggerId?: string;  // ID of dynamic component to trigger

	// Add rows to table/data component
	targetId?: string;  // ID of the component to add rows to
	rows?: any[] | ValueRef;  // Rows/data to add
}

// Base Component Properties
// All components extend BaseComponentProps for universal interactions, styling, and accessibility

/**
 * Event handlers for components
 */
export interface ComponentEvents {
	click?: ActionDefinition;
	hover?: ActionDefinition;  // Triggers on mouseenter, clears on mouseleave
}

/**
 * Custom CSS styling for components
 * Supports common CSS properties in camelCase
 */
export interface ComponentCustomStyle {
	// Layout
	display?: string;
	position?: string;
	top?: string | number;
	right?: string | number;
	bottom?: string | number;
	left?: string | number;
	width?: string | number;
	height?: string | number;
	margin?: string | number;
	padding?: string | number;

	// Typography
	fontSize?: string | number;
	fontWeight?: string | number;
	color?: string;
	textAlign?: string;
	lineHeight?: string | number;

	// Background & Border
	background?: string;
	backgroundColor?: string;
	border?: string;
	borderRadius?: string | number;
	boxShadow?: string;

	// Flexbox
	flex?: string | number;
	flexDirection?: string;
	justifyContent?: string;
	alignItems?: string;
	gap?: string | number;

	// Other common properties
	opacity?: number;
	cursor?: string;
	overflow?: string;
	zIndex?: number;
	transform?: string;
	transition?: string;

	// Allow any other CSS property
	[key: string]: string | number | undefined;
}

/**
 * Base properties inherited by all components
 * Provides universal support for interactions, styling, visibility, and accessibility
 */
export interface BaseComponentProps {
	// Unique identifier for the component
	id?: string;

	// Event handlers
	events?: ComponentEvents;

	// Confirmation message for click events
	confirmMessage?: string | ValueRef;

	// Custom styling
	customStyle?: ComponentCustomStyle;
	className?: string | ValueRef;  // Additional CSS classes

	// Visibility control
	visible?: boolean | ValueRef;

	// Accessibility
	ariaLabel?: string | ValueRef;
	ariaDescribedBy?: string | ValueRef;
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

export interface EmptyStateComponent extends BaseComponentProps {
	type: "empty-state";
	message: string;
	description?: string;
	icon?: string;
	action?: ButtonComponent;
}

export interface RichTextComponent extends BaseComponentProps {
	type: "rich-text";
	content: string | ValueRef;
	variant?: "body" | "small" | "large";
	align?: "left" | "center" | "right" | "justify";
}

export interface TableOnRowClick {
	action: "open-modal" | "navigate" | "api-call";
	target: string;
	params?: Record<string, string | ValueRef>;
}

export interface TableComponent extends BaseComponentProps {
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

export interface StatsCardsComponent extends BaseComponentProps {
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

export interface InfoGridComponent extends BaseComponentProps {
	type: "info-grid";
	items: InfoGridItem[];
	columns?: number;
}

export interface CodeBlockComponent extends BaseComponentProps {
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

export interface ChartComponent extends BaseComponentProps {
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

export interface FormComponent extends BaseComponentProps {
	type: "form";
	fields: FormFieldDefinition[];
	submitAction: ActionDefinition;
	cancelAction?: ActionDefinition;
	layout?: "vertical" | "horizontal" | "grid";
	readonly?: boolean;
}

export interface ButtonComponent extends BaseComponentProps {
	type: "button";
	label: string;
	action: ActionDefinition;
	variant?: "primary" | "secondary" | "danger" | "success";
	icon?: string;
	size?: "small" | "medium" | "large";
	disabled?: boolean;
	confirmMessage?: string | ValueRef;
}

export interface AlertComponent extends BaseComponentProps {
	type: "alert";
	message: string;
	variant: "info" | "success" | "warning" | "error";
	dismissible?: boolean;
}

export interface DividerComponent extends BaseComponentProps {
	type: "divider";
	label?: string;
	orientation?: "horizontal" | "vertical";
	variant?: "solid" | "dashed" | "dotted";
}

export interface BadgeComponent extends BaseComponentProps {
	type: "badge";
	label: string | ValueRef;
	variant?: "default" | "success" | "error" | "warning" | "info" | "primary";
	size?: "small" | "medium" | "large";
	icon?: string;
}

export interface ProgressBarComponent extends BaseComponentProps {
	type: "progress-bar";
	value: number | ValueRef;
	max?: number;
	label?: string | ValueRef;
	variant?: "default" | "success" | "error" | "warning" | "info";
	showPercentage?: boolean;
	striped?: boolean;
	animated?: boolean;
}

export interface CardComponent extends BaseComponentProps {
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

export interface AccordionComponent extends BaseComponentProps {
	type: "accordion";
	items: AccordionItem[];
	allowMultiple?: boolean;
	variant?: "default" | "bordered" | "separated";
}

export interface ImageComponent extends BaseComponentProps {
	type: "image";
	src: string | ValueRef;
	alt?: string | ValueRef;
	width?: string | ValueRef;
	height?: string | ValueRef;
	fit?: "cover" | "contain" | "fill" | "none" | "scale-down";
	rounded?: boolean;
	bordered?: boolean;
}

export interface TimelineItem {
	title: string | ValueRef;
	description?: string | ValueRef;
	timestamp?: string | ValueRef;
	icon?: string | ValueRef;
	variant?: "default" | "success" | "error" | "warning" | "info";
}

export interface TimelineComponent extends BaseComponentProps {
	type: "timeline";
	items: TimelineItem[] | ValueRef;
	position?: "left" | "right" | "alternate";
}

export interface ListItem {
	label: string | ValueRef;
	description?: string | ValueRef;
	icon?: string | ValueRef;
	action?: ActionDefinition;
	trailing?: string | ValueRef;
}

export interface ListComponent extends BaseComponentProps {
	type: "list";
	items: ListItem[] | ValueRef;
	variant?: "default" | "bordered" | "divided";
	hoverable?: boolean;
}

export interface StepperStep {
	label: string | ValueRef;
	description?: string | ValueRef;
	status?: "pending" | "active" | "completed" | "error";
}

export interface StepperComponent extends BaseComponentProps {
	type: "stepper";
	steps: StepperStep[] | ValueRef;
	currentStep?: number | ValueRef;
	orientation?: "horizontal" | "vertical";
}

export interface MetricComponent extends BaseComponentProps {
	type: "metric";
	value: string | number | ValueRef;
	label: string | ValueRef;
	unit?: string | ValueRef;
	previousValue?: number | ValueRef;
	format?: "number" | "currency" | "percentage" | "duration";
	trend?: "up" | "down" | "neutral";
	icon?: string | ValueRef;
	variant?: "default" | "success" | "error" | "warning" | "info";
}

export interface AvatarComponent extends BaseComponentProps {
	type: "avatar";
	src?: string | ValueRef;
	name: string | ValueRef;
	size?: "xs" | "sm" | "md" | "lg" | "xl";
	variant?: "circle" | "square" | "rounded";
	status?: "online" | "offline" | "away" | "busy";
}

export interface CalloutComponent extends BaseComponentProps {
	type: "callout";
	message: string | ValueRef;
	title?: string | ValueRef;
	variant?: "info" | "success" | "warning" | "error" | "neutral";
	icon?: string | ValueRef;
	dismissible?: boolean;
}

export interface SpacerComponent extends BaseComponentProps {
	type: "spacer";
	size?: "xs" | "sm" | "md" | "lg" | "xl";
	orientation?: "horizontal" | "vertical";
}

export interface BreadcrumbItem {
	label: string | ValueRef;
	href?: string | ValueRef;
	action?: ActionDefinition;
}

export interface BreadcrumbsComponent extends BaseComponentProps {
	type: "breadcrumbs";
	items: BreadcrumbItem[] | ValueRef;
	separator?: string | ValueRef;
}

export interface TooltipComponent extends BaseComponentProps {
	type: "tooltip";
	content: string | ValueRef;
	trigger: ComponentDefinition;
	placement?: "top" | "bottom" | "left" | "right";
	variant?: "dark" | "light";
}

export interface ToggleComponent extends BaseComponentProps {
	type: "toggle";
	name: string;
	label?: string | ValueRef;
	defaultChecked?: boolean | ValueRef;
	disabled?: boolean | ValueRef;
	onChange?: ActionDefinition;
	size?: "sm" | "md" | "lg";
	variant?: "default" | "success" | "error";
}

export interface ChipInputComponent extends BaseComponentProps {
	type: "chip-input";
	name: string;
	label?: string | ValueRef;
	value?: string[] | ValueRef;
	placeholder?: string | ValueRef;
	defaultValue?: string[] | ValueRef;
	maxTags?: number;
	allowDuplicates?: boolean;
	onChange?: ActionDefinition;
	variant?: "default" | "outlined" | "filled";
}

export interface SkeletonComponent extends BaseComponentProps {
	type: "skeleton";
	variant?: "text" | "circular" | "rectangular" | "rounded";
	width?: string | ValueRef;
	height?: string | ValueRef;
	count?: number;
	animation?: "pulse" | "wave" | "none";
}

export interface DropdownOption {
	value: any;
	label: string | ValueRef;
	description?: string | ValueRef;
	icon?: string | ValueRef;
	disabled?: boolean;
}

export interface DropdownComponent extends BaseComponentProps {
	type: "dropdown";
	name: string;
	label?: string | ValueRef;
	placeholder?: string | ValueRef;
	options: DropdownOption[] | ValueRef;
	defaultValue?: any | ValueRef;
	searchable?: boolean;
	clearable?: boolean;
	multiple?: boolean;
	onChange?: ActionDefinition;
	disabled?: boolean | ValueRef;
}

export interface TextInputComponent extends BaseComponentProps {
	type: "text-input";
	name: string;
	label?: string | ValueRef;
	placeholder?: string | ValueRef;
	defaultValue?: string | ValueRef;
	inputType?: "text" | "email" | "password" | "url" | "tel" | "search";
	required?: boolean | ValueRef;
	disabled?: boolean | ValueRef;
	readOnly?: boolean | ValueRef;
	maxLength?: number;
	minLength?: number;
	pattern?: string;
	onChange?: ActionDefinition;
	onBlur?: ActionDefinition;
	helperText?: string | ValueRef;
	errorText?: string | ValueRef;
}

export interface NumberInputComponent extends BaseComponentProps {
	type: "number-input";
	name: string;
	label?: string | ValueRef;
	placeholder?: string | ValueRef;
	defaultValue?: number | ValueRef;
	min?: number;
	max?: number;
	step?: number;
	required?: boolean | ValueRef;
	disabled?: boolean | ValueRef;
	readOnly?: boolean | ValueRef;
	onChange?: ActionDefinition;
	onBlur?: ActionDefinition;
	helperText?: string | ValueRef;
	errorText?: string | ValueRef;
}

export interface TextAreaComponent extends BaseComponentProps {
	type: "textarea";
	name: string;
	label?: string | ValueRef;
	placeholder?: string | ValueRef;
	defaultValue?: string | ValueRef;
	rows?: number;
	cols?: number;
	maxLength?: number;
	minLength?: number;
	required?: boolean | ValueRef;
	disabled?: boolean | ValueRef;
	readOnly?: boolean | ValueRef;
	resize?: "none" | "both" | "horizontal" | "vertical";
	onChange?: ActionDefinition;
	onBlur?: ActionDefinition;
	helperText?: string | ValueRef;
	errorText?: string | ValueRef;
}

export interface CheckboxComponent extends BaseComponentProps {
	type: "checkbox";
	name: string;
	label?: string | ValueRef;
	defaultChecked?: boolean | ValueRef;
	required?: boolean | ValueRef;
	disabled?: boolean | ValueRef;
	onChange?: ActionDefinition;
	helperText?: string | ValueRef;
	errorText?: string | ValueRef;
}

export interface RadioOption {
	value: any;
	label: string | ValueRef;
	disabled?: boolean;
}

export interface RadioComponent extends BaseComponentProps {
	type: "radio";
	name: string;
	label?: string | ValueRef;
	options: RadioOption[] | ValueRef;
	defaultValue?: any | ValueRef;
	required?: boolean | ValueRef;
	disabled?: boolean | ValueRef;
	orientation?: "horizontal" | "vertical";
	onChange?: ActionDefinition;
	helperText?: string | ValueRef;
	errorText?: string | ValueRef;
}

export interface TreeNode {
	id: string;
	label: string | ValueRef;
	icon?: string | ValueRef;
	children?: TreeNode[] | ValueRef;
	expanded?: boolean;
	action?: ActionDefinition;
	data?: any;
}

export interface TreeViewComponent extends BaseComponentProps {
	type: "tree-view";
	nodes: TreeNode[] | ValueRef;
	defaultExpanded?: boolean;
	showLines?: boolean;
	selectable?: boolean;
	onSelect?: ActionDefinition;
}

export interface FileUploadComponent extends BaseComponentProps {
	type: "file-upload";
	name: string;
	label?: string | ValueRef;
	accept?: string;
	multiple?: boolean;
	maxSize?: number;
	maxFiles?: number;
	onUpload?: ActionDefinition;
	onRemove?: ActionDefinition;
	variant?: "button" | "dropzone" | "avatar";
	showPreview?: boolean;
}

export interface DatePickerComponent extends BaseComponentProps {
	type: "date-picker";
	name: string;
	label?: string | ValueRef;
	defaultValue?: string | ValueRef;
	format?: string;
	placeholder?: string | ValueRef;
	disabled?: boolean | ValueRef;
	readonly?: boolean | ValueRef;
	clearable?: boolean;
	minDate?: string | ValueRef;
	maxDate?: string | ValueRef;
	onChange?: ActionDefinition;
}

export interface DataGridColumn {
	key: string;
	label: string;
	width?: string;
	sortable?: boolean;
	filterable?: boolean;
	editable?: boolean;
	type?: "text" | "number" | "date" | "boolean" | "select";
	options?: any[];
	renderer?: ColumnRenderer;
	format?: ColumnFormat;
}

export interface DataGridComponent extends BaseComponentProps {
	type: "data-grid";
	data: any[] | ValueRef;
	columns: DataGridColumn[];
	editable?: boolean;
	selectable?: boolean;
	rowActions?: RowActionDefinition[];
	onCellEdit?: ActionDefinition;
	onSelectionChange?: ActionDefinition;
	pagination?: TablePagination;
	height?: string | ValueRef;
	virtualized?: boolean;
}

export interface CalendarEvent {
	id: string;
	title: string | ValueRef;
	start: string | ValueRef;
	end?: string | ValueRef;
	allDay?: boolean;
	color?: string | ValueRef;
	description?: string | ValueRef;
	data?: any;
}

export interface CalendarComponent extends BaseComponentProps {
	type: "calendar";
	calendarEvents: CalendarEvent[] | ValueRef;  // Renamed from 'events' to avoid collision with BaseComponentProps
	view?: "month" | "week" | "day" | "agenda";
	defaultDate?: string | ValueRef;
	onEventClick?: ActionDefinition;
	onDateClick?: ActionDefinition;
	editable?: boolean;
	height?: string | ValueRef;
}

export interface GridComponent extends BaseComponentProps {
	type: "grid";
	items: ComponentDefinition[] | ValueRef;
	columns?: number | string;
	gap?: string | ValueRef;
	autoRows?: string | ValueRef;
}

export interface FlexComponent extends BaseComponentProps {
	type: "flex";
	items: ComponentDefinition[] | ValueRef;
	direction?: "row" | "column" | "row-reverse" | "column-reverse";
	justify?: "flex-start" | "flex-end" | "center" | "space-between" | "space-around" | "space-evenly";
	align?: "flex-start" | "flex-end" | "center" | "baseline" | "stretch";
	wrap?: "nowrap" | "wrap" | "wrap-reverse";
	gap?: string | ValueRef;
}

export interface ContainerComponent extends BaseComponentProps {
	type: "container";
	children: ComponentDefinition[] | ValueRef;
	maxWidth?: string | ValueRef;
	padding?: string | ValueRef;
	centered?: boolean;
}

export interface TabsItem {
	id: string;
	label: string | ValueRef;
	icon?: string | ValueRef;
	content: ComponentDefinition[];
	disabled?: boolean;
}

export interface TabsComponent extends BaseComponentProps {
	type: "tabs";
	items: TabsItem[];
	defaultTab?: string;
	variant?: "default" | "pills" | "underlined";
	orientation?: "horizontal" | "vertical";
}

/**
 * Defer Component - Lazy loading DSL content
 *
 * Allows components to be loaded on-demand from an endpoint,
 * triggered by various events (immediate, viewport visibility, action, scroll, conditional)
 */
export interface DeferTrigger {
	type: "action" | "intersection" | "scroll" | "conditional" | "immediate";

	// For action trigger: ID of action that triggers the load
	actionId?: string;

	// For intersection trigger: viewport intersection options
	rootMargin?: string;  // e.g., "200px" to load before entering viewport
	threshold?: number;   // 0.0 to 1.0, fraction of element that must be visible

	// For scroll trigger: scroll position threshold
	scrollThreshold?: number;  // Pixels from top or percentage

	// For conditional trigger: condition to evaluate
	condition?: ValueRef;
}

export interface DeferComponent extends BaseComponentProps {
	type: "defer";

	// Endpoint to fetch deferred content from
	endpoint: string | ValueRef;
	method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
	params?: Record<string, ValueRef | any>;  // Query parameters (?key=value&key2=value2)
	body?: Record<string, ValueRef | any>;
	headers?: Record<string, string>;

	// Trigger configuration (defaults to immediate)
	trigger?: DeferTrigger;

	// Loading state while fetching
	loadingState?: ComponentDefinition;

	// Error state on fetch failure
	errorState?: ComponentDefinition;

	// Fallback content if deferred content fails to load
	fallback?: ComponentDefinition[];

	// Caching configuration
	cache?: {
		enabled: boolean;
		key?: string | ValueRef;  // Custom cache key (defaults to endpoint)
		ttl?: number;  // Time to live in milliseconds
	};

	// Action hooks for defer lifecycle
	onTrigger?: ActionDefinition;  // Executed when defer is triggered (before fetching)
	onLoad?: ActionDefinition;     // Executed when content successfully loads
	onError?: ActionDefinition;    // Executed when loading fails
}

/**
 * Dynamic Component - Action-triggered reloadable content
 *
 * Similar to Defer but designed for repeated triggering:
 * - Triggered by action IDs
 * - Can be triggered multiple times
 * - Each trigger replaces the content (not appends)
 * - No caching - always fetches fresh content
 */
export interface DynamicComponent extends BaseComponentProps {
	type: "dynamic";

	// Action ID that triggers content loading
	triggerId: string;

	// Endpoint to fetch content from
	endpoint: string | ValueRef;
	method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
	params?: Record<string, ValueRef | any>;  // Query parameters (?key=value&key2=value2)
	body?: Record<string, ValueRef | any>;
	headers?: Record<string, string>;

	// Initial content before first trigger (optional)
	initialContent?: ComponentDefinition[];

	// Loading state while fetching
	loadingState?: ComponentDefinition;

	// Error state on fetch failure
	errorState?: ComponentDefinition;

	// Action hooks for lifecycle
	onTrigger?: ActionDefinition;  // Executed when triggered (before fetching)
	onLoad?: ActionDefinition;     // Executed when content successfully loads
	onError?: ActionDefinition;    // Executed when loading fails
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
| RichTextComponent
| DividerComponent
| BadgeComponent
| ProgressBarComponent
| CardComponent
| AccordionComponent
| ImageComponent
| TimelineComponent
| ListComponent
| StepperComponent
| MetricComponent
| AvatarComponent
| CalloutComponent
| SpacerComponent
| BreadcrumbsComponent
| TooltipComponent
| ToggleComponent
| ChipInputComponent
| SkeletonComponent
| DropdownComponent
| TreeViewComponent
| FileUploadComponent
| DatePickerComponent
| DataGridComponent
| CalendarComponent
| GridComponent
| FlexComponent
| ContainerComponent
| TabsComponent
| DeferComponent
| DynamicComponent
| TextInputComponent
| NumberInputComponent
| TextAreaComponent
| CheckboxComponent
| RadioComponent;

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

export interface PanelDefinition {
	title: string | ValueRef;
	content: ComponentDefinition[];
	width?: string | ValueRef;
	defaultOpen?: boolean;
	position?: "bottom-right" | "bottom-left" | "top-right" | "top-left";
}

// Real-time Updates

export interface SocketEventHandler {
	event: string;
	handler?: "refresh-page" | "update-component" | "show-toast";
	action?: ActionDefinition;
	componentId?: string;
	message?: string;
}

export interface PollingConfig {
	interval: number;
	endpoint: string;
	method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
	body?: Record<string, any>;
	action?: ActionDefinition;
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
	panels?: Record<string, PanelDefinition>;
	realtime?: RealtimeConfig;
	metadata?: PageMetadata;

	// Page can include data fields directly
	[key: string]: any;
}

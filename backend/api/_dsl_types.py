"""
DSL Type Definitions for Admin Panel

This module defines TypedDict structures for the admin panel DSL.
These types match the frontend TypeScript definitions and ensure type safety
when building DSL structures on the backend.
"""

from typing import TypedDict, Literal, Any, Optional, Union, List, Dict

# ============================================================================
# Value Reference Types
# ============================================================================

class ValueRef(TypedDict, total=False):
    """Reference to a dynamic value that will be resolved at runtime

    Types:
    - literal: Static value
    - field: Reference to data in context (row, form, response, etc.)
    - computed: Template string with interpolation
    - coalesce: First non-null value from options list
    - conditional: Ternary operator (if/then/else)
    - transform: Map/filter transformation on data
    """
    type: Literal["literal", "field", "computed", "coalesce", "conditional", "pagination", "transform"]

    # For literal values
    value: Any

    # For field references
    path: str  # Dot notation path like "row.user.name"
    source: Literal["row", "form", "response", "pageData", "data", "store"]

    # For computed values
    template: str  # Template with {placeholders}
    values: Dict[str, 'ValueRef']  # Values to interpolate

    # For coalesce
    options: List['ValueRef']  # Try these in order

    # For conditional
    condition: 'ValueRef'
    trueValue: 'ValueRef'
    falseValue: 'ValueRef'

    # For transform
    input: Union['ValueRef', Any]  # Input data to transform
    transform: str  # Transformation string (regex, object, tuple, or filter)


# ============================================================================
# Action Types
# ============================================================================

class ActionOnSuccess(TypedDict, total=False):
    """Success handler for actions"""
    message: Union[str, ValueRef]
    action: 'ActionDefinition'


class ActionOnError(TypedDict, total=False):
    """Error handler for actions"""
    message: Union[str, ValueRef]
    action: 'ActionDefinition'


class ActionDefinition(TypedDict, total=False):
    """Defines an action (API call, modal, navigation, etc.)"""
    type: Literal["api-call", "open-modal", "close-modal", "navigate", "refresh", "show-toast", "open-panel", "close-panel", "toggle-panel", "store-data", "map"]

    # API call config
    endpoint: Union[str, ValueRef]
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    body: Dict[str, Any]  # Can contain ValueRefs
    headers: Dict[str, Union[str, ValueRef]]

    # Success/error handling
    onSuccess: ActionOnSuccess
    onError: ActionOnError

    # Modal control
    modalId: Union[str, ValueRef]
    modalData: Dict[str, Any]  # Can contain ValueRefs

    # Panel control
    panelId: Union[str, ValueRef]
    panelData: Dict[str, Any]  # Can contain ValueRefs

    # Navigation
    page: Union[str, ValueRef]
    url: Union[str, ValueRef]

    # Toast control
    message: Union[str, ValueRef]
    toastType: Literal["success", "error", "info", "warning"]

    # Store data control
    key: Union[str, ValueRef]  # Key to store data under (for store-data action)
    value: Any  # Value to store (can be ValueRef, dict, string, etc.)

    # Map transformation control
    input: Any  # Input data to transform (can be ValueRef)
    transform: str  # Transformation string (regex, object, or tuple)
    output: Union[str, ValueRef]  # Optional key to store result in datastore


# ============================================================================
# Table Component Types
# ============================================================================

class StatusBadgeConfig(TypedDict):
    """Configuration for status badge rendering"""
    label: Union[str, ValueRef]
    variant: Literal["success", "error", "warning", "info"]


class ColumnRenderer(TypedDict, total=False):
    """Column renderer configuration"""
    type: Literal["status-badge", "date", "code", "custom"]
    config: Dict[str, StatusBadgeConfig]  # For status-badge: maps values to configs


class ColumnFormat(TypedDict, total=False):
    """Column format configuration"""
    type: Literal["date", "number", "currency"]
    options: Any


class ColumnDefinition(TypedDict, total=False):
    """Table column definition"""
    key: str  # Required
    label: Union[str, ValueRef]  # Required
    type: Literal["text", "number", "date", "boolean", "status", "code"]
    sortable: bool
    filterable: bool
    width: Union[str, ValueRef]
    renderer: ColumnRenderer
    format: ColumnFormat
    truncate: bool
    align: Literal["left", "center", "right"]
    hidden: bool  # If true, column is not displayed but data is available for actions/refs


class RowActionDefinition(TypedDict, total=False):
    """Row-level action definition"""
    id: str  # Required - identifier, not dynamic
    label: Union[str, ValueRef]  # Required
    action: ActionDefinition  # Required
    icon: Union[str, ValueRef]
    confirmMessage: Union[str, ValueRef]
    condition: Any  # Condition expression


class TableActionDefinition(TypedDict, total=False):
    """Table header action definition"""
    id: str  # Required - identifier, not dynamic
    label: Union[str, ValueRef]  # Required
    action: ActionDefinition  # Required
    icon: Union[str, ValueRef]
    position: Literal["left", "right"]
    confirmMessage: Union[str, ValueRef]


class TablePagination(TypedDict, total=False):
    """Table pagination configuration

    Supports two modes:
    - Client-side: All data loaded upfront, pagination in browser
    - Server-side: Data loaded page-by-page via API calls
    """
    enabled: bool  # Required
    pageSize: int  # Required

    # Pagination mode
    mode: Literal["client", "server"]  # Default: "client"

    # Server-side pagination fields
    totalItems: Union[int, ValueRef]  # Total number of items across all pages
    currentPage: Union[int, ValueRef]  # Current page number (1-indexed)
    onPageChange: ActionDefinition  # Action called when page changes (receives pageNumber, pageSize in context)

    # UI configuration
    showPageNumbers: bool  # Show page number buttons (default: true)
    maxPageButtons: int  # Max page buttons to show (default: 7)
    showFirstLast: bool  # Show first/last page buttons (default: true)
    showPrevNext: bool  # Show previous/next buttons (default: true)


class TableOnRowClick(TypedDict, total=False):
    """Row click handler configuration"""
    action: Literal["open-modal", "navigate", "api-call"]
    target: Union[str, ValueRef]
    params: Dict[str, Union[str, ValueRef]]


class TableComponent(TypedDict, total=False):
    """Table component definition"""
    type: Literal["table"]  # Required
    data: Union[List[Any], ValueRef]  # Required
    columns: Union[List[ColumnDefinition], ValueRef]  # Required - can be dynamic
    actions: List[TableActionDefinition]
    rowActions: List[RowActionDefinition]
    sortable: bool
    filterable: bool
    pagination: TablePagination
    emptyState: 'EmptyStateComponent'
    onRowClick: TableOnRowClick
    density: Literal["comfortable", "compact", "dense"]


# ============================================================================
# Stats & Info Components
# ============================================================================

class StatCardTrend(TypedDict):
    """Stat card trend indicator"""
    direction: Literal["up", "down"]
    value: Union[str, ValueRef]


class StatCard(TypedDict, total=False):
    """Single stat card"""
    label: Union[str, ValueRef]  # Required
    value: Union[str, int, float, ValueRef]  # Required
    total: Union[int, float, ValueRef]
    icon: Union[str, ValueRef]
    color: Union[str, ValueRef]
    trend: StatCardTrend


class StatsCardsComponent(TypedDict, total=False):
    """Stats cards component"""
    type: Literal["stats-cards"]  # Required
    stats: Union[List[StatCard], ValueRef]  # Required - can be dynamic
    columns: int


class InfoGridItem(TypedDict, total=False):
    """Info grid item"""
    label: Union[str, ValueRef]  # Required
    value: Union[str, int, float, ValueRef]  # Required
    type: Literal["text", "code", "status", "date"]
    icon: Union[str, ValueRef]
    copyable: bool


class InfoGridComponent(TypedDict, total=False):
    """Info grid component"""
    type: Literal["info-grid"]  # Required
    items: Union[List[InfoGridItem], ValueRef]  # Required - can be dynamic
    columns: int


# ============================================================================
# Display Components
# ============================================================================

class CodeBlockComponent(TypedDict, total=False):
    """Code block component"""
    type: Literal["code-block"]  # Required
    content: Union[str, Dict, ValueRef]  # Required
    language: Literal["json", "javascript", "python", "yaml", "text"]
    copyable: bool
    collapsible: bool


class ChartSeries(TypedDict, total=False):
    """Chart series definition"""
    dataKey: Union[str, ValueRef]  # Required
    name: Union[str, ValueRef]  # Required
    color: Union[str, ValueRef]


class ChartAxis(TypedDict, total=False):
    """Chart axis configuration"""
    dataKey: Union[str, ValueRef]
    label: Union[str, ValueRef]


class ChartConfig(TypedDict, total=False):
    """Chart configuration"""
    series: Union[List[ChartSeries], ValueRef]  # Required - can be dynamic
    xAxis: ChartAxis
    yAxis: ChartAxis
    legend: bool
    height: int


class ChartComponent(TypedDict, total=False):
    """Chart component"""
    type: Literal["chart"]  # Required
    chartType: Literal["bar", "line", "pie", "area", "scatter"]  # Required
    data: Union[List[Any], ValueRef]  # Required
    config: ChartConfig  # Required


class DividerComponent(TypedDict, total=False):
    """Divider component for visual separation"""
    type: Literal["divider"]  # Required
    label: Union[str, ValueRef]
    orientation: Literal["horizontal", "vertical"]
    variant: Literal["solid", "dashed", "dotted"]


class BadgeComponent(TypedDict, total=False):
    """Badge component for labels/tags"""
    type: Literal["badge"]  # Required
    label: Union[str, ValueRef]  # Required
    variant: Literal["default", "success", "error", "warning", "info", "primary"]
    size: Literal["small", "medium", "large"]
    icon: str


class ProgressBarComponent(TypedDict, total=False):
    """Progress bar component"""
    type: Literal["progress-bar"]  # Required
    value: Union[int, float, ValueRef]  # Required
    max: Union[int, float]
    label: Union[str, ValueRef]
    variant: Literal["default", "success", "error", "warning", "info"]
    showPercentage: bool
    striped: bool
    animated: bool


class ImageComponent(TypedDict, total=False):
    """Image component"""
    type: Literal["image"]  # Required
    src: Union[str, ValueRef]  # Required
    alt: Union[str, ValueRef]
    width: Union[str, ValueRef]
    height: Union[str, ValueRef]
    fit: Literal["cover", "contain", "fill", "none", "scale-down"]
    rounded: bool
    bordered: bool


class TimelineItem(TypedDict, total=False):
    """Timeline item"""
    title: Union[str, ValueRef]  # Required
    description: Union[str, ValueRef]
    timestamp: Union[str, ValueRef]
    icon: Union[str, ValueRef]
    variant: Literal["default", "success", "error", "warning", "info"]


class TimelineComponent(TypedDict, total=False):
    """Timeline component for chronological events"""
    type: Literal["timeline"]  # Required
    items: Union[List[TimelineItem], ValueRef]  # Required - can be dynamic
    position: Literal["left", "right", "alternate"]


class ListItem(TypedDict, total=False):
    """List item"""
    label: Union[str, ValueRef]  # Required
    description: Union[str, ValueRef]
    icon: Union[str, ValueRef]
    action: ActionDefinition
    trailing: Union[str, ValueRef]  # Text or badge on the right


class ListComponent(TypedDict, total=False):
    """List component"""
    type: Literal["list"]  # Required
    items: Union[List[ListItem], ValueRef]  # Required - can be dynamic
    variant: Literal["default", "bordered", "divided"]
    hoverable: bool


class StepperStep(TypedDict, total=False):
    """Stepper step"""
    label: Union[str, ValueRef]  # Required
    description: Union[str, ValueRef]
    status: Literal["pending", "active", "completed", "error"]


class StepperComponent(TypedDict, total=False):
    """Stepper component for multi-step processes"""
    type: Literal["stepper"]  # Required
    steps: Union[List[StepperStep], ValueRef]  # Required - can be dynamic
    currentStep: Union[int, ValueRef]
    orientation: Literal["horizontal", "vertical"]


class MetricComponent(TypedDict, total=False):
    """Metric/KPI component for displaying key metrics"""
    type: Literal["metric"]  # Required
    value: Union[str, int, float, ValueRef]  # Required
    label: Union[str, ValueRef]  # Required
    unit: Union[str, ValueRef]
    previousValue: Union[int, float, ValueRef]
    format: Literal["number", "currency", "percentage", "duration"]
    trend: Literal["up", "down", "neutral"]
    icon: Union[str, ValueRef]
    variant: Literal["default", "success", "error", "warning", "info"]


class AvatarComponent(TypedDict, total=False):
    """Avatar component for user/entity representation"""
    type: Literal["avatar"]  # Required
    src: Union[str, ValueRef]
    name: Union[str, ValueRef]  # Used for initials if no src
    size: Literal["xs", "sm", "md", "lg", "xl"]
    variant: Literal["circle", "square", "rounded"]
    status: Literal["online", "offline", "away", "busy"]


class CalloutComponent(TypedDict, total=False):
    """Callout component for highlighted notices"""
    type: Literal["callout"]  # Required
    message: Union[str, ValueRef]  # Required
    title: Union[str, ValueRef]
    variant: Literal["info", "success", "warning", "error", "neutral"]
    icon: Union[str, ValueRef]
    dismissible: bool


class SpacerComponent(TypedDict, total=False):
    """Spacer component for adding spacing"""
    type: Literal["spacer"]  # Required
    size: Literal["xs", "sm", "md", "lg", "xl"]
    orientation: Literal["horizontal", "vertical"]


class BreadcrumbItem(TypedDict, total=False):
    """Breadcrumb item"""
    label: Union[str, ValueRef]  # Required
    href: Union[str, ValueRef]
    active: bool


class BreadcrumbsComponent(TypedDict, total=False):
    """Breadcrumbs navigation component"""
    type: Literal["breadcrumbs"]  # Required
    items: Union[List[BreadcrumbItem], ValueRef]  # Required - can be dynamic
    separator: Union[str, ValueRef]


class TooltipComponent(TypedDict, total=False):
    """Tooltip component for contextual help"""
    type: Literal["tooltip"]  # Required
    content: Union[str, ValueRef]  # Required - tooltip text
    trigger: "ComponentDefinition"  # Required - component that triggers tooltip
    placement: Literal["top", "bottom", "left", "right"]


class ToggleComponent(TypedDict, total=False):
    """Toggle/Switch component for boolean inputs"""
    type: Literal["toggle"]  # Required
    name: str  # Required - form field name
    label: Union[str, ValueRef]
    checked: Union[bool, ValueRef]
    disabled: Union[bool, ValueRef]
    onChange: ActionDefinition
    size: Literal["sm", "md", "lg"]


class ChipInputComponent(TypedDict, total=False):
    """Chip/Tag input component for multiple values"""
    type: Literal["chip-input"]  # Required
    name: str  # Required - form field name
    label: Union[str, ValueRef]
    value: Union[List[str], ValueRef]
    placeholder: Union[str, ValueRef]
    maxTags: int
    onChange: ActionDefinition


class SkeletonComponent(TypedDict, total=False):
    """Skeleton loader component"""
    type: Literal["skeleton"]  # Required
    variant: Literal["text", "circular", "rectangular", "card", "table"]  # Required
    width: Union[str, ValueRef]
    height: Union[str, ValueRef]
    lines: int  # For text variant
    rows: int  # For table variant
    animated: bool


class DropdownMenuItem(TypedDict, total=False):
    """Dropdown menu item"""
    label: Union[str, ValueRef]  # Required
    icon: Union[str, ValueRef]
    action: ActionDefinition
    variant: Literal["default", "danger"]
    divider: bool  # If true, renders as a divider


class DropdownOption(TypedDict, total=False):
    """Dropdown option"""
    value: Any  # Required
    label: Union[str, ValueRef]  # Required
    description: Union[str, ValueRef]
    icon: Union[str, ValueRef]
    disabled: bool


class DropdownComponent(TypedDict, total=False):
    """Dropdown select component"""
    type: Literal["dropdown"]  # Required
    name: str  # Required - form field name
    label: Union[str, ValueRef]
    placeholder: Union[str, ValueRef]
    options: Union[List[DropdownOption], ValueRef]  # Required - can be dynamic
    default_value: Union[Any, ValueRef]
    searchable: bool
    clearable: bool
    multiple: bool
    on_change: ActionDefinition
    disabled: Union[bool, ValueRef]


class TreeNode(TypedDict, total=False):
    """Tree node definition"""
    id: str  # Required - unique identifier
    label: Union[str, ValueRef]  # Required
    icon: Union[str, ValueRef]
    children: List['TreeNode']
    expanded: bool
    action: ActionDefinition


class TreeViewComponent(TypedDict, total=False):
    """Tree view component for hierarchical data"""
    type: Literal["tree-view"]  # Required
    nodes: Union[List[TreeNode], ValueRef]  # Required - can be dynamic
    expandAll: bool
    showIcons: bool


class FileUploadComponent(TypedDict, total=False):
    """File upload component"""
    type: Literal["file-upload"]  # Required
    name: str  # Required - form field name
    label: Union[str, ValueRef]
    accept: List[str]  # File types: ["image/*", ".pdf"]
    multiple: bool
    maxSize: Union[int, str]  # Bytes or "10MB"
    maxFiles: int
    showPreview: bool
    onUpload: ActionDefinition
    onRemove: ActionDefinition  # Called when a file is removed from the list


class DataGridColumn(TypedDict, total=False):
    """Data grid column definition"""
    key: str  # Required
    label: Union[str, ValueRef]  # Required
    type: Literal["text", "number", "date", "boolean", "select"]
    editable: bool
    width: Union[str, ValueRef]
    options: List["FormFieldOption"]  # For select type


class DataGridComponent(TypedDict, total=False):
    """Data grid component - advanced editable table"""
    type: Literal["data-grid"]  # Required
    data: Union[List[Any], ValueRef]  # Required
    columns: Union[List[DataGridColumn], ValueRef]  # Required - can be dynamic
    editable: bool
    onCellEdit: ActionDefinition
    onRowAdd: ActionDefinition
    onRowDelete: ActionDefinition
    pagination: TablePagination


class CalendarEvent(TypedDict, total=False):
    """Calendar event"""
    id: str  # Required
    title: Union[str, ValueRef]  # Required
    start: Union[str, ValueRef]  # Required - ISO date string
    end: Union[str, ValueRef]
    allDay: bool
    color: Union[str, ValueRef]
    action: ActionDefinition


class CalendarComponent(TypedDict, total=False):
    """Calendar component"""
    type: Literal["calendar"]  # Required
    events: Union[List[CalendarEvent], ValueRef]  # Required - can be dynamic
    view: Literal["month", "week", "day", "agenda"]
    onEventClick: ActionDefinition
    onDateClick: ActionDefinition


class GridComponent(TypedDict, total=False):
    """Grid layout component for arranging components in a grid"""
    type: Literal["grid"]  # Required
    items: Union[List['ComponentDefinition'], ValueRef]  # Required - components to display in grid
    columns: Union[int, str]  # Number of columns or CSS grid template (e.g. "1fr 2fr" or 3)
    gap: Union[str, ValueRef]  # Gap between grid items (e.g. "1rem", "20px")
    autoRows: Union[str, ValueRef]  # CSS grid-auto-rows value (e.g. "minmax(100px, auto)")


# ============================================================================
# Form Components
# ============================================================================

class ValidationRule(TypedDict, total=False):
    """Form field validation rule"""
    type: Literal["required", "email", "min", "max", "pattern", "custom"]  # Required
    value: Any
    message: Union[str, ValueRef]
    validator: str


class FormFieldOption(TypedDict, total=False):
    """Form field option (for select/radio)"""
    value: Any  # Required
    label: Union[str, ValueRef]  # Required
    description: Union[str, ValueRef]


class FormFieldDefinition(TypedDict, total=False):
    """Form field definition"""
    name: str  # Required - identifier, not dynamic
    label: Union[str, ValueRef]  # Required
    type: Literal["text", "number", "email", "password", "textarea", "select",
                  "checkbox", "radio", "date", "datetime", "file"]  # Required
    required: bool
    defaultValue: Union[Any, ValueRef]
    placeholder: Union[str, ValueRef]
    helpText: Union[str, ValueRef]
    validation: Union[List[ValidationRule], ValueRef]
    options: Union[List[FormFieldOption], ValueRef]
    condition: Any
    readonly: bool


class FormComponent(TypedDict, total=False):
    """Form component"""
    type: Literal["form"]  # Required
    fields: Union[List[FormFieldDefinition], ValueRef]  # Required - can be dynamic
    submitAction: ActionDefinition  # Required
    cancelAction: ActionDefinition
    layout: Literal["vertical", "horizontal", "grid"]
    readonly: bool


# ============================================================================
# Interactive Components
# ============================================================================

class ButtonComponent(TypedDict, total=False):
    """Button component"""
    type: Literal["button"]  # Required
    label: Union[str, ValueRef]  # Required
    action: ActionDefinition  # Required
    variant: Literal["primary", "secondary", "danger", "success"]
    icon: Union[str, ValueRef]
    size: Literal["small", "medium", "large"]
    disabled: Union[bool, ValueRef]
    confirmMessage: Union[str, ValueRef]


class AlertComponent(TypedDict, total=False):
    """Alert component"""
    type: Literal["alert"]  # Required
    message: Union[str, ValueRef]  # Required
    variant: Literal["info", "success", "warning", "error"]  # Required
    dismissible: bool


class EmptyStateComponent(TypedDict, total=False):
    """Empty state component"""
    type: Literal["empty-state"]  # Required
    message: Union[str, ValueRef]  # Required
    description: Union[str, ValueRef]
    icon: Union[str, ValueRef]
    action: ButtonComponent


# ============================================================================
# Container Components
# ============================================================================

class CardComponent(TypedDict, total=False):
    """Card component for grouping content"""
    type: Literal["card"]  # Required
    content: Union[List['ComponentDefinition'], ValueRef]  # Required - can be dynamic
    title: Union[str, ValueRef]
    subtitle: Union[str, ValueRef]
    actions: Union[List[ButtonComponent], ValueRef]
    variant: Literal["default", "outlined", "elevated"]
    padding: Literal["none", "small", "medium", "large"]


class AccordionItem(TypedDict, total=False):
    """Single accordion item"""
    id: str  # Required - identifier, not dynamic
    title: Union[str, ValueRef]  # Required
    content: Union[List['ComponentDefinition'], ValueRef]  # Required - can be dynamic
    defaultExpanded: bool


class AccordionComponent(TypedDict, total=False):
    """Accordion component for collapsible sections"""
    type: Literal["accordion"]  # Required
    items: Union[List[AccordionItem], ValueRef]  # Required - can be dynamic
    allowMultiple: bool
    variant: Literal["default", "bordered", "separated"]


# ============================================================================
# Component Union Type
# ============================================================================

ComponentDefinition = Union[
    StatsCardsComponent,
    TableComponent,
    InfoGridComponent,
    CodeBlockComponent,
    ChartComponent,
    FormComponent,
    ButtonComponent,
    AlertComponent,
    EmptyStateComponent,
    DividerComponent,
    BadgeComponent,
    ProgressBarComponent,
    CardComponent,
    AccordionComponent,
    ImageComponent,
    TimelineComponent,
    ListComponent,
    StepperComponent,
    MetricComponent,
    AvatarComponent,
    CalloutComponent,
    SpacerComponent,
    BreadcrumbsComponent,
    TooltipComponent,
    ToggleComponent,
    ChipInputComponent,
    SkeletonComponent,
    DropdownComponent,
    TreeViewComponent,
    FileUploadComponent,
    DataGridComponent,
    CalendarComponent,
    GridComponent,
]


# ============================================================================
# Layout Types
# ============================================================================

class SectionComponent(TypedDict, total=False):
    """Section component (groups components)"""
    components: Union[List[ComponentDefinition], ValueRef]  # Required - can be dynamic
    id: str  # Identifier, not dynamic
    title: Union[str, ValueRef]
    collapsible: bool
    defaultCollapsed: bool
    className: str


class TabDefinition(TypedDict, total=False):
    """Tab definition"""
    id: str  # Required - identifier, not dynamic
    label: Union[str, ValueRef]  # Required
    content: 'LayoutComponent'  # Required
    icon: Union[str, ValueRef]


class LayoutComponent(TypedDict, total=False):
    """Layout component"""
    type: Literal["vertical", "horizontal", "grid", "tabs"]  # Required
    sections: Union[List[SectionComponent], ValueRef]
    tabs: Union[List[TabDefinition], ValueRef]
    gap: str
    className: str


# ============================================================================
# Modal Types
# ============================================================================

class ModalDefinition(TypedDict, total=False):
    """Modal definition"""
    title: Union[str, ValueRef]  # Required
    content: Union[List[ComponentDefinition], ValueRef]  # Required - can be dynamic
    size: Literal["small", "medium", "large", "fullscreen"]
    actions: Union[List[ButtonComponent], ValueRef]
    closeOnOverlayClick: bool


class PanelDefinition(TypedDict, total=False):
    """Panel definition for bottom-right collapsible panel"""
    title: Union[str, ValueRef]  # Required
    content: Union[List[ComponentDefinition], ValueRef]  # Required - can be dynamic
    width: Union[str, ValueRef]  # Width of panel (e.g., "400px", "30%")
    defaultOpen: bool  # Whether panel starts open
    position: Literal["bottom-right", "bottom-left", "top-right", "top-left"]  # Panel position


# ============================================================================
# Real-time Update Types
# ============================================================================

class SocketEventHandler(TypedDict, total=False):
    """Socket event handler

    Can either use a simple handler type or execute a DSL action.
    If 'action' is provided, it takes precedence over 'handler'.
    """
    event: str  # Required
    handler: Literal["refresh-page", "update-component", "show-toast"]
    action: ActionDefinition  # Execute a DSL action when event is received
    componentId: Union[str, ValueRef]
    message: Union[str, ValueRef]


class PollingConfig(TypedDict, total=False):
    """Polling configuration

    Polls an endpoint at regular intervals and executes an action with the response.
    """
    interval: int  # Required (milliseconds)
    endpoint: Union[str, ValueRef]  # Required - endpoint to poll
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]  # HTTP method (default: GET)
    body: Dict[str, Any]  # Request body for POST/PUT/PATCH
    action: ActionDefinition  # Action to execute with poll response
    componentId: Union[str, ValueRef]  # Legacy: component to update


class RealtimeConfig(TypedDict, total=False):
    """Real-time update configuration"""
    enabled: bool  # Required
    socketEvents: List[SocketEventHandler]
    polling: PollingConfig


# ============================================================================
# Page Types
# ============================================================================

class PageMetadata(TypedDict, total=False):
    """Page metadata"""
    refreshInterval: int
    requiresAuth: bool
    permissions: List[str]


class PageDSL(TypedDict, total=False):
    """Complete page DSL definition"""
    type: Literal["page"]  # Required
    title: Union[str, ValueRef]  # Required
    layout: LayoutComponent  # Required
    description: Union[str, ValueRef]
    actions: Union[List[ActionDefinition], ValueRef]
    modals: Dict[str, ModalDefinition]
    panels: Dict[str, PanelDefinition]
    realtime: RealtimeConfig
    metadata: PageMetadata

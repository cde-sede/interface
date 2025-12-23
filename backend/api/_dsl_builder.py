"""
DSL Builder Utilities for Admin Panel

This module provides builder classes and helper functions to construct
DSL structures more easily on the backend.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from ._dsl_types import *


class ValueRefBuilder:
    """Helper to create value references"""

    @staticmethod
    def literal(value: Any) -> ValueRef:
        """Create a literal value reference"""
        return ValueRef(type="literal", value=value)

    @staticmethod
    def field(source: Literal["row", "form", "response", "pageData", "data", "pagination"], path: str) -> ValueRef:
        """Create a field value reference

        Sources:
        - "row": Row data (in table row actions/renderers)
        - "form": Current form data (values being entered)
        - "response": Response from the last API call (in onSuccess handlers)
        - "pageData": The entire page DSL data
        - "data": Modal data (when in a modal) or component-level data
        """
        return ValueRef(type="field", source=source, path=path)

    @staticmethod
    def computed(template: str, **values: ValueRef) -> ValueRef:
        """Create a computed value reference with template interpolation

        Example:
            ValueRefBuilder.computed("Hello, {name}!", name=ValueRefBuilder.field("form", "name"))
        """
        return ValueRef(type="computed", template=template, values=values)

    @staticmethod
    def coalesce(*options: ValueRef) -> ValueRef:
        """Create a coalesce value reference that returns the first non-null/undefined value

        Example:
            # Use form.value if defined, otherwise use data.default
            ValueRefBuilder.coalesce(
                ValueRefBuilder.field("form", "value"),
                ValueRefBuilder.field("data", "default")
            )
        """
        return ValueRef(type="coalesce", options=list(options))

    @staticmethod
    def conditional(condition: ValueRef, true_value: ValueRef, false_value: ValueRef) -> ValueRef:
        """Create a conditional value reference (ternary operator)

        Example:
            # If form.enabled is truthy, use "Enabled", otherwise "Disabled"
            ValueRefBuilder.conditional(
                ValueRefBuilder.field("form", "enabled"),
                ValueRefBuilder.literal("Enabled"),
                ValueRefBuilder.literal("Disabled")
            )
        """
        return ValueRef(type="conditional", condition=condition, trueValue=true_value, falseValue=false_value)


class ActionBuilder:
    """Builder for action definitions"""

    def __init__(self):
        self.action: ActionDefinition = ActionDefinition()

    def api_call(
        self,
        endpoint: Union[str, ValueRef],
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "POST",
        body: Optional[Dict[str, Any] | ValueRef] = None
    ) -> 'ActionBuilder':
        """Configure an API call action"""
        self.action["type"] = "api-call"
        self.action["endpoint"] = endpoint
        self.action["method"] = method
        if body:
            self.action["body"] = body
        return self

    def open_modal(self, modal_id: str, modal_data: Optional[Dict[str, Any]] = None) -> 'ActionBuilder':
        """Configure an open modal action"""
        self.action["type"] = "open-modal"
        self.action["modalId"] = modal_id
        if modal_data:
            self.action["modalData"] = modal_data
        return self

    def close_modal(self, modal_id: str, message: Optional[Union[str, ValueRef]] = None, toast_type: Literal["success", "error", "info", "warning"] = "info") -> 'ActionBuilder':
        """Configure a close modal action

        Args:
            modal_id: ID of the modal to close
            message: Optional message to show as a toast when closing
            toast_type: Type of toast to show (default: info)
        """
        self.action["type"] = "close-modal"
        self.action["modalId"] = modal_id
        if message:
            self.action["message"] = message
            self.action["toastType"] = toast_type
        return self

    def navigate(self, page: str) -> 'ActionBuilder':
        """Configure a navigate action"""
        self.action["type"] = "navigate"
        self.action["page"] = page
        return self

    def refresh(self) -> 'ActionBuilder':
        """Configure a refresh action"""
        self.action["type"] = "refresh"
        return self

    def show_toast(
        self,
        message: Union[str, ValueRef],
        toast_type: Literal["success", "error", "info", "warning"] = "info"
    ) -> 'ActionBuilder':
        """Configure a show toast action"""
        self.action["type"] = "show-toast"
        self.action["message"] = message
        self.action["toastType"] = toast_type
        return self

    def on_success(self, message: Optional[str] = None, action: Optional['ActionBuilder'] = None) -> 'ActionBuilder':
        """Add success handler"""
        success_handler = ActionOnSuccess()
        if message:
            success_handler["message"] = message
        if action:
            success_handler["action"] = action.build()
        self.action["onSuccess"] = success_handler
        return self

    def on_error(self, message: Optional[str] = None) -> 'ActionBuilder':
        """Add error handler"""
        error_handler = ActionOnError()
        if message:
            error_handler["message"] = message
        self.action["onError"] = error_handler
        return self

    def build(self) -> ActionDefinition:
        """Build the action definition"""
        return self.action


class TableBuilder:
    """Builder for table components"""

    def __init__(self, data: Union[List[Any], ValueRef], columns: Optional[Union[List[ColumnDefinition], ValueRef]] = None):
        self.table: TableComponent = TableComponent(type="table", data=data, columns=columns if columns is not None else [])

    def add_column(
        self,
        key: str,
        label: str,
        type: Literal["text", "number", "date", "boolean", "status", "code"] = "text",
        hidden: bool = False,
        **kwargs
    ) -> 'TableBuilder':
        """Add a column to the table

        Args:
            key: Column key (data field name)
            label: Column label (display name)
            type: Column type
            hidden: If True, column is not displayed but data is available for actions/refs
            **kwargs: Additional column properties
        """
        column: ColumnDefinition = ColumnDefinition(key=key, label=label, type=type)
        if hidden:
            column["hidden"] = hidden
        column.update(kwargs)
        self.table["columns"].append(column)
        return self

    def add_hidden_column(self, key: str, label: str = "") -> 'TableBuilder':
        """Add a hidden column (data available for actions/refs but not displayed)

        Args:
            key: Column key (data field name)
            label: Column label (optional, not displayed anyway)
        """
        return self.add_column(key, label or key, type="text", hidden=True)

    def add_status_column(
        self,
        key: str,
        label: str,
        config: Dict[str, StatusBadgeConfig]
    ) -> 'TableBuilder':
        """Add a status column with badge rendering"""
        column: ColumnDefinition = ColumnDefinition(
            key=key,
            label=label,
            type="status",
            renderer=ColumnRenderer(type="status-badge", config=config)
        )
        self.table["columns"].append(column)
        return self

    def add_header_action(
        self,
        id: str,
        label: str,
        action: ActionBuilder,
        icon: Optional[str] = None,
        confirm_message: Optional[Union[str, ValueRef]] = None
    ) -> 'TableBuilder':
        """Add a header-level action"""
        if "actions" not in self.table:
            self.table["actions"] = []

        table_action: TableActionDefinition = TableActionDefinition(
            id=id,
            label=label,
            action=action.build()
        )
        if icon:
            table_action["icon"] = icon
        if confirm_message:
            table_action["confirmMessage"] = confirm_message

        self.table["actions"].append(table_action)
        return self

    def add_row_action(
        self,
        id: str,
        label: str,
        action: ActionBuilder,
        icon: Optional[str] = None,
        confirm_message: Optional[Union[str, ValueRef]] = None,
        condition: Optional[Any] = None
    ) -> 'TableBuilder':
        """Add a row-level action"""
        if "rowActions" not in self.table:
            self.table["rowActions"] = []

        row_action: RowActionDefinition = RowActionDefinition(
            id=id,
            label=label,
            action=action.build()
        )
        if icon:
            row_action["icon"] = icon
        if confirm_message:
            row_action["confirmMessage"] = confirm_message
        if condition:
            row_action["condition"] = condition

        self.table["rowActions"].append(row_action)
        return self

    def set_sortable(self, sortable: bool = True) -> 'TableBuilder':
        """Enable/disable sorting"""
        self.table["sortable"] = sortable
        return self

    def set_filterable(self, filterable: bool = True) -> 'TableBuilder':
        """Enable/disable filtering"""
        self.table["filterable"] = filterable
        return self

    def set_pagination(
        self,
        enabled: bool = True,
        page_size: int = 20,
        mode: Literal["client", "server"] = "client",
        total_items: Optional[Union[int, ValueRef]] = None,
        current_page: Optional[Union[int, ValueRef]] = None,
        on_page_change: Optional[ActionBuilder] = None,
        show_page_numbers: bool = True,
        max_page_buttons: int = 7,
        show_first_last: bool = True,
        show_prev_next: bool = True
    ) -> 'TableBuilder':
        """Configure pagination

        Args:
            enabled: Enable pagination
            page_size: Number of items per page
            mode: "client" for client-side pagination, "server" for lazy loading
            total_items: Total number of items (required for server-side pagination)
            current_page: Current page number (1-indexed, for server-side)
            on_page_change: Action called when page changes (for server-side pagination)
            show_page_numbers: Show page number buttons
            max_page_buttons: Maximum page buttons to display
            show_first_last: Show first/last page buttons
            show_prev_next: Show previous/next buttons
        """
        pagination = TablePagination(
            enabled=enabled,
            pageSize=page_size,
            mode=mode,
            showPageNumbers=show_page_numbers,
            maxPageButtons=max_page_buttons,
            showFirstLast=show_first_last,
            showPrevNext=show_prev_next
        )

        if total_items is not None:
            pagination["totalItems"] = total_items
        if current_page is not None:
            pagination["currentPage"] = current_page
        if on_page_change is not None:
            pagination["onPageChange"] = on_page_change.build()

        self.table["pagination"] = pagination
        return self

    def set_empty_state(self, message: str, description: Optional[str] = None) -> 'TableBuilder':
        """Set empty state"""
        empty_state: EmptyStateComponent = EmptyStateComponent(type="empty-state", message=message)
        if description:
            empty_state["description"] = description
        self.table["emptyState"] = empty_state
        return self

    def on_row_click(
        self,
        action: Literal["open-modal", "navigate", "api-call"],
        target: str,
        params: Optional[Dict[str, Union[str, ValueRef]]] = None
    ) -> 'TableBuilder':
        """Set row click handler"""
        row_click: TableOnRowClick = TableOnRowClick(action=action, target=target)
        if params:
            row_click["params"] = params
        self.table["onRowClick"] = row_click
        return self

    def build(self) -> TableComponent:
        """Build the table component"""
        return self.table


class FormBuilder:
    """Builder for form components"""

    def __init__(self, submit_action: ActionBuilder):
        self.form: FormComponent = FormComponent(
            type="form",
            fields=[],
            submitAction=submit_action.build()
        )

    def add_field(
        self,
        name: str,
        label: str,
        type: Literal["text", "number", "email", "password", "textarea",
                      "select", "checkbox", "radio", "date", "datetime", "file"] = "text",
        **kwargs
    ) -> 'FormBuilder':
        """Add a field to the form"""
        field: FormFieldDefinition = FormFieldDefinition(name=name, label=label, type=type)
        field.update(kwargs)
        self.form["fields"].append(field)
        return self

    def add_select_field(
        self,
        name: str,
        label: str,
        options: List[FormFieldOption],
        **kwargs
    ) -> 'FormBuilder':
        """Add a select field"""
        field: FormFieldDefinition = FormFieldDefinition(
            name=name,
            label=label,
            type="select",
            options=options
        )
        field.update(kwargs)
        self.form["fields"].append(field)
        return self

    def set_cancel_action(self, cancel_action: ActionBuilder) -> 'FormBuilder':
        """Set cancel action"""
        self.form["cancelAction"] = cancel_action.build()
        return self

    def set_layout(self, layout: Literal["vertical", "horizontal", "grid"]) -> 'FormBuilder':
        """Set form layout"""
        self.form["layout"] = layout
        return self

    def set_readonly(self, readonly: bool = True) -> 'FormBuilder':
        """Set readonly mode"""
        self.form["readonly"] = readonly
        return self

    def build(self) -> FormComponent:
        """Build the form component"""
        return self.form


class SectionBuilder:
    """Builder for section components"""

    def __init__(self, title: Optional[Union[str, ValueRef]] = None, components: Optional[Union[List[ComponentDefinition], ValueRef]] = None):
        self.section: SectionComponent = SectionComponent(components=components if components is not None else [])
        if title:
            self.section["title"] = title

    def add_component(self, component: ComponentDefinition) -> 'SectionBuilder':
        """Add a component to the section"""
        self.section["components"].append(component)
        return self

    def add_stats_cards(self, stats: List[StatCard], columns: int = 4) -> 'SectionBuilder':
        """Add stats cards component"""
        component: StatsCardsComponent = StatsCardsComponent(
            type="stats-cards",
            stats=stats,
            columns=columns
        )
        self.section["components"].append(component)
        return self

    def add_info_grid(self, items: List[InfoGridItem], columns: int = 4) -> 'SectionBuilder':
        """Add info grid component"""
        component: InfoGridComponent = InfoGridComponent(
            type="info-grid",
            items=items,
            columns=columns
        )
        self.section["components"].append(component)
        return self

    def add_code_block(
        self,
        content: Union[str, Dict, ValueRef],
        language: Literal["json", "javascript", "python", "yaml", "text"] = "json",
        copyable: bool = True
    ) -> 'SectionBuilder':
        """Add code block component"""
        component: CodeBlockComponent = CodeBlockComponent(
            type="code-block",
            content=content,
            language=language,
            copyable=copyable
        )
        self.section["components"].append(component)
        return self

    def add_table(self, table_builder: TableBuilder) -> 'SectionBuilder':
        """Add a table component"""
        self.section["components"].append(table_builder.build())
        return self

    def add_button(
        self,
        label: str,
        action: ActionBuilder,
        variant: Literal["primary", "secondary", "danger", "success"] = "primary",
        **kwargs
    ) -> 'SectionBuilder':
        """Add a button component"""
        button: ButtonComponent = ButtonComponent(
            type="button",
            label=label,
            action=action.build(),
            variant=variant
        )
        button.update(kwargs)
        self.section["components"].append(button)
        return self

    def add_form(self, form_builder: FormBuilder) -> 'SectionBuilder':
        """Add a form component"""
        self.section["components"].append(form_builder.build())
        return self

    def add_chart(self, chart_builder: 'ChartBuilder') -> 'SectionBuilder':
        """Add a chart component"""
        self.section["components"].append(chart_builder.build())
        return self

    def add_divider(
        self,
        label: Optional[str] = None,
        orientation: Literal["horizontal", "vertical"] = "horizontal",
        variant: Literal["solid", "dashed", "dotted"] = "solid"
    ) -> 'SectionBuilder':
        """Add a divider component"""
        self.section["components"].append(create_divider(label, orientation, variant))
        return self

    def add_badge(
        self,
        label: Union[str, ValueRef],
        variant: Literal["default", "success", "error", "warning", "info", "primary"] = "default",
        size: Literal["small", "medium", "large"] = "medium",
        icon: Optional[str] = None
    ) -> 'SectionBuilder':
        """Add a badge component"""
        self.section["components"].append(create_badge(label, variant, size, icon))
        return self

    def add_progress_bar(
        self,
        value: Union[int, float, ValueRef],
        max: Union[int, float] = 100,
        label: Optional[Union[str, ValueRef]] = None,
        variant: Literal["default", "success", "error", "warning", "info"] = "default"
    ) -> 'SectionBuilder':
        """Add a progress bar component"""
        self.section["components"].append(create_progress_bar(value, max, label, variant))
        return self

    def add_card(self, card_builder: 'CardBuilder') -> 'SectionBuilder':
        """Add a card component"""
        self.section["components"].append(card_builder.build())
        return self

    def add_accordion(self, accordion_builder: 'AccordionBuilder') -> 'SectionBuilder':
        """Add an accordion component"""
        self.section["components"].append(accordion_builder.build())
        return self

    def set_id(self, id: str) -> 'SectionBuilder':
        """Set section ID"""
        self.section["id"] = id
        return self

    def set_collapsible(self, collapsible: bool = True, default_collapsed: bool = False) -> 'SectionBuilder':
        """Set collapsible configuration"""
        self.section["collapsible"] = collapsible
        self.section["defaultCollapsed"] = default_collapsed
        return self

    def build(self) -> SectionComponent:
        """Build the section component"""
        return self.section


class PageBuilder:
    """Builder for page DSL"""

    def __init__(self, title: Union[str, ValueRef], description: Optional[Union[str, ValueRef]] = None):
        self.page: PageDSL = PageDSL(
            type="page",
            title=title,
            layout=LayoutComponent(type="vertical", sections=[])
        )
        if description:
            self.page["description"] = description

    def add_section(self, section_builder: SectionBuilder) -> 'PageBuilder':
        """Add a section to the page"""
        if "sections" not in self.page["layout"]:
            self.page["layout"]["sections"] = []
        self.page["layout"]["sections"].append(section_builder.build())
        return self

    def add_modal(self, modal_id: str, modal: ModalDefinition) -> 'PageBuilder':
        """Add a modal definition"""
        if "modals" not in self.page:
            self.page["modals"] = {}
        self.page["modals"][modal_id] = modal
        return self

    def set_realtime(
        self,
        socket_events: Optional[List[SocketEventHandler]] = None,
        polling: Optional[PollingConfig] = None
    ) -> 'PageBuilder':
        """Configure real-time updates"""
        realtime: RealtimeConfig = RealtimeConfig(enabled=True)
        if socket_events:
            realtime["socketEvents"] = socket_events
        if polling:
            realtime["polling"] = polling
        self.page["realtime"] = realtime
        return self

    def set_metadata(
        self,
        refresh_interval: Optional[int] = None,
        requires_auth: Optional[bool] = None,
        permissions: Optional[List[str]] = None
    ) -> 'PageBuilder':
        """Set page metadata"""
        metadata: PageMetadata = PageMetadata()
        if refresh_interval is not None:
            metadata["refreshInterval"] = refresh_interval
        if requires_auth is not None:
            metadata["requiresAuth"] = requires_auth
        if permissions:
            metadata["permissions"] = permissions
        self.page["metadata"] = metadata
        return self

    def build(self) -> PageDSL:
        """Build the page DSL"""
        return self.page


# ============================================================================
# Helper Functions
# ============================================================================

def create_status_badge_config(
    value: str,
    label: str,
    variant: Literal["success", "error", "warning", "info"]
) -> tuple[str, StatusBadgeConfig]:
    """Helper to create status badge configuration"""
    return (value, StatusBadgeConfig(label=label, variant=variant))


def create_stat_card(
    label: str,
    value: Union[str, int, float],
    total: Optional[Union[int, float]] = None,
    icon: Optional[str] = None
) -> StatCard:
    """Helper to create a stat card"""
    card: StatCard = StatCard(label=label, value=value)
    if total is not None:
        card["total"] = total
    if icon:
        card["icon"] = icon
    return card


def create_info_item(
    label: str,
    value: Union[str, int, float, ValueRef],
    type: Literal["text", "code", "status", "date"] = "text",
    copyable: bool = False
) -> InfoGridItem:
    """Helper to create an info grid item"""
    item: InfoGridItem = InfoGridItem(label=label, value=value, type=type)
    if copyable:
        item["copyable"] = copyable
    return item


def create_divider(
    label: Optional[str] = None,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    variant: Literal["solid", "dashed", "dotted"] = "solid"
) -> DividerComponent:
    """Helper to create a divider component"""
    divider: DividerComponent = DividerComponent(type="divider")
    if label:
        divider["label"] = label
    divider["orientation"] = orientation
    divider["variant"] = variant
    return divider


def create_badge(
    label: Union[str, ValueRef],
    variant: Literal["default", "success", "error", "warning", "info", "primary"] = "default",
    size: Literal["small", "medium", "large"] = "medium",
    icon: Optional[str] = None
) -> BadgeComponent:
    """Helper to create a badge component"""
    badge: BadgeComponent = BadgeComponent(type="badge", label=label)
    badge["variant"] = variant
    badge["size"] = size
    if icon:
        badge["icon"] = icon
    return badge


def create_progress_bar(
    value: Union[int, float, ValueRef],
    max: Union[int, float] = 100,
    label: Optional[Union[str, ValueRef]] = None,
    variant: Literal["default", "success", "error", "warning", "info"] = "default",
    show_percentage: bool = True
) -> ProgressBarComponent:
    """Helper to create a progress bar component"""
    progress: ProgressBarComponent = ProgressBarComponent(
        type="progress-bar",
        value=value
    )
    progress["max"] = max
    if label:
        progress["label"] = label
    progress["variant"] = variant
    progress["showPercentage"] = show_percentage
    return progress


# ============================================================================
# Advanced Component Builders
# ============================================================================

class ChartBuilder:
    """Builder for chart components"""

    def __init__(
        self,
        chart_type: Literal["bar", "line", "pie", "area", "scatter"],
        data: Union[List[Any], ValueRef]
    ):
        self.chart: ChartComponent = ChartComponent(
            type="chart",
            chartType=chart_type,
            data=data,
            config=ChartConfig(series=[])
        )

    def add_series(
        self,
        data_key: str,
        name: str,
        color: Optional[str] = None
    ) -> 'ChartBuilder':
        """Add a series to the chart"""
        series: ChartSeries = ChartSeries(dataKey=data_key, name=name)
        if color:
            series["color"] = color
        self.chart["config"]["series"].append(series)
        return self

    def set_x_axis(self, data_key: str, label: Optional[str] = None) -> 'ChartBuilder':
        """Set X axis configuration"""
        self.chart["config"]["xAxis"] = ChartAxis(dataKey=data_key)
        if label:
            self.chart["config"]["xAxis"]["label"] = label
        return self

    def set_y_axis(self, label: Optional[str] = None) -> 'ChartBuilder':
        """Set Y axis configuration"""
        self.chart["config"]["yAxis"] = ChartAxis()
        if label:
            self.chart["config"]["yAxis"]["label"] = label
        return self

    def set_legend(self, enabled: bool = True) -> 'ChartBuilder':
        """Enable/disable legend"""
        self.chart["config"]["legend"] = enabled
        return self

    def set_height(self, height: int) -> 'ChartBuilder':
        """Set chart height"""
        self.chart["config"]["height"] = height
        return self

    def build(self) -> ChartComponent:
        """Build the chart component"""
        return self.chart


class CardBuilder:
    """Builder for card components"""

    def __init__(self, title: Optional[Union[str, ValueRef]] = None, content: Optional[Union[List[ComponentDefinition], ValueRef]] = None):
        self.card: CardComponent = CardComponent(type="card", content=content if content is not None else [])
        if title:
            self.card["title"] = title

    def set_subtitle(self, subtitle: Union[str, ValueRef]) -> 'CardBuilder':
        """Set card subtitle"""
        self.card["subtitle"] = subtitle
        return self

    def add_component(self, component: ComponentDefinition) -> 'CardBuilder':
        """Add a component to the card"""
        self.card["content"].append(component)
        return self

    def add_action(self, action: ButtonComponent) -> 'CardBuilder':
        """Add an action button to the card"""
        if "actions" not in self.card:
            self.card["actions"] = []
        self.card["actions"].append(action)
        return self

    def set_variant(self, variant: Literal["default", "outlined", "elevated"]) -> 'CardBuilder':
        """Set card variant"""
        self.card["variant"] = variant
        return self

    def set_padding(self, padding: Literal["none", "small", "medium", "large"]) -> 'CardBuilder':
        """Set card padding"""
        self.card["padding"] = padding
        return self

    def build(self) -> CardComponent:
        """Build the card component"""
        return self.card


class AccordionBuilder:
    """Builder for accordion components"""

    def __init__(self, items: Optional[Union[List[AccordionItem], ValueRef]] = None):
        self.accordion: AccordionComponent = AccordionComponent(type="accordion", items=items if items is not None else [])

    def add_item(
        self,
        id: str,
        title: Union[str, ValueRef],
        content: Union[List[ComponentDefinition], ValueRef],
        default_expanded: bool = False
    ) -> 'AccordionBuilder':
        """Add an item to the accordion"""
        item: AccordionItem = AccordionItem(
            id=id,
            title=title,
            content=content
        )
        if default_expanded:
            item["defaultExpanded"] = default_expanded
        self.accordion["items"].append(item)
        return self

    def set_allow_multiple(self, allow_multiple: bool = True) -> 'AccordionBuilder':
        """Allow multiple items to be expanded"""
        self.accordion["allowMultiple"] = allow_multiple
        return self

    def set_variant(self, variant: Literal["default", "bordered", "separated"]) -> 'AccordionBuilder':
        """Set accordion variant"""
        self.accordion["variant"] = variant
        return self

    def build(self) -> AccordionComponent:
        """Build the accordion component"""
        return self.accordion

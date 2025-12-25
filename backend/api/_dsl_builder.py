"""
DSL Builder Utilities for Admin Panel

This module provides builder classes and helper functions to construct
DSL structures more easily on the backend.
"""

from typing import Self
from ._dsl_types import *


# TODO ComponentDefinitionBuilder


class ValueRefBuilder:
	"""Helper to create value references"""

	@staticmethod
	def literal(value: Any) -> ValueRef:
		"""Create a literal value reference"""
		return ValueRef(type="literal", value=value)

	@staticmethod
	def field(source: Literal["row", "form", "response", "pageData", "data", "store"], path: str) -> ValueRef:
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
		return ValueRef(type="coalesce", options=list(options))  # type: ignore[typeddict-item]

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

	@staticmethod
	def transform(input: Union[ValueRef, Any], transform: str) -> ValueRef:
		"""Create a transform value reference for map/filter operations

		Transform types:
		- Regex map: "/pattern/->replacement" - Apply regex on strings
		- Object map: "&->.field1,.field2" - Extract fields as object
		- Tuple map: "#->.field1,.field2" - Extract fields as array
		- Regex filter: "/pattern/~>" or "/pattern/~>!" - Filter array of strings
		- Object filter: ".field>value~>" or ".field>value~>!" - Filter array of objects

		Examples:
			# Extract fields from response object
			ValueRefBuilder.transform(
				ValueRefBuilder.field("response", "user"),
				"&->.id,name,email"
			)

			# Filter array of users where active == true
			ValueRefBuilder.transform(
				ValueRefBuilder.field("response", "users"),
				".active==true~>"
			)

			# Add newline to each filename
			ValueRefBuilder.transform(
				ValueRefBuilder.field("response", "filenames"),
				"/(.*)/->\1\n"
			)

			# Remove strings with newlines
			ValueRefBuilder.transform(
				ValueRefBuilder.field("response", "lines"),
				"/.*\\n/~>!"
			)
		"""
		return ValueRef(type="transform", input=input, transform=transform)


class ActionBuilder:
	"""Builder for action definitions"""

	def __init__(self):
		self.action: ActionDefinition = ActionDefinition()

	def api_call(
		self,
		endpoint: Union[str, ValueRef],
		method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "POST",
		body: Optional[Dict[str, Any] | ValueRef] = None
	) -> Self:
		"""Configure an API call action"""
		self.action["type"] = "api-call"
		self.action["endpoint"] = endpoint
		self.action["method"] = method
		if body:
			self.action["body"] = body  # type: ignore[typeddict-item]
		return self

	def open_modal(self, modal_id: str, modal_data: Optional[Dict[str, Any]] = None) -> Self:
		"""Configure an open modal action"""
		self.action["type"] = "open-modal"
		self.action["modalId"] = modal_id
		if modal_data:
			self.action["modalData"] = modal_data
		return self

	def close_modal(self, modal_id: str, message: Optional[Union[str, ValueRef]] = None, toast_type: Literal["success", "error", "info", "warning"] = "info") -> Self:
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

	def open_panel(self, panel_id: str, panel_data: Optional[Dict[str, Any]] = None) -> Self:
		"""Configure an open panel action"""
		self.action["type"] = "open-panel"
		self.action["panelId"] = panel_id
		if panel_data:
			self.action["panelData"] = panel_data
		return self

	def close_panel(self, panel_id: str) -> Self:
		"""Configure a close panel action"""
		self.action["type"] = "close-panel"
		self.action["panelId"] = panel_id
		return self

	def toggle_panel(self, panel_id: str, panel_data: Optional[Dict[str, Any]] = None) -> Self:
		"""Configure a toggle panel action"""
		self.action["type"] = "toggle-panel"
		self.action["panelId"] = panel_id
		if panel_data:
			self.action["panelData"] = panel_data
		return self

	def navigate(self, page: str) -> Self:
		"""Configure a navigate action"""
		self.action["type"] = "navigate"
		self.action["page"] = page
		return self

	def refresh(self) -> Self:
		"""Configure a refresh action"""
		self.action["type"] = "refresh"
		return self

	def show_toast(
		self,
		message: Union[str, ValueRef],
		toast_type: Literal["success", "error", "info", "warning"] = "info"
	) -> Self:
		"""Configure a show toast action"""
		self.action["type"] = "show-toast"
		self.action["message"] = message
		self.action["toastType"] = toast_type
		return self

	def on_success(self, message: Optional[str] = None, action: Optional['ActionBuilder | ActionDefinition'] = None) -> Self:
		"""Add success handler"""
		success_handler = ActionOnSuccess()
		if message:
			success_handler["message"] = message
		if action and isinstance(action, ActionBuilder):
			success_handler["action"] = action.build()
		elif action:
			success_handler["action"] = action
		self.action["onSuccess"] = success_handler
		return self

	def on_error(self, message: Optional[str] = None) -> Self:
		"""Add error handler"""
		error_handler = ActionOnError()
		if message:
			error_handler["message"] = message
		self.action["onError"] = error_handler
		return self

	def store_data(self, key: Union[str, ValueRef], value: Any) -> Self:
		"""Configure a store data action

		Args:
			key: The key to store data under (accessible via {"$ref": "store.{key}"})
			value: The value to store (can be a ValueRef like {"$ref": "response.id"})

		Example:
			ActionBuilder().store_data("userId", {"$ref": "response.id"})
		"""
		self.action["type"] = "store-data"
		self.action["key"] = key
		self.action["value"] = value
		return self

	def map_transform(self, input: Any, transform: str, output: Optional[Union[str, ValueRef]] = None) -> Self:
		"""Configure a map transformation action

		Transform types:
		- Regex map: "/pattern/->replacement" - Apply regex on strings
		- Object map: "&->.field1,.field2" - Extract fields as object
		- Tuple map: "#->.field1,.field2" - Extract fields as array
		- Regex filter: "/pattern/~>" or "/pattern/~>!" - Filter array of strings
		- Object filter: ".field>value~>" or ".field>value~>!" - Filter array of objects

		Args:
			input: Input data to transform (can be ValueRef)
			transform: Transformation string
			output: Optional key to store result in datastore

		Examples:
			# MAP: Add newline to string
			ActionBuilder().map_transform(
				input=ref("response.filename"),
				transform="/(.*)/->\1\n",
				output="formattedFilename"
			)

			# MAP: Extract specific fields from object
			ActionBuilder().map_transform(
				input=ref("response.user"),
				transform="&->.id,name,email",
				output="userSubset"
			)

			# MAP: Extract fields as tuple
			ActionBuilder().map_transform(
				input=ref("response.user"),
				transform="#->.name,email",
				output="userTuple"
			)

			# MAP: Apply to array (maps over each element)
			ActionBuilder().map_transform(
				input=ref("response.users"),
				transform="&->.id,name",
				output="simplifiedUsers"
			)

			# FILTER: Keep strings matching pattern
			ActionBuilder().map_transform(
				input=ref("response.lines"),
				transform="/.*error.*/~>",
				output="errorLines"
			)

			# FILTER: Remove strings matching pattern
			ActionBuilder().map_transform(
				input=ref("response.lines"),
				transform="/.*\\n/~>!",
				output="cleanLines"
			)

			# FILTER: Keep objects where size > 10
			ActionBuilder().map_transform(
				input=ref("response.items"),
				transform=".size>10~>",
				output="largeItems"
			)

			# FILTER: Remove objects where active == false
			ActionBuilder().map_transform(
				input=ref("response.users"),
				transform=".active==false~>!",
				output="activeUsers"
			)

			# FILTER: Supports operators: >, <, >=, <=, ==, !=
			ActionBuilder().map_transform(
				input=ref("response.products"),
				transform=".price<=100~>",
				output="affordableProducts"
			)
		"""
		self.action["type"] = "map"
		self.action["input"] = input
		self.action["transform"] = transform
		if output:
			self.action["output"] = output
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
	) -> Self:
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
		column.update(kwargs)                 # type: ignore[index]
		self.table["columns"].append(column)  # type: ignore[index]
		return self

	def add_hidden_column(self, key: str, label: str = "") -> Self:
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
	) -> Self:
		"""Add a status column with badge rendering"""
		column: ColumnDefinition = ColumnDefinition(
			key=key,
			label=label,
			type="status",
			renderer=ColumnRenderer(type="status-badge", config=config)
		)
		self.table["columns"].append(column)  # type: ignore[index]
		return self

	def add_header_action(
		self,
		id: str,
		label: str,
		action: ActionBuilder | ActionDefinition,
		icon: Optional[str] = None,
		confirm_message: Optional[Union[str, ValueRef]] = None
	) -> Self:
		"""Add a header-level action"""
		if "actions" not in self.table:
			self.table["actions"] = []

		table_action: TableActionDefinition = TableActionDefinition(
			id=id,
			label=label,
			action=action.build() if isinstance(action, ActionBuilder) else action
		)
		if icon:
			table_action["icon"] = icon
		if confirm_message:
			table_action["confirmMessage"] = confirm_message

		self.table["actions"].append(table_action)  # type: ignore[index]
		return self

	def add_row_action(
		self,
		id: str,
		label: str,
		action: ActionBuilder | ActionDefinition,
		icon: Optional[str] = None,
		confirm_message: Optional[Union[str, ValueRef]] = None,
		condition: Optional[Any] = None
	) -> Self:
		"""Add a row-level action"""
		if "rowActions" not in self.table:
			self.table["rowActions"] = []

		row_action: RowActionDefinition = RowActionDefinition(
			id=id,
			label=label,
			action=action.build() if isinstance(action, ActionBuilder) else action
		)
		if icon:
			row_action["icon"] = icon
		if confirm_message:
			row_action["confirmMessage"] = confirm_message
		if condition:
			row_action["condition"] = condition

		self.table["rowActions"].append(row_action)
		return self

	def set_sortable(self, sortable: bool = True) -> Self:
		"""Enable/disable sorting"""
		self.table["sortable"] = sortable
		return self

	def set_filterable(self, filterable: bool = True) -> Self:
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
		on_page_change: Optional[ActionBuilder | ActionDefinition] = None,
		show_page_numbers: bool = True,
		max_page_buttons: int = 7,
		show_first_last: bool = True,
		show_prev_next: bool = True
	) -> Self:
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
			pagination["onPageChange"] = on_page_change.build() if isinstance(on_page_change, ActionBuilder) else on_page_change

		self.table["pagination"] = pagination
		return self

	def set_empty_state(self, message: str, description: Optional[str] = None) -> Self:
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
	) -> Self:
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

	def __init__(self, submit_action: ActionBuilder | ActionDefinition):
		self.form: FormComponent = FormComponent(
			type="form",
			fields=[],
			submitAction=submit_action.build() if isinstance(submit_action, ActionBuilder) else submit_action
		)

	def add_field(
		self,
		name: str,
		label: str,
		type: Literal["text", "number", "email", "password", "textarea",
					  "select", "checkbox", "radio", "date", "datetime", "file"] = "text",
		**kwargs
	) -> Self:
		"""Add a field to the form"""
		field: FormFieldDefinition = FormFieldDefinition(name=name, label=label, type=type)
		field.update(kwargs)               # type: ignore[index]
		self.form["fields"].append(field)  # type: ignore[index]
		return self

	def add_select_field(
		self,
		name: str,
		label: str,
		options: List[FormFieldOption],
		**kwargs
	) -> Self:
		"""Add a select field"""
		field: FormFieldDefinition = FormFieldDefinition(
			name=name,
			label=label,
			type="select",
			options=options
		)
		field.update(kwargs)               # type: ignore[index]
		self.form["fields"].append(field)  # type: ignore[index]
		return self

	def set_cancel_action(self, cancel_action: ActionBuilder | ActionDefinition) -> Self:
		"""Set cancel action"""
		self.form["cancelAction"] = cancel_action.build() if isinstance(cancel_action, ActionBuilder) else cancel_action
		return self

	def set_layout(self, layout: Literal["vertical", "horizontal", "grid"]) -> Self:
		"""Set form layout"""
		self.form["layout"] = layout
		return self

	def set_readonly(self, readonly: bool = True) -> Self:
		"""Set readonly mode"""
		self.form["readonly"] = readonly
		return self

	def build(self) -> FormComponent:
		"""Build the form component"""
		return self.form


class TabBuilder:
	"""Builder for tab content - allows adding sections to a tab"""

	def __init__(self, tab: TabDefinition):
		raise NotImplementedError()


class ModalBuilder:
	"""Builder for modal content"""

	def __init__(self, title: Union[str, ValueRef], size: Literal["small", "medium", "large", "fullscreen"] = "medium"):
		self.modal: ModalDefinition = ModalDefinition(
			title=title,
			content=[],
			size=size
		)

	def add_component(self, component: ComponentDefinition) -> Self:
		"""Add a component to the modal"""
		self.modal["content"].append(component)  # type: ignore[index]
		return self

	def add_action(self, label: str, action: ActionBuilder | ActionDefinition, variant: Literal["primary", "secondary", "danger", "success"] = "primary") -> Self:
		"""Add an action button to the modal"""
		if "actions" not in self.modal:
			self.modal["actions"] = []
		button: ButtonComponent = ButtonComponent(
			type="button",
			label=label,
			action=action.build() if isinstance(action, ActionBuilder) else action,
			variant=variant
		)
		self.modal["actions"].append(button)  # type: ignore[index]
		return self

	def build(self) -> ModalDefinition:
		"""Build the modal definition"""
		return self.modal


class PanelBuilder:
	"""Builder for panel content"""

	def __init__(self, title: Union[str, ValueRef], position: Literal["bottom-right", "bottom-left", "top-right", "top-left"] = "bottom-right", width: Union[str, ValueRef] = "400px", default_open: bool = False):
		self.panel: PanelDefinition = PanelDefinition(
			title=title,
			content=[],
			position=position,
			width=width,
			defaultOpen=default_open
		)

	def add_component(self, component: ComponentDefinition) -> Self:
		"""Add a component to the panel"""
		self.panel["content"].append(component)  # type: ignore[index]
		return self

	def build(self) -> PanelDefinition:
		"""Build the panel definition"""
		return self.panel

		

# ============================================================================
# Helper Functions for Simple Components
# ============================================================================

def create_divider(
	label: Optional[str] = None,
	orientation: Literal["horizontal", "vertical"] = "horizontal",
	variant: Literal["solid", "dashed", "dotted"] = "solid"
) -> DividerComponent:
	"""Create a divider component"""
	component: DividerComponent = DividerComponent(type="divider", orientation=orientation, variant=variant)
	if label:
		component["label"] = label
	return component


def create_badge(
	label: Union[str, ValueRef],
	variant: Literal["default", "success", "error", "warning", "info", "primary"] = "default",
	size: Literal["small", "medium", "large"] = "medium",
	icon: Optional[str] = None
) -> BadgeComponent:
	"""Create a badge component"""
	component: BadgeComponent = BadgeComponent(type="badge", label=label, variant=variant, size=size)
	if icon:
		component["icon"] = icon
	return component


def create_progress_bar(
	value: Union[int, float, ValueRef],
	max: Union[int, float] = 100,
	label: Optional[Union[str, ValueRef]] = None,
	variant: Literal["default", "success", "error", "warning", "info"] = "default"
) -> ProgressBarComponent:
	"""Create a progress bar component"""
	component: ProgressBarComponent = ProgressBarComponent(type="progress-bar", value=value, max=max, variant=variant)
	if label:
		component["label"] = label
	return component


def create_image(
	src: Union[str, ValueRef],
	alt: Optional[Union[str, ValueRef]] = None,
	width: Optional[Union[str, ValueRef]] = None,
	height: Optional[Union[str, ValueRef]] = None,
	fit: Literal["cover", "contain", "fill", "none", "scale-down"] = "cover",
	rounded: bool = False
) -> ImageComponent:
	"""Create an image component"""
	component: ImageComponent = ImageComponent(type="image", src=src, fit=fit, rounded=rounded)
	if alt:
		component["alt"] = alt
	if width:
		component["width"] = width
	if height:
		component["height"] = height
	return component


def create_timeline(
	items: Union[List[TimelineItem], ValueRef],
	position: Literal["left", "right", "alternate"] = "left"
) -> TimelineComponent:
	"""Create a timeline component"""
	return TimelineComponent(type="timeline", items=items, position=position)


def create_list(
	items: Union[List[ListItem], ValueRef],
	variant: Literal["default", "bordered", "divided"] = "default",
	hoverable: bool = False
) -> ListComponent:
	"""Create a list component"""
	return ListComponent(type="list", items=items, variant=variant, hoverable=hoverable)


def create_stepper(
	steps: Union[List[StepperStep], ValueRef],
	current_step: Union[int, ValueRef] = 0,
	orientation: Literal["horizontal", "vertical"] = "horizontal"
) -> StepperComponent:
	"""Create a stepper component"""
	return StepperComponent(type="stepper", steps=steps, currentStep=current_step, orientation=orientation)


def create_metric(
	value: Union[str, int, float, ValueRef],
	label: Union[str, ValueRef],
	unit: Optional[Union[str, ValueRef]] = None,
	format: Literal["number", "currency", "percentage", "duration"] = "number",
	trend: Optional[Literal["up", "down", "neutral"]] = None,
	variant: Literal["default", "success", "error", "warning", "info"] = "default"
) -> MetricComponent:
	"""Create a metric component"""
	component: MetricComponent = MetricComponent(type="metric", value=value, label=label, format=format, variant=variant)
	if unit:
		component["unit"] = unit
	if trend:
		component["trend"] = trend
	return component


def create_avatar(
	name: Union[str, ValueRef],
	src: Optional[Union[str, ValueRef]] = None,
	size: Literal["xs", "sm", "md", "lg", "xl"] = "md",
	variant: Literal["circle", "square", "rounded"] = "circle",
	status: Optional[Literal["online", "offline", "away", "busy"]] = None
) -> AvatarComponent:
	"""Create an avatar component"""
	component: AvatarComponent = AvatarComponent(type="avatar", name=name, size=size, variant=variant)
	if src:
		component["src"] = src
	if status:
		component["status"] = status
	return component


def create_callout(
	message: Union[str, ValueRef],
	title: Optional[Union[str, ValueRef]] = None,
	variant: Literal["info", "success", "warning", "error", "neutral"] = "info",
	icon: Optional[Union[str, ValueRef]] = None,
	dismissible: bool = False
) -> CalloutComponent:
	"""Create a callout component"""
	component: CalloutComponent = CalloutComponent(type="callout", message=message, variant=variant, dismissible=dismissible)
	if title:
		component["title"] = title
	if icon:
		component["icon"] = icon
	return component


def create_spacer(
	size: Literal["xs", "sm", "md", "lg", "xl"] = "md",
	orientation: Literal["horizontal", "vertical"] = "vertical"
) -> SpacerComponent:
	"""Create a spacer component"""
	return SpacerComponent(type="spacer", size=size, orientation=orientation)


def create_alert(
	message: Union[str, ValueRef],
	variant: Literal["info", "success", "warning", "error"] = "info",
	dismissible: bool = False
) -> AlertComponent:
	"""Create an alert component"""
	return AlertComponent(type="alert", message=message, variant=variant, dismissible=dismissible)


def create_button(
	label: Union[str, ValueRef],
	action: Union[ActionBuilder, ActionDefinition],
	variant: Literal["primary", "secondary", "danger", "success"] = "primary",
	icon: Optional[Union[str, ValueRef]] = None,
	size: Literal["small", "medium", "large"] = "medium",
	disabled: Union[bool, ValueRef] = False
) -> ButtonComponent:
	"""Create a button component"""
	component: ButtonComponent = ButtonComponent(
		type="button",
		label=label,
		action=action.build() if isinstance(action, ActionBuilder) else action,
		variant=variant,
		size=size,
		disabled=disabled
	)
	if icon:
		component["icon"] = icon
	return component


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


def create_timeline_item(
    title: Union[str, ValueRef],
    description: Optional[Union[str, ValueRef]] = None,
    timestamp: Optional[Union[str, ValueRef]] = None,
    icon: Optional[Union[str, ValueRef]] = None,
    variant: Literal["default", "success", "error", "warning", "info"] = "default"
) -> TimelineItem:
    """Helper to create a timeline item"""
    item: TimelineItem = TimelineItem(title=title)
    if description:
        item["description"] = description
    if timestamp:
        item["timestamp"] = timestamp
    if icon:
        item["icon"] = icon
    item["variant"] = variant
    return item


def create_list_item(
    label: Union[str, ValueRef],
    description: Optional[Union[str, ValueRef]] = None,
    icon: Optional[Union[str, ValueRef]] = None,
    action: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    trailing: Optional[Union[str, ValueRef]] = None
) -> ListItem:
    """Helper to create a list item"""
    item: ListItem = ListItem(label=label)
    if description:
        item["description"] = description
    if icon:
        item["icon"] = icon
    if action:
        item["action"] = action.build() if isinstance(action, ActionBuilder) else action
    if trailing:
        item["trailing"] = trailing
    return item


def create_stepper_step(
    label: Union[str, ValueRef],
    description: Optional[Union[str, ValueRef]] = None,
    status: Literal["pending", "active", "completed", "error"] = "pending"
) -> StepperStep:
    """Helper to create a stepper step"""
    step: StepperStep = StepperStep(label=label, status=status)
    if description:
        step["description"] = description
    return step


def create_breadcrumb_item(
    label: Union[str, ValueRef],
    href: Optional[Union[str, ValueRef]] = None,
    active: bool = False
) -> BreadcrumbItem:
    """Helper to create a breadcrumb item"""
    item: BreadcrumbItem = BreadcrumbItem(label=label, active=active)
    if href:
        item["href"] = href
    return item


def create_breadcrumbs(
    items: Union[List[BreadcrumbItem], ValueRef],
    separator: Optional[Union[str, ValueRef]] = None
) -> BreadcrumbsComponent:
    """Helper to create breadcrumbs component"""
    breadcrumbs: BreadcrumbsComponent = BreadcrumbsComponent(type="breadcrumbs", items=items)
    if separator:
        breadcrumbs["separator"] = separator
    return breadcrumbs


def create_tooltip(
    content: Union[str, ValueRef],
    trigger: ComponentDefinition,
    placement: Literal["top", "bottom", "left", "right"] = "top"
) -> TooltipComponent:
    """Helper to create a tooltip component"""
    return TooltipComponent(type="tooltip", content=content, trigger=trigger, placement=placement)


def create_toggle(
    name: str,
    label: Optional[Union[str, ValueRef]] = None,
    checked: Union[bool, ValueRef] = False,
    disabled: Union[bool, ValueRef] = False,
    on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    size: Literal["sm", "md", "lg"] = "md"
) -> ToggleComponent:
    """Helper to create a toggle/switch component"""
    toggle: ToggleComponent = ToggleComponent(type="toggle", name=name, checked=checked, size=size)
    if label:
        toggle["label"] = label
    if disabled:
        toggle["disabled"] = disabled
    if on_change:
        toggle["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change
    return toggle


def create_chip_input(
    name: str,
    label: Optional[Union[str, ValueRef]] = None,
    value: Optional[Union[List[str], ValueRef]] = None,
    placeholder: Optional[Union[str, ValueRef]] = None,
    max_tags: Optional[int] = None,
    on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None
) -> ChipInputComponent:
    """Helper to create a chip/tag input component"""
    chip_input: ChipInputComponent = ChipInputComponent(type="chip-input", name=name)
    if label:
        chip_input["label"] = label
    if value:
        chip_input["value"] = value
    if placeholder:
        chip_input["placeholder"] = placeholder
    if max_tags:
        chip_input["maxTags"] = max_tags
    if on_change:
        chip_input["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change
    return chip_input


def create_skeleton(
    variant: Literal["text", "circular", "rectangular", "card", "table"] = "text",
    width: Optional[Union[str, ValueRef]] = None,
    height: Optional[Union[str, ValueRef]] = None,
    lines: int = 1,
    rows: int = 3,
    animated: bool = True
) -> SkeletonComponent:
    """Helper to create a skeleton loader component"""
    skeleton: SkeletonComponent = SkeletonComponent(type="skeleton", variant=variant, animated=animated)
    if width:
        skeleton["width"] = width
    if height:
        skeleton["height"] = height
    if variant == "text":
        skeleton["lines"] = lines
    if variant == "table":
        skeleton["rows"] = rows
    return skeleton


def create_dropdown_item(
    label: Union[str, ValueRef],
    action: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    icon: Optional[Union[str, ValueRef]] = None,
    variant: Literal["default", "danger"] = "default",
    divider: bool = False
) -> DropdownMenuItem:
    """Helper to create a dropdown menu item"""
    item: DropdownMenuItem = DropdownMenuItem(label=label, variant=variant, divider=divider)
    if action:
        item["action"] = action.build() if isinstance(action, ActionBuilder) else action
    if icon:
        item["icon"] = icon
    return item


def create_dropdown(
    name: str,
    options: Union[List[Dict[str, Any]], ValueRef],  # Accepts dict for convenience
    label: Optional[Union[str, ValueRef]] = None,
    placeholder: Optional[Union[str, ValueRef]] = None,
    default_value: Optional[Union[Any, ValueRef]] = None,
    searchable: bool = False,
    clearable: bool = False,
    multiple: bool = False,
    on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    disabled: Union[bool, ValueRef] = False
) -> DropdownComponent:
    """Helper to create a dropdown select component"""
    dropdown: DropdownComponent = DropdownComponent(
        type="dropdown",
        name=name,
        options=options,  # type: ignore[typeddict-item]
        searchable=searchable,
        clearable=clearable,
        multiple=multiple,
        disabled=disabled
    )
    if label:
        dropdown["label"] = label
    if placeholder:
        dropdown["placeholder"] = placeholder
    if default_value is not None:
        dropdown["default_value"] = default_value
    if on_change:
        dropdown["on_change"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change
    return dropdown


def create_tree_node(
    id: str,
    label: Union[str, ValueRef],
    icon: Optional[Union[str, ValueRef]] = None,
    children: Optional[List[TreeNode]] = None,
    expanded: bool = False,
    action: Optional[Union[ActionBuilder, ActionDefinition]] = None
) -> TreeNode:
    """Helper to create a tree node"""
    node: TreeNode = TreeNode(id=id, label=label, expanded=expanded)
    if icon:
        node["icon"] = icon
    if children:
        node["children"] = children
    if action:
        node["action"] = action.build() if isinstance(action, ActionBuilder) else action
    return node


def create_tree_view(
    nodes: Union[List[TreeNode], ValueRef],
    expand_all: bool = False,
    show_icons: bool = True
) -> TreeViewComponent:
    """Helper to create a tree view component"""
    return TreeViewComponent(type="tree-view", nodes=nodes, expandAll=expand_all, showIcons=show_icons)


def create_file_upload(
    name: str,
    label: Optional[Union[str, ValueRef]] = None,
    accept: Optional[List[str]] = None,
    multiple: bool = False,
    max_size: Optional[Union[int, str]] = None,
    max_files: Optional[int] = None,
    show_preview: bool = True,
    on_upload: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    on_remove: Optional[Union[ActionBuilder, ActionDefinition]] = None
) -> FileUploadComponent:
    """Helper to create a file upload component"""
    upload: FileUploadComponent = FileUploadComponent(
        type="file-upload",
        name=name,
        multiple=multiple,
        showPreview=show_preview
    )
    if label:
        upload["label"] = label
    if accept is not None:
        upload["accept"] = accept
    if max_size:
        upload["maxSize"] = max_size
    if max_files:
        upload["maxFiles"] = max_files
    if on_upload:
        upload["onUpload"] = on_upload.build() if isinstance(on_upload, ActionBuilder) else on_upload
    if on_remove:
        upload["onRemove"] = on_remove.build() if isinstance(on_remove, ActionBuilder) else on_remove
    return upload


def create_data_grid_column(
    key: str,
    label: Union[str, ValueRef],
    type: Literal["text", "number", "date", "boolean", "select"] = "text",
    editable: bool = True,
    width: Optional[Union[str, ValueRef]] = None,
    options: Optional[List[FormFieldOption]] = None
) -> DataGridColumn:
    """Helper to create a data grid column"""
    column: DataGridColumn = DataGridColumn(key=key, label=label, type=type, editable=editable)
    if width:
        column["width"] = width
    if options:
        column["options"] = options
    return column


def create_data_grid(
    data: Union[List[Any], ValueRef],
    columns: Union[List[DataGridColumn], ValueRef],
    editable: bool = True,
    on_cell_edit: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    on_row_add: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    on_row_delete: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    pagination: Optional[TablePagination] = None
) -> DataGridComponent:
    """Helper to create a data grid component"""
    grid: DataGridComponent = DataGridComponent(type="data-grid", data=data, columns=columns, editable=editable)
    if on_cell_edit:
        grid["onCellEdit"] = on_cell_edit.build() if isinstance(on_cell_edit, ActionBuilder) else on_cell_edit
    if on_row_add:
        grid["onRowAdd"] = on_row_add.build() if isinstance(on_row_add, ActionBuilder) else on_row_add
    if on_row_delete:
        grid["onRowDelete"] = on_row_delete.build() if isinstance(on_row_delete, ActionBuilder) else on_row_delete
    if pagination:
        grid["pagination"] = pagination
    return grid


def create_calendar_event(
    id: str,
    title: Union[str, ValueRef],
    start: Union[str, ValueRef],
    end: Optional[Union[str, ValueRef]] = None,
    all_day: bool = False,
    color: Optional[Union[str, ValueRef]] = None,
    action: Optional[Union[ActionBuilder, ActionDefinition]] = None
) -> CalendarEvent:
    """Helper to create a calendar event"""
    event: CalendarEvent = CalendarEvent(id=id, title=title, start=start, allDay=all_day)
    if end:
        event["end"] = end
    if color:
        event["color"] = color
    if action:
        event["action"] = action.build() if isinstance(action, ActionBuilder) else action
    return event


def create_calendar(
    events: Union[List[CalendarEvent], ValueRef],
    view: Literal["month", "week", "day", "agenda"] = "month",
    on_event_click: Optional[Union[ActionBuilder, ActionDefinition]] = None,
    on_date_click: Optional[Union[ActionBuilder, ActionDefinition]] = None
) -> CalendarComponent:
    """Helper to create a calendar component"""
    calendar: CalendarComponent = CalendarComponent(type="calendar", events=events, view=view)
    if on_event_click:
        calendar["onEventClick"] = on_event_click.build() if isinstance(on_event_click, ActionBuilder) else on_event_click
    if on_date_click:
        calendar["onDateClick"] = on_date_click.build() if isinstance(on_date_click, ActionBuilder) else on_date_click
    return calendar


def create_grid(
    items: Union[List[ComponentDefinition], ValueRef],
    columns: Union[int, str] = 3,
    gap: Optional[Union[str, ValueRef]] = None,
    auto_rows: Optional[Union[str, ValueRef]] = None
) -> GridComponent:
    """Helper to create a grid layout component

    Args:
        items: List of components to display in the grid
        columns: Number of columns (int) or CSS grid-template-columns value (str)
        gap: Gap between grid items (e.g., "1rem", "20px")
        auto_rows: CSS grid-auto-rows value (e.g., "minmax(100px, auto)")

    Example:
        create_grid(
            items=[badge1, badge2, badge3],
            columns=3,
            gap="1rem"
        )
    """
    grid: GridComponent = GridComponent(type="grid", items=items, columns=columns)
    if gap:
        grid["gap"] = gap
    if auto_rows:
        grid["autoRows"] = auto_rows
    return grid


# ============================================================================
# Additional Component Builders
# ============================================================================

class BreadcrumbsBuilder:
	"""Builder for breadcrumbs component"""

	def __init__(self, items: Optional[Union[List[BreadcrumbItem], ValueRef]] = None):
		self.breadcrumbs: BreadcrumbsComponent = BreadcrumbsComponent(type="breadcrumbs", items=items if items is not None else [])

	def add_item(self, label: Union[str, ValueRef], href: Optional[Union[str, ValueRef]] = None, active: bool = False) -> Self:
		"""Add a breadcrumb item"""
		item: BreadcrumbItem = BreadcrumbItem(label=label, active=active)
		if href:
			item["href"] = href
		self.breadcrumbs["items"].append(item)  # type: ignore[index]
		return self

	def set_separator(self, separator: Union[str, ValueRef]) -> Self:
		"""Set breadcrumb separator"""
		self.breadcrumbs["separator"] = separator
		return self

	def build(self) -> BreadcrumbsComponent:
		"""Build the breadcrumbs component"""
		return self.breadcrumbs


class TooltipBuilder:
	"""Builder for tooltip component"""

	def __init__(self, content: Union[str, ValueRef], trigger: ComponentDefinition):
		self.tooltip: TooltipComponent = TooltipComponent(type="tooltip", content=content, trigger=trigger)

	def set_position(self, position: Literal["top", "bottom", "left", "right"]) -> Self:
		"""Set tooltip position"""
		self.tooltip["position"] = position
		return self

	def build(self) -> TooltipComponent:
		"""Build the tooltip component"""
		return self.tooltip


class ToggleBuilder:
	"""Builder for toggle component"""

	def __init__(self, name: str, label: Optional[Union[str, ValueRef]] = None):
		self.toggle: ToggleComponent = ToggleComponent(type="toggle", name=name)
		if label:
			self.toggle["label"] = label

	def set_checked(self, checked: Union[bool, ValueRef]) -> Self:
		"""Set checked state"""
		self.toggle["checked"] = checked
		return self

	def set_disabled(self, disabled: Union[bool, ValueRef]) -> Self:
		"""Set disabled state"""
		self.toggle["disabled"] = disabled
		return self

	def set_size(self, size: Literal["sm", "md", "lg"]) -> Self:
		"""Set toggle size"""
		self.toggle["size"] = size
		return self

	def on_change(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onChange action"""
		self.toggle["onChange"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def build(self) -> ToggleComponent:
		"""Build the toggle component"""
		return self.toggle


class ChipInputBuilder:
	"""Builder for chip input component"""

	def __init__(self, name: str, label: Optional[Union[str, ValueRef]] = None):
		self.chip_input: ChipInputComponent = ChipInputComponent(type="chip-input", name=name)
		if label:
			self.chip_input["label"] = label

	def set_value(self, value: Union[List[str], ValueRef]) -> Self:
		"""Set initial value"""
		self.chip_input["value"] = value
		return self

	def set_placeholder(self, placeholder: Union[str, ValueRef]) -> Self:
		"""Set placeholder"""
		self.chip_input["placeholder"] = placeholder
		return self

	def set_max_tags(self, max_tags: int) -> Self:
		"""Set maximum number of tags"""
		self.chip_input["maxTags"] = max_tags
		return self

	def on_change(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onChange action"""
		self.chip_input["onChange"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def build(self) -> ChipInputComponent:
		"""Build the chip input component"""
		return self.chip_input


class SkeletonBuilder:
	"""Builder for skeleton loader component"""

	def __init__(self, variant: Literal["text", "circular", "rectangular", "card", "table"]):
		self.skeleton: SkeletonComponent = SkeletonComponent(type="skeleton", variant=variant)

	def set_width(self, width: Union[str, ValueRef]) -> Self:
		"""Set skeleton width"""
		self.skeleton["width"] = width
		return self

	def set_height(self, height: Union[str, ValueRef]) -> Self:
		"""Set skeleton height"""
		self.skeleton["height"] = height
		return self

	def set_lines(self, lines: int) -> Self:
		"""Set number of lines (for text variant)"""
		self.skeleton["lines"] = lines
		return self

	def set_rows(self, rows: int) -> Self:
		"""Set number of rows (for table variant)"""
		self.skeleton["rows"] = rows
		return self

	def set_animated(self, animated: bool = True) -> Self:
		"""Enable/disable animation"""
		self.skeleton["animated"] = animated
		return self

	def build(self) -> SkeletonComponent:
		"""Build the skeleton component"""
		return self.skeleton


class DropdownBuilder:
	"""Builder for dropdown component"""

	def __init__(self, name: str, options: Union[List[DropdownOption], ValueRef]):
		self.dropdown: DropdownComponent = DropdownComponent(type="dropdown", name=name, options=options)

	def set_label(self, label: Union[str, ValueRef]) -> Self:
		"""Set dropdown label"""
		self.dropdown["label"] = label
		return self

	def set_placeholder(self, placeholder: Union[str, ValueRef]) -> Self:
		"""Set placeholder"""
		self.dropdown["placeholder"] = placeholder
		return self

	def set_default_value(self, default_value: Union[Any, ValueRef]) -> Self:
		"""Set default value"""
		self.dropdown["default_value"] = default_value
		return self

	def set_searchable(self, searchable: bool = True) -> Self:
		"""Enable/disable search"""
		self.dropdown["searchable"] = searchable
		return self

	def set_clearable(self, clearable: bool = True) -> Self:
		"""Enable/disable clear button"""
		self.dropdown["clearable"] = clearable
		return self

	def set_multiple(self, multiple: bool = True) -> Self:
		"""Enable/disable multiple selection"""
		self.dropdown["multiple"] = multiple
		return self

	def set_disabled(self, disabled: Union[bool, ValueRef]) -> Self:
		"""Set disabled state"""
		self.dropdown["disabled"] = disabled
		return self

	def on_change(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onChange action"""
		self.dropdown["on_change"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def build(self) -> DropdownComponent:
		"""Build the dropdown component"""
		return self.dropdown


class TreeViewBuilder:
	"""Builder for tree view component"""

	def __init__(self, nodes: Union[List[TreeNode], ValueRef]):
		self.tree_view: TreeViewComponent = TreeViewComponent(type="tree-view", nodes=nodes)

	def set_expand_all(self, expand_all: bool = True) -> Self:
		"""Set expand all nodes"""
		self.tree_view["expandAll"] = expand_all
		return self

	def set_show_icons(self, show_icons: bool = True) -> Self:
		"""Enable/disable icons"""
		self.tree_view["showIcons"] = show_icons
		return self

	def build(self) -> TreeViewComponent:
		"""Build the tree view component"""
		return self.tree_view


class FileUploadBuilder:
	"""Builder for file upload component"""

	def __init__(self, name: str):
		self.file_upload: FileUploadComponent = FileUploadComponent(type="file-upload", name=name)

	def set_label(self, label: Union[str, ValueRef]) -> Self:
		"""Set upload label"""
		self.file_upload["label"] = label
		return self

	def set_accept(self, accept: List[str]) -> Self:
		"""Set accepted file types"""
		self.file_upload["accept"] = accept
		return self

	def set_multiple(self, multiple: bool = True) -> Self:
		"""Enable/disable multiple files"""
		self.file_upload["multiple"] = multiple
		return self

	def set_max_size(self, max_size: Union[int, str]) -> Self:
		"""Set maximum file size"""
		self.file_upload["maxSize"] = max_size
		return self

	def set_max_files(self, max_files: int) -> Self:
		"""Set maximum number of files"""
		self.file_upload["maxFiles"] = max_files
		return self

	def set_show_preview(self, show_preview: bool = True) -> Self:
		"""Enable/disable preview"""
		self.file_upload["showPreview"] = show_preview
		return self

	def on_upload(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onUpload action"""
		self.file_upload["onUpload"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def on_remove(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onRemove action"""
		self.file_upload["onRemove"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def build(self) -> FileUploadComponent:
		"""Build the file upload component"""
		return self.file_upload


class DataGridBuilder:
	"""Builder for data grid component"""

	def __init__(self, data: Union[List[Any], ValueRef], columns: Union[List[DataGridColumn], ValueRef]):
		self.data_grid: DataGridComponent = DataGridComponent(type="data-grid", data=data, columns=columns)

	def set_editable(self, editable: bool = True) -> Self:
		"""Enable/disable editing"""
		self.data_grid["editable"] = editable
		return self

	def on_cell_edit(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onCellEdit action"""
		self.data_grid["onCellEdit"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def on_row_add(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onRowAdd action"""
		self.data_grid["onRowAdd"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def on_row_delete(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onRowDelete action"""
		self.data_grid["onRowDelete"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def set_pagination(
		self,
		enabled: bool = True,
		page_size: int = 20,
		mode: Literal["client", "server"] = "client",
		total_items: Optional[Union[int, ValueRef]] = None,
		current_page: Optional[Union[int, ValueRef]] = None,
		on_page_change: Optional[Union[ActionBuilder, ActionDefinition]] = None
	) -> Self:
		"""Configure pagination"""
		pagination = TablePagination(enabled=enabled, pageSize=page_size, mode=mode)
		if total_items is not None:
			pagination["totalItems"] = total_items
		if current_page is not None:
			pagination["currentPage"] = current_page
		if on_page_change is not None:
			pagination["onPageChange"] = on_page_change.build() if isinstance(on_page_change, ActionBuilder) else on_page_change
		self.data_grid["pagination"] = pagination
		return self

	def build(self) -> DataGridComponent:
		"""Build the data grid component"""
		return self.data_grid


class CalendarBuilder:
	"""Builder for calendar component"""

	def __init__(self, events: Union[List[CalendarEvent], ValueRef]):
		self.calendar: CalendarComponent = CalendarComponent(type="calendar", events=events)

	def set_view(self, view: Literal["month", "week", "day", "agenda"]) -> Self:
		"""Set calendar view"""
		self.calendar["view"] = view
		return self

	def on_event_click(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onEventClick action"""
		self.calendar["onEventClick"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def on_date_click(self, action: Union[ActionBuilder, ActionDefinition]) -> Self:
		"""Set onDateClick action"""
		self.calendar["onDateClick"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def build(self) -> CalendarComponent:
		"""Build the calendar component"""
		return self.calendar


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
	) -> Self:
		"""Add a series to the chart"""
		series: ChartSeries = ChartSeries(dataKey=data_key, name=name)
		if color:
			series["color"] = color
		self.chart["config"]["series"].append(series)  # type: ignore[index]
		return self

	def set_x_axis(self, data_key: str, label: Optional[str] = None) -> Self:
		"""Set X axis configuration"""
		self.chart["config"]["xAxis"] = ChartAxis(dataKey=data_key)  # type: ignore[index]
		if label:
			self.chart["config"]["xAxis"]["label"] = label  # type: ignore[index]
		return self

	def set_y_axis(self, label: Optional[str] = None) -> Self:
		"""Set Y axis configuration"""
		self.chart["config"]["yAxis"] = ChartAxis()  # type: ignore[index]
		if label:
			self.chart["config"]["yAxis"]["label"] = label  # type: ignore[index]
		return self

	def set_legend(self, enabled: bool = True) -> Self:
		"""Enable/disable legend"""
		self.chart["config"]["legend"] = enabled  # type: ignore[index]
		return self

	def set_height(self, height: int) -> Self:
		"""Set chart height"""
		self.chart["config"]["height"] = height  # type: ignore[index]
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

	def set_subtitle(self, subtitle: Union[str, ValueRef]) -> Self:
		"""Set card subtitle"""
		self.card["subtitle"] = subtitle
		return self

	def add_component(self, component: ComponentDefinition) -> Self:
		"""Add a component to the card"""
		self.card["content"].append(component)  # type: ignore[index]
		return self

	def add_action(self, action: ButtonComponent) -> Self:
		"""Add an action button to the card"""
		if "actions" not in self.card:
			self.card["actions"] = []
		self.card["actions"].append(action)  # type: ignore[index]
		return self

	def set_variant(self, variant: Literal["default", "outlined", "elevated"]) -> Self:
		"""Set card variant"""
		self.card["variant"] = variant
		return self

	def set_padding(self, padding: Literal["none", "small", "medium", "large"]) -> Self:
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
	) -> Self:
		"""Add an item to the accordion"""
		item: AccordionItem = AccordionItem(
			id=id,
			title=title,
			content=content
		)
		if default_expanded:
			item["defaultExpanded"] = default_expanded
		self.accordion["items"].append(item)  # type: ignore[index]
		return self

	def set_allow_multiple(self, allow_multiple: bool = True) -> Self:
		"""Allow multiple items to be expanded"""
		self.accordion["allowMultiple"] = allow_multiple
		return self

	def set_variant(self, variant: Literal["default", "bordered", "separated"]) -> Self:
		"""Set accordion variant"""
		self.accordion["variant"] = variant
		return self

	def build(self) -> AccordionComponent:
		"""Build the accordion component"""
		return self.accordion

class SectionBuilder:
	"""Builder for section components"""

	def __init__(self, title: Optional[Union[str, ValueRef]] = None, components: Optional[Union[List[ComponentDefinition], ValueRef]] = None):
		self.section: SectionComponent = SectionComponent(components=components if components is not None else [])
		if title:
			self.section["title"] = title

	def add_component(self, component: ComponentDefinition) -> Self:
		"""Add a component to the section"""
		self.section["components"].append(component)  # type: ignore[index]
		return self

	def add_stats_cards(self, stats: List[StatCard], columns: int = 4) -> Self:
		"""Add stats cards component"""
		component: StatsCardsComponent = StatsCardsComponent(
			type="stats-cards",
			stats=stats,
			columns=columns
		)
		self.section["components"].append(component)  # type: ignore[index]
		return self

	def add_info_grid(self, items: List[InfoGridItem], columns: int = 4) -> Self:
		"""Add info grid component"""
		component: InfoGridComponent = InfoGridComponent(
			type="info-grid",
			items=items,
			columns=columns
		)
		self.section["components"].append(component)  # type: ignore[index]
		return self

	def add_code_block(
		self,
		content: Union[str, Dict, ValueRef],
		language: Literal["json", "javascript", "python", "yaml", "text"] = "json",
		copyable: bool = True
	) -> Self:
		"""Add code block component"""
		component: CodeBlockComponent = CodeBlockComponent(
			type="code-block",
			content=content,
			language=language,
			copyable=copyable
		)
		self.section["components"].append(component)  # type: ignore[index]
		return self

	def add_table(self, table_builder: Union[TableBuilder, TableComponent]) -> Self:
		"""Add a table component"""
		self.section["components"].append(table_builder.build() if isinstance(table_builder, TableBuilder) else table_builder)  # type: ignore[index]
		return self

	def add_button(
		self,
		label: str,
		action: ActionBuilder | ActionDefinition,
		variant: Literal["primary", "secondary", "danger", "success"] = "primary",
		**kwargs
	) -> Self:
		"""Add a button component"""
		button: ButtonComponent = ButtonComponent(
			type="button",
			label=label,
			action=action.build() if isinstance(action, ActionBuilder) else action,
			variant=variant
		)
		button.update(kwargs)                      # type: ignore[typeddict-item]
		self.section["components"].append(button)  # type: ignore[index]
		return self

	def add_form(self, form_builder: Union[FormBuilder, FormComponent]) -> Self:
		"""Add a form component"""
		self.section["components"].append(form_builder.build() if isinstance(form_builder, FormBuilder) else form_builder)  # type: ignore[index]
		return self

	def add_chart(self, chart_builder: Union[ChartBuilder, ChartComponent]) -> Self:
		"""Add a chart component"""
		self.section["components"].append(chart_builder.build() if isinstance(chart_builder, ChartBuilder) else chart_builder)  # type: ignore[index]
		return self

	def add_divider(
		self,
		label: Optional[str] = None,
		orientation: Literal["horizontal", "vertical"] = "horizontal",
		variant: Literal["solid", "dashed", "dotted"] = "solid"
	) -> Self:
		"""Add a divider component"""
		self.section["components"].append(create_divider(label, orientation, variant))  # type: ignore[index]
		return self

	def add_badge(
		self,
		label: Union[str, ValueRef],
		variant: Literal["default", "success", "error", "warning", "info", "primary"] = "default",
		size: Literal["small", "medium", "large"] = "medium",
		icon: Optional[str] = None
	) -> Self:
		"""Add a badge component"""
		self.section["components"].append(create_badge(label, variant, size, icon))  # type: ignore[index]
		return self

	def add_progress_bar(
		self,
		value: Union[int, float, ValueRef],
		max: Union[int, float] = 100,
		label: Optional[Union[str, ValueRef]] = None,
		variant: Literal["default", "success", "error", "warning", "info"] = "default"
	) -> Self:
		"""Add a progress bar component"""
		self.section["components"].append(create_progress_bar(value, max, label, variant))  # type: ignore[index]
		return self

	def add_card(self, card_builder: Union[CardBuilder, CardComponent]) -> Self:
		"""Add a card component"""
		self.section["components"].append(card_builder.build() if isinstance(card_builder, CardBuilder) else card_builder)  # type: ignore[index]
		return self

	def add_accordion(self, accordion_builder: Union[AccordionBuilder, AccordionComponent]) -> Self:
		"""Add an accordion component"""
		self.section["components"].append(accordion_builder.build() if isinstance(accordion_builder, AccordionBuilder) else accordion_builder)  # type: ignore[index]
		return self

	def add_image(
		self,
		src: Union[str, ValueRef],
		alt: Optional[Union[str, ValueRef]] = None,
		width: Optional[Union[str, ValueRef]] = None,
		height: Optional[Union[str, ValueRef]] = None,
		fit: Literal["cover", "contain", "fill", "none", "scale-down"] = "cover",
		rounded: bool = False
	) -> Self:
		"""Add an image component"""
		self.section["components"].append(create_image(src, alt, width, height, fit, rounded))  # type: ignore[index]
		return self

	def add_timeline(
		self,
		items: Union[List[TimelineItem], ValueRef],
		position: Literal["left", "right", "alternate"] = "left"
	) -> Self:
		"""Add a timeline component"""
		self.section["components"].append(create_timeline(items, position))  # type: ignore[index]
		return self

	def add_list(
		self,
		items: Union[List[ListItem], ValueRef],
		variant: Literal["default", "bordered", "divided"] = "default",
		hoverable: bool = False
	) -> Self:
		"""Add a list component"""
		self.section["components"].append(create_list(items, variant, hoverable))  # type: ignore[index]
		return self

	def add_stepper(
		self,
		steps: Union[List[StepperStep], ValueRef],
		current_step: Union[int, ValueRef] = 0,
		orientation: Literal["horizontal", "vertical"] = "horizontal"
	) -> Self:
		"""Add a stepper component"""
		self.section["components"].append(create_stepper(steps, current_step, orientation))  # type: ignore[index]
		return self

	def add_metric(
		self,
		value: Union[str, int, float, ValueRef],
		label: Union[str, ValueRef],
		unit: Optional[Union[str, ValueRef]] = None,
		format: Literal["number", "currency", "percentage", "duration"] = "number",
		trend: Optional[Literal["up", "down", "neutral"]] = None,
		variant: Literal["default", "success", "error", "warning", "info"] = "default"
	) -> Self:
		"""Add a metric component"""
		self.section["components"].append(create_metric(value, label, unit, format, trend, variant))  # type: ignore[index]
		return self

	def add_avatar(
		self,
		name: Union[str, ValueRef],
		src: Optional[Union[str, ValueRef]] = None,
		size: Literal["xs", "sm", "md", "lg", "xl"] = "md",
		variant: Literal["circle", "square", "rounded"] = "circle",
		status: Optional[Literal["online", "offline", "away", "busy"]] = None
	) -> Self:
		"""Add an avatar component"""
		self.section["components"].append(create_avatar(name, src, size, variant, status))  # type: ignore[index]
		return self

	def add_callout(
		self,
		message: Union[str, ValueRef],
		title: Optional[Union[str, ValueRef]] = None,
		variant: Literal["info", "success", "warning", "error", "neutral"] = "info",
		icon: Optional[Union[str, ValueRef]] = None,
		dismissible: bool = False
	) -> Self:
		"""Add a callout component"""
		self.section["components"].append(create_callout(message, title, variant, icon, dismissible))  # type: ignore[index]
		return self

	def add_spacer(
		self,
		size: Literal["xs", "sm", "md", "lg", "xl"] = "md",
		orientation: Literal["horizontal", "vertical"] = "vertical"
	) -> Self:
		"""Add a spacer component"""
		self.section["components"].append(create_spacer(size, orientation))  # type: ignore[index]
		return self

	def add_alert(
		self,
		message: Union[str, ValueRef],
		variant: Literal["info", "success", "warning", "error"] = "info",
		dismissible: bool = False
	) -> Self:
		"""Add an alert component"""
		self.section["components"].append(create_alert(message, variant, dismissible))  # type: ignore[index]
		return self

	def add_breadcrumbs(self, breadcrumbs_builder: Union[BreadcrumbsBuilder, BreadcrumbsComponent]) -> Self:
		"""Add a breadcrumbs component"""
		self.section["components"].append(breadcrumbs_builder.build() if isinstance(breadcrumbs_builder, BreadcrumbsBuilder) else breadcrumbs_builder)  # type: ignore[index]
		return self

	def add_tooltip(self, tooltip_builder: Union[TooltipBuilder, TooltipComponent]) -> Self:
		"""Add a tooltip component"""
		self.section["components"].append(tooltip_builder.build() if isinstance(tooltip_builder, TooltipBuilder) else tooltip_builder)  # type: ignore[index]
		return self

	def add_toggle(self, toggle_builder: Union[ToggleBuilder, ToggleComponent]) -> Self:
		"""Add a toggle component"""
		self.section["components"].append(toggle_builder.build() if isinstance(toggle_builder, ToggleBuilder) else toggle_builder)  # type: ignore[index]
		return self

	def add_chip_input(self, chip_input_builder: Union[ChipInputBuilder, ChipInputComponent]) -> Self:
		"""Add a chip input component"""
		self.section["components"].append(chip_input_builder.build() if isinstance(chip_input_builder, ChipInputBuilder) else chip_input_builder)  # type: ignore[index]
		return self

	def add_skeleton(self, skeleton_builder: Union[SkeletonBuilder, SkeletonComponent]) -> Self:
		"""Add a skeleton loader component"""
		self.section["components"].append(skeleton_builder.build() if isinstance(skeleton_builder, SkeletonBuilder) else skeleton_builder)  # type: ignore[index]
		return self

	def add_dropdown(self, dropdown_builder: Union[DropdownBuilder, DropdownComponent]) -> Self:
		"""Add a dropdown component"""
		self.section["components"].append(dropdown_builder.build() if isinstance(dropdown_builder, DropdownBuilder) else dropdown_builder)  # type: ignore[index]
		return self

	def add_tree_view(self, tree_view_builder: Union[TreeViewBuilder, TreeViewComponent]) -> Self:
		"""Add a tree view component"""
		self.section["components"].append(tree_view_builder.build() if isinstance(tree_view_builder, TreeViewBuilder) else tree_view_builder)  # type: ignore[index]
		return self

	def add_file_upload(self, file_upload_builder: Union[FileUploadBuilder, FileUploadComponent]) -> Self:
		"""Add a file upload component"""
		self.section["components"].append(file_upload_builder.build() if isinstance(file_upload_builder, FileUploadBuilder) else file_upload_builder)  # type: ignore[index]
		return self

	def add_data_grid(self, data_grid_builder: Union[DataGridBuilder, DataGridComponent]) -> Self:
		"""Add a data grid component"""
		self.section["components"].append(data_grid_builder.build() if isinstance(data_grid_builder, DataGridBuilder) else data_grid_builder)  # type: ignore[index]
		return self

	def add_calendar(self, calendar_builder: Union[CalendarBuilder, CalendarComponent]) -> Self:
		"""Add a calendar component"""
		self.section["components"].append(calendar_builder.build() if isinstance(calendar_builder, CalendarBuilder) else calendar_builder)  # type: ignore[index]
		return self

	def set_id(self, id: str) -> Self:
		"""Set section ID"""
		self.section["id"] = id
		return self

	def set_collapsible(self, collapsible: bool = True, default_collapsed: bool = False) -> Self:
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

	def add_section(self, section_builder: SectionBuilder | SectionComponent) -> Self:
		"""Add a section to the page"""
		if "sections" not in self.page["layout"]:  # type: ignore[index]
			self.page["layout"]["sections"] = []  # type: ignore[index]
		section = section_builder.build() if isinstance(section_builder, SectionBuilder) else section_builder
		self.page["layout"]["sections"].append(section) # type: ignore[index]
		return self

	def add_modal(self, modal_id: str, modal_builder: ModalBuilder | ModalDefinition) -> Self:
		"""Add a modal definition"""
		if "modals" not in self.page:
			self.page["modals"] = {}
		modal = modal_builder.build() if isinstance(modal_builder, ModalBuilder) else modal_builder
		self.page["modals"][modal_id] = modal
		return self

	def add_panel(self, panel_id: str, panel_builder: PanelBuilder | PanelDefinition) -> Self:
		"""Add a panel definition"""
		if "panels" not in self.page:
			self.page["panels"] = {}
		panel = panel_builder.build() if isinstance(panel_builder, PanelBuilder) else panel_builder
		self.page["panels"][panel_id] = panel
		return self

	def set_layout_type(self, layout_type: Literal["vertical", "horizontal", "grid", "tabs"]) -> Self:
		"""Set the layout type for the page"""
		self.page["layout"]["type"] = layout_type  # type: ignore[index]
		if layout_type == "tabs" and "tabs" not in self.page["layout"]:  # type: ignore[index]
			self.page["layout"]["tabs"] = []  # type: ignore[index]
		return self

	# TODO add_tab
	#def add_tab(self, tab_id: str, label: Union[str, ValueRef], icon: Optional[Union[str, ValueRef]] = None) -> Self:

	def set_realtime(
		self,
		socket_events: Optional[List[SocketEventHandler]] = None,
		polling: Optional[PollingConfig] = None
	) -> Self:
		"""Configure real-time updates"""
		realtime: RealtimeConfig = RealtimeConfig(enabled=True)
		if socket_events:
			realtime["socketEvents"] = socket_events
		if polling:
			realtime["polling"] = polling
		self.page["realtime"] = realtime
		return self

	def add_socket_event(self, event: str, action: ActionBuilder | ActionDefinition) -> Self:
		"""Add a socket event handler"""
		if "realtime" not in self.page:
			self.page["realtime"] = RealtimeConfig(enabled=True, socketEvents=[])
		if "socketEvents" not in self.page["realtime"]:
			self.page["realtime"]["socketEvents"] = []

		handler: SocketEventHandler = SocketEventHandler(
				event=event,
				action=action.build() if isinstance(action, ActionBuilder) else action)
		self.page["realtime"]["socketEvents"].append(handler)  # type: ignore[index]
		return self

	def add_polling(
		self,
		endpoint: Union[str, ValueRef],
		interval: int = 30000,
		action: Optional[ActionBuilder | ActionDefinition] = None
	) -> Self:
		"""Add a polling configuration"""
		if "realtime" not in self.page:
			self.page["realtime"] = RealtimeConfig(enabled=True)

		polling: PollingConfig = PollingConfig(
			endpoint=endpoint,
			interval=interval
		)
		if action: polling["action"] = action.build() if isinstance(action, ActionBuilder) else action

		self.page["realtime"]["polling"] = polling
		return self

	def set_metadata(
		self,
		refresh_interval: Optional[int] = None,
		requires_auth: Optional[bool] = None,
		permissions: Optional[List[str]] = None
	) -> Self:
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



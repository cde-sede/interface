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
		return {"type": "literal", "value": value}

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
		return {"type": "field", "source": source, "path": path}

	@staticmethod
	def computed(template: str, **values: ValueRef | str) -> ValueRef:
		"""Create a computed value reference with template interpolation

		Example:
			ValueRefBuilder.computed("Hello, {name}!", name=ValueRefBuilder.field("form", "name"))
		"""
		return {"type": "computed", "template": template, "values": values}

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
		return {"type": "coalesce", "options": list(options)}  # type: ignore[typeddict-item]

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
		return {"type": "conditional", "condition": condition, "trueValue": true_value, "falseValue": false_value}

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
		return {"type": "transform", "input": input, "transform": transform}

	@staticmethod
	def urlencode(value: Union[ValueRef, Any]) -> ValueRef:
		"""Create a URL encode value reference that encodes a value using encodeURIComponent

		Example:
			# Encode a search query for use in URL
			ValueRefBuilder.urlencode(ValueRefBuilder.field("form", "search"))

			# Encode a literal value
			ValueRefBuilder.urlencode("#empty")
		"""
		return {"type": "urlencode", "encode": value}


class ActionBuilder:
	"""Builder for action definitions"""

	def __init__(self):
		self.action: ActionDefinition = {}

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
		message: Union[str, ValueRef, RichTextComponent],
		toast_type: Literal["success", "error", "info", "warning"] = "info"
	) -> Self:
		"""Configure a show toast action

		Args:
			message: Plain text, ValueRef, or RichTextComponent for formatted text
			toast_type: Toast notification type

		Example:
			# Plain text
			ActionBuilder().show_toast("Success!")

			# With formatting
			ActionBuilder().show_toast(
				create_rich_text("**Success!** Operation completed *successfully*")
			)
		"""
		self.action["type"] = "show-toast"
		self.action["message"] = message
		self.action["toastType"] = toast_type
		return self

	def on_success(self, message: Optional[str] = None, action: Optional['ActionBuilder | ActionDefinition'] = None) -> Self:
		"""Add success handler"""
		success_handler: ActionOnSuccess = {}
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
		error_handler: ActionOnError = {}
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

	def copy_to_clipboard(
		self,
		value: Union[str, ValueRef],
		success_message: Optional[str] = "Copied to clipboard!"
	) -> Self:
		"""Configure a copy to clipboard action

		Args:
			value: Value to copy (can be static string or ValueRef)
			success_message: Optional custom success message

		Examples:
			# Copy static text
			ActionBuilder().copy_to_clipboard("Hello World")

			# Copy field from row
			ActionBuilder().copy_to_clipboard(ref("row", "api_key"))

			# Copy with custom message
			ActionBuilder().copy_to_clipboard(
				ref("response", "token"),
				success_message="API token copied!"
			)
		"""
		self.action["type"] = "copy-to-clipboard"
		self.action["copyValue"] = value
		if success_message:
			self.on_success(message=success_message)
		return self

	def trigger_dynamic(self, trigger_id: str, params: Optional[Dict[str, Any]] = None) -> Self:
		"""Trigger a dynamic component to reload its content

		Args:
			trigger_id: ID of the dynamic component to trigger
			params: Optional params to pass to the component (merged into endpoint query params)

		Examples:
			# Trigger a dynamic component
			ActionBuilder().trigger_dynamic("user-list")

			# Trigger with params (e.g., for pagination)
			ActionBuilder().trigger_dynamic("table-view", params={
				"page": ValueRefBuilder.field("pagination", "pageNumber"),
				"pageSize": ValueRefBuilder.field("pagination", "pageSize")
			})

			# Chain with other actions
			ActionBuilder()
				.api_call("/api/users", method="POST", body={"name": ref("form", "name")})
				.on_success(action=ActionBuilder().trigger_dynamic("user-list"))
		"""
		self.action["type"] = "trigger-dynamic"
		self.action["triggerId"] = trigger_id
		if params:
			self.action["params"] = params
		return self

	def add_rows(
		self,
		target_id: str,
		rows: Union[List[Any], ValueRef],
		success_message: Optional[str] = None
	) -> Self:
		"""Configure an add rows action

		Args:
			target_id: ID of the table/data component to add rows to
			rows: List of rows/data to add (can be ValueRef)
			success_message: Optional success message to show

		Examples:
			# Add static rows
			ActionBuilder().add_rows("my_table", [
				{"name": "John", "age": 30},
				{"name": "Jane", "age": 25}
			])

			# Add rows from API response
			ActionBuilder()
				.api_call("/api/users", "GET")
				.on_success(action=ActionBuilder().add_rows("my_table", {"$ref": "@response.users"}))
		"""
		self.action["type"] = "add-rows"
		self.action["targetId"] = target_id
		self.action["rows"] = rows
		if success_message:
			self.action["onSuccess"] = {
				"message": success_message
			}
		return self

	def build(self) -> ActionDefinition:
		"""Build the action definition"""
		return self.action


class BaseComponentBuilder:
	"""Base builder with common methods for all components

	Provides universal properties:
	- Event handlers (onClick, onHover)
	- Custom styling
	- Visibility control
	- Accessibility attributes
	"""

	def __init__(self):
		self.component: Dict[str, Any] = {}

	def id(self, component_id: str) -> Self:
		"""Set component ID"""
		self.component["id"] = component_id
		return self

	def on_click(
		self,
		action: Union['ActionBuilder', ActionDefinition],
		confirm_message: Optional[Union[str, ValueRef]] = None
	) -> Self:
		"""Add click event handler

		Args:
			action: Action to execute on click
			confirm_message: Optional confirmation message before executing

		Examples:
			.on_click(ActionBuilder().show_toast("Clicked!"))
			.on_click(
				ActionBuilder().api_call("/api/delete", method="DELETE"),
				confirm_message="Are you sure?"
			)
		"""
		if "events" not in self.component:
			self.component["events"] = {}

		if isinstance(action, ActionBuilder):
			self.component["events"]["click"] = action.build()
		else:
			self.component["events"]["click"] = action

		if confirm_message:
			self.component["confirmMessage"] = confirm_message

		return self

	def on_hover(self, action: Union['ActionBuilder', ActionDefinition]) -> Self:
		"""Add hover event handler

		Args:
			action: Action to execute on hover (triggers on mouseenter, clears on mouseleave)

		Examples:
			.on_hover(ActionBuilder().show_toast("Hover!", toast_type="info"))
		"""
		if "events" not in self.component:
			self.component["events"] = {}

		if isinstance(action, ActionBuilder):
			self.component["events"]["hover"] = action.build()
		else:
			self.component["events"]["hover"] = action

		return self

	def style(self, **styles: Any) -> Self:
		"""Add custom CSS styles

		Args:
			**styles: CSS properties in camelCase (e.g., backgroundColor="#f00", padding="1rem")

		Examples:
			.style(backgroundColor="#f0f0f0", padding="1.5rem", borderRadius="8px")
			.style(display="flex", justifyContent="center", alignItems="center")
		"""
		if "customStyle" not in self.component:
			self.component["customStyle"] = {}

		self.component["customStyle"].update(styles)
		return self

	def class_name(self, class_name: Union[str, ValueRef]) -> Self:
		"""Add CSS class name

		Args:
			class_name: CSS class name (can be ValueRef for dynamic classes)

		Examples:
			.class_name("my-custom-class")
			.class_name(ref("row", "statusClass"))
		"""
		self.component["className"] = class_name
		return self

	def visible(self, condition: Union[bool, ValueRef]) -> Self:
		"""Set visibility condition

		Args:
			condition: Boolean or ValueRef that determines visibility

		Examples:
			.visible(True)  # Always visible
			.visible(ref("form", "showAdvanced"))  # Conditional visibility
		"""
		self.component["visible"] = condition
		return self

	def aria_label(self, label: Union[str, ValueRef]) -> Self:
		"""Set ARIA label for accessibility

		Args:
			label: Accessible label for screen readers

		Examples:
			.aria_label("Close dialog")
			.aria_label(ref("row", "userName"))
		"""
		self.component["ariaLabel"] = label
		return self


class TableBuilder(BaseComponentBuilder):
	"""Builder for table components"""

	def __init__(self, data: Union[List[Any], ValueRef], columns: Optional[Union[List[ColumnDefinition], ValueRef]] = None):
		super().__init__()
		self.table: TableComponent = {
			"type": "table",
			"data": data,
			"columns": columns if columns is not None else []
		}
		self.component = self.table

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
		column: ColumnDefinition = {"key": key, "label": label, "type": type}
		if hidden:
			column["hidden"] = hidden
		column.update(kwargs)				 # type: ignore[index]
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
		column: ColumnDefinition = {
			"key": key,
			"label": label,
			"type": "status",
			"renderer": {"type": "status-badge", "config": config}
		}
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

		table_action: TableActionDefinition = {
			"id": id,
			"label": label,
			"action": action.build() if isinstance(action, ActionBuilder) else action
		}
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

		row_action: RowActionDefinition = {
			"id": id,
			"label": label,
			"action": action.build() if isinstance(action, ActionBuilder) else action
		}
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
		pagination: TablePagination = {
			"enabled": enabled,
			"pageSize": page_size,
			"mode": mode,
			"showPageNumbers": show_page_numbers,
			"maxPageButtons": max_page_buttons,
			"showFirstLast": show_first_last,
			"showPrevNext": show_prev_next
		}

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
		empty_state: EmptyStateComponent = {"type": "empty-state", "message": message}
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
		row_click: TableOnRowClick = {"action": action, "target": target}
		if params:
			row_click["params"] = params
		self.table["onRowClick"] = row_click
		return self

	def build(self) -> TableComponent:
		"""Build the table component"""
		return self.table


class FormBuilder(BaseComponentBuilder):
	"""Builder for form components"""

	def __init__(self, submit_action: ActionBuilder | ActionDefinition):
		super().__init__()
		self.form: FormComponent = {
			"type": "form",
			"fields": [],
			"submitAction": submit_action.build() if isinstance(submit_action, ActionBuilder) else submit_action
		}
		self.component = self.form

	def add_field(
		self,
		name: str,
		label: str,
		type: Literal["text", "number", "email", "password", "textarea",
					  "select", "checkbox", "radio", "date", "datetime", "file"] = "text",
		**kwargs
	) -> Self:
		"""Add a field to the form"""
		field: FormFieldDefinition = {"name": name, "label": label, "type": type}
		field.update(kwargs)			   # type: ignore[index]
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
		field: FormFieldDefinition = {
			"name": name,
			"label": label,
			"type": "select",
			"options": options
		}
		field.update(kwargs)			   # type: ignore[index]
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
	"""Builder for creating individual tab items"""

	def __init__(self, id: str, label: Union[str, ValueRef]):
		"""
		Initialize tab builder

		Args:
			id: Unique identifier for the tab
			label: Tab label text
		"""
		self.tab: TabsItem = {
			"id": id,
			"label": label,
			"content": []
		}

	def icon(self, icon: Union[str, ValueRef]) -> Self:
		"""Set tab icon"""
		self.tab["icon"] = icon
		return self

	def disabled(self, disabled: bool = True) -> Self:
		"""Set tab as disabled"""
		self.tab["disabled"] = disabled
		return self

	def add_component(self, component: ComponentDefinition) -> Self:
		"""Add a component to the tab content"""
		self.tab["content"].append(component)
		return self

	def add_components(self, *components: ComponentDefinition) -> Self:
		"""Add multiple components to the tab content"""
		self.tab["content"].extend(components)
		return self

	def build(self) -> TabsItem:
		"""Build the tab item"""
		return self.tab


class TabsBuilder(BaseComponentBuilder):
	"""Builder for tabs component"""

	def __init__(self):
		"""Initialize tabs builder"""
		super().__init__()
		self.tabs: TabsComponent = {
			"type": "tabs",
			"items": []
		}
		self.component = self.tabs

	def add_tab(self, tab: Union[TabBuilder, TabsItem]) -> Self:
		"""Add a tab to the tabs component"""
		if isinstance(tab, TabBuilder):
			self.tabs["items"].append(tab.build())
		else:
			self.tabs["items"].append(tab)
		return self

	def add_tabs(self, *tabs: Union[TabBuilder, TabsItem]) -> Self:
		"""Add multiple tabs"""
		for tab in tabs:
			self.add_tab(tab)
		return self

	def default_tab(self, tab_id: str) -> Self:
		"""Set the default active tab"""
		self.tabs["defaultTab"] = tab_id
		return self

	def variant(self, variant: Literal["default", "pills", "underlined"]) -> Self:
		"""Set tabs variant style"""
		self.tabs["variant"] = variant
		return self

	def orientation(self, orientation: Literal["horizontal", "vertical"]) -> Self:
		"""Set tabs orientation"""
		self.tabs["orientation"] = orientation
		return self

	def build(self) -> TabsComponent:
		"""Build the tabs component"""
		return self.tabs


class ModalBuilder(BaseComponentBuilder):
	"""Builder for modal content"""

	def __init__(self, title: Union[str, ValueRef], size: Literal["small", "medium", "large", "fullscreen"] = "medium"):
		super().__init__()
		self.modal: ModalDefinition = {
			"title": title,
			"content": [],
			"size": size
		}
		self.component = self.modal

	def add_component(self, component: ComponentDefinition) -> Self:
		"""Add a component to the modal"""
		self.modal["content"].append(component)  # type: ignore[index]
		return self

	def add_action(self, label: str, action: ActionBuilder | ActionDefinition, variant: Literal["primary", "secondary", "danger", "success"] = "primary") -> Self:
		"""Add an action button to the modal"""
		if "actions" not in self.modal:
			self.modal["actions"] = []
		button: ButtonComponent = {
			"type": "button",
			"label": label,
			"action": action.build() if isinstance(action, ActionBuilder) else action,
			"variant": variant
		}
		self.modal["actions"].append(button)  # type: ignore[index]
		return self

	def close_on_overlay_click(self, enabled: bool = True) -> Self:
		"""Set whether clicking the overlay closes the modal"""
		self.modal["closeOnOverlayClick"] = enabled
		return self

	def on_close(self, action: ActionBuilder | ActionDefinition) -> Self:
		"""Set action to execute when modal closes"""
		self.modal["onClose"] = action.build() if isinstance(action, ActionBuilder) else action
		return self

	def build(self) -> ModalDefinition:
		"""Build the modal definition"""
		return self.modal


class PanelBuilder(BaseComponentBuilder):
	"""Builder for panel content"""

	def __init__(self, title: Union[str, ValueRef], position: Literal["bottom-right", "bottom-left", "top-right", "top-left"] = "bottom-right", width: Union[str, ValueRef] = "400px", default_open: bool = False):
		super().__init__()
		self.panel: PanelDefinition = PanelDefinition(
			title=title,
			content=[],
			position=position,
			width=width,
			defaultOpen=default_open
		)
		self.component = self.panel

	def add_component(self, component: ComponentDefinition) -> Self:
		"""Add a component to the panel"""
		self.panel["content"].append(component)  # type: ignore[index]
		return self

	def set_width(self, width: Union[str, ValueRef]) -> Self:
		"""Set panel width"""
		self.panel["width"] = width
		return self

	def set_position(self, position: Literal["bottom-right", "bottom-left", "top-right", "top-left"]) -> Self:
		"""Set panel position"""
		self.panel["position"] = position
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
	variant: Literal["solid", "dashed", "dotted"] = "solid",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> DividerComponent:
	"""Create a divider component"""
	component: DividerComponent = DividerComponent(type="divider", orientation=orientation, variant=variant)
	if label:
		component["label"] = label

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_badge(
	label: Union[str, ValueRef],
	variant: Literal["default", "success", "error", "warning", "info", "primary"] = "default",
	size: Literal["small", "medium", "large"] = "medium",
	icon: Optional[str] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> BadgeComponent:
	"""Create a badge component"""
	component: BadgeComponent = BadgeComponent(type="badge", label=label, variant=variant, size=size)
	if icon:
		component["icon"] = icon

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_progress_bar(
	value: Union[int, float, ValueRef],
	max: Union[int, float] = 100,
	label: Optional[Union[str, ValueRef]] = None,
	variant: Literal["default", "success", "error", "warning", "info"] = "default",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> ProgressBarComponent:
	"""Create a progress bar component"""
	component: ProgressBarComponent = ProgressBarComponent(type="progress-bar", value=value, max=max, variant=variant)
	if label:
		component["label"] = label

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_image(
	src: Union[str, ValueRef],
	alt: Optional[Union[str, ValueRef]] = None,
	width: Optional[Union[str, ValueRef]] = None,
	height: Optional[Union[str, ValueRef]] = None,
	fit: Literal["cover", "contain", "fill", "none", "scale-down"] = "cover",
	rounded: bool = False,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None
) -> ImageComponent:
	"""Create an image component

	Args:
		src: Image source URL
		alt: Alt text
		width: Image width
		height: Image height
		fit: Object fit mode
		rounded: Whether to round corners
		custom_style: Custom CSS styles (e.g., {"margin": "0"})
		class_name: CSS class name
		visible: Visibility condition
		events: Event handlers (e.g., {"click": action, "hover": action})

	Example:
		create_image("url.jpg", height="180px",
					custom_style={"margin": "0"},
					events={"click": ActionBuilder().show_toast("Clicked!").build()})
	"""
	component: ImageComponent = ImageComponent(type="image", src=src, fit=fit, rounded=rounded)
	if alt:
		component["alt"] = alt
	if width:
		component["width"] = width
	if height:
		component["height"] = height

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events

	return component


def create_timeline(
	items: Union[List[TimelineItem], ValueRef],
	position: Literal["left", "right", "alternate"] = "left",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> TimelineComponent:
	"""Create a timeline component"""
	component: TimelineComponent = TimelineComponent(type="timeline", items=items, position=position)

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_list(
	items: Union[List[ListItem], ValueRef],
	variant: Literal["default", "bordered", "divided"] = "default",
	hoverable: bool = False,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> ListComponent:
	"""Create a list component"""
	component: ListComponent = ListComponent(type="list", items=items, variant=variant, hoverable=hoverable)

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_stepper(
	steps: Union[List[StepperStep], ValueRef],
	current_step: Union[int, ValueRef] = 0,
	orientation: Literal["horizontal", "vertical"] = "horizontal",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> StepperComponent:
	"""Create a stepper component"""
	component: StepperComponent = StepperComponent(type="stepper", steps=steps, currentStep=current_step, orientation=orientation)

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_metric(
	value: Union[str, int, float, ValueRef],
	label: Union[str, ValueRef],
	unit: Optional[Union[str, ValueRef]] = None,
	format: Literal["number", "currency", "percentage", "duration"] = "number",
	trend: Optional[Literal["up", "down", "neutral"]] = None,
	variant: Literal["default", "success", "error", "warning", "info"] = "default",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> MetricComponent:
	"""Create a metric component"""
	component: MetricComponent = MetricComponent(type="metric", value=value, label=label, format=format, variant=variant)
	if unit:
		component["unit"] = unit
	if trend:
		component["trend"] = trend

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_avatar(
	name: Union[str, ValueRef],
	src: Optional[Union[str, ValueRef]] = None,
	size: Literal["xs", "sm", "md", "lg", "xl"] = "md",
	variant: Literal["circle", "square", "rounded"] = "circle",
	status: Optional[Literal["online", "offline", "away", "busy"]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> AvatarComponent:
	"""Create an avatar component"""
	component: AvatarComponent = AvatarComponent(type="avatar", name=name, size=size, variant=variant)
	if src:
		component["src"] = src
	if status:
		component["status"] = status

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_callout(
	message: Union[str, ValueRef],
	title: Optional[Union[str, ValueRef]] = None,
	variant: Literal["info", "success", "warning", "error", "neutral"] = "info",
	icon: Optional[Union[str, ValueRef]] = None,
	dismissible: bool = False,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> CalloutComponent:
	"""Create a callout component"""
	component: CalloutComponent = CalloutComponent(type="callout", message=message, variant=variant, dismissible=dismissible)
	if title:
		component["title"] = title
	if icon:
		component["icon"] = icon

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_spacer(
	size: Literal["xs", "sm", "md", "lg", "xl"] = "md",
	orientation: Literal["horizontal", "vertical"] = "vertical",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> SpacerComponent:
	"""Create a spacer component"""
	component: SpacerComponent = SpacerComponent(type="spacer", size=size, orientation=orientation)

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_alert(
	message: Union[str, ValueRef],
	variant: Literal["info", "success", "warning", "error"] = "info",
	dismissible: bool = False,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> AlertComponent:
	"""Create an alert component"""
	component: AlertComponent = AlertComponent(type="alert", message=message, variant=variant, dismissible=dismissible)

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_rich_text(
	content: Union[str, ValueRef],
	variant: Literal["body", "small", "large"] = "body",
	align: Literal["left", "center", "right", "justify"] = "left",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> RichTextComponent:
	"""Create a rich text component with markdown-style formatting

	Supports:
	- **bold** text
	- *italic* or _italic_ text
	- `code` text
	- [link text](url)
	- Newlines (\\n)

	Args:
		content: Text content with markdown-style formatting
		variant: Text size variant (body, small, large)
		align: Text alignment (left, center, right, justify)

	Example:
		create_rich_text("Hello **bold** world!\\nNew line with *italic*")
		create_rich_text("Visit [our site](https://example.com) for `code` examples")
	"""
	component: RichTextComponent = RichTextComponent(
		type="rich-text",
		content=content,
		variant=variant,
		align=align
	)

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_button(
	label: Union[str, ValueRef],
	action: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	variant: Literal["primary", "secondary", "danger", "success"] = "primary",
	icon: Optional[Union[str, ValueRef]] = None,
	size: Literal["small", "medium", "large"] = "medium",
	disabled: Union[bool, ValueRef] = False,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None
) -> ButtonComponent:
	"""Create a button component

	Example:
		# Old way (still supported)
		create_button("Click me", ActionBuilder().show_toast("Hello"))

		# New way with events
		create_button(
			"Copy Text",
			events={"click": ActionBuilder().copy_to_clipboard("text").build()}
		)
	"""
	component: ButtonComponent = ButtonComponent(
		type="button",
		label=label,
		variant=variant,
		size=size,
		disabled=disabled
	)

	# Handle action (old way) - action goes directly on button component
	if action:
		component["action"] = action.build() if isinstance(action, ActionBuilder) else action

	if icon:
		component["icon"] = icon

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events

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
	separator: Optional[Union[str, ValueRef]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> BreadcrumbsComponent:
	"""Helper to create breadcrumbs component"""
	breadcrumbs: BreadcrumbsComponent = BreadcrumbsComponent(type="breadcrumbs", items=items)
	if separator:
		breadcrumbs["separator"] = separator

	# Add base component props
	if custom_style:
		breadcrumbs["customStyle"] = custom_style
	if class_name:
		breadcrumbs["className"] = class_name
	if visible is not None:
		breadcrumbs["visible"] = visible
	if events:
		breadcrumbs["events"] = events
	if id:
		breadcrumbs["id"] = id
	if aria_label:
		breadcrumbs["ariaLabel"] = aria_label
	if aria_describedby:
		breadcrumbs["ariaDescribedBy"] = aria_describedby

	return breadcrumbs


def create_tooltip(
	content: Union[str, ValueRef],
	trigger: ComponentDefinition,
	placement: Literal["top", "bottom", "left", "right"] = "top",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> TooltipComponent:
	"""Helper to create a tooltip component"""
	component: TooltipComponent = TooltipComponent(type="tooltip", content=content, trigger=trigger, placement=placement)

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_toggle(
	name: str,
	label: Optional[Union[str, ValueRef]] = None,
	checked: Union[bool, ValueRef] = False,
	disabled: Union[bool, ValueRef] = False,
	on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	size: Literal["sm", "md", "lg"] = "md",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> ToggleComponent:
	"""Helper to create a toggle/switch component"""
	toggle: ToggleComponent = ToggleComponent(type="toggle", name=name, checked=checked, size=size)
	if label:
		toggle["label"] = label
	if disabled:
		toggle["disabled"] = disabled
	if on_change:
		toggle["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change

	# Add base component props
	if custom_style:
		toggle["customStyle"] = custom_style
	if class_name:
		toggle["className"] = class_name
	if visible is not None:
		toggle["visible"] = visible
	if events:
		toggle["events"] = events
	if id:
		toggle["id"] = id
	if aria_label:
		toggle["ariaLabel"] = aria_label
	if aria_describedby:
		toggle["ariaDescribedBy"] = aria_describedby

	return toggle


def create_chip_input(
	name: str,
	label: Optional[Union[str, ValueRef]] = None,
	value: Optional[Union[List[str], ValueRef]] = None,
	placeholder: Optional[Union[str, ValueRef]] = None,
	max_tags: Optional[int] = None,
	on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
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

	# Add base component props
	if custom_style:
		chip_input["customStyle"] = custom_style
	if class_name:
		chip_input["className"] = class_name
	if visible is not None:
		chip_input["visible"] = visible
	if events:
		chip_input["events"] = events
	if id:
		chip_input["id"] = id
	if aria_label:
		chip_input["ariaLabel"] = aria_label
	if aria_describedby:
		chip_input["ariaDescribedBy"] = aria_describedby

	return chip_input


def create_skeleton(
	variant: Literal["text", "circular", "rectangular", "card", "table"] = "text",
	width: Optional[Union[str, ValueRef]] = None,
	height: Optional[Union[str, ValueRef]] = None,
	lines: int = 1,
	rows: int = 3,
	animated: bool = True,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None
) -> SkeletonComponent:
	"""Helper to create a skeleton loader component

	Args:
		variant: Skeleton variant
		width: Width of skeleton
		height: Height of skeleton
		lines: Number of lines for text variant
		rows: Number of rows for table variant
		animated: Whether to animate
		custom_style: Custom CSS styles (e.g., {"margin": "0"})
		class_name: CSS class name
		visible: Visibility condition
		events: Event handlers (e.g., {"click": action, "hover": action})

	Example:
		create_skeleton("rectangular", width="100px", height="100px",
					   custom_style={"margin": "0", "borderRadius": "8px"})
	"""
	skeleton: SkeletonComponent = SkeletonComponent(type="skeleton", variant=variant, animated=animated)
	if width:
		skeleton["width"] = width
	if height:
		skeleton["height"] = height
	if variant == "text":
		skeleton["lines"] = lines
	if variant == "table":
		skeleton["rows"] = rows

	# Add base component props
	if custom_style:
		skeleton["customStyle"] = custom_style
	if class_name:
		skeleton["className"] = class_name
	if visible is not None:
		skeleton["visible"] = visible
	if events:
		skeleton["events"] = events

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
	disabled: Union[bool, ValueRef] = False,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
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

	# Add base component props
	if custom_style:
		dropdown["customStyle"] = custom_style
	if class_name:
		dropdown["className"] = class_name
	if visible is not None:
		dropdown["visible"] = visible
	if events:
		dropdown["events"] = events
	if id:
		dropdown["id"] = id
	if aria_label:
		dropdown["ariaLabel"] = aria_label
	if aria_describedby:
		dropdown["ariaDescribedBy"] = aria_describedby

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
	show_icons: bool = True,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> TreeViewComponent:
	"""Helper to create a tree view component"""
	component: TreeViewComponent = TreeViewComponent(type="tree-view", nodes=nodes, expandAll=expand_all, showIcons=show_icons)

	# Add base component props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_file_upload(
	name: str,
	label: Optional[Union[str, ValueRef]] = None,
	accept: Optional[List[str]] = None,
	multiple: bool = False,
	max_size: Optional[Union[int, str]] = None,
	max_files: Optional[int] = None,
	show_preview: bool = True,
	on_upload: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	on_remove: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
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

	# Add base component props
	if custom_style:
		upload["customStyle"] = custom_style
	if class_name:
		upload["className"] = class_name
	if visible is not None:
		upload["visible"] = visible
	if events:
		upload["events"] = events
	if id:
		upload["id"] = id
	if aria_label:
		upload["ariaLabel"] = aria_label
	if aria_describedby:
		upload["ariaDescribedBy"] = aria_describedby

	return upload


def create_date_picker(
	name: str,
	label: Optional[Union[str, ValueRef]] = None,
	default_value: Optional[Union[str, ValueRef]] = None,
	format: str = "YYYY-MM-DD",
	placeholder: Optional[Union[str, ValueRef]] = None,
	disabled: Union[bool, ValueRef] = False,
	readonly: Union[bool, ValueRef] = False,
	clearable: bool = True,
	min_date: Optional[Union[str, ValueRef]] = None,
	max_date: Optional[Union[str, ValueRef]] = None,
	on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> DatePickerComponent:
	"""Helper to create a date picker component with customizable formatting

	Args:
		name: Form field name
		label: Optional label for the date picker
		default_value: Default date value (ISO string)
		format: Date format string (e.g., "YYYY-MM-DD", "MM/DD/YYYY", "MMMM D, YYYY")
		placeholder: Placeholder text
		disabled: Whether the date picker is disabled
		readonly: Whether the date picker is readonly
		clearable: Whether to show the clear button
		min_date: Minimum selectable date (ISO string)
		max_date: Maximum selectable date (ISO string)
		on_change: Action to execute when date changes

	Returns:
		DatePickerComponent
	"""
	picker: DatePickerComponent = DatePickerComponent(
		type="date-picker",
		name=name,
		format=format,
		clearable=clearable
	)
	if label:
		picker["label"] = label
	if default_value:
		picker["defaultValue"] = default_value
	if placeholder:
		picker["placeholder"] = placeholder
	if disabled:
		picker["disabled"] = disabled
	if readonly:
		picker["readonly"] = readonly
	if min_date:
		picker["minDate"] = min_date
	if max_date:
		picker["maxDate"] = max_date
	if on_change:
		picker["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change

	# Add base component props
	if custom_style:
		picker["customStyle"] = custom_style
	if class_name:
		picker["className"] = class_name
	if visible is not None:
		picker["visible"] = visible
	if events:
		picker["events"] = events
	if id:
		picker["id"] = id
	if aria_label:
		picker["ariaLabel"] = aria_label
	if aria_describedby:
		picker["ariaDescribedBy"] = aria_describedby

	return picker


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
	pagination: Optional[TablePagination] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
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

	# Add base component props
	if custom_style:
		grid["customStyle"] = custom_style
	if class_name:
		grid["className"] = class_name
	if visible is not None:
		grid["visible"] = visible
	if events:
		grid["events"] = events
	if id:
		grid["id"] = id
	if aria_label:
		grid["ariaLabel"] = aria_label
	if aria_describedby:
		grid["ariaDescribedBy"] = aria_describedby

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
	on_date_click: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events_prop: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> CalendarComponent:
	"""Helper to create a calendar component"""
	calendar: CalendarComponent = CalendarComponent(type="calendar", calendarEvents=events, view=view)
	if on_event_click:
		calendar["onEventClick"] = on_event_click.build() if isinstance(on_event_click, ActionBuilder) else on_event_click
	if on_date_click:
		calendar["onDateClick"] = on_date_click.build() if isinstance(on_date_click, ActionBuilder) else on_date_click

	# Add base component props
	if custom_style:
		calendar["customStyle"] = custom_style
	if class_name:
		calendar["className"] = class_name
	if visible is not None:
		calendar["visible"] = visible
	if events_prop:
		calendar["events"] = events_prop
	if id:
		calendar["id"] = id
	if aria_label:
		calendar["ariaLabel"] = aria_label
	if aria_describedby:
		calendar["ariaDescribedBy"] = aria_describedby

	return calendar


def create_grid(
	items: Union[Sequence[ComponentDefinition], ValueRef],
	columns: Union[int, str] = 3,
	gap: Optional[Union[str, ValueRef]] = None,
	auto_rows: Optional[Union[str, ValueRef]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
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

	# Add base component props
	if custom_style:
		grid["customStyle"] = custom_style
	if class_name:
		grid["className"] = class_name
	if visible is not None:
		grid["visible"] = visible
	if events:
		grid["events"] = events
	if id:
		grid["id"] = id
	if aria_label:
		grid["ariaLabel"] = aria_label
	if aria_describedby:
		grid["ariaDescribedBy"] = aria_describedby

	return grid


def create_defer_trigger_immediate() -> DeferTrigger:
	"""Create an immediate defer trigger (loads on mount)"""
	return DeferTrigger(type="immediate")


def create_defer_trigger_intersection(
	root_margin: str = "200px",
	threshold: float = 0.1
) -> DeferTrigger:
	"""Create an intersection observer defer trigger (loads when visible)

	Args:
		root_margin: Margin around viewport (e.g., "200px" loads before entering viewport)
		threshold: 0.0 to 1.0, fraction of element that must be visible to trigger
	"""
	return DeferTrigger(type="intersection", rootMargin=root_margin, threshold=threshold)


def create_defer_trigger_scroll(threshold: int = 500) -> DeferTrigger:
	"""Create a scroll defer trigger (loads after scrolling N pixels)

	Args:
		threshold: Number of pixels from top to trigger load
	"""
	return DeferTrigger(type="scroll", scrollThreshold=threshold)


def create_defer_trigger_action(action_id: str) -> DeferTrigger:
	"""Create an action-based defer trigger (loads when action is triggered)

	Args:
		action_id: ID of the action that triggers the load
	"""
	return DeferTrigger(type="action", actionId=action_id)


def create_defer_trigger_conditional(condition: ValueRef) -> DeferTrigger:
	"""Create a conditional defer trigger (loads when condition is true)

	Args:
		condition: ValueRef that evaluates to boolean
	"""
	return DeferTrigger(type="conditional", condition=condition)


def create_defer(
	endpoint: Union[str, ValueRef],
	method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET",
	params: Optional[Dict[str, Union[ValueRef, Any]]] = None,
	trigger: Optional[DeferTrigger] = None,
	loading_state: Optional[ComponentDefinition] = None,
	error_state: Optional[ComponentDefinition] = None,
	fallback: Optional[Sequence[ComponentDefinition]] = None,
	cache_enabled: bool = False,
	cache_ttl: Optional[int] = None,
	body: Optional[Dict[str, Any]] = None,
	headers: Optional[Dict[str, str]] = None,
	# Action hooks
	on_trigger: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	on_load: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	on_error: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> DeferComponent:
	"""Create a defer component for lazy loading DSL content

	Args:
		endpoint: URL to fetch deferred content from (use "#" to trigger hooks without fetching)
		method: HTTP method (GET, POST, PUT, DELETE, PATCH)
		params: Query parameters to append to endpoint (?key=value&key2=value2)
		trigger: Trigger configuration (defaults to immediate)
		loading_state: Component to show while loading
		error_state: Component to show on error
		fallback: Fallback components if load fails
		cache_enabled: Enable caching of loaded content
		cache_ttl: Cache time-to-live in milliseconds
		body: Request body for POST/PUT/PATCH
		headers: Custom HTTP headers
		on_trigger: Action to execute when defer is triggered (before fetching)
		on_load: Action to execute when content successfully loads
		on_error: Action to execute when loading fails

	Example:
		# Load content when visible in viewport
		create_defer(
			endpoint="/api/heavy-content",
			trigger=create_defer_trigger_intersection(root_margin="100px"),
			loading_state=create_skeleton(variant="text", count=3),
			cache_enabled=True,
			cache_ttl=60000  # 1 minute
		)

		# Load content with action hooks
		create_defer(
			endpoint="/api/details",
			trigger=create_defer_trigger_action("load-details"),
			on_trigger=ActionBuilder().show_toast("Loading...", toast_type="info"),
			on_load=ActionBuilder().show_toast("Loaded!", toast_type="success"),
			on_error=ActionBuilder().show_toast("Failed to load", toast_type="error")
		)

		# Trigger actions without fetching (endpoint="#")
		create_defer(
			endpoint="#",
			trigger=create_defer_trigger_action("refresh-data"),
			on_trigger=ActionBuilder().api_call("/api/refresh", method="POST"),
			on_load=ActionBuilder().show_toast("Data refreshed!", toast_type="success")
		)
	"""
	defer: DeferComponent = DeferComponent(type="defer", endpoint=endpoint, method=method)

	if params:
		defer["params"] = params

	if trigger:
		defer["trigger"] = trigger

	if loading_state:
		defer["loadingState"] = loading_state

	if error_state:
		defer["errorState"] = error_state

	if fallback:
		defer["fallback"] = fallback

	if cache_enabled:
		cache_config: DeferCache = DeferCache(enabled=True)
		if cache_ttl is not None:
			cache_config["ttl"] = cache_ttl
		defer["cache"] = cache_config

	if body:
		defer["body"] = body

	if headers:
		defer["headers"] = headers

	# Add action hooks
	if on_trigger:
		defer["onTrigger"] = on_trigger.build() if isinstance(on_trigger, ActionBuilder) else on_trigger
	if on_load:
		defer["onLoad"] = on_load.build() if isinstance(on_load, ActionBuilder) else on_load
	if on_error:
		defer["onError"] = on_error.build() if isinstance(on_error, ActionBuilder) else on_error

	# Add base component props
	if custom_style:
		defer["customStyle"] = custom_style
	if class_name:
		defer["className"] = class_name
	if visible is not None:
		defer["visible"] = visible
	if events:
		defer["events"] = events
	if id:
		defer["id"] = id
	if aria_label:
		defer["ariaLabel"] = aria_label
	if aria_describedby:
		defer["ariaDescribedBy"] = aria_describedby

	return defer


def create_dynamic(
	trigger_id: str,
	endpoint: Union[str, ValueRef],
	method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET",
	params: Optional[Dict[str, Union[ValueRef, Any]]] = None,
	initial_content: Optional[Sequence[ComponentDefinition]] = None,
	loading_state: Optional[ComponentDefinition] = None,
	error_state: Optional[ComponentDefinition] = None,
	body: Optional[Dict[str, Any]] = None,
	headers: Optional[Dict[str, str]] = None,
	# Action hooks
	on_trigger: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	on_load: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	on_error: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> DynamicComponent:
	"""Create a dynamic component for action-triggered reloadable content

	Similar to Defer but designed for repeated triggering:
	- Triggered by action IDs
	- Can be triggered multiple times
	- Each trigger replaces the content (not appends)
	- No caching - always fetches fresh content

	Args:
		trigger_id: Action ID that triggers content loading
		endpoint: URL to fetch content from
		method: HTTP method (GET, POST, PUT, DELETE, PATCH)
		params: Query parameters to append to endpoint (?key=value&key2=value2)
		initial_content: Initial content before first trigger
		loading_state: Component to show while loading
		error_state: Component to show on error
		body: Request body for POST/PUT/PATCH
		headers: Custom HTTP headers
		on_trigger: Action to execute when triggered (before fetching)
		on_load: Action to execute when content successfully loads
		on_error: Action to execute when loading fails

	Example:
		# Create a dynamic user list that can be refreshed
		user_list = create_dynamic(
			trigger_id="refresh-users",
			endpoint="/api/users",
			loading_state=create_skeleton(variant="text", count=5),
			error_state=create_alert(message="Failed to load users", variant="error")
		)

		# Trigger it with a button
		refresh_button = create_button(
			label="Refresh Users",
			action=ActionBuilder().trigger_dynamic("refresh-users")
		)

		# Or chain after an action
		add_user_button = create_button(
			label="Add User",
			action=ActionBuilder()
				.api_call("/api/users", method="POST", body={"name": ref("form", "name")})
				.on_success(action=ActionBuilder().trigger_dynamic("refresh-users"))
		)
	"""
	dynamic: DynamicComponent = DynamicComponent(
		type="dynamic",
		triggerId=trigger_id,
		endpoint=endpoint,
		method=method
	)

	if params:
		dynamic["params"] = params

	if initial_content:
		dynamic["initialContent"] = list(initial_content)

	if loading_state:
		dynamic["loadingState"] = loading_state

	if error_state:
		dynamic["errorState"] = error_state

	if body:
		dynamic["body"] = body

	if headers:
		dynamic["headers"] = headers

	# Add action hooks
	if on_trigger:
		dynamic["onTrigger"] = on_trigger.build() if isinstance(on_trigger, ActionBuilder) else on_trigger
	if on_load:
		dynamic["onLoad"] = on_load.build() if isinstance(on_load, ActionBuilder) else on_load
	if on_error:
		dynamic["onError"] = on_error.build() if isinstance(on_error, ActionBuilder) else on_error

	# Add base component props
	if custom_style:
		dynamic["customStyle"] = custom_style
	if class_name:
		dynamic["className"] = class_name
	if visible is not None:
		dynamic["visible"] = visible
	if events:
		dynamic["events"] = events
	if id:
		dynamic["id"] = id
	if aria_label:
		dynamic["ariaLabel"] = aria_label
	if aria_describedby:
		dynamic["ariaDescribedBy"] = aria_describedby

	return dynamic


# ============================================================================
# Additional Component Builders
# ============================================================================

class BreadcrumbsBuilder(BaseComponentBuilder):
	"""Builder for breadcrumbs component"""

	def __init__(self, items: Optional[Union[List[BreadcrumbItem], ValueRef]] = None):
		super().__init__()
		self.breadcrumbs: BreadcrumbsComponent = BreadcrumbsComponent(type="breadcrumbs", items=items if items is not None else [])
		self.component = self.breadcrumbs

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


class TooltipBuilder(BaseComponentBuilder):
	"""Builder for tooltip component"""

	def __init__(self, content: Union[str, ValueRef], trigger: ComponentDefinition):
		super().__init__()
		self.tooltip: TooltipComponent = TooltipComponent(type="tooltip", content=content, trigger=trigger)
		self.component = self.tooltip

	def set_position(self, position: Literal["top", "bottom", "left", "right"]) -> Self:
		"""Set tooltip position"""
		self.tooltip["position"] = position
		return self

	def build(self) -> TooltipComponent:
		"""Build the tooltip component"""
		return self.tooltip


class ToggleBuilder(BaseComponentBuilder):
	"""Builder for toggle component"""

	def __init__(self, name: str, label: Optional[Union[str, ValueRef]] = None):
		super().__init__()
		self.toggle: ToggleComponent = ToggleComponent(type="toggle", name=name)
		if label:
			self.toggle["label"] = label
		self.component = self.toggle

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


class ChipInputBuilder(BaseComponentBuilder):
	"""Builder for chip input component"""

	def __init__(self, name: str, label: Optional[Union[str, ValueRef]] = None):
		super().__init__()
		self.chip_input: ChipInputComponent = ChipInputComponent(type="chip-input", name=name)
		if label:
			self.chip_input["label"] = label
		self.component = self.chip_input

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


class SkeletonBuilder(BaseComponentBuilder):
	"""Builder for skeleton loader component"""

	def __init__(self, variant: Literal["text", "circular", "rectangular", "card", "table"]):
		super().__init__()
		self.skeleton: SkeletonComponent = SkeletonComponent(type="skeleton", variant=variant)
		self.component = self.skeleton

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


class DropdownBuilder(BaseComponentBuilder):
	"""Builder for dropdown component"""

	def __init__(self, name: str, options: Union[List[DropdownOption], ValueRef]):
		super().__init__()
		self.dropdown: DropdownComponent = DropdownComponent(type="dropdown", name=name, options=options)
		self.component = self.dropdown

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


class TreeViewBuilder(BaseComponentBuilder):
	"""Builder for tree view component"""

	def __init__(self, nodes: Union[List[TreeNode], ValueRef]):
		super().__init__()
		self.tree_view: TreeViewComponent = TreeViewComponent(type="tree-view", nodes=nodes)
		self.component = self.tree_view

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


class FileUploadBuilder(BaseComponentBuilder):
	"""Builder for file upload component"""

	def __init__(self, name: str):
		super().__init__()
		self.file_upload: FileUploadComponent = FileUploadComponent(type="file-upload", name=name)
		self.component = self.file_upload

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


class DataGridBuilder(BaseComponentBuilder):
	"""Builder for data grid component"""

	def __init__(self, data: Union[List[Any], ValueRef], columns: Union[List[DataGridColumn], ValueRef]):
		super().__init__()
		self.data_grid: DataGridComponent = DataGridComponent(type="data-grid", data=data, columns=columns)
		self.component = self.data_grid

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


class CalendarBuilder(BaseComponentBuilder):
	"""Builder for calendar component"""

	def __init__(self, events: Union[List[CalendarEvent], ValueRef]):
		super().__init__()
		self.calendar: CalendarComponent = CalendarComponent(type="calendar", events=events)
		self.component = self.calendar

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


class GridBuilder(BaseComponentBuilder):
	"""Builder for CSS Grid layout components

	Provides a flexible way to create grid layouts with dynamic item addition.

	Example:
		grid = (GridBuilder(columns=3, gap="1rem")
			.add_item(badge1)
			.add_item(badge2)
			.add_item(badge3)
			.style(padding="2rem")
			.build())
	"""

	def __init__(
		self,
		columns: Union[int, str] = 3,
		gap: Optional[Union[str, ValueRef]] = None,
		auto_rows: Optional[Union[str, ValueRef]] = None
	):
		super().__init__()
		self.grid: GridComponent = GridComponent(
			type="grid",
			items=[],
			columns=columns
		)
		if gap:
			self.grid["gap"] = gap
		if auto_rows:
			self.grid["autoRows"] = auto_rows
		self.component = self.grid

	def add_item(self, item: ComponentDefinition) -> Self:
		"""Add a single item to the grid"""
		if not isinstance(self.grid["items"], list):
			self.grid["items"] = []
		self.grid["items"].append(item)  # type: ignore[union-attr]
		return self

	def add_items(self, items: Sequence[ComponentDefinition]) -> Self:
		"""Add multiple items to the grid"""
		if not isinstance(self.grid["items"], list):
			self.grid["items"] = []
		self.grid["items"].extend(items)  # type: ignore[union-attr]
		return self

	def set_items(self, items: Union[Sequence[ComponentDefinition], ValueRef]) -> Self:
		"""Set the grid items (replaces existing items)"""
		self.grid["items"] = items
		return self

	def columns(self, columns: Union[int, str]) -> Self:
		"""Set the number of columns or CSS grid-template-columns value

		Args:
			columns: Number of columns (int) or CSS value like "1fr 2fr 1fr"
		"""
		self.grid["columns"] = columns
		return self

	def gap(self, gap: Union[str, ValueRef]) -> Self:
		"""Set the gap between grid items (e.g., "1rem", "20px")"""
		self.grid["gap"] = gap
		return self

	def auto_rows(self, auto_rows: Union[str, ValueRef]) -> Self:
		"""Set CSS grid-auto-rows value (e.g., "minmax(100px, auto)")"""
		self.grid["autoRows"] = auto_rows
		return self

	def build(self) -> GridComponent:
		"""Build the grid component"""
		return self.grid


class FlexBuilder(BaseComponentBuilder):
	"""Builder for flexbox layout components

	Provides a flexible way to create flex layouts with dynamic item addition.

	Example:
		flex = (FlexBuilder(direction="row", justify="space-between", gap="1rem")
			.add_item(button1)
			.add_item(button2)
			.add_item(button3)
			.build())
	"""

	def __init__(
		self,
		direction: Literal["row", "column", "row-reverse", "column-reverse"] = "row",
		justify: Literal["flex-start", "flex-end", "center", "space-between", "space-around", "space-evenly"] = "flex-start",
		align: Literal["flex-start", "flex-end", "center", "baseline", "stretch"] = "stretch",
		wrap: Literal["nowrap", "wrap", "wrap-reverse"] = "nowrap",
		gap: Optional[Union[str, ValueRef]] = None
	):
		super().__init__()
		self.flex: FlexComponent = FlexComponent(
			type="flex",
			items=[],
			direction=direction,
			justify=justify,
			align=align,
			wrap=wrap
		)
		if gap:
			self.flex["gap"] = gap
		self.component = self.flex

	def add_item(self, item: ComponentDefinition) -> Self:
		"""Add a single item to the flex container"""
		if not isinstance(self.flex["items"], list):
			self.flex["items"] = []
		self.flex["items"].append(item)  # type: ignore[union-attr]
		return self

	def add_items(self, items: Sequence[ComponentDefinition]) -> Self:
		"""Add multiple items to the flex container"""
		if not isinstance(self.flex["items"], list):
			self.flex["items"] = []
		self.flex["items"].extend(items)  # type: ignore[union-attr]
		return self

	def set_items(self, items: Union[Sequence[ComponentDefinition], ValueRef]) -> Self:
		"""Set the flex items (replaces existing items)"""
		self.flex["items"] = items
		return self

	def direction(self, direction: Literal["row", "column", "row-reverse", "column-reverse"]) -> Self:
		"""Set the flex direction"""
		self.flex["direction"] = direction
		return self

	def justify(self, justify: Literal["flex-start", "flex-end", "center", "space-between", "space-around", "space-evenly"]) -> Self:
		"""Set justify-content"""
		self.flex["justify"] = justify
		return self

	def align(self, align: Literal["flex-start", "flex-end", "center", "baseline", "stretch"]) -> Self:
		"""Set align-items"""
		self.flex["align"] = align
		return self

	def wrap(self, wrap: Literal["nowrap", "wrap", "wrap-reverse"]) -> Self:
		"""Set flex-wrap"""
		self.flex["wrap"] = wrap
		return self

	def gap(self, gap: Union[str, ValueRef]) -> Self:
		"""Set the gap between items (e.g., "1rem", "20px")"""
		self.flex["gap"] = gap
		return self

	def build(self) -> FlexComponent:
		"""Build the flex component"""
		return self.flex


class ContainerBuilder(BaseComponentBuilder):
	"""Builder for container/wrapper components

	Provides a way to wrap content with max-width and padding constraints.

	Example:
		container = (ContainerBuilder(max_width="1200px", centered=True)
			.add_child(header)
			.add_child(content)
			.padding("2rem")
			.build())
	"""

	def __init__(
		self,
		max_width: Optional[Union[str, ValueRef]] = None,
		padding: Optional[Union[str, ValueRef]] = None,
		centered: bool = False
	):
		super().__init__()
		self.container: ContainerComponent = ContainerComponent(
			type="container",
			children=[],
			centered=centered
		)
		if max_width:
			self.container["maxWidth"] = max_width
		if padding:
			self.container["padding"] = padding
		self.component = self.container

	def add_child(self, child: ComponentDefinition) -> Self:
		"""Add a single child to the container"""
		if not isinstance(self.container["children"], list):
			self.container["children"] = []
		self.container["children"].append(child)  # type: ignore[union-attr]
		return self

	def add_children(self, children: Sequence[ComponentDefinition]) -> Self:
		"""Add multiple children to the container"""
		if not isinstance(self.container["children"], list):
			self.container["children"] = []
		self.container["children"].extend(children)  # type: ignore[union-attr]
		return self

	def set_children(self, children: Union[Sequence[ComponentDefinition], ValueRef]) -> Self:
		"""Set the container children (replaces existing children)"""
		self.container["children"] = children
		return self

	def max_width(self, max_width: Union[str, ValueRef]) -> Self:
		"""Set the maximum width of the container"""
		self.container["maxWidth"] = max_width
		return self

	def padding(self, padding: Union[str, ValueRef]) -> Self:
		"""Set the padding inside the container"""
		self.container["padding"] = padding
		return self

	def centered(self, centered: bool = True) -> Self:
		"""Center the container horizontally"""
		self.container["centered"] = centered
		return self

	def build(self) -> ContainerComponent:
		"""Build the container component"""
		return self.container


class ChartBuilder(BaseComponentBuilder):
	"""Builder for chart components"""

	def __init__(
		self,
		chart_type: Literal["bar", "line", "pie", "area", "scatter"],
		data: Union[List[Any], ValueRef]
	):
		super().__init__()
		self.chart: ChartComponent = ChartComponent(
			type="chart",
			chartType=chart_type,
			data=data,
			config=ChartConfig(series=[])
		)
		self.component = self.chart

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


class CardBuilder(BaseComponentBuilder):
	"""Builder for card components"""

	def __init__(self, title: Optional[Union[str, ValueRef]] = None, content: Optional[Union[Sequence[ComponentDefinition], ValueRef]] = None):
		super().__init__()
		self.card: CardComponent = CardComponent(type="card", content=content if content is not None else [])
		if title:
			self.card["title"] = title
		self.component = self.card

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


class AccordionBuilder(BaseComponentBuilder):
	"""Builder for accordion components"""

	def __init__(self, items: Optional[Union[List[AccordionItem], ValueRef]] = None):
		super().__init__()
		self.accordion: AccordionComponent = AccordionComponent(type="accordion", items=items if items is not None else [])
		self.component = self.accordion

	def add_item(
		self,
		id: str,
		title: Union[str, ValueRef],
		content: Union[Sequence[ComponentDefinition], ValueRef],
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

class SectionBuilder(BaseComponentBuilder):
	"""Builder for section components"""

	def __init__(self, title: Optional[Union[str, ValueRef]] = None, components: Optional[Union[Sequence[ComponentDefinition], ValueRef]] = None):
		super().__init__()
		self.section: SectionComponent = SectionComponent(components=components if components is not None else [])
		if title:
			self.section["title"] = title
		self.component = self.section

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
		button.update(kwargs)					  # type: ignore[typeddict-item]
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


class LayoutBuilder(BaseComponentBuilder):
	"""Builder for page layout configuration

	Creates layouts for organizing page sections in different arrangements:
	- vertical: Stack sections vertically (default)
	- horizontal: Arrange sections side-by-side
	- grid: Grid layout for sections
	- tabs: Tabbed interface for sections

	Example:
		# Vertical layout
		layout = LayoutBuilder("vertical", gap="2rem")
			.add_section(section1)
			.add_section(section2)
			.build()

		# Tabs layout
		layout = LayoutBuilder("tabs")
			.add_tab("overview", "Overview", icon="home", sections=[section1])
			.add_tab("details", "Details", icon="info", sections=[section2])
			.build()
	"""

	def __init__(
		self,
		layout_type: Literal["vertical", "horizontal", "grid", "tabs"] = "vertical",
		gap: Optional[str] = None
	):
		super().__init__()
		self.layout: LayoutComponent = LayoutComponent(
			type=layout_type,
			sections=[]
		)
		if gap:
			self.layout["gap"] = gap
		if layout_type == "tabs":
			self.layout["tabs"] = []
		self.component = self.layout

	def add_section(self, section: Union[SectionBuilder, SectionComponent]) -> Self:
		"""Add a section to the layout"""
		if "sections" not in self.layout:
			self.layout["sections"] = []
		built_section = section.build() if isinstance(section, SectionBuilder) else section
		self.layout["sections"].append(built_section)  # type: ignore[union-attr]
		return self

	def add_sections(self, sections: Sequence[Union[SectionBuilder, SectionComponent]]) -> Self:
		"""Add multiple sections to the layout"""
		for section in sections:
			self.add_section(section)
		return self

	def add_tab(
		self,
		tab_id: str,
		label: Union[str, ValueRef],
		sections: Optional[Sequence[Union[SectionBuilder, SectionComponent]]] = None,
		icon: Optional[Union[str, ValueRef]] = None,
		disabled: bool = False
	) -> Self:
		"""Add a tab to the layout (only for tabs layout type)

		Args:
			tab_id: Unique identifier for the tab
			label: Tab label text
			sections: Sections to display in this tab
			icon: Optional icon for the tab
			disabled: Whether the tab is disabled
		"""
		if self.layout["type"] != "tabs":
			raise ValueError("add_tab() can only be used with 'tabs' layout type")

		if "tabs" not in self.layout:
			self.layout["tabs"] = []

		# Build sections
		built_sections = []
		if sections:
			for section in sections:
				built_sections.append(section.build() if isinstance(section, SectionBuilder) else section)

		tab: TabDefinition = TabDefinition(
			id=tab_id,
			label=label,
			sections=built_sections
		)
		if icon:
			tab["icon"] = icon
		if disabled:
			tab["disabled"] = disabled

		self.layout["tabs"].append(tab)  # type: ignore[union-attr]
		return self

	def gap(self, gap: str) -> Self:
		"""Set the gap between sections/tabs"""
		self.layout["gap"] = gap
		return self

	def build(self) -> LayoutComponent:
		"""Build the layout component"""
		return self.layout


class PageBuilder(BaseComponentBuilder):
	"""Builder for page DSL"""

	def __init__(self, title: Union[str, ValueRef], description: Optional[Union[str, ValueRef]] = None):
		super().__init__()
		self.page: PageDSL = PageDSL(
			type="page",
			title=title,
			layout=LayoutComponent(type="vertical", sections=[])
		)
		if description:
			self.page["description"] = description
		self.component = self.page

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

	def set_layout(self, layout: Union[LayoutBuilder, LayoutComponent]) -> Self:
		"""Set a custom layout for the page

		Args:
			layout: A LayoutBuilder or LayoutComponent to use as the page layout

		Example:
			page = PageBuilder("My Page")
				.set_layout(
					LayoutBuilder("tabs")
						.add_tab("overview", "Overview", sections=[section1])
						.add_tab("details", "Details", sections=[section2])
				)
				.build()
		"""
		self.page["layout"] = layout.build() if isinstance(layout, LayoutBuilder) else layout
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


# ============================================================================
# Standalone Input Component Builders
# ============================================================================

def create_text_input(
	name: str,
	label: Optional[Union[str, ValueRef]] = None,
	placeholder: Optional[Union[str, ValueRef]] = None,
	default_value: Optional[Union[str, ValueRef]] = None,
	input_type: Literal["text", "email", "password", "url", "tel", "search"] = "text",
	required: Union[bool, ValueRef] = False,
	disabled: Union[bool, ValueRef] = False,
	read_only: Union[bool, ValueRef] = False,
	max_length: Optional[int] = None,
	min_length: Optional[int] = None,
	pattern: Optional[str] = None,
	on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	on_blur: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	helper_text: Optional[Union[str, ValueRef]] = None,
	error_text: Optional[Union[str, ValueRef]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> TextInputComponent:
	"""Create a text input component

	Args:
		name: Input field name
		label: Optional label
		placeholder: Placeholder text
		default_value: Default value
		input_type: Type of input (text, email, password, url, tel, search)
		required: Whether input is required
		disabled: Whether input is disabled
		read_only: Whether input is readonly
		max_length: Maximum length
		min_length: Minimum length
		pattern: Regex pattern for validation
		on_change: Action to execute when value changes
		on_blur: Action to execute when input loses focus
		helper_text: Helper text shown below input
		error_text: Error text shown when validation fails

	Example:
		create_text_input(
			name="email",
			label="Email Address",
			input_type="email",
			placeholder="Enter your email",
			required=True,
			on_change=ActionBuilder().show_toast("Email changed")
		)
	"""
	component: TextInputComponent = TextInputComponent(
		type="text-input",
		name=name,
		inputType=input_type,
		required=required,
		disabled=disabled,
		readOnly=read_only
	)

	if label:
		component["label"] = label
	if placeholder:
		component["placeholder"] = placeholder
	if default_value is not None:
		component["defaultValue"] = default_value
	if max_length is not None:
		component["maxLength"] = max_length
	if min_length is not None:
		component["minLength"] = min_length
	if pattern:
		component["pattern"] = pattern
	if on_change:
		component["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change
	if on_blur:
		component["onBlur"] = on_blur.build() if isinstance(on_blur, ActionBuilder) else on_blur
	if helper_text:
		component["helperText"] = helper_text
	if error_text:
		component["errorText"] = error_text

	# Base props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_number_input(
	name: str,
	label: Optional[Union[str, ValueRef]] = None,
	placeholder: Optional[Union[str, ValueRef]] = None,
	default_value: Optional[Union[int, float, ValueRef]] = None,
	min: Optional[Union[int, float]] = None,
	max: Optional[Union[int, float]] = None,
	step: Optional[Union[int, float]] = None,
	required: Union[bool, ValueRef] = False,
	disabled: Union[bool, ValueRef] = False,
	read_only: Union[bool, ValueRef] = False,
	on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	on_blur: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	helper_text: Optional[Union[str, ValueRef]] = None,
	error_text: Optional[Union[str, ValueRef]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> NumberInputComponent:
	"""Create a number input component

	Args:
		name: Input field name
		label: Optional label
		placeholder: Placeholder text
		default_value: Default numeric value
		min: Minimum value
		max: Maximum value
		step: Step increment
		required: Whether input is required
		disabled: Whether input is disabled
		read_only: Whether input is readonly
		on_change: Action to execute when value changes
		on_blur: Action to execute when input loses focus
		helper_text: Helper text shown below input
		error_text: Error text shown when validation fails

	Example:
		create_number_input(
			name="age",
			label="Age",
			min=0,
			max=120,
			step=1,
			required=True
		)
	"""
	component: NumberInputComponent = NumberInputComponent(
		type="number-input",
		name=name,
		required=required,
		disabled=disabled,
		readOnly=read_only
	)

	if label:
		component["label"] = label
	if placeholder:
		component["placeholder"] = placeholder
	if default_value is not None:
		component["defaultValue"] = default_value
	if min is not None:
		component["min"] = min
	if max is not None:
		component["max"] = max
	if step is not None:
		component["step"] = step
	if on_change:
		component["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change
	if on_blur:
		component["onBlur"] = on_blur.build() if isinstance(on_blur, ActionBuilder) else on_blur
	if helper_text:
		component["helperText"] = helper_text
	if error_text:
		component["errorText"] = error_text

	# Base props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_textarea(
	name: str,
	label: Optional[Union[str, ValueRef]] = None,
	placeholder: Optional[Union[str, ValueRef]] = None,
	default_value: Optional[Union[str, ValueRef]] = None,
	rows: int = 3,
	cols: Optional[int] = None,
	max_length: Optional[int] = None,
	min_length: Optional[int] = None,
	required: Union[bool, ValueRef] = False,
	disabled: Union[bool, ValueRef] = False,
	read_only: Union[bool, ValueRef] = False,
	resize: Literal["none", "both", "horizontal", "vertical"] = "vertical",
	on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	on_blur: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	helper_text: Optional[Union[str, ValueRef]] = None,
	error_text: Optional[Union[str, ValueRef]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> TextAreaComponent:
	"""Create a textarea component for multiline text input

	Args:
		name: Input field name
		label: Optional label
		placeholder: Placeholder text
		default_value: Default value
		rows: Number of rows
		cols: Number of columns
		max_length: Maximum length
		min_length: Minimum length
		required: Whether input is required
		disabled: Whether input is disabled
		read_only: Whether input is readonly
		resize: Resize behavior (none, both, horizontal, vertical)
		on_change: Action to execute when value changes
		on_blur: Action to execute when input loses focus
		helper_text: Helper text shown below input
		error_text: Error text shown when validation fails

	Example:
		create_textarea(
			name="description",
			label="Description",
			placeholder="Enter a description",
			rows=5,
			resize="vertical"
		)
	"""
	component: TextAreaComponent = TextAreaComponent(
		type="textarea",
		name=name,
		rows=rows,
		required=required,
		disabled=disabled,
		readOnly=read_only,
		resize=resize
	)

	if label:
		component["label"] = label
	if placeholder:
		component["placeholder"] = placeholder
	if default_value is not None:
		component["defaultValue"] = default_value
	if cols is not None:
		component["cols"] = cols
	if max_length is not None:
		component["maxLength"] = max_length
	if min_length is not None:
		component["minLength"] = min_length
	if on_change:
		component["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change
	if on_blur:
		component["onBlur"] = on_blur.build() if isinstance(on_blur, ActionBuilder) else on_blur
	if helper_text:
		component["helperText"] = helper_text
	if error_text:
		component["errorText"] = error_text

	# Base props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_checkbox(
	name: str,
	label: Optional[Union[str, ValueRef]] = None,
	default_checked: Union[bool, ValueRef] = False,
	required: Union[bool, ValueRef] = False,
	disabled: Union[bool, ValueRef] = False,
	on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	helper_text: Optional[Union[str, ValueRef]] = None,
	error_text: Optional[Union[str, ValueRef]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> CheckboxComponent:
	"""Create a checkbox component

	Args:
		name: Input field name
		label: Optional label
		default_checked: Default checked state
		required: Whether checkbox is required
		disabled: Whether checkbox is disabled
		on_change: Action to execute when checked state changes
		helper_text: Helper text shown below checkbox
		error_text: Error text shown when validation fails

	Example:
		create_checkbox(
			name="agree",
			label="I agree to the terms and conditions",
			required=True,
			on_change=ActionBuilder().show_toast("Thank you!")
		)
	"""
	component: CheckboxComponent = CheckboxComponent(
		type="checkbox",
		name=name,
		defaultChecked=default_checked,
		required=required,
		disabled=disabled
	)

	if label:
		component["label"] = label
	if on_change:
		component["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change
	if helper_text:
		component["helperText"] = helper_text
	if error_text:
		component["errorText"] = error_text

	# Base props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component


def create_radio_option(
	value: Any,
	label: Union[str, ValueRef],
	disabled: bool = False
) -> RadioOption:
	"""Create a radio button option

	Args:
		value: Option value
		label: Option label
		disabled: Whether option is disabled

	Example:
		create_radio_option("small", "Small"),
		create_radio_option("medium", "Medium"),
		create_radio_option("large", "Large")
	"""
	return RadioOption(value=value, label=label, disabled=disabled)


def create_radio(
	name: str,
	options: Union[List[RadioOption], ValueRef],
	label: Optional[Union[str, ValueRef]] = None,
	default_value: Optional[Union[Any, ValueRef]] = None,
	required: Union[bool, ValueRef] = False,
	disabled: Union[bool, ValueRef] = False,
	orientation: Literal["horizontal", "vertical"] = "vertical",
	on_change: Optional[Union[ActionBuilder, ActionDefinition]] = None,
	helper_text: Optional[Union[str, ValueRef]] = None,
	error_text: Optional[Union[str, ValueRef]] = None,
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> RadioComponent:
	"""Create a radio button group component

	Args:
		name: Input field name
		options: List of radio options
		label: Optional label for the group
		default_value: Default selected value
		required: Whether selection is required
		disabled: Whether all options are disabled
		orientation: Layout orientation (horizontal or vertical)
		on_change: Action to execute when selection changes
		helper_text: Helper text shown below radio group
		error_text: Error text shown when validation fails

	Example:
		create_radio(
			name="size",
			label="Select Size",
			options=[
				create_radio_option("small", "Small"),
				create_radio_option("medium", "Medium"),
				create_radio_option("large", "Large")
			],
			default_value="medium",
			orientation="horizontal"
		)
	"""
	component: RadioComponent = RadioComponent(
		type="radio",
		name=name,
		options=options,
		required=required,
		disabled=disabled,
		orientation=orientation
	)

	if label:
		component["label"] = label
	if default_value is not None:
		component["defaultValue"] = default_value
	if on_change:
		component["onChange"] = on_change.build() if isinstance(on_change, ActionBuilder) else on_change
	if helper_text:
		component["helperText"] = helper_text
	if error_text:
		component["errorText"] = error_text

	# Base props
	if custom_style:
		component["customStyle"] = custom_style
	if class_name:
		component["className"] = class_name
	if visible is not None:
		component["visible"] = visible
	if events:
		component["events"] = events
	if id:
		component["id"] = id
	if aria_label:
		component["ariaLabel"] = aria_label
	if aria_describedby:
		component["ariaDescribedBy"] = aria_describedby

	return component




# ============================================================================
# Tabs Helpers
# ============================================================================

def create_tab_item(
	id: str,
	label: Union[str, ValueRef],
	content: List[ComponentDefinition],
	icon: Optional[Union[str, ValueRef]] = None,
	disabled: bool = False
) -> TabsItem:
	"""Helper to create a tab item

	Args:
		id: Unique identifier for the tab
		label: Tab label text
		content: List of components to display in the tab
		icon: Optional icon for the tab
		disabled: Whether the tab is disabled

	Example:
		create_tab_item(
			"overview",
			"Overview",
			[
				create_rich_text("Welcome to the overview tab"),
				create_card("Summary", [create_rich_text("Some content")])
			],
			icon="📊"
		)
	"""
	tab: TabsItem = {
		"id": id,
		"label": label,
		"content": content
	}
	if icon:
		tab["icon"] = icon
	if disabled:
		tab["disabled"] = disabled
	return tab


def create_tabs(
	items: List[Union[TabBuilder, TabsItem]],
	default_tab: Optional[str] = None,
	variant: Literal["default", "pills", "underlined"] = "default",
	orientation: Literal["horizontal", "vertical"] = "horizontal",
	# Base component props
	custom_style: Optional[CustomStyle] = None,
	class_name: Optional[Union[str, ValueRef]] = None,
	visible: Optional[Union[bool, ValueRef]] = None,
	events: Optional[ComponentEvents] = None,
	id: Optional[str] = None,
	aria_label: Optional[Union[str, ValueRef]] = None,
	aria_describedby: Optional[Union[str, ValueRef]] = None
) -> TabsComponent:
	"""Helper to create a tabs component

	Args:
		items: List of tab items (TabsItem or TabBuilder)
		default_tab: ID of the default active tab
		variant: Visual style of the tabs
		orientation: Horizontal or vertical tabs
		custom_style: Custom CSS styles
		class_name: Additional CSS class names
		visible: Visibility condition
		events: Component events
		id: Component ID
		aria_label: ARIA label
		aria_describedby: ARIA described by

	Example:
		create_tabs([
			create_tab_item("tab1", "First Tab", [create_rich_text("Content 1")]),
			create_tab_item("tab2", "Second Tab", [create_rich_text("Content 2")])
		], default_tab="tab1", variant="pills")
	"""
	# Build tab items
	built_items = []
	for item in items:
		if isinstance(item, TabBuilder):
			built_items.append(item.build())
		else:
			built_items.append(item)

	tabs: TabsComponent = {
		"type": "tabs",
		"items": built_items,
		"variant": variant,
		"orientation": orientation
	}

	if default_tab:
		tabs["defaultTab"] = default_tab

	# Add base component props
	if custom_style:
		tabs["customStyle"] = custom_style
	if class_name:
		tabs["className"] = class_name
	if visible is not None:
		tabs["visible"] = visible
	if events:
		tabs["events"] = events
	if id:
		tabs["id"] = id
	if aria_label:
		tabs["ariaLabel"] = aria_label
	if aria_describedby:
		tabs["ariaDescribedBy"] = aria_describedby

	return tabs

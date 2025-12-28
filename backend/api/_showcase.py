"""
DSL Showcase - Tabbed Organization

Organized into logical tabs for better navigation and component discovery.
"""
from typing import Dict, Any
from flask import Flask, jsonify
from backend.api._dsl_builder import *


def build_showcase_page() -> PageDSL:
	"""Build tabbed DSL showcase page"""

	# Create page
	page = PageBuilder(
		title="DSL Component Showcase",
		description="Interactive demonstration of all DSL components, organized by category"
	)

	# Build tabs using the new TabsBuilder
	showcase_tabs = (TabsBuilder()
		.add_tab(build_display_tab())
		.add_tab(build_forms_tab())
		.add_tab(build_interactive_tab())
		.add_tab(build_data_tab())
		.add_tab(build_layout_tab())
		.add_tab(build_feedback_tab())
		.default_tab("display")
		.variant("pills")
		.build()
	)

	# Add tabs as a component in a section
	page.add_section(
		SectionBuilder()
			.add_component(showcase_tabs)
	)

	# Add modals and panels
	page = add_modals_and_panels(page)

	return page.build()


def build_display_tab() -> TabsItem:
	"""Display Components tab - badges, avatars, metrics, images, etc."""
	return (TabBuilder("display", "Display")
		.add_component(create_rich_text("# Display Components\nVisual elements for showing information"))
		.add_component(create_spacer(size="md"))
		
		# Badges and Metrics
		.add_component(create_rich_text("## Badges & Metrics"))
		.add_component(create_badge(label="Active", variant="success", icon="✓"))
		.add_component(create_spacer(size="sm"))
		.add_component(create_badge(label="Pending", variant="warning"))
		.add_component(create_spacer(size="md"))
		.add_component(create_metric(value=1543, label="Total Users", format="number", trend="up", variant="success"))
		.add_component(create_spacer(size="md"))
		
		# Progress
		.add_component(create_rich_text("## Progress"))
		.add_component(create_progress_bar(value=75, label="Upload Progress", variant="success"))
		.add_component(create_spacer(size="md"))
		
		# Avatar
		.add_component(create_rich_text("## Avatar"))
		.add_component(create_avatar(name="John Doe", src="https://i.pravatar.cc/150?img=1", size="lg", status="online"))
		.add_component(create_spacer(size="md"))
		
		# Images
		.add_component(create_rich_text("## Images"))
		.add_component(create_image(
			src="https://picsum.photos/800/400",
			alt="Showcase Image",
			width="100%",
			height="300px",
			fit="cover",
			rounded=True
		))
		.add_component(create_spacer(size="md"))
		
		# Metrics Grid
		.add_component(create_rich_text("## Metrics"))
		.add_component(create_grid(
			items=[
				create_metric(value=342, label="Active Sessions", format="number", variant="success", trend="up"),
				create_metric(value=12543, label="Total Revenue", format="currency", variant="default"),
				create_metric(value=87, label="Completion Rate", format="percentage", variant="success"),
			],
			columns=3
		))
		.add_component(create_spacer(size="md"))

		# Cards Grid
		.add_component(create_rich_text("## Cards"))
		.add_component(create_grid(
			items=[
				CardBuilder("Server Info")
					.add_component(create_rich_text("**IP:** 192.168.1.100"))
					.add_component(create_rich_text("**Status:** Active"))
					.build(),
				CardBuilder("System Info")
					.add_component(create_rich_text("**Version:** 1.2.3"))
					.add_component(create_rich_text("**Updated:** 2025-12-24"))
					.build(),
			],
			columns=2
		))
		.add_component(create_spacer(size="md"))
		
		# Skeletons
		.add_component(create_rich_text("## Loading States"))
		.add_component(create_skeleton(variant="text", lines=3, width="100%"))
		.add_component(create_spacer(size="sm"))
		.add_component(create_skeleton(variant="rectangular", width="100%", height="100px"))
		.build()
	)


def build_forms_tab() -> TabsItem:
	"""Forms & Input tab - all form controls"""
	return (TabBuilder("forms", "Forms & Input")
		.add_component(create_rich_text("# Forms & Input\nData entry and form controls"))
		.add_component(create_spacer(size="md"))
		
		# Text Input
		.add_component(create_text_input(
			name="username",
			label="Username",
			placeholder="Enter your username...",
			required=True
		))
		.add_component(create_spacer(size="sm"))
		
		# Number Input
		.add_component(create_number_input(
			name="age",
			label="Age",
			min=0,
			max=120,
			placeholder="Enter your age..."
		))
		.add_component(create_spacer(size="sm"))
		
		# Textarea
		.add_component(create_textarea(
			name="description",
			label="Description",
			placeholder="Enter description...",
			rows=4
		))
		.add_component(create_spacer(size="sm"))
		
		# Dropdown
		.add_component(create_dropdown(
			name="country",
			label="Select Country",
			placeholder="Choose a country...",
			options=[
				{"label": "United States", "value": "us"},
				{"label": "United Kingdom", "value": "uk"},
				{"label": "Canada", "value": "ca"},
			],
			searchable=True,
			clearable=True
		))
		.add_component(create_spacer(size="sm"))
		
		# Date Picker
		.add_component(create_date_picker(
			name="birth_date",
			label="Birth Date",
			format="MMMM D, YYYY",
			placeholder="Select date..."
		))
		.add_component(create_spacer(size="sm"))
		
		# Checkbox
		.add_component(create_checkbox(
			name="terms",
			label="I agree to the terms and conditions"
		))
		.add_component(create_spacer(size="sm"))
		
		# Radio
		.add_component(create_radio(
			name="size",
			label="Select Size",
			options=[
				create_radio_option("small", "Small"),
				create_radio_option("medium", "Medium"),
				create_radio_option("large", "Large"),
			]
		))
		.add_component(create_spacer(size="md"))
		
		# Complete Form Example
		.add_component(create_rich_text("## Complete Form"))
		.add_component(FormBuilder(
			submit_action=ActionBuilder()
				.api_call(endpoint="/api/submit", method="POST")
				.on_success(message="Form submitted successfully!")
		)
			.add_field(name="name", label="Full Name", type="text", required=True)
			.add_field(name="email", label="Email", type="email", required=True)
			.add_select_field(
				name="role",
				label="Role",
				options=[
					{"label": "Developer", "value": "dev"},
					{"label": "Designer", "value": "design"},
					{"label": "Manager", "value": "mgr"},
				]
			)
			.build()
		)
		.build()
	)


def build_interactive_tab() -> TabsItem:
	"""Interactive tab - buttons, toggles, accordions, etc."""
	return (TabBuilder("interactive", "Interactive")
		.add_component(create_rich_text("# Interactive Components\nClickable and interactive elements"))
		.add_component(create_spacer(size="md"))
		
		# Buttons
		.add_component(create_rich_text("## Buttons"))
		.add_component(create_button(
			label="Primary Button",
			action=ActionBuilder().show_toast("Primary clicked!", "success"),
			variant="primary"
		))
		.add_component(create_spacer(size="sm"))
		.add_component(create_button(
			label="Secondary Button",
			action=ActionBuilder().show_toast("Secondary clicked", "info"),
			variant="secondary"
		))
		.add_component(create_spacer(size="sm"))
		.add_component(create_button(
			label="Danger Button",
			action=ActionBuilder().show_toast("Danger action!", "warning"),
			variant="danger"
		))
		.add_component(create_spacer(size="md"))
		
		# Toggles
		.add_component(create_rich_text("## Toggles"))
		.add_component(create_toggle(
			name="notifications",
			label="Enable Notifications",
			checked=True,
			size="md"
		))
		.add_component(create_spacer(size="sm"))
		.add_component(create_toggle(
			name="dark_mode",
			label="Dark Mode",
			checked=False,
			size="lg"
		))
		.add_component(create_spacer(size="md"))
		
		# Accordion
		.add_component(create_rich_text("## Accordion"))
		.add_component(AccordionBuilder()
			.add_item("item1", "Section 1", [
				create_rich_text("Content for section 1")
			], default_expanded=True)
			.add_item("item2", "Section 2", [
				create_rich_text("Content for section 2")
			])
			.add_item("item3", "Section 3", [
				create_rich_text("Content for section 3")
			])
			.build()
		)
		.add_component(create_spacer(size="md"))
		
		# Chip Input
		.add_component(create_rich_text("## Chip Input"))
		.add_component(create_chip_input(
			name="keywords",
			label="Keywords",
			placeholder="Type and press Enter...",
			value=["python", "react", "docker"]
		))
		.build()
	)


def build_data_tab() -> TabsItem:
	"""Data Display tab - tables, charts, grids"""
	return (TabBuilder("data", "Data Display")
		.add_component(create_rich_text("# Data Display\nTables, charts, and data visualizations"))
		.add_component(create_spacer(size="md"))
		
		# Table
		.add_component(create_rich_text("## Table"))
		.add_component(TableBuilder(
			data=[
				{"id": 1, "name": "Item 1", "status": "active", "created_at": "2025-01-01"},
				{"id": 2, "name": "Item 2", "status": "pending", "created_at": "2025-01-02"},
				{"id": 3, "name": "Item 3", "status": "completed", "created_at": "2025-01-03"},
			]
		)
			.id("test_table")
			.add_column("id", "ID", type="text", width="80px", sortable=True)
			.add_column("name", "Name", type="text", sortable=True)
			.add_column("status", "Status", type="status", sortable=True)
			.add_column("created_at", "Created", type="date")
			.build()
		)
		.add_component(create_spacer(size="md"))
		.add_component(
			create_button("Add row",
				 action=ActionBuilder()
				 .add_rows("test_table", rows=ValueRefBuilder.literal([
					{"id": 4, "name": "Item 4", "status": "active", "created_at": "2025-01-04"},
					{"id": 5, "name": "Item 5", "status": "pending", "created_at": "2025-01-05"},
					{"id": 6, "name": "Item 6", "status": "completed", "created_at": "2025-01-06"},
				]))
			)
		)

		.add_component(create_spacer(size="md"))
		
		# Chart
		.add_component(create_rich_text("## Chart"))
		.add_component(ChartBuilder(
			chart_type="line",
			data=[
				{"month": "Jan", "value": 400},
				{"month": "Feb", "value": 300},
				{"month": "Mar", "value": 600},
				{"month": "Apr", "value": 800},
				{"month": "May", "value": 500},
			]
		)
			.add_series("value", "Sales", color="#10b981")
			.set_x_axis("month", "Month")
			.build()
		)
		.build()
	)


def build_layout_tab() -> TabsItem:
	"""Layout tab - grid, flex, container"""
	return (TabBuilder("layout", "Layout")
		.add_component(create_rich_text("# Layout Components\nStructural components for arranging content"))
		.add_component(create_spacer(size="md"))
		
		# Grid
		.add_component(create_rich_text("## Grid Layout"))
		.add_component(create_grid(
			items=[
				CardBuilder("Card 1").add_component(create_rich_text("Content 1")).build(),
				CardBuilder("Card 2").add_component(create_rich_text("Content 2")).build(),
				CardBuilder("Card 3").add_component(create_rich_text("Content 3")).build(),
			],
			columns=3,
			gap="1rem"
		))
		.add_component(create_spacer(size="md"))
		
		# Flex
		.add_component(create_rich_text("## Flex Layout"))
		.add_component(FlexBuilder(direction="row", justify="space-between", align="center", gap="1rem")
			.add_item(create_button("Left", ActionBuilder().show_toast("Left")))
			.add_item(create_button("Center", ActionBuilder().show_toast("Center")))
			.add_item(create_button("Right", ActionBuilder().show_toast("Right")))
			.build()
		)
		.add_component(create_spacer(size="md"))
		
		# Container
		.add_component(create_rich_text("## Container"))
		.add_component(ContainerBuilder(max_width="800px", padding="2rem", centered=True)
			.add_child(create_rich_text("This content is in a centered container with max-width of 800px", align="center"))
			.build()
		)
		.build()
	)


def build_feedback_tab() -> TabsItem:
	"""Feedback tab - toasts, modals, panels, alerts"""
	return (TabBuilder("feedback", "Feedback")
		.add_component(create_rich_text("# Feedback Components\nNotifications, dialogs, and user feedback"))
		.add_component(create_spacer(size="md"))
		
		# Toast Examples
		.add_component(create_rich_text("## Toasts"))
		.add_component(create_button(
			label="Success Toast",
			action=ActionBuilder().show_toast("Operation successful!", "success"),
			variant="success"
		))
		.add_component(create_spacer(size="sm"))
		.add_component(create_button(
			label="Error Toast",
			action=ActionBuilder().show_toast("Something went wrong!", "error"),
			variant="danger"
		))
		.add_component(create_spacer(size="sm"))
		.add_component(create_button(
			label="Info Toast",
			action=ActionBuilder().show_toast("Here's some information", "info"),
			variant="secondary"
		))
		.add_component(create_spacer(size="md"))
		
		# Modal Example
		.add_component(create_rich_text("## Modals"))
		.add_component(create_button(
			label="Open Modal",
			action=ActionBuilder().open_modal("demo-modal"),
			variant="primary"
		))
		.add_component(create_spacer(size="md"))
		
		# Panel Example
		.add_component(create_rich_text("## Panels"))
		.add_component(create_button(
			label="Open Side Panel",
			action=ActionBuilder().open_panel("info-panel"),
			variant="secondary"
		))
		.add_component(create_button(
			label="Open Side Panel",
			action=ActionBuilder().open_panel("info-panel2"),
			variant="secondary"
		))
		.add_component(create_button(
			label="Open Side Panel",
			action=ActionBuilder().open_panel("info-panel3"),
			variant="secondary"
		))
		.add_component(create_button(
			label="Open Side Panel",
			action=ActionBuilder().open_panel("info-panel4"),
			variant="secondary"
		))
		.add_component(create_button(
			label="Open Side Panel",
			action=ActionBuilder().open_panel("info-panel5"),
			variant="secondary"
		))
		.add_component(create_spacer(size="md"))
		
		# Alerts
		.add_component(create_rich_text("## Alerts"))
		.add_component(create_alert(
			message="This is an informational alert",
			variant="info",
			dismissible=True
		))
		.add_component(create_spacer(size="sm"))
		.add_component(create_alert(
			message="Warning: This action cannot be undone",
			variant="warning"
		))
		.add_component(create_spacer(size="sm"))
		.add_component(create_callout(
			title="Important",
			message="Callout for highlighting important information",
			variant="success",
			icon="✓"
		))
		.build()
	)


def add_modals_and_panels(page: PageBuilder) -> PageBuilder:
	"""Add modal and panel definitions to the page"""
	
	# Demo Modal
	demo_modal = (ModalBuilder("Demo Modal", size="medium")
		.add_component(create_rich_text("This is a modal dialog"))
		.add_component(create_spacer(size="md"))
		.add_component(create_rich_text("Modals are great for forms, confirmations, and detailed views"))
		.add_action("Close", ActionBuilder().close_modal("demo-modal"), variant="secondary")
		.add_action("Confirm", ActionBuilder().show_toast("Confirmed!", "success"), variant="primary")
		.build()
	)
	
	page.add_modal("demo-modal", demo_modal)
	
	# Info Panel
	info_panel = (PanelBuilder("Information Panel")
		.add_component(create_rich_text("## Side Panel"))
		.add_component(create_spacer(size="md"))
		.add_component(create_rich_text("Panels slide in from the side and are perfect for auxiliary information."))
		.add_component(create_spacer(size="md"))
		.add_component(create_button(
			label="Close Panel",
			action=ActionBuilder().close_panel("info-panel"),
			variant="secondary"
		))
		.set_width("400px")
		.set_position("bottom-right")
		.build()
	)
	
	page.add_panel("info-panel", info_panel)
	page.add_panel("info-panel2", info_panel)
	page.add_panel("info-panel3", info_panel)
	page.add_panel("info-panel4", info_panel)
	page.add_panel("info-panel5", info_panel)
	
	return page

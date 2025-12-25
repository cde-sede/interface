"""
DSL Showcase - Building incrementally
"""
from typing import Dict, Any
from flask import Flask, jsonify
from backend.api._dsl_builder import *


def build_showcase_page() -> PageDSL:
    """Build DSL showcase page"""

    # Create page
    page = PageBuilder(
        title="DSL Component Showcase",
        description="Interactive demonstration of DSL components"
    )

    # Add a simple section with display components
    section = (SectionBuilder(title="Display Components")
        .add_badge(label="Active", variant="success", icon="check")
        .add_spacer(size="md")
        .add_progress_bar(value=75, label="Upload Progress", variant="success")
        .add_spacer(size="md")
        .add_avatar(name="John Doe", src="https://i.pravatar.cc/150?img=1", size="lg", status="online")
        .add_spacer(size="md")
        .add_metric(value=1543, label="Total Users", format="number", trend="up", variant="success")
        .add_spacer(size="md")
        .add_component(
            create_image(
                src="https://picsum.photos/800/400",
                alt="Showcase Image",
                width="100%",
                height="400px",
                fit="cover",
                rounded=True
            )
        )
        .add_spacer(size="lg")
        .add_divider(label="More Components", variant="solid")
        .add_spacer(size="md")
        .add_callout(
            title="Welcome",
            message="This is a callout component for important information",
            variant="info",
            icon="info"
        )
        .add_spacer(size="md")
        .add_component(
            create_alert(
                message="This is an alert component - distinct from callout with different styling",
                variant="warning",
                dismissible=True
            )
        )
        .add_spacer(size="md")
        .add_stats_cards(
            stats=[
                create_stat_card(label="Active Sessions", value=342, total=500, icon="users"),
                create_stat_card(label="Total Revenue", value=12543, icon="dollar-sign"),
                create_stat_card(label="Completion Rate", value=87, total=100, icon="percent"),
            ],
            columns=3
        )
        .add_spacer(size="md")
        .add_info_grid(
            items=[
                create_info_item(label="Server IP", value="192.168.1.100", type="code", copyable=True),
                create_info_item(label="Status", value="active", type="status"),
                create_info_item(label="Last Updated", value="2025-12-24 10:30:00", type="date"),
                create_info_item(label="Version", value="1.2.3", type="text"),
            ],
            columns=2
        )
        .add_spacer(size="lg")
        .add_divider(label="Loading States", variant="solid")
        .add_spacer(size="md")
        .add_component(create_skeleton(variant="text", lines=3, width="100%"))
        .add_spacer(size="md")
        .add_component(create_skeleton(variant="circular", width="60px", height="60px"))
        .add_spacer(size="md")
        .add_component(create_skeleton(variant="rectangular", width="100%", height="200px"))
        .add_spacer(size="md")
        .add_component(create_skeleton(variant="card"))
    )

    page.add_section(section)

    # Interactive Components Section
    interactive_section = (SectionBuilder(title="Interactive Components")
        .add_button(
            label="Click Me",
            action=ActionBuilder().show_toast("Button clicked!", "success"),
            variant="primary"
        )
        .add_spacer(size="md")
        .add_button(
            label="Secondary Action",
            action=ActionBuilder().show_toast("Secondary button clicked", "info"),
            variant="secondary"
        )
        .add_spacer(size="md")
        .add_component(
            create_toggle(
                name="notifications",
                label="Enable Notifications",
                checked=True,
                on_change=ActionBuilder().show_toast("Toggle changed", "info"),
                size="md"
            )
        )
        .add_spacer(size="sm")
        .add_component(
            create_toggle(
                name="dark_mode",
                label="Dark Mode",
                checked=False,
                size="lg"
            )
        )
        .add_spacer(size="md")
        .add_component(
            create_dropdown(
                name="country",
                label="Select Country",
                placeholder="Choose a country...",
                options=[
                    {"label": "United States", "value": "us"},
                    {"label": "United Kingdom", "value": "uk"},
                    {"label": "Canada", "value": "ca"},
                    {"label": "Australia", "value": "au"},
                ],
                searchable=True,
                clearable=True,
                on_change=ActionBuilder().show_toast("Country selected", "success")
            )
        )
        .add_spacer(size="sm")
        .add_component(
            create_dropdown(
                name="tags",
                label="Select Tags",
                placeholder="Choose multiple tags...",
                options=[
                    {"label": "Development", "value": "dev"},
                    {"label": "Production", "value": "prod"},
                    {"label": "Testing", "value": "test"},
                    {"label": "Staging", "value": "stage"},
                ],
                multiple=True,
                searchable=True
            )
        )
        .add_spacer(size="md")
        .add_component(
            create_chip_input(
                name="keywords",
                label="Keywords",
                placeholder="Type and press Enter to add keywords...",
                value=["python", "react", "docker"],
                max_tags=10,
                on_change=ActionBuilder().show_toast("Keywords updated", "info")
            )
        )
        .add_spacer(size="md")
        .add_component(
            create_file_upload(
                name="documents",
                label="Upload Documents",
                accept=[".pdf", ".doc", ".docx"],
                multiple=True,
                max_size="10MB",
                max_files=5,
                show_preview=True,
                on_upload=(ActionBuilder()
				    .store_data("uploadedFiles", ValueRefBuilder.transform(ValueRefBuilder.field("form", "files"), "&->.name"))
                    .on_success("Files uploaded and stored", ActionBuilder().show_toast("Check stored files with the button below", "success"))
                ),
                on_remove=(ActionBuilder()
                    .store_data("uploadedFiles", ValueRefBuilder().field("form", "remainingFiles"))
                    .on_success("Store cleared", ActionBuilder().show_toast("File removed, store cleared", "info"))
                )
            )
        )
        .add_spacer(size="md")
        .add_button(
            label="Show Uploaded Files",
            action=ActionBuilder().show_toast(ValueRefBuilder().field("store", "uploadedFiles.*.name"), "info"),
            variant="secondary"
        )
        .add_spacer(size="md")
        .add_component(
            create_tooltip(
                content="This is a helpful tooltip",
                trigger=create_badge(label="Hover me", variant="info", icon="info"),
                placement="top"
            )
        )
        .add_spacer(size="sm")
        .add_component(
            create_tooltip(
                content="Tooltips can appear in different positions",
                trigger=create_button(
                    label="Button with tooltip",
                    action=ActionBuilder().show_toast("Button clicked!", "success"),
                    variant="secondary"
                ),
                placement="bottom"
            )
        )
    )

    page.add_section(interactive_section)

    # Process Components Section
    process_section = (SectionBuilder(title="Process Components")
        .add_component(
            create_breadcrumbs(
                items=[
                    create_breadcrumb_item(label="Home", href="/"),
                    create_breadcrumb_item(label="Dashboard", href="/dashboard"),
                    create_breadcrumb_item(label="Settings", href="/settings"),
                    create_breadcrumb_item(label="Profile", active=True),
                ],
                separator="/"
            )
        )
        .add_spacer(size="lg")
        .add_component(
            create_stepper(
                steps=[
                    create_stepper_step(label="Account Setup", description="Create your account", status="completed"),
                    create_stepper_step(label="Profile Information", description="Add your details", status="completed"),
                    create_stepper_step(label="Preferences", description="Configure settings", status="active"),
                    create_stepper_step(label="Review", description="Confirm and finish", status="pending"),
                ],
                current_step=2,
                orientation="horizontal"
            )
        )
        .add_spacer(size="lg")
        .add_component(
            create_stepper(
                steps=[
                    create_stepper_step(label="Start", description="Begin the process", status="completed"),
                    create_stepper_step(label="Processing", description="Working on it", status="active"),
                    create_stepper_step(label="Complete", description="All done", status="pending"),
                ],
                current_step=1,
                orientation="vertical"
            )
        )
    )

    page.add_section(process_section)

    # Data Display Section with table
    table = (TableBuilder(
        data=[
            {"id": 1, "name": "Alice", "role": "Admin", "status": "active"},
            {"id": 2, "name": "Bob", "role": "User", "status": "active"},
            {"id": 3, "name": "Carol", "role": "User", "status": "inactive"}
        ]
    )
        .add_column("id", "ID", type="text", sortable=True)
        .add_column("name", "Name", type="text", sortable=True)
        .add_column("role", "Role", type="text", sortable=True)
        .add_column("status", "Status", type="text", sortable=True)
    )

    data_section = (SectionBuilder(title="Data Display")
        .add_table(table)
        .add_spacer(size="lg")
        .add_component(
            create_tree_view(
                nodes=[
                    create_tree_node(
                        id="root",
                        label="Project Root",
                        icon="folder",
                        expanded=True,
                        children=[
                            create_tree_node(
                                id="src",
                                label="src",
                                icon="folder",
                                expanded=True,
                                children=[
                                    create_tree_node(id="app", label="app.py", icon="file", action=ActionBuilder().show_toast("app.py clicked", "info")),
                                    create_tree_node(id="utils", label="utils.py", icon="file"),
                                ]
                            ),
                            create_tree_node(
                                id="tests",
                                label="tests",
                                icon="folder",
                                children=[
                                    create_tree_node(id="test_app", label="test_app.py", icon="file"),
                                ]
                            ),
                            create_tree_node(id="readme", label="README.md", icon="file-text"),
                        ]
                    )
                ],
                show_icons=True
            )
        )
        .add_spacer(size="lg")
        .add_component(
            create_data_grid(
                data=[
                    {"id": 1, "product": "Laptop", "price": 1200, "stock": 15, "available": True},
                    {"id": 2, "product": "Mouse", "price": 25, "stock": 50, "available": True},
                    {"id": 3, "product": "Keyboard", "price": 75, "stock": 0, "available": False},
                ],
                columns=[
                    create_data_grid_column(key="id", label="ID", type="number", editable=False),
                    create_data_grid_column(key="product", label="Product", type="text", editable=True),
                    create_data_grid_column(key="price", label="Price", type="number", editable=True),
                    create_data_grid_column(key="stock", label="Stock", type="number", editable=True),
                    create_data_grid_column(key="available", label="Available", type="boolean", editable=True),
                ],
                editable=True,
                on_cell_edit=ActionBuilder().show_toast("Cell edited", "success"),
                on_row_add=ActionBuilder().show_toast("Row added", "success"),
                on_row_delete=ActionBuilder().show_toast("Row deleted", "info")
            )
        )
        .add_spacer(size="lg")
        .add_component(
            create_calendar(
                events=[
                    create_calendar_event(
                        id="event1",
                        title="Team Meeting",
                        start="2025-12-24T10:00:00",
                        end="2025-12-24T11:00:00",
                        color="#4CAF50",
                        action=ActionBuilder().show_toast("Team Meeting clicked", "info")
                    ),
                    create_calendar_event(
                        id="event2",
                        title="Project Deadline",
                        start="2025-12-26T00:00:00",
                        all_day=True,
                        color="#F44336"
                    ),
                    create_calendar_event(
                        id="event3",
                        title="Client Call",
                        start="2025-12-27T14:00:00",
                        end="2025-12-27T15:00:00",
                        color="#2196F3"
                    ),
                ],
                view="month",
                on_event_click=ActionBuilder().show_toast("Event clicked", "info"),
                on_date_click=ActionBuilder().show_toast("Date clicked", "info")
            )
        )
        .add_spacer(size="lg")
        .add_component(
            ChartBuilder(
                chart_type="bar",
                data=[
                    {"month": "Jan", "sales": 4000, "expenses": 2400},
                    {"month": "Feb", "sales": 3000, "expenses": 1398},
                    {"month": "Mar", "sales": 2000, "expenses": 9800},
                    {"month": "Apr", "sales": 2780, "expenses": 3908},
                    {"month": "May", "sales": 1890, "expenses": 4800},
                    {"month": "Jun", "sales": 2390, "expenses": 3800},
                ]
            )
                .set_x_axis("month", "Month")
                .set_y_axis("Amount ($)")
                .add_series("sales", "Sales", "#4CAF50")
                .add_series("expenses", "Expenses", "#F44336")
                .set_legend(True)
                .set_height(300)
                .build()
        )
        .add_spacer(size="md")
        .add_component(
            ChartBuilder(
                chart_type="line",
                data=[
                    {"day": "Mon", "users": 120},
                    {"day": "Tue", "users": 150},
                    {"day": "Wed", "users": 180},
                    {"day": "Thu", "users": 220},
                    {"day": "Fri", "users": 260},
                    {"day": "Sat", "users": 190},
                    {"day": "Sun", "users": 140},
                ]
            )
                .set_x_axis("day", "Day")
                .set_y_axis("Users")
                .add_series("users", "Active Users", "#2196F3")
                .set_height(250)
                .build()
        )
        .add_spacer(size="md")
        .add_component(
            ChartBuilder(
                chart_type="pie",
                data=[
                    {"name": "Desktop", "value": 45},
                    {"name": "Mobile", "value": 35},
                    {"name": "Tablet", "value": 20},
                ]
            )
                .add_series("value", "Device Usage")
                .set_height(300)
                .build()
        )
    )

    page.add_section(data_section)

    # Forms Section
    form = (FormBuilder(submit_action=ActionBuilder().show_toast("Form submitted!", "success"))
        .add_field("name", "Full Name", type="text", required=True)
        .add_field("email", "Email Address", type="email", required=True)
        .add_field("message", "Message", type="textarea")
    )

    forms_section = SectionBuilder(title="Forms").add_form(form)

    page.add_section(forms_section)

    # Layout Components Section
    card = (CardBuilder(title="Sample Card")
        .set_subtitle("This is a card subtitle")
        .add_component(
            create_callout(
                message="Cards can contain any components and have action buttons.",
                variant="neutral"
            )
        )
        .add_action(create_button(
			label="Primary Action",
			action=ActionBuilder().show_toast("Card action clicked", "success"),
			variant="primary",
		))
        .set_variant("elevated")
    )

    accordion = (AccordionBuilder()
        .add_item(
            id="item1",
            title="System Information",
            content=[
                create_metric(value=8, label="CPU Cores", format="number"),
                create_metric(value=16384, label="RAM (MB)", format="number"),
            ],
            default_expanded=True
        )
        .add_item(
            id="item2",
            title="Network Status",
            content=[
                create_badge(label="Connected", variant="success", icon="wifi"),
                create_callout(
                    message="All network interfaces are operational",
                    variant="success"
                )
            ]
        )
        .add_item(
            id="item3",
            title="Storage Information",
            content=[
                create_metric(value=512, label="Total Storage (GB)", format="number"),
                create_metric(value=234, label="Used Storage (GB)", format="number"),
            ]
        )
        .set_variant("bordered")
        .set_allow_multiple(True)
    )

    layout_section = (SectionBuilder(title="Layout Components")
        .add_card(card)
        .add_spacer(size="lg")
        .add_accordion(accordion)
        .add_spacer(size="lg")
        .add_component(
            create_grid(
                items=[
                    create_badge(label="Badge 1", variant="success", icon="check"),
                    create_badge(label="Badge 2", variant="info", icon="info"),
                    create_badge(label="Badge 3", variant="warning", icon="alert-triangle"),
                    create_badge(label="Badge 4", variant="error", icon="x"),
                    create_badge(label="Badge 5", variant="neutral", icon="circle"),
                    create_badge(label="Badge 6", variant="success", icon="star"),
                ],
                columns=3,
                gap="1rem"
            )
        )
        .add_spacer(size="md")
        .add_component(
            create_grid(
                items=[
                    create_metric(value=350, label="Online Users", format="number", variant="success"),
                    create_metric(value=1250, label="Total Orders", format="number", variant="info"),
                    create_metric(value=89, label="Success Rate", format="number", variant="success"),
                    create_metric(value=45, label="Pending Tasks", format="number", variant="warning"),
                ],
                columns=4,
                gap="1.5rem"
            )
        )
    )

    page.add_section(layout_section)

    # Timeline Section
    timeline_section = (SectionBuilder(title="Activity Timeline")
        .add_timeline(
            items=[
                create_timeline_item(
                    title="System Started",
                    description="All services initialized successfully",
                    timestamp="2025-12-23 10:00:00",
                    icon="power",
                    variant="success"
                ),
                create_timeline_item(
                    title="Configuration Updated",
                    description="Updated network settings",
                    timestamp="2025-12-23 10:15:00",
                    icon="settings",
                    variant="info"
                ),
                create_timeline_item(
                    title="Backup Completed",
                    description="Full system backup completed successfully",
                    timestamp="2025-12-23 10:30:00",
                    icon="save",
                    variant="success"
                ),
                create_timeline_item(
                    title="Warning Detected",
                    description="High memory usage detected",
                    timestamp="2025-12-23 10:45:00",
                    icon="alert-triangle",
                    variant="warning"
                ),
            ],
            position="left"
        )
    )

    page.add_section(timeline_section)

    # List Section
    list_section = (SectionBuilder(title="Settings Menu")
        .add_list(
            items=[
                create_list_item(
                    label="User Profile",
                    description="Manage your account settings",
                    icon="user",
                    trailing=">"
                ),
                create_list_item(
                    label="Notifications",
                    description="Configure notification preferences",
                    icon="bell",
                    trailing=">"
                ),
                create_list_item(
                    label="Security",
                    description="Password and authentication settings",
                    icon="shield",
                    trailing=">"
                ),
                create_list_item(
                    label="Privacy",
                    description="Data and privacy controls",
                    icon="lock",
                    trailing=">"
                ),
                create_list_item(
                    label="About",
                    description="Version and system information",
                    icon="info",
                    action=ActionBuilder().show_toast("About clicked", "info"),
                ),
            ],
            variant="divided",
            hoverable=True
        )
    )

    page.add_section(list_section)

    return page.build()

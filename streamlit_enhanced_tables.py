"""
Enhanced Interactive Data Tables for EdAgent Streamlit App
Provides sortable, filterable, and paginated data tables with accessibility features.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re
from datetime import datetime, date
import math


class ColumnType(Enum):
    """Column data types for enhanced formatting"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    EMAIL = "email"
    URL = "url"
    IMAGE = "image"
    BADGE = "badge"
    PROGRESS = "progress"


class SortDirection(Enum):
    """Sort direction options"""
    ASC = "asc"
    DESC = "desc"
    NONE = "none"


@dataclass
class ColumnConfig:
    """Configuration for table columns"""
    key: str
    label: str
    type: ColumnType = ColumnType.TEXT
    sortable: bool = True
    filterable: bool = True
    searchable: bool = True
    width: Optional[str] = None
    align: str = "left"
    format_func: Optional[Callable] = None
    render_func: Optional[Callable] = None
    hidden: bool = False
    frozen: bool = False


@dataclass
class TableConfig:
    """Configuration for enhanced tables"""
    page_size: int = 10
    show_pagination: bool = True
    show_search: bool = True
    show_filters: bool = True
    show_export: bool = True
    show_column_selector: bool = True
    selectable_rows: bool = False
    multi_select: bool = False
    sticky_header: bool = True
    compact_mode: bool = False
    striped_rows: bool = True
    hover_effects: bool = True
    responsive: bool = True


class EnhancedDataTable:
    """Enhanced interactive data table component"""
    
    def __init__(self, data: pd.DataFrame, 
                 columns: List[ColumnConfig],
                 config: Optional[TableConfig] = None,
                 table_id: str = "table"):
        
        self.data = data.copy()
        self.columns = {col.key: col for col in columns}
        self.config = config or TableConfig()
        self.table_id = table_id
        
        # Initialize session state
        self._init_session_state()
        
        # Apply initial processing
        self.filtered_data = self.data.copy()
        self._apply_filters()
        self._apply_sorting()
    
    def _init_session_state(self):
        """Initialize session state for table"""
        state_key = f"{self.table_id}_state"
        
        if state_key not in st.session_state:
            st.session_state[state_key] = {
                "current_page": 0,
                "page_size": self.config.page_size,
                "sort_column": None,
                "sort_direction": SortDirection.NONE,
                "search_query": "",
                "column_filters": {},
                "selected_rows": [],
                "visible_columns": [col.key for col in self.columns.values() if not col.hidden],
                "compact_mode": self.config.compact_mode
            }
        
        self.state = st.session_state[state_key]
    
    def _apply_filters(self):
        """Apply search and column filters to data"""
        filtered = self.data.copy()
        
        # Apply search filter
        if self.state["search_query"]:
            search_query = self.state["search_query"].lower()
            searchable_columns = [col.key for col in self.columns.values() if col.searchable]
            
            if searchable_columns:
                search_mask = pd.Series([False] * len(filtered))
                
                for col_key in searchable_columns:
                    if col_key in filtered.columns:
                        col_mask = filtered[col_key].astype(str).str.lower().str.contains(
                            search_query, na=False, regex=False
                        )
                        search_mask = search_mask | col_mask
                
                filtered = filtered[search_mask]
        
        # Apply column filters
        for col_key, filter_value in self.state["column_filters"].items():
            if filter_value and col_key in filtered.columns:
                col_config = self.columns.get(col_key)
                if not col_config or not col_config.filterable:
                    continue
                
                if col_config.type == ColumnType.TEXT:
                    filtered = filtered[
                        filtered[col_key].astype(str).str.lower().str.contains(
                            filter_value.lower(), na=False, regex=False
                        )
                    ]
                elif col_config.type in [ColumnType.NUMBER, ColumnType.CURRENCY, ColumnType.PERCENTAGE]:
                    try:
                        numeric_filter = float(filter_value)
                        filtered = filtered[filtered[col_key] == numeric_filter]
                    except ValueError:
                        pass
                elif col_config.type == ColumnType.BOOLEAN:
                    bool_filter = filter_value.lower() in ['true', '1', 'yes', 'on']
                    filtered = filtered[filtered[col_key] == bool_filter]
        
        self.filtered_data = filtered
    
    def _apply_sorting(self):
        """Apply sorting to filtered data"""
        if (self.state["sort_column"] and 
            self.state["sort_direction"] != SortDirection.NONE and
            self.state["sort_column"] in self.filtered_data.columns):
            
            ascending = self.state["sort_direction"] == SortDirection.ASC
            self.filtered_data = self.filtered_data.sort_values(
                by=self.state["sort_column"],
                ascending=ascending,
                na_position='last'
            )
    
    def _get_page_data(self) -> pd.DataFrame:
        """Get data for current page"""
        if not self.config.show_pagination:
            return self.filtered_data
        
        start_idx = self.state["current_page"] * self.state["page_size"]
        end_idx = start_idx + self.state["page_size"]
        
        return self.filtered_data.iloc[start_idx:end_idx]
    
    def _render_search_bar(self):
        """Render search bar"""
        if not self.config.show_search:
            return
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Search table",
                value=self.state["search_query"],
                placeholder="Search across all columns...",
                key=f"{self.table_id}_search",
                label_visibility="collapsed"
            )
            
            if search_query != self.state["search_query"]:
                self.state["search_query"] = search_query
                self.state["current_page"] = 0  # Reset to first page
                self._apply_filters()
                st.rerun()
        
        with col2:
            if st.button("Clear", key=f"{self.table_id}_clear_search"):
                self.state["search_query"] = ""
                self.state["current_page"] = 0
                self._apply_filters()
                st.rerun()
    
    def _render_filters(self):
        """Render column filters"""
        if not self.config.show_filters:
            return
        
        filterable_columns = [col for col in self.columns.values() if col.filterable and not col.hidden]
        
        if not filterable_columns:
            return
        
        with st.expander("🔧 Advanced Filters", expanded=False):
            # Create filter columns
            num_cols = min(3, len(filterable_columns))
            filter_cols = st.columns(num_cols)
            
            for i, col_config in enumerate(filterable_columns):
                col_idx = i % num_cols
                
                with filter_cols[col_idx]:
                    current_filter = self.state["column_filters"].get(col_config.key, "")
                    
                    if col_config.type == ColumnType.BOOLEAN:
                        filter_value = st.selectbox(
                            f"Filter {col_config.label}",
                            options=["", "True", "False"],
                            index=0 if not current_filter else (1 if current_filter.lower() == "true" else 2),
                            key=f"{self.table_id}_filter_{col_config.key}"
                        )
                    else:
                        filter_value = st.text_input(
                            f"Filter {col_config.label}",
                            value=current_filter,
                            placeholder=f"Filter by {col_config.label.lower()}...",
                            key=f"{self.table_id}_filter_{col_config.key}"
                        )
                    
                    if filter_value != current_filter:
                        self.state["column_filters"][col_config.key] = filter_value
                        self.state["current_page"] = 0
                        self._apply_filters()
                        st.rerun()
            
            # Clear all filters button
            if st.button("Clear All Filters", key=f"{self.table_id}_clear_filters"):
                self.state["column_filters"] = {}
                self.state["current_page"] = 0
                self._apply_filters()
                st.rerun()
    
    def _render_column_selector(self):
        """Render column visibility selector"""
        if not self.config.show_column_selector:
            return
        
        with st.expander("👁️ Column Visibility", expanded=False):
            all_columns = [col for col in self.columns.values() if not col.frozen]
            
            for col_config in all_columns:
                is_visible = col_config.key in self.state["visible_columns"]
                
                new_visibility = st.checkbox(
                    col_config.label,
                    value=is_visible,
                    key=f"{self.table_id}_col_vis_{col_config.key}"
                )
                
                if new_visibility != is_visible:
                    if new_visibility:
                        if col_config.key not in self.state["visible_columns"]:
                            self.state["visible_columns"].append(col_config.key)
                    else:
                        if col_config.key in self.state["visible_columns"]:
                            self.state["visible_columns"].remove(col_config.key)
                    st.rerun()
    
    def _render_table_controls(self):
        """Render table control buttons"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Compact mode toggle
            compact = st.checkbox(
                "Compact view",
                value=self.state["compact_mode"],
                key=f"{self.table_id}_compact"
            )
            
            if compact != self.state["compact_mode"]:
                self.state["compact_mode"] = compact
                st.rerun()
        
        with col2:
            # Page size selector
            if self.config.show_pagination:
                page_size = st.selectbox(
                    "Rows per page",
                    options=[5, 10, 25, 50, 100],
                    index=[5, 10, 25, 50, 100].index(self.state["page_size"]),
                    key=f"{self.table_id}_page_size"
                )
                
                if page_size != self.state["page_size"]:
                    self.state["page_size"] = page_size
                    self.state["current_page"] = 0
                    st.rerun()
        
        with col3:
            # Export button
            if self.config.show_export:
                if st.button("📥 Export CSV", key=f"{self.table_id}_export"):
                    csv = self.filtered_data.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"table_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"{self.table_id}_download"
                    )
        
        with col4:
            # Refresh button
            if st.button("🔄 Refresh", key=f"{self.table_id}_refresh"):
                # Clear cache and refresh
                st.cache_data.clear()
                st.rerun()
    
    def _format_cell_value(self, value: Any, col_config: ColumnConfig) -> str:
        """Format cell value based on column type"""
        if pd.isna(value):
            return ""
        
        # Use custom format function if provided
        if col_config.format_func:
            try:
                return col_config.format_func(value)
            except Exception:
                pass
        
        # Default formatting based on type
        if col_config.type == ColumnType.CURRENCY:
            try:
                return f"${float(value):,.2f}"
            except (ValueError, TypeError):
                return str(value)
        
        elif col_config.type == ColumnType.PERCENTAGE:
            try:
                return f"{float(value):.1%}"
            except (ValueError, TypeError):
                return str(value)
        
        elif col_config.type == ColumnType.DATE:
            if isinstance(value, (date, datetime)):
                return value.strftime("%Y-%m-%d")
            return str(value)
        
        elif col_config.type == ColumnType.DATETIME:
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            return str(value)
        
        elif col_config.type == ColumnType.BOOLEAN:
            return "✅" if value else "❌"
        
        elif col_config.type == ColumnType.EMAIL:
            return f"[{value}](mailto:{value})"
        
        elif col_config.type == ColumnType.URL:
            return f"[🔗 Link]({value})"
        
        elif col_config.type == ColumnType.PROGRESS:
            try:
                progress = float(value)
                progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
                return f"{progress_bar} {progress:.1%}"
            except (ValueError, TypeError):
                return str(value)
        
        else:
            return str(value)
    
    def _render_table_header(self, visible_columns: List[str]):
        """Render table header with sorting"""
        header_cols = st.columns([1] + [3] * len(visible_columns))
        
        # Row selector header
        if self.config.selectable_rows:
            with header_cols[0]:
                if self.config.multi_select:
                    select_all = st.checkbox(
                        "All",
                        key=f"{self.table_id}_select_all",
                        label_visibility="collapsed"
                    )
                    
                    if select_all:
                        self.state["selected_rows"] = list(self.filtered_data.index)
                    else:
                        self.state["selected_rows"] = []
        
        # Column headers
        for i, col_key in enumerate(visible_columns):
            col_config = self.columns[col_key]
            
            with header_cols[i + 1]:
                # Create sortable header
                if col_config.sortable:
                    sort_icon = ""
                    if self.state["sort_column"] == col_key:
                        if self.state["sort_direction"] == SortDirection.ASC:
                            sort_icon = " ↑"
                        elif self.state["sort_direction"] == SortDirection.DESC:
                            sort_icon = " ↓"
                    
                    if st.button(
                        f"{col_config.label}{sort_icon}",
                        key=f"{self.table_id}_sort_{col_key}",
                        use_container_width=True
                    ):
                        # Toggle sort direction
                        if self.state["sort_column"] == col_key:
                            if self.state["sort_direction"] == SortDirection.ASC:
                                self.state["sort_direction"] = SortDirection.DESC
                            elif self.state["sort_direction"] == SortDirection.DESC:
                                self.state["sort_direction"] = SortDirection.NONE
                                self.state["sort_column"] = None
                            else:
                                self.state["sort_direction"] = SortDirection.ASC
                        else:
                            self.state["sort_column"] = col_key
                            self.state["sort_direction"] = SortDirection.ASC
                        
                        self._apply_sorting()
                        st.rerun()
                else:
                    st.markdown(f"**{col_config.label}**")
    
    def _render_table_rows(self, page_data: pd.DataFrame, visible_columns: List[str]):
        """Render table rows"""
        for idx, (row_idx, row) in enumerate(page_data.iterrows()):
            row_cols = st.columns([1] + [3] * len(visible_columns))
            
            # Row selector
            if self.config.selectable_rows:
                with row_cols[0]:
                    is_selected = row_idx in self.state["selected_rows"]
                    
                    selected = st.checkbox(
                        "",
                        value=is_selected,
                        key=f"{self.table_id}_row_{row_idx}",
                        label_visibility="collapsed"
                    )
                    
                    if selected != is_selected:
                        if selected:
                            if self.config.multi_select:
                                if row_idx not in self.state["selected_rows"]:
                                    self.state["selected_rows"].append(row_idx)
                            else:
                                self.state["selected_rows"] = [row_idx]
                        else:
                            if row_idx in self.state["selected_rows"]:
                                self.state["selected_rows"].remove(row_idx)
            
            # Data cells
            for i, col_key in enumerate(visible_columns):
                col_config = self.columns[col_key]
                cell_value = row[col_key] if col_key in row else ""
                
                with row_cols[i + 1]:
                    # Use custom render function if provided
                    if col_config.render_func:
                        try:
                            col_config.render_func(cell_value, row, row_idx)
                        except Exception:
                            st.write(str(cell_value))
                    else:
                        formatted_value = self._format_cell_value(cell_value, col_config)
                        
                        # Handle special types
                        if col_config.type in [ColumnType.EMAIL, ColumnType.URL]:
                            st.markdown(formatted_value)
                        elif col_config.type == ColumnType.IMAGE:
                            if formatted_value:
                                st.image(formatted_value, width=50)
                        elif col_config.type == ColumnType.BADGE:
                            st.markdown(f"`{formatted_value}`")
                        else:
                            st.write(formatted_value)
            
            # Add separator for non-compact mode
            if not self.state["compact_mode"] and idx < len(page_data) - 1:
                st.divider()
    
    def _render_pagination(self):
        """Render pagination controls"""
        if not self.config.show_pagination:
            return
        
        total_rows = len(self.filtered_data)
        total_pages = math.ceil(total_rows / self.state["page_size"])
        
        if total_pages <= 1:
            return
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", disabled=self.state["current_page"] == 0, key=f"{self.table_id}_first"):
                self.state["current_page"] = 0
                st.rerun()
        
        with col2:
            if st.button("◀️ Prev", disabled=self.state["current_page"] == 0, key=f"{self.table_id}_prev"):
                self.state["current_page"] = max(0, self.state["current_page"] - 1)
                st.rerun()
        
        with col3:
            st.markdown(f"<div style='text-align: center; padding: 0.5rem;'>Page {self.state['current_page'] + 1} of {total_pages}<br><small>{total_rows} total rows</small></div>", unsafe_allow_html=True)
        
        with col4:
            if st.button("Next ▶️", disabled=self.state["current_page"] >= total_pages - 1, key=f"{self.table_id}_next"):
                self.state["current_page"] = min(total_pages - 1, self.state["current_page"] + 1)
                st.rerun()
        
        with col5:
            if st.button("Last ⏭️", disabled=self.state["current_page"] >= total_pages - 1, key=f"{self.table_id}_last"):
                self.state["current_page"] = total_pages - 1
                st.rerun()
    
    def render(self) -> Dict[str, Any]:
        """Render the complete enhanced table"""
        
        # Table header with info
        col1, col2 = st.columns([2, 1])
        
        with col1:
            total_rows = len(self.data)
            filtered_rows = len(self.filtered_data)
            
            if filtered_rows != total_rows:
                st.markdown(f"**Showing {filtered_rows} of {total_rows} rows** (filtered)")
            else:
                st.markdown(f"**{total_rows} rows**")
        
        with col2:
            if self.state["selected_rows"]:
                st.markdown(f"**{len(self.state['selected_rows'])} selected**")
        
        # Search bar
        self._render_search_bar()
        
        # Filters and controls
        control_col1, control_col2 = st.columns(2)
        
        with control_col1:
            self._render_filters()
        
        with control_col2:
            self._render_column_selector()
        
        # Table controls
        self._render_table_controls()
        
        st.divider()
        
        # Main table
        if len(self.filtered_data) == 0:
            st.info("No data matches the current filters.")
            return {
                "selected_rows": self.state["selected_rows"],
                "filtered_data": self.filtered_data,
                "total_rows": len(self.data)
            }
        
        # Get visible columns
        visible_columns = [col for col in self.state["visible_columns"] if col in self.data.columns]
        
        if not visible_columns:
            st.warning("No columns are visible. Please select columns to display.")
            return {
                "selected_rows": self.state["selected_rows"],
                "filtered_data": self.filtered_data,
                "total_rows": len(self.data)
            }
        
        # Render table
        page_data = self._get_page_data()
        
        # Table container with styling
        table_classes = ["enhanced-table"]
        if self.state["compact_mode"]:
            table_classes.append("compact")
        if self.config.striped_rows:
            table_classes.append("striped")
        
        with st.container():
            # Render header
            self._render_table_header(visible_columns)
            
            st.divider()
            
            # Render rows
            self._render_table_rows(page_data, visible_columns)
        
        # Pagination
        self._render_pagination()
        
        return {
            "selected_rows": self.state["selected_rows"],
            "filtered_data": self.filtered_data,
            "page_data": page_data,
            "total_rows": len(self.data),
            "visible_columns": visible_columns
        }
    
    def get_selected_data(self) -> pd.DataFrame:
        """Get data for selected rows"""
        if not self.state["selected_rows"]:
            return pd.DataFrame()
        
        return self.data.loc[self.state["selected_rows"]]
    
    def clear_selection(self):
        """Clear row selection"""
        self.state["selected_rows"] = []
    
    def select_all_filtered(self):
        """Select all filtered rows"""
        self.state["selected_rows"] = list(self.filtered_data.index)
    
    def reset_filters(self):
        """Reset all filters and search"""
        self.state["search_query"] = ""
        self.state["column_filters"] = {}
        self.state["current_page"] = 0
        self._apply_filters()


# Convenience functions for common table types

def create_user_table(users_data: pd.DataFrame, table_id: str = "users") -> EnhancedDataTable:
    """Create a table for user data"""
    columns = [
        ColumnConfig("id", "ID", ColumnType.TEXT, width="80px"),
        ColumnConfig("name", "Name", ColumnType.TEXT),
        ColumnConfig("email", "Email", ColumnType.EMAIL),
        ColumnConfig("created_at", "Created", ColumnType.DATETIME),
        ColumnConfig("active", "Active", ColumnType.BOOLEAN, width="80px"),
    ]
    
    config = TableConfig(
        page_size=15,
        selectable_rows=True,
        multi_select=True
    )
    
    return EnhancedDataTable(users_data, columns, config, table_id)


def create_assessment_table(assessments_data: pd.DataFrame, table_id: str = "assessments") -> EnhancedDataTable:
    """Create a table for assessment data"""
    columns = [
        ColumnConfig("id", "Assessment ID", ColumnType.TEXT, width="120px"),
        ColumnConfig("skill_area", "Skill Area", ColumnType.TEXT),
        ColumnConfig("score", "Score", ColumnType.PERCENTAGE, width="100px"),
        ColumnConfig("status", "Status", ColumnType.BADGE, width="100px"),
        ColumnConfig("completed_at", "Completed", ColumnType.DATETIME),
        ColumnConfig("duration", "Duration", ColumnType.TEXT, width="100px"),
    ]
    
    config = TableConfig(
        page_size=10,
        selectable_rows=True
    )
    
    return EnhancedDataTable(assessments_data, columns, config, table_id)


def create_learning_path_table(paths_data: pd.DataFrame, table_id: str = "learning_paths") -> EnhancedDataTable:
    """Create a table for learning path data"""
    columns = [
        ColumnConfig("id", "Path ID", ColumnType.TEXT, width="100px"),
        ColumnConfig("title", "Title", ColumnType.TEXT),
        ColumnConfig("progress", "Progress", ColumnType.PROGRESS, width="150px"),
        ColumnConfig("difficulty", "Difficulty", ColumnType.BADGE, width="100px"),
        ColumnConfig("estimated_hours", "Est. Hours", ColumnType.NUMBER, width="100px"),
        ColumnConfig("created_at", "Created", ColumnType.DATE),
        ColumnConfig("status", "Status", ColumnType.BADGE, width="100px"),
    ]
    
    config = TableConfig(
        page_size=8,
        selectable_rows=True,
        compact_mode=True
    )
    
    return EnhancedDataTable(paths_data, columns, config, table_id)
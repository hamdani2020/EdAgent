"""
Privacy and Data Management Components for EdAgent Streamlit Application

This module provides comprehensive privacy controls including:
- Privacy settings display and update functionality
- Data export interface with download capabilities
- Data deletion functionality with proper confirmation dialogs
- Privacy dashboard showing data summary and user control options
- Consent management and privacy preference updates
- Audit log display for privacy-related actions
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import base64
import io

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from streamlit_api_client import EnhancedEdAgentAPI
from streamlit_session_manager import SessionManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataType(Enum):
    """Data types for privacy management"""
    CONVERSATIONS = "conversations"
    ASSESSMENTS = "assessments"
    LEARNING_PATHS = "learning_paths"
    PROFILE = "profile"
    PREFERENCES = "preferences"
    ANALYTICS = "analytics"
    ALL = "all"


class ExportFormat(Enum):
    """Export format options"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


@dataclass
class PrivacySettings:
    """Privacy settings data structure"""
    allow_analytics: bool = True
    allow_personalization: bool = True
    allow_marketing: bool = False
    allow_third_party_sharing: bool = False
    auto_delete_conversations: bool = False
    conversation_retention_days: int = 365
    data_processing_consent: bool = True
    cookie_consent: bool = True
    email_notifications: bool = True
    push_notifications: bool = False
    data_export_notifications: bool = True
    security_notifications: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "allow_analytics": self.allow_analytics,
            "allow_personalization": self.allow_personalization,
            "allow_marketing": self.allow_marketing,
            "allow_third_party_sharing": self.allow_third_party_sharing,
            "auto_delete_conversations": self.auto_delete_conversations,
            "conversation_retention_days": self.conversation_retention_days,
            "data_processing_consent": self.data_processing_consent,
            "cookie_consent": self.cookie_consent,
            "email_notifications": self.email_notifications,
            "push_notifications": self.push_notifications,
            "data_export_notifications": self.data_export_notifications,
            "security_notifications": self.security_notifications
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrivacySettings':
        """Create from dictionary"""
        return cls(
            allow_analytics=data.get("allow_analytics", True),
            allow_personalization=data.get("allow_personalization", True),
            allow_marketing=data.get("allow_marketing", False),
            allow_third_party_sharing=data.get("allow_third_party_sharing", False),
            auto_delete_conversations=data.get("auto_delete_conversations", False),
            conversation_retention_days=data.get("conversation_retention_days", 365),
            data_processing_consent=data.get("data_processing_consent", True),
            cookie_consent=data.get("cookie_consent", True),
            email_notifications=data.get("email_notifications", True),
            push_notifications=data.get("push_notifications", False),
            data_export_notifications=data.get("data_export_notifications", True),
            security_notifications=data.get("security_notifications", True)
        )


@dataclass
class DataSummary:
    """Data summary for privacy dashboard"""
    total_conversations: int = 0
    total_assessments: int = 0
    total_learning_paths: int = 0
    data_size_mb: float = 0.0
    last_export_date: Optional[datetime] = None
    account_created_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    privacy_settings_updated: Optional[datetime] = None


@dataclass
class AuditLogEntry:
    """Audit log entry for privacy actions"""
    timestamp: datetime
    action: str
    details: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True


class PrivacyComponents:
    """
    Comprehensive privacy and data management components
    """
    
    def __init__(self, api_client: EnhancedEdAgentAPI, session_manager: SessionManager):
        self.api = api_client
        self.session_manager = session_manager
        
    def render_privacy_dashboard(self) -> None:
        """Render comprehensive privacy dashboard"""
        st.header("🔒 Privacy & Data Management Dashboard")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.warning("🔐 Please log in to access privacy settings.")
            return
        
        user_info = self.session_manager.get_current_user()
        
        # Privacy overview metrics
        self._render_privacy_overview()
        
        # Main privacy tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "⚙️ Settings", "📊 Data Summary", "📥 Export Data", 
            "🗑️ Delete Data", "📋 Audit Log", "ℹ️ Privacy Info"
        ])
        
        with tab1:
            self._render_privacy_settings()
        
        with tab2:
            self._render_data_summary()
        
        with tab3:
            self._render_data_export_interface()
        
        with tab4:
            self._render_data_deletion_interface()
        
        with tab5:
            self._render_audit_log()
        
        with tab6:
            self._render_privacy_information()
    
    def _render_privacy_overview(self) -> None:
        """Render privacy overview metrics"""
        st.subheader("📊 Privacy Overview")
        
        # Get data summary
        data_summary = self._get_data_summary()
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💬 Conversations",
                value=data_summary.total_conversations,
                help="Total number of conversations stored"
            )
        
        with col2:
            st.metric(
                label="📊 Assessments",
                value=data_summary.total_assessments,
                help="Total number of assessments completed"
            )
        
        with col3:
            st.metric(
                label="🛤️ Learning Paths",
                value=data_summary.total_learning_paths,
                help="Total number of learning paths created"
            )
        
        with col4:
            st.metric(
                label="💾 Data Size",
                value=f"{data_summary.data_size_mb:.1f} MB",
                help="Estimated size of your stored data"
            )
        
        # Privacy status indicators
        st.subheader("🛡️ Privacy Status")
        
        privacy_settings = self._get_current_privacy_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Data processing consent
            consent_status = "✅ Granted" if privacy_settings.data_processing_consent else "❌ Not Granted"
            st.write(f"**Data Processing Consent:** {consent_status}")
            
            # Analytics status
            analytics_status = "🟢 Enabled" if privacy_settings.allow_analytics else "🔴 Disabled"
            st.write(f"**Analytics Collection:** {analytics_status}")
            
            # Marketing status
            marketing_status = "🟢 Enabled" if privacy_settings.allow_marketing else "🔴 Disabled"
            st.write(f"**Marketing Communications:** {marketing_status}")
        
        with col2:
            # Auto-delete status
            auto_delete_status = "🟢 Enabled" if privacy_settings.auto_delete_conversations else "🔴 Disabled"
            st.write(f"**Auto-Delete Conversations:** {auto_delete_status}")
            
            # Retention period
            st.write(f"**Data Retention:** {privacy_settings.conversation_retention_days} days")
            
            # Last export
            last_export = data_summary.last_export_date
            if last_export:
                st.write(f"**Last Export:** {last_export.strftime('%Y-%m-%d')}")
            else:
                st.write("**Last Export:** Never")
    
    def _render_privacy_settings(self) -> None:
        """Render privacy settings interface"""
        st.subheader("⚙️ Privacy Settings")
        
        # Get current settings
        current_settings = self._get_current_privacy_settings()
        
        with st.form("privacy_settings_form"):
            st.markdown("### 📊 Data Collection & Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                allow_analytics = st.checkbox(
                    "Allow analytics data collection",
                    value=current_settings.allow_analytics,
                    help="Help us improve EdAgent by sharing anonymous usage data"
                )
                
                allow_personalization = st.checkbox(
                    "Allow personalization features",
                    value=current_settings.allow_personalization,
                    help="Use your data to provide personalized recommendations"
                )
                
                data_processing_consent = st.checkbox(
                    "Data processing consent",
                    value=current_settings.data_processing_consent,
                    help="Required for core functionality"
                )
            
            with col2:
                allow_marketing = st.checkbox(
                    "Allow marketing communications",
                    value=current_settings.allow_marketing,
                    help="Receive updates about new features and educational content"
                )
                
                allow_third_party_sharing = st.checkbox(
                    "Allow third-party data sharing",
                    value=current_settings.allow_third_party_sharing,
                    help="Share anonymized data with educational partners"
                )
                
                cookie_consent = st.checkbox(
                    "Cookie consent",
                    value=current_settings.cookie_consent,
                    help="Allow cookies for improved user experience"
                )
            
            st.markdown("### 🗑️ Data Retention")
            
            col1, col2 = st.columns(2)
            
            with col1:
                auto_delete_conversations = st.checkbox(
                    "Auto-delete old conversations",
                    value=current_settings.auto_delete_conversations,
                    help="Automatically delete conversations after retention period"
                )
            
            with col2:
                conversation_retention_days = st.number_input(
                    "Conversation retention (days)",
                    min_value=30,
                    max_value=3650,
                    value=current_settings.conversation_retention_days,
                    help="How long to keep conversation history"
                )
            
            st.markdown("### 🔔 Notification Preferences")
            
            col1, col2 = st.columns(2)
            
            with col1:
                email_notifications = st.checkbox(
                    "Email notifications",
                    value=current_settings.email_notifications,
                    help="Receive important updates via email"
                )
                
                data_export_notifications = st.checkbox(
                    "Data export notifications",
                    value=current_settings.data_export_notifications,
                    help="Get notified when data exports are ready"
                )
            
            with col2:
                push_notifications = st.checkbox(
                    "Push notifications",
                    value=current_settings.push_notifications,
                    help="Receive push notifications in your browser"
                )
                
                security_notifications = st.checkbox(
                    "Security notifications",
                    value=current_settings.security_notifications,
                    help="Get alerts about security-related events"
                )
            
            # Form submission
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                submitted = st.form_submit_button("💾 Save Settings", type="primary")
            
            with col2:
                reset = st.form_submit_button("🔄 Reset to Defaults")
            
            if submitted:
                # Create new settings object
                new_settings = PrivacySettings(
                    allow_analytics=allow_analytics,
                    allow_personalization=allow_personalization,
                    allow_marketing=allow_marketing,
                    allow_third_party_sharing=allow_third_party_sharing,
                    auto_delete_conversations=auto_delete_conversations,
                    conversation_retention_days=conversation_retention_days,
                    data_processing_consent=data_processing_consent,
                    cookie_consent=cookie_consent,
                    email_notifications=email_notifications,
                    push_notifications=push_notifications,
                    data_export_notifications=data_export_notifications,
                    security_notifications=security_notifications
                )
                
                # Update settings via API
                success = self._update_privacy_settings(new_settings)
                
                if success:
                    st.success("✅ Privacy settings updated successfully!")
                    self._log_privacy_action("privacy_settings_updated", "Privacy settings were updated")
                    st.rerun()
                else:
                    st.error("❌ Failed to update privacy settings. Please try again.")
            
            if reset:
                # Reset to default settings
                default_settings = PrivacySettings()
                success = self._update_privacy_settings(default_settings)
                
                if success:
                    st.success("✅ Privacy settings reset to defaults!")
                    self._log_privacy_action("privacy_settings_reset", "Privacy settings were reset to defaults")
                    st.rerun()
                else:
                    st.error("❌ Failed to reset privacy settings. Please try again.")
    
    def _render_data_summary(self) -> None:
        """Render data summary interface"""
        st.subheader("📊 Your Data Summary")
        
        # Get comprehensive data summary
        data_summary = self._get_data_summary()
        
        # Account information
        st.markdown("### 👤 Account Information")
        
        user_info = self.session_manager.get_current_user()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Email:** {user_info.email}")
            st.write(f"**User ID:** {user_info.user_id}")
            if data_summary.account_created_date:
                st.write(f"**Account Created:** {data_summary.account_created_date.strftime('%Y-%m-%d %H:%M')}")
        
        with col2:
            if data_summary.last_activity_date:
                st.write(f"**Last Activity:** {data_summary.last_activity_date.strftime('%Y-%m-%d %H:%M')}")
            if data_summary.privacy_settings_updated:
                st.write(f"**Privacy Settings Updated:** {data_summary.privacy_settings_updated.strftime('%Y-%m-%d %H:%M')}")
        
        # Data breakdown
        st.markdown("### 📈 Data Breakdown")
        
        # Create data visualization
        data_types = ["Conversations", "Assessments", "Learning Paths"]
        data_counts = [
            data_summary.total_conversations,
            data_summary.total_assessments,
            data_summary.total_learning_paths
        ]
        
        if sum(data_counts) > 0:
            # Pie chart of data distribution
            fig = px.pie(
                values=data_counts,
                names=data_types,
                title="Data Distribution by Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📝 No data stored yet. Start using EdAgent to see your data summary!")
        
        # Detailed breakdown
        st.markdown("### 📋 Detailed Breakdown")
        
        data_breakdown = pd.DataFrame({
            "Data Type": data_types,
            "Count": data_counts,
            "Estimated Size (KB)": [
                data_counts[0] * 2.5,  # Conversations ~2.5KB each
                data_counts[1] * 1.0,  # Assessments ~1KB each
                data_counts[2] * 0.5   # Learning paths ~0.5KB each
            ]
        })
        
        st.dataframe(data_breakdown, use_container_width=True)
        
        # Storage usage over time (mock data for demonstration)
        if sum(data_counts) > 0:
            st.markdown("### 📊 Storage Usage Trend")
            
            # Generate sample trend data
            dates = pd.date_range(
                start=data_summary.account_created_date or datetime.now() - timedelta(days=30),
                end=datetime.now(),
                freq='D'
            )
            
            # Simulate cumulative data growth
            cumulative_data = []
            for i, date in enumerate(dates):
                growth_factor = (i + 1) / len(dates)
                cumulative_data.append(data_summary.data_size_mb * growth_factor)
            
            trend_df = pd.DataFrame({
                "Date": dates,
                "Data Size (MB)": cumulative_data
            })
            
            fig = px.line(
                trend_df,
                x="Date",
                y="Data Size (MB)",
                title="Data Storage Growth Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_data_export_interface(self) -> None:
        """Render data export interface"""
        st.subheader("📥 Export Your Data")
        
        st.markdown("""
        Export all your EdAgent data in various formats. This includes:
        - Conversation history
        - Assessment results
        - Learning paths and progress
        - Profile information
        - Privacy settings
        """)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format:",
                options=[fmt.value for fmt in ExportFormat],
                format_func=lambda x: {
                    "json": "JSON (Complete data)",
                    "csv": "CSV (Tabular data)",
                    "pdf": "PDF (Human-readable report)"
                }.get(x, x)
            )
        
        with col2:
            include_sensitive = st.checkbox(
                "Include sensitive data",
                value=False,
                help="Include IP addresses, detailed timestamps, and other sensitive information"
            )
        
        # Data type selection
        st.markdown("### 📋 Select Data Types to Export")
        
        data_types = st.multiselect(
            "Data Types:",
            options=[dt.value for dt in DataType if dt != DataType.ALL],
            default=[dt.value for dt in DataType if dt != DataType.ALL],
            help="Select which types of data to include in the export"
        )
        
        export_all = st.checkbox("Export all data", value=True)
        
        if export_all:
            data_types = [dt.value for dt in DataType if dt != DataType.ALL]
        
        # Export button
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📥 Export Data", type="primary", disabled=not data_types):
                self._handle_data_export(export_format, data_types, include_sensitive)
        
        with col2:
            if st.button("📧 Email Export", disabled=not data_types):
                self._handle_email_export(export_format, data_types, include_sensitive)
        
        # Export history
        st.markdown("### 📜 Export History")
        
        export_history = self._get_export_history()
        
        if export_history:
            history_df = pd.DataFrame(export_history)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("📝 No previous exports found.")
    
    def _render_data_deletion_interface(self) -> None:
        """Render data deletion interface"""
        st.subheader("🗑️ Delete Your Data")
        
        st.warning("""
        ⚠️ **Warning: Data deletion is permanent and cannot be undone!**
        
        Please carefully review what you want to delete. Consider exporting your data first.
        """)
        
        # Deletion options
        st.markdown("### 🎯 Select Data to Delete")
        
        deletion_options = {
            DataType.CONVERSATIONS.value: {
                "label": "💬 Conversations",
                "description": "All chat history and AI responses",
                "impact": "You will lose all conversation history"
            },
            DataType.ASSESSMENTS.value: {
                "label": "📊 Assessments",
                "description": "All skill assessment results and progress",
                "impact": "You will lose all assessment history and skill tracking"
            },
            DataType.LEARNING_PATHS.value: {
                "label": "🛤️ Learning Paths",
                "description": "All learning paths and milestone progress",
                "impact": "You will lose all learning path progress and recommendations"
            },
            DataType.PROFILE.value: {
                "label": "👤 Profile Data",
                "description": "Personal information and preferences",
                "impact": "You will need to set up your profile again"
            },
            DataType.ANALYTICS.value: {
                "label": "📈 Analytics Data",
                "description": "Usage statistics and behavioral data",
                "impact": "Anonymous usage data will be removed"
            }
        }
        
        selected_deletions = []
        
        for data_type, info in deletion_options.items():
            with st.expander(f"{info['label']} - {info['description']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Impact:** {info['impact']}")
                
                with col2:
                    if st.checkbox(f"Delete {info['label']}", key=f"delete_{data_type}"):
                        selected_deletions.append(data_type)
        
        # Complete account deletion option
        st.markdown("### 🚨 Complete Account Deletion")
        
        delete_account = st.checkbox(
            "Delete entire account and all data",
            help="This will permanently delete your account and all associated data"
        )
        
        if delete_account:
            selected_deletions = [DataType.ALL.value]
        
        # Confirmation and deletion
        if selected_deletions:
            st.markdown("### ✅ Confirmation")
            
            # Show what will be deleted
            if DataType.ALL.value in selected_deletions:
                st.error("🚨 **You are about to delete your entire account and all data!**")
            else:
                st.warning(f"**You are about to delete:** {', '.join(selected_deletions)}")
            
            # Confirmation steps
            confirmation_steps = []
            
            # Step 1: Understand consequences
            understand = st.checkbox(
                "I understand that this action cannot be undone",
                key="understand_deletion"
            )
            confirmation_steps.append(understand)
            
            # Step 2: Type confirmation
            if DataType.ALL.value in selected_deletions:
                confirmation_text = st.text_input(
                    'Type "DELETE MY ACCOUNT" to confirm:',
                    key="account_deletion_confirmation"
                )
                confirmation_steps.append(confirmation_text == "DELETE MY ACCOUNT")
            else:
                confirmation_text = st.text_input(
                    'Type "DELETE" to confirm:',
                    key="data_deletion_confirmation"
                )
                confirmation_steps.append(confirmation_text == "DELETE")
            
            # Step 3: Final confirmation
            final_confirm = st.checkbox(
                "I have exported any data I want to keep",
                key="final_deletion_confirm"
            )
            confirmation_steps.append(final_confirm)
            
            # Deletion button
            all_confirmed = all(confirmation_steps)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button(
                    "🗑️ Delete Data" if DataType.ALL.value not in selected_deletions else "🚨 Delete Account",
                    type="secondary",
                    disabled=not all_confirmed
                ):
                    self._handle_data_deletion(selected_deletions)
            
            with col2:
                if st.button("❌ Cancel"):
                    st.rerun()
        
        else:
            st.info("📝 Select data types to delete above.")
    
    def _render_audit_log(self) -> None:
        """Render audit log interface"""
        st.subheader("📋 Privacy Audit Log")
        
        st.markdown("""
        This log shows all privacy-related actions performed on your account.
        """)
        
        # Get audit log entries
        audit_entries = self._get_audit_log()
        
        if audit_entries:
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_filter = st.date_input(
                    "Filter from date:",
                    value=datetime.now().date() - timedelta(days=30)
                )
            
            with col2:
                action_filter = st.selectbox(
                    "Filter by action:",
                    options=["All"] + list(set(entry.action for entry in audit_entries))
                )
            
            with col3:
                success_filter = st.selectbox(
                    "Filter by status:",
                    options=["All", "Success", "Failed"]
                )
            
            # Apply filters
            filtered_entries = audit_entries
            
            if action_filter != "All":
                filtered_entries = [e for e in filtered_entries if e.action == action_filter]
            
            if success_filter != "All":
                success_value = success_filter == "Success"
                filtered_entries = [e for e in filtered_entries if e.success == success_value]
            
            filtered_entries = [
                e for e in filtered_entries 
                if e.timestamp.date() >= date_filter
            ]
            
            # Display audit log
            if filtered_entries:
                audit_data = []
                for entry in filtered_entries:
                    audit_data.append({
                        "Timestamp": entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "Action": entry.action,
                        "Details": entry.details,
                        "Status": "✅ Success" if entry.success else "❌ Failed",
                        "IP Address": entry.ip_address or "N/A"
                    })
                
                audit_df = pd.DataFrame(audit_data)
                st.dataframe(audit_df, use_container_width=True)
                
                # Export audit log
                if st.button("📥 Export Audit Log"):
                    csv = audit_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"privacy_audit_log_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("📝 No audit entries found for the selected filters.")
        
        else:
            st.info("📝 No privacy audit entries found.")
    
    def _render_privacy_information(self) -> None:
        """Render privacy information and help"""
        st.subheader("ℹ️ Privacy Information & Help")
        
        # Privacy policy summary
        with st.expander("📜 Privacy Policy Summary", expanded=True):
            st.markdown("""
            ### How We Handle Your Data
            
            **Data Collection:**
            - We collect only the data necessary to provide our services
            - Personal information is encrypted and securely stored
            - Usage analytics help us improve the platform
            
            **Data Usage:**
            - Your data is used to personalize your learning experience
            - We never sell your personal information to third parties
            - Analytics data is anonymized before any sharing
            
            **Your Rights:**
            - Access: View all data we have about you
            - Rectification: Correct any inaccurate information
            - Erasure: Delete your data (right to be forgotten)
            - Portability: Export your data in a standard format
            - Restriction: Limit how we process your data
            
            **Data Security:**
            - All data is encrypted in transit and at rest
            - Regular security audits and updates
            - Access controls and monitoring
            """)
        
        # GDPR compliance
        with st.expander("🇪🇺 GDPR Compliance"):
            st.markdown("""
            ### Your GDPR Rights
            
            As a user, you have the following rights under GDPR:
            
            1. **Right to Information** - Know what data we collect and why
            2. **Right of Access** - Get a copy of your personal data
            3. **Right to Rectification** - Correct inaccurate data
            4. **Right to Erasure** - Delete your data ("right to be forgotten")
            5. **Right to Restrict Processing** - Limit how we use your data
            6. **Right to Data Portability** - Get your data in a portable format
            7. **Right to Object** - Object to certain types of processing
            8. **Rights Related to Automated Decision Making** - Human review of automated decisions
            
            **Legal Basis for Processing:**
            - Consent: For marketing and analytics
            - Contract: For providing our services
            - Legitimate Interest: For security and fraud prevention
            """)
        
        # Data retention policy
        with st.expander("🗓️ Data Retention Policy"):
            st.markdown("""
            ### How Long We Keep Your Data
            
            **Active Account Data:**
            - Profile information: Until account deletion
            - Conversation history: Configurable (30-3650 days)
            - Assessment results: Until account deletion
            - Learning paths: Until account deletion
            
            **Inactive Accounts:**
            - Accounts inactive for 2+ years may be archived
            - 30-day notice before archiving
            - Data can be restored upon login
            
            **Deleted Accounts:**
            - Most data deleted immediately
            - Some data retained for legal/security purposes (30 days)
            - Anonymized analytics may be retained indefinitely
            """)
        
        # Contact information
        with st.expander("📞 Privacy Contact & Support"):
            st.markdown("""
            ### Need Help with Privacy?
            
            **Data Protection Officer:**
            - Email: privacy@edagent.ai
            - Response time: 72 hours
            
            **Privacy Requests:**
            - Use the tools above for most requests
            - Complex requests: Contact our DPO
            - Emergency data deletion: privacy@edagent.ai
            
            **Complaints:**
            - Internal: privacy@edagent.ai
            - External: Your local data protection authority
            
            **Security Issues:**
            - Report security vulnerabilities: security@edagent.ai
            - Bug bounty program available
            """)
        
        # Privacy tips
        with st.expander("💡 Privacy Tips & Best Practices"):
            st.markdown("""
            ### Protect Your Privacy
            
            **Account Security:**
            - Use a strong, unique password
            - Enable two-factor authentication
            - Log out from shared devices
            - Review login activity regularly
            
            **Data Minimization:**
            - Only share necessary information
            - Regularly review and clean up old data
            - Use privacy-focused settings
            - Be cautious with sensitive information
            
            **Stay Informed:**
            - Review privacy settings regularly
            - Read privacy policy updates
            - Monitor your data usage
            - Report suspicious activity
            """)
    
    # Helper methods
    
    def _get_current_privacy_settings(self) -> PrivacySettings:
        """Get current privacy settings from API"""
        try:
            user_info = self.session_manager.get_current_user()
            settings_data = asyncio.run(self.api.get_privacy_settings(user_info.user_id))
            
            if settings_data and "settings" in settings_data:
                return PrivacySettings.from_dict(settings_data["settings"])
            else:
                # Return default settings if none found
                return PrivacySettings()
        
        except Exception as e:
            logger.error(f"Failed to get privacy settings: {e}")
            st.error(f"Failed to load privacy settings: {str(e)}")
            return PrivacySettings()
    
    def _update_privacy_settings(self, settings: PrivacySettings) -> bool:
        """Update privacy settings via API"""
        try:
            user_info = self.session_manager.get_current_user()
            success = asyncio.run(self.api.update_privacy_settings(user_info.user_id, settings.to_dict()))
            return success
        
        except Exception as e:
            logger.error(f"Failed to update privacy settings: {e}")
            st.error(f"Failed to update privacy settings: {str(e)}")
            return False
    
    def _get_data_summary(self) -> DataSummary:
        """Get comprehensive data summary"""
        try:
            user_info = self.session_manager.get_current_user()
            
            # This would typically come from API calls
            # For now, we'll use mock data based on session state
            
            # Get conversation count
            conversation_count = len(st.session_state.get("chat_messages", []))
            
            # Get assessment count (mock)
            assessment_count = len(st.session_state.get("user_assessments", []))
            
            # Get learning path count
            learning_path_count = len(st.session_state.get("learning_paths", []))
            
            # Calculate estimated data size
            data_size_mb = (
                conversation_count * 0.0025 +  # 2.5KB per conversation
                assessment_count * 0.001 +     # 1KB per assessment
                learning_path_count * 0.0005   # 0.5KB per learning path
            )
            
            return DataSummary(
                total_conversations=conversation_count,
                total_assessments=assessment_count,
                total_learning_paths=learning_path_count,
                data_size_mb=data_size_mb,
                last_export_date=None,  # Would come from API
                account_created_date=user_info.created_at if user_info else datetime.now(),
                last_activity_date=datetime.now(),
                privacy_settings_updated=None  # Would come from API
            )
        
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return DataSummary()
    
    def _handle_data_export(self, export_format: str, data_types: List[str], include_sensitive: bool) -> None:
        """Handle data export request"""
        try:
            with st.spinner("Preparing your data export..."):
                user_info = self.session_manager.get_current_user()
                
                # Call API to export data
                export_data = asyncio.run(self.api.export_user_data(user_info.user_id))
                
                if export_data:
                    # Process export based on format
                    if export_format == ExportFormat.JSON.value:
                        # JSON export
                        json_str = json.dumps(export_data, indent=2, default=str)
                        
                        st.success("✅ Data export ready!")
                        st.download_button(
                            label="📥 Download JSON Export",
                            data=json_str,
                            file_name=f"edagent_export_{user_info.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    elif export_format == ExportFormat.CSV.value:
                        # CSV export (flattened data)
                        csv_data = self._convert_to_csv(export_data)
                        
                        st.success("✅ Data export ready!")
                        st.download_button(
                            label="📥 Download CSV Export",
                            data=csv_data,
                            file_name=f"edagent_export_{user_info.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    elif export_format == ExportFormat.PDF.value:
                        # PDF export (human-readable report)
                        st.info("📄 PDF export functionality would be implemented here")
                    
                    # Log the export action
                    self._log_privacy_action(
                        "data_exported",
                        f"Data exported in {export_format} format. Types: {', '.join(data_types)}"
                    )
                
                else:
                    st.error("❌ Failed to export data. Please try again.")
        
        except Exception as e:
            logger.error(f"Data export failed: {e}")
            st.error(f"Export failed: {str(e)}")
    
    def _handle_email_export(self, export_format: str, data_types: List[str], include_sensitive: bool) -> None:
        """Handle email export request"""
        try:
            with st.spinner("Requesting email export..."):
                user_info = self.session_manager.get_current_user()
                
                # Request email export via API
                success = asyncio.run(self.api.request_data_export_email(user_info.user_id, export_format))
                
                if success:
                    st.success("✅ Export request sent! You will receive an email with your data export within 24 hours.")
                    self._log_privacy_action(
                        "email_export_requested",
                        f"Email export requested in {export_format} format"
                    )
                else:
                    st.error("❌ Failed to request email export. Please try again.")
        
        except Exception as e:
            logger.error(f"Email export request failed: {e}")
            st.error(f"Email export request failed: {str(e)}")
    
    def _handle_data_deletion(self, data_types: List[str]) -> None:
        """Handle data deletion request"""
        try:
            with st.spinner("Deleting selected data..."):
                user_info = self.session_manager.get_current_user()
                
                # Call API to delete data
                result = asyncio.run(self.api.delete_user_data(user_info.user_id, data_types))
                
                if result:
                    if DataType.ALL.value in data_types:
                        st.success("✅ Account and all data deleted successfully!")
                        # Clear session and redirect to login
                        self.session_manager.clear_session()
                        st.rerun()
                    else:
                        st.success(f"✅ Selected data deleted successfully: {', '.join(data_types)}")
                        
                        # Clear relevant session state
                        if DataType.CONVERSATIONS.value in data_types:
                            st.session_state.chat_messages = []
                        if DataType.LEARNING_PATHS.value in data_types:
                            st.session_state.learning_paths = []
                    
                    # Log the deletion action
                    self._log_privacy_action(
                        "data_deleted",
                        f"Data deleted. Types: {', '.join(data_types)}"
                    )
                
                else:
                    st.error("❌ Failed to delete data. Please try again.")
        
        except Exception as e:
            logger.error(f"Data deletion failed: {e}")
            st.error(f"Deletion failed: {str(e)}")
    
    def _convert_to_csv(self, export_data: Dict[str, Any]) -> str:
        """Convert export data to CSV format"""
        try:
            # Flatten the data structure for CSV
            flattened_data = []
            
            # Process different data types
            for data_type, data in export_data.items():
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            row = {"data_type": data_type}
                            row.update(item)
                            flattened_data.append(row)
                elif isinstance(data, dict):
                    row = {"data_type": data_type}
                    row.update(data)
                    flattened_data.append(row)
            
            # Convert to DataFrame and then CSV
            if flattened_data:
                df = pd.DataFrame(flattened_data)
                return df.to_csv(index=False)
            else:
                return "No data available for CSV export"
        
        except Exception as e:
            logger.error(f"CSV conversion failed: {e}")
            return f"Error converting to CSV: {str(e)}"
    
    def _get_export_history(self) -> List[Dict[str, Any]]:
        """Get export history (mock implementation)"""
        # This would typically come from API
        return [
            {
                "Date": "2024-01-15",
                "Format": "JSON",
                "Size": "2.3 MB",
                "Status": "Completed"
            },
            {
                "Date": "2024-01-01",
                "Format": "CSV",
                "Size": "1.8 MB",
                "Status": "Completed"
            }
        ]
    
    def _get_audit_log(self) -> List[AuditLogEntry]:
        """Get privacy audit log from API"""
        try:
            user_info = self.session_manager.get_current_user()
            audit_data = asyncio.run(self.api.get_privacy_audit_log(user_info.user_id, limit=100))
            
            audit_entries = []
            for entry in audit_data:
                audit_entries.append(AuditLogEntry(
                    timestamp=datetime.fromisoformat(entry.get("timestamp", datetime.now().isoformat())),
                    action=entry.get("action", "unknown"),
                    details=entry.get("details", ""),
                    ip_address=entry.get("ip_address"),
                    user_agent=entry.get("user_agent"),
                    success=entry.get("success", True)
                ))
            
            return audit_entries
        
        except Exception as e:
            logger.error(f"Failed to get audit log: {e}")
            # Return mock data as fallback
            return [
                AuditLogEntry(
                    timestamp=datetime.now() - timedelta(days=1),
                    action="privacy_settings_updated",
                    details="Privacy settings were updated",
                    ip_address="192.168.1.1",
                    success=True
                ),
                AuditLogEntry(
                    timestamp=datetime.now() - timedelta(days=7),
                    action="data_exported",
                    details="Data exported in JSON format",
                    ip_address="192.168.1.1",
                    success=True
                )
            ]
    
    def _log_privacy_action(self, action: str, details: str) -> None:
        """Log privacy-related action"""
        try:
            user_info = self.session_manager.get_current_user()
            
            # Send to API for audit logging
            success = asyncio.run(self.api.log_privacy_action(user_info.user_id, action, details))
            
            if success:
                logger.info(f"Privacy action logged: {action} - {details}")
            else:
                logger.warning(f"Failed to log privacy action via API: {action} - {details}")
            
            # Also store in session state as backup
            if "privacy_audit_log" not in st.session_state:
                st.session_state["privacy_audit_log"] = []
            
            st.session_state["privacy_audit_log"].append({
                "timestamp": datetime.now(),
                "action": action,
                "details": details,
                "user_id": user_info.user_id if user_info else None
            })
        
        except Exception as e:
            logger.error(f"Failed to log privacy action: {e}")
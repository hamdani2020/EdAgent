"""
Network Connectivity Monitor for EdAgent Streamlit App
Provides real-time network connectivity detection, offline mode, and user guidance.
"""

import streamlit as st
import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import httpx
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectivityStatus(Enum):
    """Network connectivity status"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    CHECKING = "checking"
    UNKNOWN = "unknown"


class ConnectionQuality(Enum):
    """Connection quality levels"""
    EXCELLENT = "excellent"  # < 100ms latency
    GOOD = "good"           # 100-300ms latency
    FAIR = "fair"           # 300-1000ms latency
    POOR = "poor"           # > 1000ms latency


@dataclass
class ConnectivityCheck:
    """Result of a connectivity check"""
    timestamp: datetime
    status: ConnectivityStatus
    latency: Optional[float] = None
    error: Optional[str] = None
    endpoint: Optional[str] = None
    quality: Optional[ConnectionQuality] = None
    
    def __post_init__(self):
        if self.latency is not None and self.quality is None:
            self.quality = self._calculate_quality()
    
    def _calculate_quality(self) -> ConnectionQuality:
        """Calculate connection quality based on latency"""
        if self.latency < 0.1:
            return ConnectionQuality.EXCELLENT
        elif self.latency < 0.3:
            return ConnectionQuality.GOOD
        elif self.latency < 1.0:
            return ConnectionQuality.FAIR
        else:
            return ConnectionQuality.POOR


@dataclass
class OfflineCapability:
    """Defines offline capabilities for different features"""
    feature_name: str
    can_work_offline: bool
    cached_data_available: bool = False
    offline_message: str = "This feature requires an internet connection"
    fallback_action: Optional[Callable] = None
    cache_duration: timedelta = field(default_factory=lambda: timedelta(hours=1))


class NetworkConnectivityMonitor:
    """Monitor network connectivity and provide offline capabilities"""
    
    def __init__(self):
        self.current_status = ConnectivityStatus.UNKNOWN
        self.last_check_time = None
        self.check_interval = 30  # seconds
        self.connectivity_history: List[ConnectivityCheck] = []
        self.max_history_size = 100
        
        # Test endpoints for connectivity checks
        self.test_endpoints = [
            "https://httpbin.org/status/200",
            "https://www.google.com/generate_204",
            "https://cloudflare.com/cdn-cgi/trace"
        ]
        
        # Offline capabilities registry
        self.offline_capabilities: Dict[str, OfflineCapability] = {}
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Callbacks for status changes
        self.status_change_callbacks: List[Callable] = []
    
    def register_offline_capability(self, capability: OfflineCapability) -> None:
        """Register offline capability for a feature"""
        self.offline_capabilities[capability.feature_name] = capability
        logger.info(f"Registered offline capability for {capability.feature_name}")
    
    def add_status_change_callback(self, callback: Callable) -> None:
        """Add callback for status changes"""
        self.status_change_callbacks.append(callback)
    
    async def check_connectivity(self, timeout: float = 5.0) -> ConnectivityCheck:
        """Perform a comprehensive connectivity check"""
        start_time = time.time()
        
        # Try multiple endpoints
        for endpoint in self.test_endpoints:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(endpoint)
                    
                    if response.status_code in [200, 204]:
                        latency = time.time() - start_time
                        
                        check = ConnectivityCheck(
                            timestamp=datetime.now(),
                            status=ConnectivityStatus.ONLINE,
                            latency=latency,
                            endpoint=endpoint
                        )
                        
                        self._update_status(check)
                        return check
            
            except Exception as e:
                logger.debug(f"Connectivity check failed for {endpoint}: {e}")
                continue
        
        # All endpoints failed
        check = ConnectivityCheck(
            timestamp=datetime.now(),
            status=ConnectivityStatus.OFFLINE,
            error="All connectivity checks failed"
        )
        
        self._update_status(check)
        return check
    
    def _update_status(self, check: ConnectivityCheck) -> None:
        """Update connectivity status and history"""
        old_status = self.current_status
        self.current_status = check.status
        self.last_check_time = check.timestamp
        
        # Add to history
        self.connectivity_history.append(check)
        if len(self.connectivity_history) > self.max_history_size:
            self.connectivity_history.pop(0)
        
        # Notify callbacks if status changed
        if old_status != self.current_status:
            for callback in self.status_change_callbacks:
                try:
                    callback(old_status, self.current_status)
                except Exception as e:
                    logger.error(f"Status change callback failed: {e}")
    
    def get_current_status(self) -> ConnectivityStatus:
        """Get current connectivity status"""
        # Check if we need to refresh status
        if (self.last_check_time is None or 
            (datetime.now() - self.last_check_time).total_seconds() > self.check_interval):
            # Trigger async check (don't wait for it)
            asyncio.create_task(self.check_connectivity())
        
        return self.current_status
    
    def is_online(self) -> bool:
        """Check if currently online"""
        return self.get_current_status() == ConnectivityStatus.ONLINE
    
    def get_connection_quality(self) -> Optional[ConnectionQuality]:
        """Get current connection quality"""
        if not self.connectivity_history:
            return None
        
        recent_checks = [
            check for check in self.connectivity_history[-5:]
            if check.status == ConnectivityStatus.ONLINE and check.quality
        ]
        
        if not recent_checks:
            return None
        
        # Return the most common quality level
        qualities = [check.quality for check in recent_checks]
        return max(set(qualities), key=qualities.count)
    
    def get_connectivity_stats(self) -> Dict[str, Any]:
        """Get connectivity statistics"""
        if not self.connectivity_history:
            return {"uptime_percentage": 0, "average_latency": None, "total_checks": 0}
        
        online_checks = [
            check for check in self.connectivity_history
            if check.status == ConnectivityStatus.ONLINE
        ]
        
        uptime_percentage = len(online_checks) / len(self.connectivity_history) * 100
        
        latencies = [check.latency for check in online_checks if check.latency]
        average_latency = sum(latencies) / len(latencies) if latencies else None
        
        return {
            "uptime_percentage": uptime_percentage,
            "average_latency": average_latency,
            "total_checks": len(self.connectivity_history),
            "online_checks": len(online_checks),
            "current_status": self.current_status.value,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None
        }
    
    def can_use_feature_offline(self, feature_name: str) -> bool:
        """Check if a feature can be used offline"""
        capability = self.offline_capabilities.get(feature_name)
        if not capability:
            return False
        
        return capability.can_work_offline or capability.cached_data_available
    
    def get_offline_message(self, feature_name: str) -> str:
        """Get offline message for a feature"""
        capability = self.offline_capabilities.get(feature_name)
        if not capability:
            return "This feature requires an internet connection"
        
        return capability.offline_message
    
    def execute_fallback_action(self, feature_name: str) -> Any:
        """Execute fallback action for offline feature"""
        capability = self.offline_capabilities.get(feature_name)
        if capability and capability.fallback_action:
            try:
                return capability.fallback_action()
            except Exception as e:
                logger.error(f"Fallback action failed for {feature_name}: {e}")
        
        return None
    
    def start_monitoring(self) -> None:
        """Start background connectivity monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started connectivity monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop background connectivity monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped connectivity monitoring")
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Run async check in new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.check_connectivity())
                loop.close()
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.check_interval)


class ConnectivityUI:
    """UI components for connectivity status and offline mode"""
    
    def __init__(self, monitor: NetworkConnectivityMonitor):
        self.monitor = monitor
    
    def show_connectivity_status(self, location: str = "sidebar") -> None:
        """Show connectivity status indicator"""
        status = self.monitor.get_current_status()
        quality = self.monitor.get_connection_quality()
        
        # Status icons and colors
        status_info = {
            ConnectivityStatus.ONLINE: {"icon": "🟢", "text": "Online", "color": "green"},
            ConnectivityStatus.OFFLINE: {"icon": "🔴", "text": "Offline", "color": "red"},
            ConnectivityStatus.DEGRADED: {"icon": "🟡", "text": "Degraded", "color": "orange"},
            ConnectivityStatus.CHECKING: {"icon": "🔵", "text": "Checking...", "color": "blue"},
            ConnectivityStatus.UNKNOWN: {"icon": "⚪", "text": "Unknown", "color": "gray"}
        }
        
        info = status_info[status]
        
        if location == "sidebar":
            with st.sidebar:
                st.markdown("---")
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"<span style='font-size: 20px;'>{info['icon']}</span>", 
                              unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**{info['text']}**")
                    
                    if quality and status == ConnectivityStatus.ONLINE:
                        quality_text = quality.value.title()
                        st.caption(f"Quality: {quality_text}")
        
        elif location == "header":
            col1, col2, col3 = st.columns([1, 1, 8])
            
            with col1:
                st.markdown(f"<span style='font-size: 24px;'>{info['icon']}</span>", 
                          unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**{info['text']}**")
            
            # Show quality if online
            if quality and status == ConnectivityStatus.ONLINE:
                with col3:
                    st.caption(f"Connection quality: {quality.value.title()}")
    
    def show_connectivity_dashboard(self) -> None:
        """Show detailed connectivity dashboard"""
        st.subheader("🌐 Network Connectivity Dashboard")
        
        # Current status
        status = self.monitor.get_current_status()
        quality = self.monitor.get_connection_quality()
        stats = self.monitor.get_connectivity_stats()
        
        # Status overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_colors = {
                ConnectivityStatus.ONLINE: "green",
                ConnectivityStatus.OFFLINE: "red",
                ConnectivityStatus.DEGRADED: "orange"
            }
            color = status_colors.get(status, "gray")
            st.markdown(f"**Status:** :{color}[{status.value.upper()}]")
        
        with col2:
            if quality:
                st.write(f"**Quality:** {quality.value.title()}")
            else:
                st.write("**Quality:** Unknown")
        
        with col3:
            st.metric("Uptime", f"{stats['uptime_percentage']:.1f}%")
        
        with col4:
            if stats['average_latency']:
                st.metric("Avg Latency", f"{stats['average_latency']*1000:.0f}ms")
            else:
                st.metric("Avg Latency", "N/A")
        
        # Connectivity history chart
        if self.monitor.connectivity_history:
            st.subheader("📊 Connectivity History")
            
            # Prepare data for chart
            history_data = []
            for check in self.monitor.connectivity_history[-20:]:  # Last 20 checks
                history_data.append({
                    "Time": check.timestamp.strftime("%H:%M:%S"),
                    "Status": 1 if check.status == ConnectivityStatus.ONLINE else 0,
                    "Latency": check.latency * 1000 if check.latency else None
                })
            
            if history_data:
                import pandas as pd
                import plotly.express as px
                
                df = pd.DataFrame(history_data)
                
                # Status chart
                fig_status = px.line(df, x="Time", y="Status", 
                                   title="Connection Status Over Time",
                                   labels={"Status": "Online (1) / Offline (0)"})
                st.plotly_chart(fig_status, use_container_width=True)
                
                # Latency chart (only for online periods)
                online_data = df[df["Latency"].notna()]
                if not online_data.empty:
                    fig_latency = px.line(online_data, x="Time", y="Latency",
                                        title="Connection Latency Over Time",
                                        labels={"Latency": "Latency (ms)"})
                    st.plotly_chart(fig_latency, use_container_width=True)
        
        # Manual connectivity check
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Check Connectivity Now"):
                with st.spinner("Checking connectivity..."):
                    check = asyncio.run(self.monitor.check_connectivity())
                    
                    if check.status == ConnectivityStatus.ONLINE:
                        st.success(f"✅ Online! Latency: {check.latency*1000:.0f}ms")
                    else:
                        st.error(f"❌ Offline: {check.error}")
        
        with col2:
            if st.button("📈 View Statistics"):
                st.json(stats)
    
    def show_offline_mode_info(self, feature_name: str) -> bool:
        """Show offline mode information for a feature"""
        if self.monitor.is_online():
            return True
        
        capability = self.monitor.offline_capabilities.get(feature_name)
        
        if not capability:
            st.error("🌐 This feature requires an internet connection")
            self._show_connectivity_guidance()
            return False
        
        if capability.can_work_offline:
            st.info(f"📱 **Offline Mode:** {capability.offline_message}")
            return True
        
        elif capability.cached_data_available:
            st.warning(f"💾 **Using Cached Data:** {capability.offline_message}")
            
            # Option to use fallback
            if capability.fallback_action:
                if st.button("📂 Use Cached Data", key=f"fallback_{feature_name}"):
                    return True
            
            return False
        
        else:
            st.error(f"🚫 **Offline:** {capability.offline_message}")
            self._show_connectivity_guidance()
            return False
    
    def _show_connectivity_guidance(self) -> None:
        """Show guidance for connectivity issues"""
        with st.expander("🔧 Troubleshooting Connection Issues"):
            st.write("**Try these steps to restore connectivity:**")
            
            steps = [
                "Check if other websites are working in your browser",
                "Restart your router or modem",
                "Disable VPN if you're using one",
                "Clear your browser cache and cookies",
                "Try using a different browser or device",
                "Contact your internet service provider if issues persist"
            ]
            
            for i, step in enumerate(steps, 1):
                st.write(f"{i}. {step}")
            
            st.write("**Alternative options:**")
            st.write("• Use mobile data if available")
            st.write("• Try connecting to a different network")
            st.write("• Work offline with cached data where possible")


class OfflineDataManager:
    """Manage offline data caching and synchronization"""
    
    def __init__(self):
        self.cache_storage = {}
        self.cache_metadata = {}
        
    def cache_data(self, key: str, data: Any, ttl: timedelta = timedelta(hours=1)) -> None:
        """Cache data for offline use"""
        self.cache_storage[key] = data
        self.cache_metadata[key] = {
            "cached_at": datetime.now(),
            "ttl": ttl,
            "size": len(str(data))
        }
        
        logger.info(f"Cached data for key: {key}")
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if available and not expired"""
        if key not in self.cache_storage:
            return None
        
        metadata = self.cache_metadata[key]
        age = datetime.now() - metadata["cached_at"]
        
        if age <= metadata["ttl"]:
            logger.info(f"Retrieved cached data for key: {key}")
            return self.cache_storage[key]
        
        # Remove expired data
        self.remove_cached_data(key)
        return None
    
    def remove_cached_data(self, key: str) -> None:
        """Remove cached data"""
        if key in self.cache_storage:
            del self.cache_storage[key]
        if key in self.cache_metadata:
            del self.cache_metadata[key]
        
        logger.info(f"Removed cached data for key: {key}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        total_size = sum(meta["size"] for meta in self.cache_metadata.values())
        
        return {
            "total_items": len(self.cache_storage),
            "total_size_bytes": total_size,
            "items": [
                {
                    "key": key,
                    "cached_at": meta["cached_at"].isoformat(),
                    "ttl_seconds": meta["ttl"].total_seconds(),
                    "size_bytes": meta["size"]
                }
                for key, meta in self.cache_metadata.items()
            ]
        }
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache_storage.clear()
        self.cache_metadata.clear()
        logger.info("Cleared all cached data")


# Global instances
connectivity_monitor = NetworkConnectivityMonitor()
connectivity_ui = ConnectivityUI(connectivity_monitor)
offline_data_manager = OfflineDataManager()


# Convenience functions
def check_online_status() -> bool:
    """Quick check if online"""
    return connectivity_monitor.is_online()


def require_online_connection(feature_name: str) -> bool:
    """Decorator/function to require online connection for a feature"""
    return connectivity_ui.show_offline_mode_info(feature_name)


def with_offline_fallback(feature_name: str, fallback_data: Any = None):
    """Decorator to provide offline fallback for functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if connectivity_monitor.is_online():
                try:
                    result = func(*args, **kwargs)
                    # Cache successful result
                    if result is not None:
                        offline_data_manager.cache_data(f"{feature_name}_result", result)
                    return result
                except Exception as e:
                    # If online but function fails, try cached data
                    cached_result = offline_data_manager.get_cached_data(f"{feature_name}_result")
                    if cached_result is not None:
                        st.warning("🔄 Using cached data due to service issues")
                        return cached_result
                    raise e
            else:
                # Offline mode
                cached_result = offline_data_manager.get_cached_data(f"{feature_name}_result")
                if cached_result is not None:
                    st.info("📱 Using cached data (offline mode)")
                    return cached_result
                elif fallback_data is not None:
                    st.info("📱 Using fallback data (offline mode)")
                    return fallback_data
                else:
                    st.error(f"🚫 {feature_name} is not available offline")
                    return None
        
        return wrapper
    return decorator


# Initialize default offline capabilities
def setup_default_offline_capabilities():
    """Setup default offline capabilities for common features"""
    
    # Chat - limited offline capability
    connectivity_monitor.register_offline_capability(OfflineCapability(
        feature_name="chat",
        can_work_offline=False,
        cached_data_available=True,
        offline_message="Chat history is available offline, but new messages require internet connection"
    ))
    
    # Assessments - no offline capability
    connectivity_monitor.register_offline_capability(OfflineCapability(
        feature_name="assessments",
        can_work_offline=False,
        offline_message="Skill assessments require an internet connection to function properly"
    ))
    
    # Learning paths - cached data available
    connectivity_monitor.register_offline_capability(OfflineCapability(
        feature_name="learning_paths",
        can_work_offline=False,
        cached_data_available=True,
        offline_message="Previously loaded learning paths are available offline"
    ))
    
    # User profile - cached data available
    connectivity_monitor.register_offline_capability(OfflineCapability(
        feature_name="user_profile",
        can_work_offline=False,
        cached_data_available=True,
        offline_message="Profile data is cached and viewable offline, but changes require internet connection"
    ))
    
    # Analytics - cached data available
    connectivity_monitor.register_offline_capability(OfflineCapability(
        feature_name="analytics",
        can_work_offline=True,
        cached_data_available=True,
        offline_message="Analytics data is available offline using cached information"
    ))


# Initialize on import
setup_default_offline_capabilities()
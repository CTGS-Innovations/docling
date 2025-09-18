"""
Deployment Profile Manager for MVP-Fusion
Handles different deployment environments with memory and worker management
"""

from typing import Dict, Any, Optional
from utils.logging_config import get_fusion_logger

class DeploymentManager:
    """
    Manages deployment profiles for different environments:
    - local: High-performance local machine
    - cloudflare: Cloudflare Workers edge computing
    - aws: Amazon Web Services cloud deployment
    - gcp: Google Cloud Platform deployment
    - docker: Containerized deployment
    - disabled: No memory management
    """
    
    def __init__(self, config: Dict[str, Any], profile_override: Optional[str] = None):
        self.config = config
        self.logger = get_fusion_logger(__name__)
        
        # Use override profile or config default
        self.profile_name = profile_override or self._get_active_profile_name()
        self.active_profile = self._load_profile(self.profile_name)
        
        self.logger.stage(f"🚀 Deployment Profile: {self.active_profile['name']}")
        if self.active_profile.get('description'):
            self.logger.logger.info(f"   {self.active_profile['description']}")
    
    def _get_active_profile_name(self) -> str:
        """Get the active profile name from config"""
        deployment = self.config.get('deployment', {})
        return deployment.get('active_profile', 'local')
    
    def _load_profile(self, profile_name: str) -> Dict[str, Any]:
        """Load a specific deployment profile"""
        deployment = self.config.get('deployment', {})
        profiles = deployment.get('profiles', {})
        
        if profile_name not in profiles:
            self.logger.logger.warning(f"⚠️  Profile '{profile_name}' not found, using 'local'")
            profile_name = 'local'
        
        profile = profiles.get(profile_name, {})
        
        # If profile is disabled, return fallback configuration
        if not profile.get('enabled', True):
            return self._get_fallback_profile()
        
        # Add the profile name for logging
        profile['profile_name'] = profile_name
        return profile
    
    def _get_fallback_profile(self) -> Dict[str, Any]:
        """Get fallback configuration when memory management is disabled"""
        performance = self.config.get('performance', {})
        return {
            'name': 'Fallback Configuration',
            'description': 'Using performance section settings (no memory management)',
            'enabled': False,
            'max_workers': performance.get('max_workers', 8),
            'memory_mb': None,
            'memory_threshold': None,
            'queue_size': None,
            'profile_name': 'disabled'
        }
    
    def get_max_workers(self, cli_override: Optional[int] = None) -> int:
        """Get the number of workers to use"""
        if cli_override:
            self.logger.logger.info(f"   Workers overridden by CLI: {cli_override}")
            return cli_override
        
        workers = self.active_profile.get('max_workers', 8)
        self.logger.logger.info(f"   Workers: {workers}")
        return workers
    
    def get_memory_limit_mb(self) -> Optional[int]:
        """Get memory limit in MB (None if disabled)"""
        memory_mb = self.active_profile.get('memory_mb')
        if memory_mb:
            threshold = self.active_profile.get('memory_threshold', 0.8)
            usable_memory = int(memory_mb * threshold)
            self.logger.logger.info(f"   Memory: {usable_memory}MB usable ({memory_mb}MB * {threshold})")
            return usable_memory
        else:
            self.logger.logger.info(f"   Memory: Unlimited")
            return None
    
    def get_queue_size(self) -> Optional[int]:
        """Get queue size limit (None if unlimited)"""
        queue_size = self.active_profile.get('queue_size')
        if queue_size:
            self.logger.logger.info(f"   Queue Size: {queue_size}")
        else:
            self.logger.logger.info(f"   Queue Size: Unlimited")
        return queue_size
    
    def is_memory_management_enabled(self) -> bool:
        """Check if memory management is enabled"""
        return self.active_profile.get('enabled', True)
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get a summary of the active profile"""
        return {
            'profile_name': self.profile_name,
            'name': self.active_profile.get('name', 'Unknown'),
            'description': self.active_profile.get('description', ''),
            'max_workers': self.get_max_workers(),
            'memory_limit_mb': self.get_memory_limit_mb(),
            'queue_size': self.get_queue_size(),
            'memory_management_enabled': self.is_memory_management_enabled()
        }
    
    @classmethod
    def list_available_profiles(cls, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """List all available deployment profiles"""
        deployment = config.get('deployment', {})
        profiles = deployment.get('profiles', {})
        
        summary = {}
        for name, profile in profiles.items():
            summary[name] = {
                'name': profile.get('name', name),
                'description': profile.get('description', ''),
                'memory_mb': profile.get('memory_mb', 'Unlimited'),
                'max_workers': profile.get('max_workers', 'From performance section'),
                'enabled': profile.get('enabled', True)
            }
        
        return summary
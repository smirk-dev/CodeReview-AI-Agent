"""Memory bank for shared agent context and long-term memory.

This module provides a shared memory system that allows agents to:
- Store and retrieve contextual information
- Share findings across agents
- Maintain long-term memory of code reviews
- Enable context-aware agent interactions
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryBank:
    """Shared memory system for agent context and state.
    
    This class provides long-term memory capabilities:
    - Store/retrieve arbitrary data by key
    - Automatic timestamping
    - Memory search and filtering
    - Context compaction for large datasets
    """
    
    def __init__(self, max_items: int = 1000):
        """Initialize the memory bank.
        
        Args:
            max_items: Maximum number of items to store (for compaction)
        """
        self.memory: Dict[str, Dict[str, Any]] = {}
        self.max_items = max_items
        self.access_log: List[Dict] = []
        logger.info(f"MemoryBank initialized with max_items={max_items}")
    
    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """Store data in memory.
        
        Args:
            key: Unique identifier for the data
            value: Data to store (can be any JSON-serializable type)
            metadata: Optional metadata about the stored data
        
        Returns:
            True if stored successfully
        """
        try:
            self.memory[key] = {
                'value': value,
                'stored_at': datetime.now().isoformat(),
                'accessed_count': 0,
                'last_accessed': None,
                'metadata': metadata or {}
            }
            
            logger.info(f"Stored data in memory: {key}")
            
            # Check if compaction is needed
            if len(self.memory) > self.max_items:
                self._compact()
            
            return True
        
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve data from memory.
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
        
        Returns:
            Stored value or default
        """
        if key not in self.memory:
            logger.debug(f"Key not found in memory: {key}")
            return default
        
        # Update access tracking
        self.memory[key]['accessed_count'] += 1
        self.memory[key]['last_accessed'] = datetime.now().isoformat()
        
        # Log access
        self.access_log.append({
            'key': key,
            'timestamp': datetime.now().isoformat(),
            'action': 'get'
        })
        
        logger.debug(f"Retrieved data from memory: {key}")
        return self.memory[key]['value']
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in memory.
        
        Args:
            key: Key to check
        
        Returns:
            True if key exists
        """
        return key in self.memory
    
    def delete(self, key: str) -> bool:
        """Delete data from memory.
        
        Args:
            key: Key to delete
        
        Returns:
            True if deleted successfully
        """
        if key in self.memory:
            del self.memory[key]
            logger.info(f"Deleted from memory: {key}")
            return True
        
        logger.warning(f"Cannot delete non-existent key: {key}")
        return False
    
    def clear(self) -> None:
        """Clear all data from memory."""
        count = len(self.memory)
        self.memory.clear()
        self.access_log.clear()
        logger.info(f"Cleared {count} items from memory")
    
    def search(self, pattern: str) -> List[str]:
        """Search for keys matching a pattern.
        
        Args:
            pattern: Search pattern (substring match)
        
        Returns:
            List of matching keys
        """
        matches = [key for key in self.memory.keys() if pattern in key]
        logger.debug(f"Search for '{pattern}' found {len(matches)} matches")
        return matches
    
    def get_all_keys(self) -> List[str]:
        """Get all keys in memory.
        
        Returns:
            List of all keys
        """
        return list(self.memory.keys())
    
    def get_metadata(self, key: str) -> Optional[Dict]:
        """Get metadata for a stored item.
        
        Args:
            key: Key to get metadata for
        
        Returns:
            Metadata dictionary or None
        """
        if key not in self.memory:
            return None
        
        return {
            'stored_at': self.memory[key]['stored_at'],
            'accessed_count': self.memory[key]['accessed_count'],
            'last_accessed': self.memory[key]['last_accessed'],
            'metadata': self.memory[key]['metadata']
        }
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of stored context.
        
        Returns:
            Summary dictionary with statistics
        """
        total_items = len(self.memory)
        total_accesses = sum(item['accessed_count'] for item in self.memory.values())
        
        summary = {
            'total_items': total_items,
            'total_accesses': total_accesses,
            'keys': list(self.memory.keys()),
            'memory_usage': f"{total_items}/{self.max_items}",
            'recent_accesses': self.access_log[-10:] if self.access_log else []
        }
        
        logger.info(f"Generated context summary: {total_items} items, {total_accesses} accesses")
        return summary
    
    def _compact(self) -> None:
        """Compact memory by removing least recently used items.
        
        This implements a simple LRU eviction policy.
        """
        logger.info("Starting memory compaction")
        
        # Sort by last accessed time (None values go first)
        sorted_items = sorted(
            self.memory.items(),
            key=lambda x: (
                x[1]['last_accessed'] is not None,
                x[1]['last_accessed'] or '',
                x[1]['accessed_count']
            )
        )
        
        # Keep only the most recently accessed items
        items_to_keep = int(self.max_items * 0.8)  # Keep 80% after compaction
        self.memory = dict(sorted_items[-items_to_keep:])
        
        logger.info(f"Memory compacted: kept {len(self.memory)} items")
    
    def export_context(self, keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Export context for sharing with agents.
        
        Args:
            keys: Optional list of specific keys to export (exports all if None)
        
        Returns:
            Dictionary of exported context
        """
        if keys:
            context = {k: self.memory[k]['value'] for k in keys if k in self.memory}
        else:
            context = {k: v['value'] for k, v in self.memory.items()}
        
        logger.info(f"Exported {len(context)} context items")
        return context
    
    def import_context(self, context: Dict[str, Any], prefix: str = "") -> int:
        """Import context from another source.
        
        Args:
            context: Dictionary of context to import
            prefix: Optional prefix for imported keys
        
        Returns:
            Number of items imported
        """
        count = 0
        for key, value in context.items():
            full_key = f"{prefix}{key}" if prefix else key
            if self.store(full_key, value):
                count += 1
        
        logger.info(f"Imported {count} context items")
        return count

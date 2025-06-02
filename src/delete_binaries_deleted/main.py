"""
Main deletion logic for Binaries_deleted table.
"""

import logging
import time
from typing import Optional
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class BinariesDeleter:
    """Handles the deletion of all records from Binaries_deleted table."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, batch_size: int = 400) -> None:
        self.db_manager = db_manager or DatabaseManager()
        self.batch_size = batch_size
        self.total_deleted = 0
        self.start_time: Optional[float] = None
    
    def validate_environment(self) -> bool:
        """Validate database connection and environment."""
        logger.info("Validating database connection...")
        
        if not self.db_manager.test_connection():
            logger.error("Database connection test failed")
            return False
        
        logger.info("Database connection validated successfully")
        return True
    
    def get_deletion_statistics(self) -> dict:
        """Get statistics about the deletion operation."""
        try:
            total_records = self.db_manager.count_binaries_deleted_records()
            estimated_batches = (total_records + self.batch_size - 1) // self.batch_size
            
            return {
                "total_records": total_records,
                "batch_size": self.batch_size,
                "estimated_batches": estimated_batches,
                "estimated_time_minutes": estimated_batches * 0.1  # Rough estimate
            }
        except Exception as e:
            logger.error(f"Error getting deletion statistics: {e}")
            raise
    
    def dry_run(self) -> dict:
        """Perform a dry run to show what would be deleted."""
        logger.info("Performing dry run...")
        
        stats = self.get_deletion_statistics()
        
        # Get a sample of records that would be deleted
        try:
            sample_batch = self.db_manager.get_binaries_deleted_batch(
                batch_size=min(10, stats["total_records"]), 
                offset=0
            )
            
            stats["sample_records"] = [record["BinaryId"] for record in sample_batch]
            
        except Exception as e:
            logger.warning(f"Could not retrieve sample records: {e}")
            stats["sample_records"] = []
        
        return stats
    
    def delete_all_records(self, progress_callback=None) -> dict:
        """Delete all records from Binaries_deleted table in batches."""
        self.start_time = time.time()
        self.total_deleted = 0
        
        logger.info(f"Starting deletion process with batch size: {self.batch_size}")
        
        try:
            # Get initial count
            initial_count = self.db_manager.count_binaries_deleted_records()
            
            if initial_count == 0:
                logger.info("No records to delete")
                return {
                    "success": True,
                    "initial_count": 0,
                    "total_deleted": 0,
                    "batches_processed": 0,
                    "duration_seconds": 0
                }
            
            batches_processed = 0
            
            while True:
                # Get next batch
                batch = self.db_manager.get_binaries_deleted_batch(
                    batch_size=self.batch_size, 
                    offset=0  # Always 0 since we're deleting from the beginning
                )
                
                if not batch:
                    logger.info("No more records to delete")
                    break
                
                # Extract BinaryIds for deletion
                binary_ids = [record["BinaryId"] for record in batch]
                
                # Delete batch
                deleted_count = self.db_manager.delete_binaries_deleted_batch(binary_ids)
                
                self.total_deleted += deleted_count
                batches_processed += 1
                
                # Progress callback
                if progress_callback:
                    progress_callback(
                        batch_number=batches_processed,
                        batch_deleted=deleted_count,
                        total_deleted=self.total_deleted,
                        initial_count=initial_count
                    )
                
                logger.info(f"Batch {batches_processed}: Deleted {deleted_count} records (Total: {self.total_deleted})")
                
                # Small delay to prevent overwhelming the database
                time.sleep(0.1)
            
            duration = time.time() - self.start_time
            
            # Final verification
            final_count = self.db_manager.count_binaries_deleted_records()
            
            result = {
                "success": True,
                "initial_count": initial_count,
                "final_count": final_count,
                "total_deleted": self.total_deleted,
                "batches_processed": batches_processed,
                "duration_seconds": duration,
                "average_batch_time": duration / batches_processed if batches_processed > 0 else 0
            }
            
            logger.info(f"Deletion completed successfully: {result}")
            return result
            
        except Exception as e:
            duration = time.time() - self.start_time if self.start_time else 0
            logger.error(f"Deletion process failed after {duration:.2f} seconds: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "total_deleted": self.total_deleted,
                "duration_seconds": duration
            }

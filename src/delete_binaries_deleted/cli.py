"""
Command-line interface for delete-binaries-deleted tool.
"""

import logging
import sys
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Confirm
from rich.panel import Panel
from rich.text import Text

from .main import BinariesDeleter
from .database import DatabaseManager

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def display_statistics(stats: dict) -> None:
    """Display deletion statistics in a formatted table."""
    table = Table(title="Deletion Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    table.add_row("Total Records", f"{stats['total_records']:,}")
    table.add_row("Batch Size", f"{stats['batch_size']:,}")
    table.add_row("Estimated Batches", f"{stats['estimated_batches']:,}")
    table.add_row("Estimated Time", f"{stats['estimated_time_minutes']:.1f} minutes")
    
    if "sample_records" in stats and stats["sample_records"]:
        sample_str = ", ".join(map(str, stats["sample_records"][:5]))
        if len(stats["sample_records"]) > 5:
            sample_str += "..."
        table.add_row("Sample BinaryIds", sample_str)
    
    console.print(table)


def display_results(results: dict) -> None:
    """Display deletion results."""
    if results["success"]:
        # Success panel
        success_text = Text("✅ Deletion Completed Successfully", style="bold green")
        console.print(Panel(success_text, expand=False))
        
        # Results table
        table = Table(title="Deletion Results", show_header=True, header_style="bold blue")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Initial Count", f"{results['initial_count']:,}")
        table.add_row("Final Count", f"{results['final_count']:,}")
        table.add_row("Total Deleted", f"{results['total_deleted']:,}")
        table.add_row("Batches Processed", f"{results['batches_processed']:,}")
        table.add_row("Duration", f"{results['duration_seconds']:.2f} seconds")
        
        if results['batches_processed'] > 0:
            table.add_row("Avg Batch Time", f"{results['average_batch_time']:.2f} seconds")
        
        console.print(table)
        
    else:
        # Error panel
        error_text = Text(f"❌ Deletion Failed: {results.get('error', 'Unknown error')}", style="bold red")
        console.print(Panel(error_text, expand=False))
        
        if results.get('total_deleted', 0) > 0:
            console.print(f"Partial deletion: {results['total_deleted']:,} records were deleted before failure")


@click.command()
@click.option(
    "--batch-size", 
    default=400, 
    help="Number of records to delete per batch",
    type=int
)
@click.option(
    "--dry-run", 
    is_flag=True, 
    help="Show what would be deleted without actually deleting"
)
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    help="Enable verbose logging"
)
@click.option(
    "--force", 
    is_flag=True, 
    help="Skip confirmation prompt"
)
def main(batch_size: int, dry_run: bool, verbose: bool, force: bool) -> None:
    """Delete all records from Binaries_deleted table in batches."""
    
    # Setup logging
    setup_logging(verbose)
    
    # Welcome message
    console.print(Panel(
        Text("Delete Binaries Deleted Tool", style="bold blue"),
        subtitle="Safely delete all records from Binaries_deleted table"
    ))
    
    try:
        # Initialize deleter
        deleter = BinariesDeleter(batch_size=batch_size)
        
        # Validate environment
        console.print("🔍 Validating database connection...")
        if not deleter.validate_environment():
            console.print("❌ Database validation failed", style="bold red")
            sys.exit(1)
        
        console.print("✅ Database connection validated", style="bold green")
        
        # Get and display statistics
        console.print("\n📊 Analyzing data...")
        stats = deleter.get_deletion_statistics()
        display_statistics(stats)
        
        if stats["total_records"] == 0:
            console.print("\n✅ No records to delete!", style="bold green")
            return
        
        if dry_run:
            console.print("\n🔍 This was a dry run - no records were deleted", style="bold yellow")
            return
        
        # Confirmation
        if not force:
            console.print("\n⚠️  WARNING: This will permanently delete ALL records from Binaries_deleted table!", style="bold red")
            
            if not Confirm.ask(f"Are you sure you want to delete {stats['total_records']:,} records?"):
                console.print("Operation cancelled by user", style="yellow")
                return
        
        # Progress tracking
        def progress_callback(batch_number: int, batch_deleted: int, total_deleted: int, initial_count: int) -> None:
            percentage = (total_deleted / initial_count) * 100 if initial_count > 0 else 0
            console.print(f"Batch {batch_number}: {batch_deleted} deleted | Total: {total_deleted:,}/{initial_count:,} ({percentage:.1f}%)")
        
        # Perform deletion
        console.print("\n🗑️  Starting deletion process...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Deleting records...", total=stats["total_records"])
            
            def progress_update(batch_number: int, batch_deleted: int, total_deleted: int, initial_count: int) -> None:
                progress.update(task, completed=total_deleted)
                progress_callback(batch_number, batch_deleted, total_deleted, initial_count)
            
            results = deleter.delete_all_records(progress_callback=progress_update)
        
        # Display results
        console.print("\n")
        display_results(results)
        
        if not results["success"]:
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n❌ Operation cancelled by user", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="bold red")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()

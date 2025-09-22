#!/usr/bin/env python3
"""
Discovery Validation Utility for MVP-Fusion
==========================================

Command-line utility for human validation of POS-discovered entities.
Allows review and promotion of tentative corpus discoveries.

Usage:
    python utils/validate_discoveries.py --review organizations
    python utils/validate_discoveries.py --promote organizations --entities "Tesla,Inc.,CyberTech LLC"
    python utils/validate_discoveries.py --stats
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from knowledge.corpus.tentative_corpus_manager import TentativeCorpusManager


def review_discoveries(manager: TentativeCorpusManager, entity_type: str = None):
    """Interactive review of pending discoveries."""
    print("🔍 DISCOVERY REVIEW")
    print("=" * 50)
    
    pending = manager.get_pending_discoveries(entity_type)
    
    if not pending:
        print("✅ No pending discoveries to review!")
        return
    
    for ent_type, entities in pending.items():
        print(f"\n📊 {ent_type} Entities ({len(entities)} pending):")
        print("-" * 40)
        
        for i, entity in enumerate(entities, 1):
            print(f"  {i:2d}. {entity}")
        
        print()
    
    print("💡 To validate discoveries, use:")
    print("   python utils/validate_discoveries.py --promote <entity_type> --entities \"entity1,entity2\"")


def promote_all_discoveries(manager: TentativeCorpusManager, entity_type: str):
    """Promote ALL entities in the tentative file for the specified type."""
    print(f"🎯 PROMOTING ALL {entity_type.upper()} DISCOVERIES")
    print("=" * 50)
    
    # Get all pending discoveries for this type
    pending = manager.get_pending_discoveries(entity_type.upper())
    
    if entity_type.upper() not in pending:
        print(f"❌ No pending discoveries found for {entity_type.upper()}")
        return
    
    entities = pending[entity_type.upper()]
    
    if not entities:
        print(f"ℹ️  No entities to promote for {entity_type.upper()}")
        return
    
    print(f"📝 Found {len(entities)} entities in tentative file:")
    for i, entity in enumerate(entities, 1):
        print(f"  {i:2d}. {entity}")
    
    # Confirm promotion
    confirm = input(f"\n✅ Promote ALL {len(entities)} entities? (y/N): ").strip().lower()
    
    if confirm == 'y':
        success = manager.validate_discoveries(entity_type.upper(), entities)
        
        if success:
            print(f"🟢 SUCCESS: All {len(entities)} entities promoted to validated corpus")
            print("💡 Next steps:")
            print("   1. Review validated corpus file in knowledge/corpus/foundation_data/")
            print("   2. Manually merge approved entities into main corpus files")
            print("   3. Restart processing to use updated corpus")
        else:
            print("❌ FAILED: Promotion failed")
    else:
        print("❌ Promotion cancelled")


def promote_discoveries(manager: TentativeCorpusManager, entity_type: str, entity_list: str):
    """Promote validated discoveries to validated corpus."""
    print(f"🎯 PROMOTING {entity_type.upper()} DISCOVERIES")
    print("=" * 50)
    
    # Parse entity list
    entities = [e.strip() for e in entity_list.split(',') if e.strip()]
    
    if not entities:
        print("❌ No entities provided for promotion")
        return
    
    print(f"📝 Entities to promote: {len(entities)}")
    for i, entity in enumerate(entities, 1):
        print(f"  {i}. {entity}")
    
    # Confirm promotion
    confirm = input(f"\n✅ Promote these {len(entities)} entities? (y/N): ").strip().lower()
    
    if confirm == 'y':
        success = manager.validate_discoveries(entity_type.upper(), entities)
        
        if success:
            print(f"🟢 SUCCESS: {len(entities)} entities promoted to validated corpus")
            print("💡 Next steps:")
            print("   1. Review validated corpus file in knowledge/corpus/foundation_data/")
            print("   2. Manually merge approved entities into main corpus files")
            print("   3. Restart processing to use updated corpus")
        else:
            print("❌ FAILED: Promotion failed")
    else:
        print("❌ Promotion cancelled")


def show_stats(manager: TentativeCorpusManager):
    """Show discovery and validation statistics."""
    print("📈 DISCOVERY STATISTICS")
    print("=" * 50)
    
    # Validation stats
    stats = manager.get_validation_stats()
    print(f"📊 Total discoveries: {stats.total_discoveries}")
    print(f"⏳ Pending validation: {stats.pending_validation}")
    print(f"✅ Validated entries: {stats.validated_entries}")
    print(f"❌ Rejected entries: {stats.rejected_entries}")
    print(f"🎯 Promoted to main: {stats.promoted_to_main}")
    
    # Session stats
    session_stats = manager.get_session_stats()
    print(f"\n🔄 Current session:")
    print(f"   - Discoveries added: {session_stats['discoveries_added']}")
    print(f"   - Duplicates skipped: {session_stats['duplicates_skipped']}")
    print(f"   - Session duration: {session_stats['session_duration_minutes']:.1f} minutes")
    
    # Pending by type
    pending = manager.get_pending_discoveries()
    if pending:
        print(f"\n📋 Pending by type:")
        for ent_type, entities in pending.items():
            print(f"   - {ent_type}: {len(entities)} entities")
    else:
        print(f"\n✅ No pending discoveries")


def list_validated_files(corpus_dir: Path):
    """List available validated corpus files."""
    print("📁 VALIDATED CORPUS FILES")
    print("=" * 50)
    
    validated_files = list(corpus_dir.glob("validated_*.txt"))
    
    if not validated_files:
        print("ℹ️  No validated corpus files found")
        return
    
    for file_path in sorted(validated_files):
        try:
            with open(file_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            print(f"📄 {file_path.name}")
            print(f"   Entities: {len(lines)}")
            print(f"   Modified: {file_path.stat().st_mtime}")
            
            # Show sample entities
            if lines:
                sample_count = min(3, len(lines))
                print(f"   Sample: {', '.join(lines[:sample_count])}")
                if len(lines) > sample_count:
                    print(f"          ... and {len(lines) - sample_count} more")
            print()
            
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Validate and promote POS-discovered entities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Review pending discoveries
  python utils/validate_discoveries.py --review

  # Review specific entity type
  python utils/validate_discoveries.py --review organizations

  # Promote specific entities
  python utils/validate_discoveries.py --promote organizations --entities "Tesla Inc,CyberTech LLC"

  # Promote ALL entities from tentative file (recommended)
  python utils/validate_discoveries.py --promote-all organizations

  # Show statistics
  python utils/validate_discoveries.py --stats

  # List validated files
  python utils/validate_discoveries.py --list-validated
        """
    )
    
    parser.add_argument('--review', nargs='?', const='all', metavar='ENTITY_TYPE',
                       help='Review pending discoveries (all or specific type)')
    parser.add_argument('--promote', metavar='ENTITY_TYPE',
                       help='Promote entities of specified type')
    parser.add_argument('--entities', metavar='ENTITY_LIST',
                       help='Comma-separated list of entities to promote')
    parser.add_argument('--promote-all', metavar='ENTITY_TYPE',
                       help='Promote ALL entities in the tentative file for specified type')
    parser.add_argument('--stats', action='store_true',
                       help='Show discovery statistics')
    parser.add_argument('--list-validated', action='store_true',
                       help='List validated corpus files')
    
    args = parser.parse_args()
    
    # Initialize manager
    corpus_dir = Path("knowledge/corpus/foundation_data")
    manager = TentativeCorpusManager(corpus_dir=corpus_dir)
    
    print("🎯 MVP-FUSION DISCOVERY VALIDATION UTILITY")
    print("=" * 60)
    print(f"📁 Corpus directory: {corpus_dir}")
    print(f"🔧 Manager enabled: {manager.is_enabled()}")
    print()
    
    # Handle commands
    if args.review:
        entity_type = None if args.review == 'all' else args.review
        review_discoveries(manager, entity_type)
    
    elif args.promote:
        if not args.entities:
            print("❌ --entities required when using --promote")
            sys.exit(1)
        promote_discoveries(manager, args.promote, args.entities)
    
    elif args.promote_all:
        promote_all_discoveries(manager, args.promote_all)
    
    elif args.stats:
        show_stats(manager)
    
    elif args.list_validated:
        list_validated_files(corpus_dir)
    
    else:
        # Default: show stats and pending
        show_stats(manager)
        print()
        review_discoveries(manager)


if __name__ == "__main__":
    main()
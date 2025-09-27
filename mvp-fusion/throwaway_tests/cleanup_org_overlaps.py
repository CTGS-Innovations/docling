#!/usr/bin/env python3
"""
Organization File Cleanup Script
================================
Removes unicorn companies and investors from single/multi-word organization files
to eliminate overlap and ensure premium entities only appear in premium lists.

This prevents metadata loss and ensures proper premium entity recognition.
"""

import os
from pathlib import Path


def load_file_as_set(file_path: Path) -> set:
    """Load file lines into a set (lowercase for matching)"""
    data = set()
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.add(line.lower())
    return data


def load_file_preserve_case(file_path: Path) -> list:
    """Load file lines preserving original case"""
    data = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(line)
    return data


def write_file(file_path: Path, data: list):
    """Write data to file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in data:
            f.write(f"{line}\\n")


def cleanup_organization_overlaps():
    """Remove unicorns and investors from general organization files"""
    
    base_path = Path("/home/corey/projects/docling/mvp-fusion/knowledge/corpus/foundation_data/org")
    
    print("🧹 ORGANIZATION FILE CLEANUP")
    print("=" * 60)
    
    # Load premium entity lists (lowercase for matching)
    unicorns = load_file_as_set(base_path / "unicorn_companies_2025_09_18.txt")
    investors = load_file_as_set(base_path / "investors_2025_09_18.txt")
    
    print(f"📊 Loaded {len(unicorns):,} unicorns and {len(investors):,} investors")
    
    # Combine premium entities for removal
    premium_entities = unicorns.union(investors)
    print(f"📊 Total premium entities to remove: {len(premium_entities):,}")
    
    # Process single-word organizations
    print("\\n🔍 Processing single-word organizations...")
    single_word_file = base_path / "single_word_organizations.txt"
    single_word_orgs = load_file_preserve_case(single_word_file)
    
    original_single_count = len(single_word_orgs)
    cleaned_single = []
    removed_single = []
    
    for org in single_word_orgs:
        if org.lower() not in premium_entities:
            cleaned_single.append(org)
        else:
            removed_single.append(org)
    
    print(f"   Original: {original_single_count:,} organizations")
    print(f"   Removed:  {len(removed_single):,} premium overlaps")
    print(f"   Cleaned:  {len(cleaned_single):,} organizations")
    
    if removed_single:
        print(f"   Sample removed: {removed_single[:10]}")
    
    # Process multi-word organizations
    print("\\n🔍 Processing multi-word organizations...")
    multi_word_file = base_path / "multi_word_organizations.txt"
    multi_word_orgs = load_file_preserve_case(multi_word_file)
    
    original_multi_count = len(multi_word_orgs)
    cleaned_multi = []
    removed_multi = []
    
    for org in multi_word_orgs:
        if org.lower() not in premium_entities:
            cleaned_multi.append(org)
        else:
            removed_multi.append(org)
    
    print(f"   Original: {original_multi_count:,} organizations")
    print(f"   Removed:  {len(removed_multi):,} premium overlaps") 
    print(f"   Cleaned:  {len(cleaned_multi):,} organizations")
    
    if removed_multi:
        print(f"   Sample removed: {removed_multi[:10]}")
    
    # Create backup files
    print("\\n💾 Creating backup files...")
    backup_single = base_path / "single_word_organizations_backup.txt"
    backup_multi = base_path / "multi_word_organizations_backup.txt"
    
    # Write backups
    write_file(backup_single, single_word_orgs)
    write_file(backup_multi, multi_word_orgs)
    print(f"   ✅ Backups created: {backup_single.name}, {backup_multi.name}")
    
    # Write cleaned files
    print("\\n✍️  Writing cleaned files...")
    write_file(single_word_file, cleaned_single)
    write_file(multi_word_file, cleaned_multi)
    
    print(f"   ✅ Updated: {single_word_file.name}")
    print(f"   ✅ Updated: {multi_word_file.name}")
    
    # Summary
    total_removed = len(removed_single) + len(removed_multi)
    total_original = original_single_count + original_multi_count
    total_cleaned = len(cleaned_single) + len(cleaned_multi)
    
    print("\\n📈 CLEANUP SUMMARY")
    print("-" * 60)
    print(f"Total original organizations: {total_original:,}")
    print(f"Total premium overlaps removed: {total_removed:,}")
    print(f"Total cleaned organizations: {total_cleaned:,}")
    print(f"Space saved: {((total_removed / total_original) * 100):.1f}%")
    
    print("\\n🎯 NEXT STEPS:")
    print("- Premium entities now only exist in unicorn/investor lists")
    print("- Entity extraction will get proper premium metadata")
    print("- No more duplicate detections with lost metadata")
    
    return {
        'total_removed': total_removed,
        'single_removed': len(removed_single),
        'multi_removed': len(removed_multi),
        'removed_entities': removed_single + removed_multi
    }


if __name__ == "__main__":
    result = cleanup_organization_overlaps()
    print(f"\\n🟢 Cleanup complete! Removed {result['total_removed']} overlapping entities.")
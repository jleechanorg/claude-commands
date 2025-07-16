#!/usr/bin/env python3
"""
CLAUDE.md Auto-Updater
Promotes high-confidence patterns to permanent rules in CLAUDE.md
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path.home() / ".cache" / "claude-learning" / "learning_memory.json"
CLAUDE_MD_PATH = Path.cwd() / "CLAUDE.md"
BACKUP_DIR = Path.home() / ".cache" / "claude-learning" / "backups"

class ClaudeMdUpdater:
    """Safely updates CLAUDE.md with high-confidence learned patterns"""
    
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self):
        """Create timestamped backup of CLAUDE.md"""
        if not CLAUDE_MD_PATH.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"CLAUDE_md_backup_{timestamp}.md"
        
        shutil.copy2(CLAUDE_MD_PATH, backup_path)
        return backup_path
    
    def get_promotable_patterns(self):
        """Get patterns ready for promotion to CLAUDE.md"""
        if not MEMORY_FILE.exists():
            return []
        
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
        except:
            return []
        
        promotable = []
        
        for pattern_id, pattern in memory.get("entities", {}).items():
            if pattern.get("type") == "user_correction":
                confidence = pattern.get("confidence", 0.0)
                applications = pattern.get("applied_count", 0)
                success_count = pattern.get("success_count", 0)
                success_rate = success_count / max(1, applications)
                
                # Strict promotion criteria
                if (confidence >= 0.9 and 
                    applications >= 5 and 
                    success_rate >= 0.8):
                    
                    promotable.append({
                        "id": pattern_id,
                        "pattern": pattern,
                        "confidence": confidence,
                        "applications": applications,
                        "success_rate": success_rate
                    })
        
        return sorted(promotable, key=lambda x: x["confidence"], reverse=True)
    
    def format_pattern_as_rule(self, pattern_data):
        """Convert learned pattern to CLAUDE.md rule format"""
        pattern = pattern_data["pattern"]
        correction_type = pattern.get("correction_type", "")
        pattern_match = pattern.get("pattern", "")
        contexts = pattern.get("context", [])
        
        # Format based on pattern type
        if correction_type == "dont_do_instead":
            if isinstance(pattern_match, list) and len(pattern_match) >= 2:
                return f"❌ NEVER {pattern_match[0]} | ✅ ALWAYS {pattern_match[1]}"
        
        elif correction_type == "preference":
            return f"✅ USER PREFERENCE: {pattern_match}"
        
        elif correction_type == "context_behavior":
            if isinstance(pattern_match, list) and len(pattern_match) >= 2:
                context = pattern_match[0]
                behavior = pattern_match[1]
                return f"⚠️ CONTEXT RULE: When {context}, {behavior}"
        
        elif correction_type == "always_rule":
            return f"✅ ALWAYS: {pattern_match}"
        
        elif correction_type == "never_rule":
            return f"❌ NEVER: {pattern_match}"
        
        # Fallback format
        return f"📝 LEARNED RULE: {pattern_match} (context: {', '.join(contexts)})"
    
    def find_insertion_point(self, claude_md_content):
        """Find appropriate place to insert learned rules in CLAUDE.md"""
        
        # Look for specific sections where rules can be added
        insertion_points = [
            (r"## Development Guidelines", "development"),
            (r"## Code Standards", "coding"),
            (r"## Testing", "testing"),
            (r"## Critical Lessons", "lessons"),
            (r"## Project-Specific", "project")
        ]
        
        for pattern, section in insertion_points:
            match = re.search(pattern, claude_md_content, re.MULTILINE)
            if match:
                # Find end of section (next ## or end of file)
                start = match.end()
                next_section = re.search(r"\n## ", claude_md_content[start:])
                if next_section:
                    end = start + next_section.start()
                else:
                    end = len(claude_md_content)
                
                return start, end, section
        
        # Fallback: add at end
        return len(claude_md_content), len(claude_md_content), "end"
    
    def update_claude_md(self, dry_run=True):
        """Update CLAUDE.md with high-confidence patterns"""
        
        # Get promotable patterns
        promotable_patterns = self.get_promotable_patterns()
        
        if not promotable_patterns:
            return {"status": "no_patterns", "message": "No patterns ready for promotion"}
        
        if not CLAUDE_MD_PATH.exists():
            return {"status": "error", "message": "CLAUDE.md not found"}
        
        # Read current CLAUDE.md
        with open(CLAUDE_MD_PATH, 'r') as f:
            original_content = f.read()
        
        # Create backup
        backup_path = self.create_backup()
        
        # Generate new rules
        new_rules = []
        for pattern_data in promotable_patterns:
            rule = self.format_pattern_as_rule(pattern_data)
            confidence = pattern_data["confidence"]
            applications = pattern_data["applications"]
            
            new_rules.append(f"- {rule} (learned: {confidence:.2f} confidence, {applications} applications)")
        
        # Find insertion point
        insert_start, insert_end, section = self.find_insertion_point(original_content)
        
        # Create learned rules section
        learned_section = f"""

### 🧠 Learned Rules (Auto-Generated from Experience)
*Rules promoted from dynamic learning system based on user corrections*

{chr(10).join(new_rules)}

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # Insert new content
        new_content = (
            original_content[:insert_start] + 
            learned_section + 
            original_content[insert_end:]
        )
        
        if dry_run:
            return {
                "status": "dry_run",
                "message": f"Would add {len(new_rules)} rules to {section} section",
                "backup_path": str(backup_path),
                "new_rules": new_rules,
                "preview": learned_section
            }
        
        # Write updated content
        with open(CLAUDE_MD_PATH, 'w') as f:
            f.write(new_content)
        
        # Mark patterns as promoted
        self._mark_patterns_promoted(promotable_patterns)
        
        return {
            "status": "success",
            "message": f"Added {len(new_rules)} rules to CLAUDE.md",
            "backup_path": str(backup_path),
            "rules_added": len(new_rules)
        }
    
    def _mark_patterns_promoted(self, promoted_patterns):
        """Mark patterns as promoted to CLAUDE.md"""
        if not MEMORY_FILE.exists():
            return
        
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
        except:
            return
        
        for pattern_data in promoted_patterns:
            pattern_id = pattern_data["id"]
            if pattern_id in memory.get("entities", {}):
                pattern = memory["entities"][pattern_id]
                pattern["promoted_to_claude_md"] = True
                pattern["promotion_date"] = datetime.now().isoformat()
                pattern["promotion_confidence"] = pattern_data["confidence"]
        
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
    
    def rollback_to_backup(self, backup_path):
        """Rollback CLAUDE.md to a specific backup"""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            return {"status": "error", "message": "Backup file not found"}
        
        shutil.copy2(backup_file, CLAUDE_MD_PATH)
        
        return {
            "status": "success", 
            "message": f"Rolled back to backup: {backup_file.name}"
        }
    
    def list_backups(self):
        """List available CLAUDE.md backups"""
        backups = list(self.backup_dir.glob("CLAUDE_md_backup_*.md"))
        
        backup_info = []
        for backup in sorted(backups, reverse=True):
            timestamp = backup.stem.replace("CLAUDE_md_backup_", "")
            size = backup.stat().st_size
            backup_info.append({
                "path": str(backup),
                "timestamp": timestamp,
                "size": size,
                "created": datetime.fromtimestamp(backup.stat().st_mtime)
            })
        
        return backup_info

def promote_patterns_to_claude_md(dry_run=True):
    """Main function to promote high-confidence patterns to CLAUDE.md"""
    updater = ClaudeMdUpdater()
    return updater.update_claude_md(dry_run=dry_run)

if __name__ == "__main__":
    import sys
    
    updater = ClaudeMdUpdater()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            # Check what patterns are ready for promotion
            patterns = updater.get_promotable_patterns()
            if patterns:
                print(f"🚀 {len(patterns)} patterns ready for promotion:")
                for p in patterns:
                    rule = updater.format_pattern_as_rule(p)
                    print(f"  • {rule}")
                    print(f"    Confidence: {p['confidence']:.2f}, Applications: {p['applications']}")
            else:
                print("No patterns ready for promotion")
        
        elif command == "preview":
            # Show what would be added (dry run)
            result = updater.update_claude_md(dry_run=True)
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            if "preview" in result:
                print("\nPreview of changes:")
                print(result["preview"])
        
        elif command == "promote":
            # Actually update CLAUDE.md
            result = updater.update_claude_md(dry_run=False)
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            if result["status"] == "success":
                print(f"Backup created at: {result['backup_path']}")
        
        elif command == "backups":
            # List available backups
            backups = updater.list_backups()
            if backups:
                print(f"📁 {len(backups)} CLAUDE.md backups available:")
                for backup in backups:
                    print(f"  • {backup['timestamp']} ({backup['size']} bytes)")
            else:
                print("No backups found")
        
        elif command == "rollback" and len(sys.argv) > 2:
            # Rollback to specific backup
            backup_path = sys.argv[2]
            result = updater.rollback_to_backup(backup_path)
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
    
    else:
        print("Usage:")
        print("  python claude_md_updater.py check")
        print("  python claude_md_updater.py preview")
        print("  python claude_md_updater.py promote")
        print("  python claude_md_updater.py backups")
        print("  python claude_md_updater.py rollback <backup_path>")
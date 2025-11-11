#!/usr/bin/env python3
"""
Genesis Prompt Extraction Tool with Incremental Saves
Extracts 6,208 user prompts for 10-agent processing with progress checkpoints.
"""

import glob
import json
from datetime import datetime
from pathlib import Path


class PromptExtractor:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.checkpoints_dir = self.base_dir / "checkpoints"
        self.chunks_dir = self.base_dir / "chunks"
        self.summary_dir = self.base_dir / "summary"

        # Create directories if they don't exist
        for dir_path in [self.checkpoints_dir, self.chunks_dir, self.summary_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Processing state
        self.extracted_prompts = []
        self.seen_keys = set()
        self.progress_count = 0
        self.checkpoint_interval = 100

        # Exclusion patterns
        self.exclude_patterns = [
            "Caveat:",
            "<command-name>",
            "**CRITICAL FILE",
            "🚨 CRITICAL FILE"
        ]

        # Statistics
        self.stats = {
            "total_files_processed": 0,
            "total_messages_processed": 0,
            "user_messages_found": 0,
            "filtered_out": 0,
            "duplicates_removed": 0,
            "final_unique_prompts": 0,
            "processing_start_time": datetime.now().isoformat(),
            "processing_end_time": None
        }

    def get_dedup_key(self, content: str) -> str:
        """Generate deduplication key from first 100 characters."""
        return content[:100].strip().lower()

    def should_exclude(self, content: str) -> bool:
        """Check if content should be excluded based on patterns."""
        if len(content.strip()) < 10:
            return True

        for pattern in self.exclude_patterns:
            if pattern in content:
                return True

        return False

    def save_checkpoint(self, checkpoint_num: int):
        """Save incremental progress checkpoint."""
        checkpoint_file = self.checkpoints_dir / f"extraction_progress_{checkpoint_num:03d}.json"

        checkpoint_data = {
            "checkpoint_number": checkpoint_num,
            "prompts_count": len(self.extracted_prompts),
            "timestamp": datetime.now().isoformat(),
            "prompts": self.extracted_prompts[-self.checkpoint_interval:] if len(self.extracted_prompts) >= self.checkpoint_interval else self.extracted_prompts,
            "stats": self.stats.copy()
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

        print(f"💾 Checkpoint {checkpoint_num:03d} saved: {len(self.extracted_prompts)} prompts extracted")

    def extract_from_jsonl_file(self, file_path: Path):
        """Extract user prompts from a single JSONL file."""
        try:
            with open(file_path) as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        self.stats["total_messages_processed"] += 1

                        # Check if this is a user message (nested structure)
                        if data.get("type") != "user":
                            continue

                        message = data.get("message", {})
                        if message.get("role") != "user":
                            continue

                        self.stats["user_messages_found"] += 1
                        content = message.get("content", "")

                        # Handle both string and array content formats
                        if isinstance(content, list):
                            # Extract text from array format
                            text_parts = []
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    text_parts.append(item.get("text", ""))
                            content = "\n".join(text_parts)

                        content = content.strip()

                        # Apply exclusion filters
                        if self.should_exclude(content):
                            self.stats["filtered_out"] += 1
                            continue

                        # Check for duplicates
                        dedup_key = self.get_dedup_key(content)
                        if dedup_key in self.seen_keys:
                            self.stats["duplicates_removed"] += 1
                            continue

                        self.seen_keys.add(dedup_key)

                        # Extract metadata
                        prompt_data = {
                            "content": content,
                            "timestamp": data.get("timestamp"),
                            "project": str(file_path.parent.name),
                            "file": str(file_path.name),
                            "conversation_id": data.get("conversation_id"),
                            "dedup_key": dedup_key,
                            "extraction_order": len(self.extracted_prompts) + 1
                        }

                        self.extracted_prompts.append(prompt_data)
                        self.progress_count += 1

                        # Save checkpoint every 100 prompts
                        if self.progress_count % self.checkpoint_interval == 0:
                            checkpoint_num = self.progress_count // self.checkpoint_interval
                            self.save_checkpoint(checkpoint_num)

                            # Progress report
                            progress_pct = (self.progress_count / 6208) * 100
                            print(f"📊 Progress: {self.progress_count}/6208 prompts ({progress_pct:.1f}%)")

                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON decode error in {file_path}:{line_num}: {e}")
                        continue

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")

    def extract_all_prompts(self):
        """Extract prompts from all JSONL files in ~/.claude/projects/."""
        claude_projects_path = Path.home() / ".claude" / "projects"

        if not claude_projects_path.exists():
            print(f"❌ Claude projects directory not found: {claude_projects_path}")
            return

        print(f"🔍 Searching for JSONL files in: {claude_projects_path}")

        # Find all JSONL files
        jsonl_pattern = str(claude_projects_path / "*" / "*.jsonl")
        jsonl_files = glob.glob(jsonl_pattern)

        print(f"📁 Found {len(jsonl_files)} JSONL files to process")

        # Process each file
        for file_path in jsonl_files:
            file_path = Path(file_path)
            print(f"🔄 Processing: {file_path.parent.name}/{file_path.name}")
            self.stats["total_files_processed"] += 1
            self.extract_from_jsonl_file(file_path)

        # Save final checkpoint if needed
        if self.progress_count % self.checkpoint_interval != 0:
            final_checkpoint_num = (self.progress_count // self.checkpoint_interval) + 1
            self.save_checkpoint(final_checkpoint_num)

        self.stats["final_unique_prompts"] = len(self.extracted_prompts)
        self.stats["processing_end_time"] = datetime.now().isoformat()

        print(f"✅ Extraction complete: {len(self.extracted_prompts)} unique prompts extracted")

    def create_balanced_chunks(self):
        """Create 10 balanced chunks of ~620 prompts each."""
        total_prompts = len(self.extracted_prompts)
        chunk_size = total_prompts // 10
        remainder = total_prompts % 10

        print(f"📦 Creating 10 chunks from {total_prompts} prompts (base size: {chunk_size})")

        start_idx = 0
        for i in range(10):
            # Add one extra prompt to first 'remainder' chunks to balance
            current_chunk_size = chunk_size + (1 if i < remainder else 0)
            end_idx = start_idx + current_chunk_size

            chunk_data = {
                "chunk_number": i + 1,
                "total_chunks": 10,
                "prompts_count": current_chunk_size,
                "start_index": start_idx,
                "end_index": end_idx - 1,
                "creation_timestamp": datetime.now().isoformat(),
                "prompts": self.extracted_prompts[start_idx:end_idx]
            }

            chunk_file = self.chunks_dir / f"chunk_{i+1:03d}.json"
            with open(chunk_file, 'w') as f:
                json.dump(chunk_data, f, indent=2)

            print(f"📦 Chunk {i+1:02d}: {current_chunk_size} prompts ({start_idx+1}-{end_idx})")
            start_idx = end_idx

    def generate_summary(self):
        """Generate extraction summary with statistics and metadata."""
        summary = {
            "extraction_metadata": {
                "total_prompts_extracted": len(self.extracted_prompts),
                "target_prompts": 6208,
                "achievement_rate": (len(self.extracted_prompts) / 6208) * 100,
                "chunks_created": 10,
                "average_chunk_size": len(self.extracted_prompts) // 10
            },
            "processing_statistics": self.stats,
            "quality_metrics": {
                "deduplication_rate": (self.stats["duplicates_removed"] / max(self.stats["user_messages_found"], 1)) * 100,
                "filter_rate": (self.stats["filtered_out"] / max(self.stats["user_messages_found"], 1)) * 100,
                "extraction_efficiency": (len(self.extracted_prompts) / max(self.stats["total_messages_processed"], 1)) * 100
            },
            "file_structure": {
                "checkpoints_created": len(list(self.checkpoints_dir.glob("*.json"))),
                "chunks_created": len(list(self.chunks_dir.glob("*.json"))),
                "base_directory": str(self.base_dir)
            }
        }

        summary_file = self.summary_dir / "extraction_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"📋 Summary saved: {summary_file}")
        return summary

def main():
    """Main execution function."""
    base_dir = "/Users/jleechan/projects/worktree_genesis/docs/genesis/processing"

    print("🚀 Genesis Prompt Extraction Tool Starting...")
    print("=" * 60)

    extractor = PromptExtractor(base_dir)

    # Extract all prompts with incremental saves
    extractor.extract_all_prompts()

    # Create balanced chunks
    extractor.create_balanced_chunks()

    # Generate summary
    summary = extractor.generate_summary()

    print("=" * 60)
    print("📊 EXTRACTION COMPLETE")
    print(f"✅ Total prompts extracted: {summary['extraction_metadata']['total_prompts_extracted']}")
    print(f"🎯 Target achievement: {summary['extraction_metadata']['achievement_rate']:.1f}%")
    print(f"📦 Chunks created: {summary['extraction_metadata']['chunks_created']}")
    print(f"🔄 Deduplication rate: {summary['quality_metrics']['deduplication_rate']:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    main()

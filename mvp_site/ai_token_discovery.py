#!/usr/bin/env python3
"""
AI Token Discovery System

Analyzes narrative samples to discover special tokens, patterns, and syntax
that the AI might be using but aren't properly handled by the codebase.
"""

import json
import re
import os
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any
import argparse


class AITokenDiscovery:
    """Discovers and analyzes AI tokens and patterns in narrative samples."""
    
    def __init__(self):
        self.special_patterns = {
            'deletion_tokens': [r'__DELETE__', r'__REMOVE__', r'__CLEAR__'],
            'markup_tokens': [r'__[A-Z_]+__', r'\*\*[^*]+\*\*', r'\*[^*]+\*'],
            'state_commands': [r'SET_[A-Z_]+', r'UPDATE_[A-Z_]+', r'REMOVE_[A-Z_]+'],
            'json_fragments': [r'\{[^}]*\}', r'\[[^\]]*\]'],
            'special_punctuation': [r'===+', r'---+', r'\|\|\|+', r'>>>', r'<<<'],
            'ai_directives': [r'<[^>]+>', r'\([A-Z_]+\)', r'\[AI[^\]]*\]'],
        }
        
        self.discovered_tokens = defaultdict(list)
        self.token_contexts = defaultdict(list)
        self.pattern_stats = Counter()
        self.progress_counter = 0
        self.temp_dir = '/tmp/ai_token_discovery_progress'
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def analyze_narrative_samples(self, samples_file: str) -> Dict[str, Any]:
        """Analyze narrative samples for AI tokens and patterns."""
        print(f"Loading samples from {samples_file}...")
        
        with open(samples_file, 'r') as f:
            data = json.load(f)
        
        samples = data.get('samples', [])
        total_samples = len(samples)
        
        print(f"Analyzing {total_samples} narrative samples...")
        
        results = {
            'metadata': {
                'total_samples': total_samples,
                'analysis_patterns': list(self.special_patterns.keys()),
                'source_file': samples_file
            },
            'discovered_tokens': {},
            'pattern_analysis': {},
            'recommendations': []
        }
        
        # Analyze each sample
        for i, sample in enumerate(samples):
            if i % 20 == 0:
                print(f"Progress: {i}/{total_samples} samples analyzed")
            
            self._analyze_sample(sample)
            self.progress_counter += 1
            
            # Save partial progress every 10 samples
            if self.progress_counter % 10 == 0:
                self._save_partial_progress(i, total_samples)
        
        # Compile results
        results['discovered_tokens'] = dict(self.discovered_tokens)
        results['pattern_analysis'] = self._analyze_patterns()
        results['recommendations'] = self._generate_recommendations()
        
        print("Analysis complete!")
        return results
    
    def _analyze_sample(self, sample: Dict[str, Any]) -> None:
        """Analyze a single narrative sample for tokens and patterns."""
        narrative = sample.get('narrative', '')
        sample_id = sample.get('sample_id', 'unknown')
        
        # Check each pattern category
        for pattern_type, patterns in self.special_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, narrative, re.IGNORECASE)
                if matches:
                    self.discovered_tokens[pattern_type].extend(matches)
                    self.pattern_stats[pattern_type] += len(matches)
                    
                    # Store context for interesting matches
                    if pattern_type in ['deletion_tokens', 'state_commands', 'ai_directives']:
                        for match in matches:
                            context = self._extract_context(narrative, match)
                            self.token_contexts[match].append({
                                'sample_id': sample_id,
                                'context': context,
                                'full_narrative': narrative
                            })
    
    def _extract_context(self, text: str, token: str, window: int = 50) -> str:
        """Extract context around a discovered token."""
        pos = text.lower().find(token.lower())
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(token) + window)
        
        context = text[start:end]
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
            
        return context
    
    def _save_partial_progress(self, current_sample: int, total_samples: int) -> None:
        """Save partial progress to temp files."""
        progress_file = os.path.join(self.temp_dir, f'progress_{self.progress_counter}.json')
        
        partial_results = {
            'progress': {
                'samples_processed': current_sample + 1,
                'total_samples': total_samples,
                'progress_counter': self.progress_counter,
                'timestamp': f"{current_sample + 1}/{total_samples} samples analyzed"
            },
            'discovered_tokens_so_far': dict(self.discovered_tokens),
            'pattern_stats_so_far': dict(self.pattern_stats),
            'unique_tokens_found': len(set(token for tokens in self.discovered_tokens.values() for token in tokens))
        }
        
        with open(progress_file, 'w') as f:
            json.dump(partial_results, f, indent=2)
        
        print(f"Saved progress to {progress_file}")
    
    def _analyze_patterns(self) -> Dict[str, Any]:
        """Analyze discovered patterns for insights."""
        pattern_analysis = {}
        
        for pattern_type, tokens in self.discovered_tokens.items():
            if not tokens:
                continue
                
            unique_tokens = list(set(tokens))
            token_counts = Counter(tokens)
            
            pattern_analysis[pattern_type] = {
                'total_occurrences': len(tokens),
                'unique_tokens': len(unique_tokens),
                'most_common': token_counts.most_common(10),
                'sample_tokens': unique_tokens[:20]  # First 20 unique tokens
            }
        
        return pattern_analysis
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on discovered patterns."""
        recommendations = []
        
        # Check for deletion tokens
        if 'deletion_tokens' in self.discovered_tokens and self.discovered_tokens['deletion_tokens']:
            recommendations.append(
                "CRITICAL: Found deletion tokens like '__DELETE__' in narratives. "
                "Verify that code exists to process these tokens in game state updates."
            )
        
        # Check for state commands
        if 'state_commands' in self.discovered_tokens and self.discovered_tokens['state_commands']:
            recommendations.append(
                "Found state command patterns. Verify these are properly parsed and executed."
            )
        
        # Check for AI directives
        if 'ai_directives' in self.discovered_tokens and self.discovered_tokens['ai_directives']:
            recommendations.append(
                "Found AI directive patterns. These may indicate the AI is trying to "
                "communicate meta-information that isn't being processed."
            )
        
        # Check for JSON fragments
        if 'json_fragments' in self.discovered_tokens and self.discovered_tokens['json_fragments']:
            json_count = len(self.discovered_tokens['json_fragments'])
            if json_count > 10:
                recommendations.append(
                    f"Found {json_count} JSON-like fragments in narratives. "
                    "This may indicate the AI is trying to embed structured data."
                )
        
        # General recommendation
        recommendations.append(
            "Review prompts/game_state_instruction.md to ensure all documented tokens "
            "have corresponding implementation in the codebase."
        )
        
        return recommendations
    
    def search_codebase_for_tokens(self, discovered_tokens: Dict[str, List[str]], 
                                   codebase_dir: str = '.') -> Dict[str, Dict[str, bool]]:
        """Search codebase to see which discovered tokens are actually handled."""
        print("Searching codebase for token implementations...")
        
        implementation_status = {}
        
        # Get all unique tokens
        all_tokens = set()
        for token_list in discovered_tokens.values():
            all_tokens.update(token_list)
        
        # Search for each token in Python files
        python_files = []
        for root, dirs, files in os.walk(codebase_dir):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        for token in all_tokens:
            implementation_status[token] = {
                'found_in_code': False,
                'found_in_prompts': False,
                'locations': []
            }
            
            # Search in Python files
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if token in content:
                            implementation_status[token]['found_in_code'] = True
                            implementation_status[token]['locations'].append(py_file)
                except (UnicodeDecodeError, IOError):
                    continue
            
            # Search in prompt files
            prompts_dir = os.path.join(codebase_dir, 'prompts')
            if os.path.exists(prompts_dir):
                for root, dirs, files in os.walk(prompts_dir):
                    for file in files:
                        if file.endswith('.md'):
                            prompt_file = os.path.join(root, file)
                            try:
                                with open(prompt_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    if token in content:
                                        implementation_status[token]['found_in_prompts'] = True
                                        implementation_status[token]['locations'].append(prompt_file)
                            except (UnicodeDecodeError, IOError):
                                continue
        
        return implementation_status


def main():
    parser = argparse.ArgumentParser(description='Discover AI tokens in narrative samples')
    parser.add_argument('samples_file', help='Path to narrative samples JSON file')
    parser.add_argument('--output', '-o', help='Output file for results (JSON)', 
                        default='ai_token_discovery_results.json')
    parser.add_argument('--codebase-dir', help='Directory to search for token implementations',
                        default='.')
    
    args = parser.parse_args()
    
    # Run discovery
    discoverer = AITokenDiscovery()
    results = discoverer.analyze_narrative_samples(args.samples_file)
    
    # Search codebase for implementations
    implementation_status = discoverer.search_codebase_for_tokens(
        results['discovered_tokens'], args.codebase_dir
    )
    results['implementation_status'] = implementation_status
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {args.output}")
    
    # Print summary
    print("\n=== AI TOKEN DISCOVERY SUMMARY ===")
    print(f"Total samples analyzed: {results['metadata']['total_samples']}")
    
    for pattern_type, analysis in results['pattern_analysis'].items():
        print(f"\n{pattern_type.upper()}:")
        print(f"  Total occurrences: {analysis['total_occurrences']}")
        print(f"  Unique tokens: {analysis['unique_tokens']}")
        if analysis['most_common']:
            print(f"  Most common: {analysis['most_common'][0]}")
    
    print("\n=== IMPLEMENTATION GAPS ===")
    gaps_found = False
    for token, status in implementation_status.items():
        if not status['found_in_code'] and token.strip():
            if not gaps_found:
                gaps_found = True
            print(f"  '{token}' - Found in prompts: {status['found_in_prompts']}, "
                  f"Found in code: {status['found_in_code']}")
    
    if not gaps_found:
        print("  No obvious implementation gaps found.")
    
    print("\n=== RECOMMENDATIONS ===")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. {rec}")


if __name__ == '__main__':
    main()
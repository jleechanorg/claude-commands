#!/usr/bin/env python3
"""
Tests for campaign list pagination functionality.

Tests cursor-based pagination to ensure:
1. Default limit of 50 campaigns
2. Cursor-based pagination works correctly
3. has_more flag is accurate
4. next_cursor is properly generated
5. Multiple pages can be loaded sequentially
"""

import asyncio
import datetime
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

os.environ.setdefault('WORLDAI_DEV_MODE', 'true')
os.environ.setdefault('MOCK_SERVICES_MODE', 'true')

from mvp_site import firestore_service, world_logic


class TestCampaignPagination:
    """Test campaign list pagination."""

    def test_default_limit_is_50(self):
        """Test that default limit is 50 campaigns."""
        # Mock Firestore to return 60 campaigns
        with patch('mvp_site.firestore_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_collection = MagicMock()
            mock_db.collection.return_value.document.return_value.collection.return_value = mock_collection
            
            mock_query = MagicMock()
            mock_collection.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            # Create 60 mock documents
            mock_docs = []
            for i in range(60):
                mock_doc = MagicMock()
                mock_doc.id = f'campaign_{i}'
                mock_doc.to_dict.return_value = {
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                mock_docs.append(mock_doc)
            
            mock_query.stream.return_value = iter(mock_docs)
            
            campaigns, next_cursor, _ = firestore_service.get_campaigns_for_user(
                'test_user_id', limit=None, sort_by='last_played'
            )
            
            # Should return 50 campaigns (default limit)
            assert len(campaigns) == 50, f"Expected 50 campaigns, got {len(campaigns)}"
            assert next_cursor is not None, "Should have next_cursor when more results exist"

    def test_custom_limit(self):
        """Test that custom limit works."""
        with patch('mvp_site.firestore_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_collection = MagicMock()
            mock_db.collection.return_value.document.return_value.collection.return_value = mock_collection
            
            mock_query = MagicMock()
            mock_collection.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            # Create 30 mock documents
            mock_docs = []
            for i in range(30):
                mock_doc = MagicMock()
                mock_doc.id = f'campaign_{i}'
                mock_doc.to_dict.return_value = {
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                mock_docs.append(mock_doc)
            
            mock_query.stream.return_value = iter(mock_docs)
            
            campaigns, next_cursor, _ = firestore_service.get_campaigns_for_user(
                'test_user_id', limit=20, sort_by='last_played'
            )
            
            # Should return 20 campaigns
            assert len(campaigns) == 20, f"Expected 20 campaigns, got {len(campaigns)}"
            assert next_cursor is not None, "Should have next_cursor when more results exist"

    def test_no_more_results(self):
        """Test that next_cursor is None when no more results."""
        with patch('mvp_site.firestore_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_collection = MagicMock()
            mock_db.collection.return_value.document.return_value.collection.return_value = mock_collection
            
            mock_query = MagicMock()
            mock_collection.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            # Create 10 mock documents (less than limit)
            mock_docs = []
            for i in range(10):
                mock_doc = MagicMock()
                mock_doc.id = f'campaign_{i}'
                mock_doc.to_dict.return_value = {
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                mock_docs.append(mock_doc)
            
            mock_query.stream.return_value = iter(mock_docs)
            
            campaigns, next_cursor, _ = firestore_service.get_campaigns_for_user(
                'test_user_id', limit=50, sort_by='last_played'
            )
            
            # Should return 10 campaigns
            assert len(campaigns) == 10, f"Expected 10 campaigns, got {len(campaigns)}"
            assert next_cursor is None, "Should not have next_cursor when no more results"

    def test_cursor_structure(self):
        """Test that cursor has correct structure."""
        with patch('mvp_site.firestore_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_collection = MagicMock()
            mock_db.collection.return_value.document.return_value.collection.return_value = mock_collection
            
            mock_query = MagicMock()
            mock_collection.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            # Create 60 mock documents
            mock_docs = []
            for i in range(60):
                mock_doc = MagicMock()
                mock_doc.id = f'campaign_{i}'
                mock_doc.to_dict.return_value = {
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                mock_docs.append(mock_doc)
            
            mock_query.stream.return_value = iter(mock_docs)
            
            campaigns, next_cursor, _ = firestore_service.get_campaigns_for_user(
                'test_user_id', limit=50, sort_by='last_played'
            )
            
            # Check cursor structure
            assert next_cursor is not None, "Should have next_cursor"
            assert 'timestamp' in next_cursor, "Cursor should have timestamp"
            assert 'id' in next_cursor, "Cursor should have id"
            assert next_cursor['id'] == 'campaign_49', f"Cursor id should be campaign_49, got {next_cursor['id']}"

    @pytest.mark.asyncio
    async def test_get_campaigns_list_unified_pagination(self):
        """Test that get_campaigns_list_unified returns pagination metadata."""
        request_data = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
        }
        
        with patch('mvp_site.world_logic.asyncio.to_thread') as mock_to_thread:
            # Mock return value
            mock_campaigns = [
                {'id': f'campaign_{i}', 'title': f'Campaign {i}', 'last_played': f'2026-01-11T{10 + i}:00:00Z'}
                for i in range(50)
            ]
            mock_cursor = {'timestamp': '2026-01-11T10:00:00Z', 'id': 'campaign_49'}
            
            async def mock_to_thread_func(func, *args):
                return mock_campaigns, mock_cursor, None  # campaigns, cursor, total_count
            
            mock_to_thread.side_effect = mock_to_thread_func
            
            result = await world_logic.get_campaigns_list_unified(request_data)
            
            assert result.get('success') is True, "Should succeed"
            assert 'campaigns' in result, "Should have campaigns"
            assert len(result['campaigns']) == 50, f"Expected 50 campaigns, got {len(result['campaigns'])}"
            assert result.get('has_more') is True, "Should have more results"
            assert 'next_cursor' in result, "Should have next_cursor"
            assert result['next_cursor'] == mock_cursor, "Cursor should match"

    @pytest.mark.asyncio
    async def test_get_campaigns_list_unified_no_more(self):
        """Test that get_campaigns_list_unified returns has_more=False when no more results."""
        request_data = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
        }
        
        with patch('mvp_site.world_logic.asyncio.to_thread') as mock_to_thread:
            # Mock return value with only 10 campaigns
            mock_campaigns = [
                {'id': f'campaign_{i}', 'title': f'Campaign {i}', 'last_played': f'2026-01-11T{10 + i}:00:00Z'}
                for i in range(10)
            ]
            
            async def mock_to_thread_func(func, *args):
                return mock_campaigns, None, 10  # campaigns, cursor, total_count (10 total)
            
            mock_to_thread.side_effect = mock_to_thread_func
            
            result = await world_logic.get_campaigns_list_unified(request_data)
            
            assert result.get('success') is True, "Should succeed"
            assert len(result['campaigns']) == 10, f"Expected 10 campaigns, got {len(result['campaigns'])}"
            assert result.get('has_more') is False, "Should not have more results"
            assert result.get('next_cursor') is None, "Should not have next_cursor"

    def test_cursor_fallback_duplicate_timestamps(self):
        """Test fallback logic when multiple documents have same timestamp."""
        with patch('mvp_site.firestore_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_collection = MagicMock()
            mock_db.collection.return_value.document.return_value.collection.return_value = mock_collection
            
            mock_query = MagicMock()
            mock_collection.order_by.return_value = mock_query
            # Mock filtered query for fallback
            mock_filtered_query = MagicMock()
            mock_query.where.return_value = mock_filtered_query
            mock_filtered_query.limit.return_value = mock_filtered_query
            
            # Setup: 3 docs with SAME timestamp
            # We want to ensure the fallback query (using <=) captures them
            ts = '2026-01-11T12:00:00Z'
            mock_docs = []
            for i in range(3):
                mock_doc = MagicMock()
                mock_doc.id = f'campaign_{i}'
                mock_doc.to_dict.return_value = {
                    'title': f'Campaign {i}',
                    'last_played': ts,
                }
                mock_docs.append(mock_doc)
            
            # Simulate that cursor doc lookup failed (to trigger fallback)
            mock_collection.document.return_value.get.side_effect = Exception("Doc not found")
            
            # The fallback query should return the docs
            mock_filtered_query.stream.return_value = iter(mock_docs)
            
            # Execute with a cursor having the same timestamp
            start_after = {'timestamp': ts, 'id': 'missing_id'}
            
            campaigns, _, _ = firestore_service.get_campaigns_for_user(
                'test_user_id', limit=50, sort_by='last_played', start_after=start_after
            )
            
            # Verification:
            # 1. Verify fallback query used "<=" (inclusive) not "<" (exclusive)
            mock_query.where.assert_called_with('last_played', '<=', datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")))
            
            # 2. Verify all docs returned (frontend will dedupe overlaps)
            assert len(campaigns) == 3, f"Expected 3 campaigns, got {len(campaigns)}"


def run_tests():
    """Run all pagination tests."""
    test_suite = TestCampaignPagination()
    
    print("🧪 Running Campaign Pagination Tests...")
    print("=" * 80)
    
    tests = [
        ("Default limit is 50", test_suite.test_default_limit_is_50),
        ("Custom limit", test_suite.test_custom_limit),
        ("No more results", test_suite.test_no_more_results),
        ("Cursor structure", test_suite.test_cursor_structure),
        ("get_campaigns_list_unified pagination", test_suite.test_get_campaigns_list_unified_pagination),
        ("get_campaigns_list_unified no more", test_suite.test_get_campaigns_list_unified_no_more),
        ("Cursor fallback duplicate timestamps", test_suite.test_cursor_fallback_duplicate_timestamps),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                asyncio.run(test_func())
            else:
                test_func()
            print(f"✅ PASS: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAIL: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 80)
    print(f"Test Summary: {passed}/{len(tests)} passed")
    
    if failed > 0:
        print(f"❌ {failed} tests failed")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    run_tests()

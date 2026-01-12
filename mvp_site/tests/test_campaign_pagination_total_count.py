#!/usr/bin/env python3
"""
Tests for total campaign count functionality.

Tests that total_count is:
1. Calculated on first page only (include_total_count=True)
2. Not calculated on subsequent pages (include_total_count=False)
3. Included in API response when available
4. Handles aggregation failures gracefully
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

os.environ.setdefault('WORLDAI_DEV_MODE', 'true')
os.environ.setdefault('MOCK_SERVICES_MODE', 'true')

from mvp_site import firestore_service, world_logic


class TestCampaignPaginationTotalCount:
    """Test total campaign count functionality."""

    def test_total_count_included_on_first_page(self):
        """Test that total_count is included in response on first page."""
        request_data = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
            # No start_after = first page
        }
        
        with patch('mvp_site.world_logic.asyncio.to_thread') as mock_to_thread:
            mock_campaigns = [
                {'id': f'campaign_{i}', 'title': f'Campaign {i}', 'last_played': f'2026-01-11T{10 + i}:00:00Z'}
                for i in range(50)
            ]
            mock_cursor = {'timestamp': '2026-01-11T10:00:00Z', 'id': 'campaign_49'}
            total_count = 200  # Total campaigns in database
            
            async def mock_to_thread_func(func, *args):
                # Verify include_total_count=True is passed on first page
                # args are: (user_id, limit, sort_by, start_after, include_total_count)
                if len(args) >= 5:
                    include_total = args[4]
                    assert include_total is True, f"include_total_count should be True on first page, got {include_total}"
                return mock_campaigns, mock_cursor, total_count
            
            mock_to_thread.side_effect = mock_to_thread_func
            
            result = asyncio.run(world_logic.get_campaigns_list_unified(request_data))
            
            assert result.get('success') is True, "Should succeed"
            assert 'total_count' in result, "Should include total_count in response"
            assert result['total_count'] == 200, f"Expected total_count=200, got {result.get('total_count')}"

    def test_total_count_not_included_on_subsequent_pages(self):
        """Test that total_count is NOT calculated on subsequent pages."""
        request_data = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
            'start_after': {'timestamp': '2026-01-11T10:00:00Z', 'id': 'campaign_49'},
        }
        
        with patch('mvp_site.world_logic.asyncio.to_thread') as mock_to_thread:
            mock_campaigns = [
                {'id': f'campaign_{i}', 'title': f'Campaign {i}', 'last_played': f'2026-01-11T{10 + i}:00:00Z'}
                for i in range(50, 100)
            ]
            mock_cursor = {'timestamp': '2026-01-11T11:00:00Z', 'id': 'campaign_99'}
            
            async def mock_to_thread_func(func, *args):
                # Verify include_total_count=False is passed on subsequent pages
                # args are: (user_id, limit, sort_by, start_after, include_total_count)
                if len(args) >= 5:
                    include_total = args[4]
                    assert include_total is False, f"include_total_count should be False on subsequent pages, got {include_total}"
                return mock_campaigns, mock_cursor, None  # No total_count on subsequent pages
            
            mock_to_thread.side_effect = mock_to_thread_func
            
            result = asyncio.run(world_logic.get_campaigns_list_unified(request_data))
            
            assert result.get('success') is True, "Should succeed"
            # total_count should not be in response on subsequent pages
            assert 'total_count' not in result or result.get('total_count') is None, \
                "Should not include total_count on subsequent pages"

    def test_firestore_include_total_count_parameter(self):
        """Test that firestore_service.get_campaigns_for_user accepts include_total_count parameter."""
        with patch('mvp_site.firestore_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Setup the collection chain: db.collection("users").document(user_id).collection("campaigns")
            mock_users_collection = MagicMock()
            mock_user_doc_ref = MagicMock()
            mock_campaigns_collection = MagicMock()
            
            mock_db.collection.return_value = mock_users_collection
            mock_users_collection.document.return_value = mock_user_doc_ref
            mock_user_doc_ref.collection.return_value = mock_campaigns_collection
            
            mock_query = MagicMock()
            mock_campaigns_collection.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            # Mock aggregation query for count
            mock_agg_result = MagicMock()
            mock_agg_result.get.return_value = 150  # Total count
            mock_agg_query = MagicMock()
            mock_agg_query.count.return_value = mock_agg_query
            mock_agg_query.get.return_value = [mock_agg_result]
            
            # Mock AGGREGATION_QUERY
            with patch('mvp_site.firestore_service.AGGREGATION_QUERY') as mock_agg_class:
                mock_agg_class.return_value = mock_agg_query
                
                # Create mock documents
                mock_docs = []
                for i in range(50):
                    mock_doc = MagicMock()
                    mock_doc.id = f'campaign_{i}'
                    mock_doc.to_dict.return_value = {
                        'title': f'Campaign {i}',
                        'last_played': f'2026-01-11T{10 + i}:00:00Z',
                    }
                    mock_docs.append(mock_doc)
                
                mock_query.stream.return_value = iter(mock_docs)
                
                # Test with include_total_count=True
                campaigns, cursor, total_count = firestore_service.get_campaigns_for_user(
                    'test_user_id', limit=50, sort_by='last_played', 
                    start_after=None, include_total_count=True
                )
                
                assert len(campaigns) == 50, "Should return 50 campaigns"
                assert total_count == 150, f"Expected total_count=150, got {total_count}"
                # Verify aggregation query was called with campaigns_collection
                mock_agg_class.assert_called_once_with(mock_campaigns_collection)

    def test_firestore_total_count_not_calculated_on_subsequent_pages(self):
        """Test that total_count is not calculated when start_after is provided."""
        with patch('mvp_site.firestore_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_collection = MagicMock()
            mock_db.collection.return_value.document.return_value.collection.return_value = mock_collection
            
            mock_query = MagicMock()
            mock_collection.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.start_after.return_value = mock_query
            
            # Create mock documents
            mock_docs = []
            for i in range(50, 100):
                mock_doc = MagicMock()
                mock_doc.id = f'campaign_{i}'
                mock_doc.to_dict.return_value = {
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                mock_docs.append(mock_doc)
            
            mock_query.stream.return_value = iter(mock_docs)
            
            # Mock AGGREGATION_QUERY (should not be called)
            with patch('mvp_site.firestore_service.AGGREGATION_QUERY') as mock_agg_class:
                # Test with include_total_count=True but start_after provided (should skip count)
                campaigns, cursor, total_count = firestore_service.get_campaigns_for_user(
                    'test_user_id', limit=50, sort_by='last_played',
                    start_after={'timestamp': '2026-01-11T10:00:00Z', 'id': 'campaign_49'},
                    include_total_count=True
                )
                
                assert len(campaigns) == 50, "Should return 50 campaigns"
                assert total_count is None, "Should not calculate total_count when start_after is provided"
                # Verify aggregation query was NOT called
                mock_agg_class.assert_not_called()

    def test_firestore_total_count_fallback_on_aggregation_failure(self):
        """Test that total_count falls back to stream() if aggregation fails."""
        with patch('mvp_site.firestore_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Setup the collection chain: db.collection("users").document(user_id).collection("campaigns")
            mock_users_collection = MagicMock()
            mock_user_doc_ref = MagicMock()
            mock_campaigns_collection = MagicMock()
            
            mock_db.collection.return_value = mock_users_collection
            mock_users_collection.document.return_value = mock_user_doc_ref
            mock_user_doc_ref.collection.return_value = mock_campaigns_collection
            
            mock_query = MagicMock()
            mock_campaigns_collection.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            # Create mock documents for query (50 campaigns)
            mock_docs = []
            for i in range(50):
                mock_doc = MagicMock()
                mock_doc.id = f'campaign_{i}'
                mock_doc.to_dict.return_value = {
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                mock_docs.append(mock_doc)
            
            mock_query.stream.return_value = iter(mock_docs)
            
            # Mock AGGREGATION_QUERY to raise exception
            with patch('mvp_site.firestore_service.AGGREGATION_QUERY') as mock_agg_class:
                mock_agg_class.side_effect = Exception("Aggregation not available")
                
                # Mock stream() for fallback (should return all 150 campaigns for count)
                # The fallback uses campaigns_ref.stream() where campaigns_ref = user_doc.collection("campaigns")
                # But in the code, it's actually campaigns_ref which is already set up
                all_campaigns = []
                for i in range(150):
                    mock_doc = MagicMock()
                    mock_doc.id = f'campaign_{i}'
                    all_campaigns.append(mock_doc)
                # The fallback uses campaigns_ref.stream() - mock this
                mock_campaigns_collection.stream.return_value = iter(all_campaigns)
                
                campaigns, cursor, total_count = firestore_service.get_campaigns_for_user(
                    'test_user_id', limit=50, sort_by='last_played',
                    start_after=None, include_total_count=True
                )
                
                assert len(campaigns) == 50, "Should return 50 campaigns"
                # Fallback should calculate total_count from stream
                assert total_count == 150, f"Expected total_count=150 from fallback, got {total_count}"

    def test_total_count_preserved_across_pages(self):
        """Test that total_count from first page is preserved and used correctly."""
        # First page - should include total_count
        request_data_1 = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
        }
        
        with patch('mvp_site.world_logic.asyncio.to_thread') as mock_to_thread:
            page = 0
            async def mock_to_thread_func(func, *args):
                nonlocal page
                if page == 0:
                    # First page - return total_count
                    mock_campaigns = [
                        {'id': f'campaign_{i}', 'title': f'Campaign {i}', 'last_played': f'2026-01-11T{10 + i}:00:00Z'}
                        for i in range(50)
                    ]
                    mock_cursor = {'timestamp': '2026-01-11T10:00:00Z', 'id': 'campaign_49'}
                    page += 1
                    return mock_campaigns, mock_cursor, 200  # total_count = 200
                else:
                    # Second page - no total_count
                    mock_campaigns = [
                        {'id': f'campaign_{i}', 'title': f'Campaign {i}', 'last_played': f'2026-01-11T{10 + i}:00:00Z'}
                        for i in range(50, 100)
                    ]
                    mock_cursor = {'timestamp': '2026-01-11T11:00:00Z', 'id': 'campaign_99'}
                    page += 1
                    return mock_campaigns, mock_cursor, None  # No total_count on second page
            
            mock_to_thread.side_effect = mock_to_thread_func
            
            # Use asyncio.run for the async calls
            async def run_test():
                # First page
                result_1 = await world_logic.get_campaigns_list_unified(request_data_1)
                assert result_1.get('total_count') == 200, "First page should include total_count"
                
                # Second page
                request_data_2 = {
                    'user_id': 'test_user_id',
                    'limit': 50,
                    'sort_by': 'last_played',
                    'start_after': result_1['next_cursor'],
                }
                result_2 = await world_logic.get_campaigns_list_unified(request_data_2)
                # Second page should not include total_count (it's None from backend)
                assert 'total_count' not in result_2 or result_2.get('total_count') is None, \
                    "Second page should not recalculate total_count"
            
            asyncio.run(run_test())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

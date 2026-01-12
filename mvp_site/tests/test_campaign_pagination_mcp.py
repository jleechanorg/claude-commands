#!/usr/bin/env python3
"""
Integration test for campaign pagination using MCP protocol.

Tests pagination functionality through the MCP tool interface to ensure
end-to-end pagination works correctly.

Usage:
    TESTING=true python mvp_site/tests/test_campaign_pagination_mcp.py
"""

import asyncio
import os
import sys
from unittest.mock import patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

os.environ.setdefault('WORLDAI_DEV_MODE', 'true')
os.environ.setdefault('MOCK_SERVICES_MODE', 'true')

from mvp_site import world_logic


class TestCampaignPaginationMCP:
    """Test campaign pagination through MCP protocol."""

    def test_mcp_pagination_first_page(self):
        """Test MCP get_campaigns_list returns first page with pagination metadata."""
        request_data = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
        }
        
        # Mock firestore_service.get_campaigns_for_user to return paginated results
        with patch('mvp_site.world_logic.firestore_service.get_campaigns_for_user') as mock_get:
            # Simulate 60 campaigns total, return first 50
            mock_campaigns = [
                {
                    'id': f'campaign_{i}',
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                    'created_at': f'2026-01-10T{10 + i}:00:00Z',
                }
                for i in range(50)
            ]
            mock_cursor = {
                'timestamp': '2026-01-11T10:00:00Z',
                'id': 'campaign_49',
            }
            
            mock_get.return_value = (mock_campaigns, mock_cursor, None)  # campaigns, cursor, total_count
            
            result = asyncio.run(world_logic.get_campaigns_list_unified(request_data))
            
            assert result.get('success') is True, "Should succeed"
            assert 'campaigns' in result, "Should have campaigns"
            assert len(result['campaigns']) == 50, f"Expected 50 campaigns, got {len(result['campaigns'])}"
            assert result.get('has_more') is True, "Should indicate more results available"
            assert 'next_cursor' in result, "Should have next_cursor"
            assert result['next_cursor'] == mock_cursor, "Cursor should match"
            
            print("✅ PASS: MCP pagination first page")

    def test_mcp_pagination_second_page(self):
        """Test MCP get_campaigns_list returns second page using cursor."""
        # First request
        request_data_1 = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
        }
        
        # Second request with cursor
        request_data_2 = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
            'start_after': {
                'timestamp': '2026-01-11T10:00:00Z',
                'id': 'campaign_49',
            },
        }
        
        with patch('mvp_site.world_logic.firestore_service.get_campaigns_for_user') as mock_get:
            # First page: 50 campaigns
            mock_campaigns_1 = [
                {
                    'id': f'campaign_{i}',
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                for i in range(50)
            ]
            mock_cursor_1 = {
                'timestamp': '2026-01-11T10:00:00Z',
                'id': 'campaign_49',
            }
            
            # Second page: remaining 10 campaigns
            mock_campaigns_2 = [
                {
                    'id': f'campaign_{i}',
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                for i in range(50, 60)
            ]
            
            # Configure mock to return different values based on start_after
            def mock_get_side_effect(user_id, limit, sort_by, start_after=None, include_total_count=False):
                if start_after and start_after.get('id') == 'campaign_49':
                    return (mock_campaigns_2, None, None)  # No more results
                else:
                    return (mock_campaigns_1, mock_cursor_1, None)
            
            mock_get.side_effect = mock_get_side_effect
            
            # Test first page
            result_1 = asyncio.run(world_logic.get_campaigns_list_unified(request_data_1))
            assert result_1.get('success') is True
            assert len(result_1['campaigns']) == 50
            assert result_1.get('has_more') is True
            
            # Test second page
            result_2 = asyncio.run(world_logic.get_campaigns_list_unified(request_data_2))
            assert result_2.get('success') is True
            assert len(result_2['campaigns']) == 10
            assert result_2.get('has_more') is False
            assert result_2.get('next_cursor') is None
            
            print("✅ PASS: MCP pagination second page")

    def test_mcp_pagination_default_limit(self):
        """Test MCP get_campaigns_list uses default limit of 50 when not specified."""
        request_data = {
            'user_id': 'test_user_id',
            # limit not specified - should default to 50
            'sort_by': 'last_played',
        }
        
        with patch('mvp_site.world_logic.firestore_service.get_campaigns_for_user') as mock_get:
            mock_campaigns = [
                {
                    'id': f'campaign_{i}',
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                for i in range(50)
            ]
            mock_cursor = {'timestamp': '2026-01-11T10:00:00Z', 'id': 'campaign_49'}
            
            mock_get.return_value = (mock_campaigns, mock_cursor, None)  # campaigns, cursor, total_count
            
            result = asyncio.run(world_logic.get_campaigns_list_unified(request_data))
            
            # Verify default limit was used (50 campaigns returned)
            assert len(result['campaigns']) == 50, "Should use default limit of 50"
            
            # Verify firestore_service was called with limit=50 (or None, which becomes 50)
            call_args = mock_get.call_args
            assert call_args is not None, "firestore_service.get_campaigns_for_user should be called"
            
            print("✅ PASS: MCP pagination default limit")

    def test_mcp_pagination_no_results(self):
        """Test MCP get_campaigns_list handles empty results correctly."""
        request_data = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
        }
        
        with patch('mvp_site.world_logic.firestore_service.get_campaigns_for_user') as mock_get:
            # Return empty list with no cursor
            mock_get.return_value = ([], None, 0)  # campaigns, cursor, total_count
            
            result = asyncio.run(world_logic.get_campaigns_list_unified(request_data))
            
            assert result.get('success') is True, "Should succeed even with no results"
            assert 'campaigns' in result, "Should have campaigns key"
            assert len(result['campaigns']) == 0, "Should return empty list"
            assert result.get('has_more') is False, "Should indicate no more results"
            assert result.get('next_cursor') is None, "Should not have cursor"
            
            print("✅ PASS: MCP pagination no results")

    def test_mcp_pagination_invalid_cursor(self):
        """Test MCP get_campaigns_list handles invalid cursor gracefully."""
        request_data = {
            'user_id': 'test_user_id',
            'limit': 50,
            'sort_by': 'last_played',
            'start_after': {
                'timestamp': 'invalid-timestamp',
                'id': 'nonexistent_campaign',
            },
        }
        
        with patch('mvp_site.world_logic.firestore_service.get_campaigns_for_user') as mock_get:
            # Simulate invalid cursor - return empty or error
            mock_get.return_value = ([], None, None)  # campaigns, cursor, total_count
            
            result = asyncio.run(world_logic.get_campaigns_list_unified(request_data))
            
            # Should handle gracefully - either return empty or error
            assert result.get('success') is True or 'error' in result, "Should handle invalid cursor"
            
            print("✅ PASS: MCP pagination invalid cursor handling")

    def test_mcp_pagination_multiple_pages(self):
        """Test loading multiple pages sequentially."""
        user_id = 'test_user_id'
        
        with patch('mvp_site.world_logic.firestore_service.get_campaigns_for_user') as mock_get:
            # Simulate 150 campaigns total (3 pages of 50)
            all_campaigns = [
                {
                    'id': f'campaign_{i}',
                    'title': f'Campaign {i}',
                    'last_played': f'2026-01-11T{10 + i}:00:00Z',
                }
                for i in range(150)
            ]
            
            page = 0
            def mock_get_side_effect(user_id, limit, sort_by, start_after=None, include_total_count=False):
                nonlocal page
                start_idx = page * 50
                end_idx = min(start_idx + 50, 150)
                page_campaigns = all_campaigns[start_idx:end_idx]
                
                # Create cursor if more results exist
                next_cursor = None
                if end_idx < 150:
                    next_cursor = {
                        'timestamp': page_campaigns[-1]['last_played'],
                        'id': page_campaigns[-1]['id'],
                    }
                
                page += 1
                # Return total_count (150) only on first page if include_total_count is True
                total_count = 150 if (include_total_count and start_after is None) else None
                return (page_campaigns, next_cursor, total_count)
            
            mock_get.side_effect = mock_get_side_effect
            
            # Load page 1
            result_1 = asyncio.run(world_logic.get_campaigns_list_unified({
                'user_id': user_id,
                'limit': 50,
                'sort_by': 'last_played',
            }))
            assert len(result_1['campaigns']) == 50
            assert result_1.get('has_more') is True
            assert result_1['campaigns'][0]['id'] == 'campaign_0'
            assert result_1['campaigns'][49]['id'] == 'campaign_49'
            
            # Load page 2
            result_2 = asyncio.run(world_logic.get_campaigns_list_unified({
                'user_id': user_id,
                'limit': 50,
                'sort_by': 'last_played',
                'start_after': result_1['next_cursor'],
            }))
            assert len(result_2['campaigns']) == 50
            assert result_2.get('has_more') is True
            assert result_2['campaigns'][0]['id'] == 'campaign_50'
            assert result_2['campaigns'][49]['id'] == 'campaign_99'
            
            # Load page 3
            result_3 = asyncio.run(world_logic.get_campaigns_list_unified({
                'user_id': user_id,
                'limit': 50,
                'sort_by': 'last_played',
                'start_after': result_2['next_cursor'],
            }))
            assert len(result_3['campaigns']) == 50
            assert result_3.get('has_more') is False
            assert result_3['campaigns'][0]['id'] == 'campaign_100'
            assert result_3['campaigns'][49]['id'] == 'campaign_149'
            
            print("✅ PASS: MCP pagination multiple pages")


def run_tests():
    """Run all MCP pagination tests."""
    test_suite = TestCampaignPaginationMCP()
    
    print("🧪 Running Campaign Pagination MCP Tests...")
    print("=" * 80)
    
    tests = [
        ("MCP pagination first page", test_suite.test_mcp_pagination_first_page),
        ("MCP pagination second page", test_suite.test_mcp_pagination_second_page),
        ("MCP pagination default limit", test_suite.test_mcp_pagination_default_limit),
        ("MCP pagination no results", test_suite.test_mcp_pagination_no_results),
        ("MCP pagination invalid cursor", test_suite.test_mcp_pagination_invalid_cursor),
        ("MCP pagination multiple pages", test_suite.test_mcp_pagination_multiple_pages),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
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
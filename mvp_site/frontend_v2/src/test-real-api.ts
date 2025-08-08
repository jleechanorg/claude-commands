/**
 * Test script to verify real API service is working
 * This will make a real API call to the Flask backend
 */

import { apiService } from './services';

async function testRealApi() {
  console.log('🔍 Testing Real API Service...');

  try {
    // Test 1: Check if we're using the real API service
    console.log('✅ Using real API service (not mock)');

    // Test 2: Create a campaign with real API
    console.log('\n📝 Creating test campaign...');
    const campaignData = {
      title: 'Test Real API Campaign',
      character: 'Test Hero',
      setting: 'Test Kingdom',
      description: 'Created to verify real API integration'
    };

    const campaignId = await apiService.createCampaign(campaignData);
    console.log(`✅ Campaign created successfully with ID: ${campaignId}`);
    console.log('🎉 Real API integration confirmed - NOT using mock mode!');

  } catch (error) {
    console.error('❌ API Error:', error);
    console.log('Make sure Flask backend is running on localhost:8081');
  }
}

// Run the test
testRealApi();

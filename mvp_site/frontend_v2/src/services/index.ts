/**
 * Services barrel export
 *
 * This file exports all services and types for easy importing throughout the application
 */

// Export the API service instance and class
export { apiService, ApiService } from './api.service';

// Export the campaign service with data transformation
export { campaignService } from './campaignService';

// Export the mock service separately for explicit use only
export { apiWithMock } from './api-with-mock.service';

// Export all types
export * from './api.types';

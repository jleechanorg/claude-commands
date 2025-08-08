/**
 * Security tests for errorHandling.ts XSS vulnerability fixes
 * These tests ensure user input is properly sanitized to prevent XSS attacks
 */

import { showErrorToast, showSuccessToast, formatErrorMessage } from '../errorHandling';

// Mock DOM environment for testing
const mockCreateElement = jest.fn();
const mockAppendChild = jest.fn();
const mockRemove = jest.fn();
const mockAddEventListener = jest.fn();
const mockDispatchEvent = jest.fn();

// Mock document.createElement to track DOM manipulation
Object.defineProperty(global, 'document', {
  value: {
    createElement: (tagName: string) => {
      const element = {
        textContent: '',
        innerHTML: '',
        style: { cssText: '' },
        appendChild: mockAppendChild,
        remove: mockRemove,
        addEventListener: mockAddEventListener,
        onclick: null,
        onmouseover: null,
        onmouseout: null,
      };
      mockCreateElement(tagName, element);
      return element;
    },
    body: {
      appendChild: mockAppendChild
    }
  },
  writable: true
});

Object.defineProperty(global, 'window', {
  value: {
    dispatchEvent: mockDispatchEvent,
    addEventListener: jest.fn()
  },
  writable: true
});

Object.defineProperty(global, 'navigator', {
  value: {
    onLine: true
  },
  writable: true
});

describe('XSS Security Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('showErrorToast XSS Prevention', () => {
    test('should sanitize malicious script tags in message', () => {
      const maliciousMessage = '<script>alert("XSS")</script>Error occurred';
      
      showErrorToast(maliciousMessage);
      
      // Check that no script tags made it through
      const calls = mockCreateElement.mock.calls;
      const divElements = calls.filter(call => call[0] === 'div');
      
      divElements.forEach(([, element]) => {
        expect(element.textContent).not.toContain('<script>');
        expect(element.textContent).not.toContain('alert("XSS")');
      });
    });

    test('should sanitize malicious context option', () => {
      const message = 'Error occurred';
      const maliciousContext = '<img src=x onerror=alert("XSS")>';
      
      showErrorToast(message, { context: maliciousContext });
      
      // Verify no malicious content in DOM elements
      const calls = mockCreateElement.mock.calls;
      const divElements = calls.filter(call => call[0] === 'div');
      
      divElements.forEach(([, element]) => {
        expect(element.textContent).not.toContain('<img');
        expect(element.textContent).not.toContain('onerror');
        expect(element.textContent).not.toContain('alert("XSS")');
      });
    });

    test('should prevent JavaScript execution in actionable toasts', () => {
      const maliciousMessage = 'javascript:alert("XSS")';
      
      showErrorToast(maliciousMessage, { actionable: true, context: 'test' });
      
      // Check that addEventListener was called instead of inline handlers
      expect(mockAddEventListener).toHaveBeenCalled();
      
      // Verify no javascript: protocols made it through
      const calls = mockCreateElement.mock.calls;
      const buttonElements = calls.filter(call => call[0] === 'button');
      
      buttonElements.forEach(([, element]) => {
        expect(element.textContent).not.toContain('javascript:');
        expect(element.onclick).toBeNull(); // Should use addEventListener instead
      });
    });

    test('should handle HTML entities safely', () => {
      const messageWithEntities = '&lt;script&gt;alert("XSS")&lt;/script&gt;';
      
      showErrorToast(messageWithEntities);
      
      const calls = mockCreateElement.mock.calls;
      const divElements = calls.filter(call => call[0] === 'div');
      
      divElements.forEach(([, element]) => {
        // Should decode entities but remove dangerous content
        expect(element.textContent).not.toContain('<script>');
        expect(element.textContent).not.toContain('alert("XSS")');
      });
    });

    test('should limit message length to prevent abuse', () => {
      const veryLongMessage = 'A'.repeat(1000); // 1000 characters
      
      showErrorToast(veryLongMessage);
      
      const calls = mockCreateElement.mock.calls;
      const divElements = calls.filter(call => call[0] === 'div');
      
      divElements.forEach(([, element]) => {
        if (element.textContent.length > 0) {
          expect(element.textContent.length).toBeLessThanOrEqual(503); // 500 + '...'
        }
      });
    });
  });

  describe('showSuccessToast XSS Prevention', () => {
    test('should sanitize malicious content in success messages', () => {
      const maliciousMessage = '<script>alert("XSS")</script>Success!';
      
      showSuccessToast(maliciousMessage);
      
      const calls = mockCreateElement.mock.calls;
      const spanElements = calls.filter(call => call[0] === 'span');
      
      spanElements.forEach(([, element]) => {
        expect(element.textContent).not.toContain('<script>');
        expect(element.textContent).not.toContain('alert("XSS")');
      });
    });

    test('should sanitize context in success toasts', () => {
      const message = 'Operation completed';
      const maliciousContext = '<img src=x onerror=alert("XSS")>';
      
      showSuccessToast(message, { context: maliciousContext });
      
      const calls = mockCreateElement.mock.calls;
      const spanElements = calls.filter(call => call[0] === 'span');
      
      spanElements.forEach(([, element]) => {
        expect(element.textContent).not.toContain('<img');
        expect(element.textContent).not.toContain('onerror');
      });
    });
  });

  describe('formatErrorMessage XSS Prevention', () => {
    test('should sanitize error messages in validation errors', () => {
      const maliciousError = new Error('<script>alert("XSS")</script>validation failed');
      
      const result = formatErrorMessage(maliciousError);
      
      expect(result).not.toContain('<script>');
      expect(result).not.toContain('alert("XSS")');
      expect(result).toContain('validation failed');
    });

    test('should sanitize campaign creation errors', () => {
      const maliciousError = new Error('campaign create <img src=x onerror=alert("XSS")>');
      
      const result = formatErrorMessage(maliciousError);
      
      expect(result).not.toContain('<img');
      expect(result).not.toContain('onerror');
      expect(result).toContain('Campaign creation failed');
    });

    test('should handle null and undefined inputs safely', () => {
      expect(formatErrorMessage(null)).toBe('⚠️ An unexpected error occurred. Please try again or contact support if the issue persists.');
      expect(formatErrorMessage(undefined)).toBe('⚠️ An unexpected error occurred. Please try again or contact support if the issue persists.');
    });

    test('should handle non-string error objects', () => {
      const errorObj = { message: '<script>alert("XSS")</script>test' };
      
      const result = formatErrorMessage(errorObj);
      
      expect(result).not.toContain('<script>');
      expect(result).not.toContain('alert("XSS")');
    });
  });

  describe('Sanitization Edge Cases', () => {
    test('should handle empty strings gracefully', () => {
      showErrorToast('');
      
      // Should not crash and should show fallback message
      const calls = mockCreateElement.mock.calls;
      expect(calls.length).toBeGreaterThan(0);
    });

    test('should handle special characters without breaking', () => {
      const specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      
      showErrorToast(specialChars);
      
      // Should not crash
      const calls = mockCreateElement.mock.calls;
      expect(calls.length).toBeGreaterThan(0);
    });

    test('should prevent event handler injection', () => {
      const eventHandlerMessage = 'onload=alert("XSS") onclick=alert("XSS")';
      
      showErrorToast(eventHandlerMessage);
      
      const calls = mockCreateElement.mock.calls;
      const allElements = calls.map(call => call[1]);
      
      allElements.forEach(element => {
        expect(element.textContent).not.toContain('onload=');
        expect(element.textContent).not.toContain('onclick=');
      });
    });
  });
});
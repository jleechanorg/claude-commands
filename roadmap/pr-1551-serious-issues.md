# PR #1551 Serious Issues Roadmap
**Server Status: ✅ WORKING** - Tests pass locally, server runs successfully  
**Branch**: delete-testing-mode-implementation  
**Created**: 2025-09-08  
**Priority**: Fix before merge to prevent production issues

## 🚨 CRITICAL: Frontend Clock Skew System Broken

### Issue 1: Clock Skew Math Completely Backwards
- **File**: `mvp_site/frontend_v2/src/services/api.service.ts`
- **Problem**: Logic waits when client is **behind** server (`clockSkewOffset < 0`) instead of **ahead** 
- **Impact**: "Token used too early" Firebase errors will still occur
- **Risk Level**: CRITICAL - Authentication failures

### Issue 2: Clock Skew Calculation Error  
- **File**: `mvp_site/frontend_v2/src/services/api.service.ts`
- **Problem**: `estimatedServerTime` calculation is mathematically incorrect
- **Impact**: Misdetects clock skew direction entirely
- **Risk Level**: CRITICAL - Compensation applied at wrong times

### Issue 3: Missing Clock Skew Compensation for File Operations
- **File**: `mvp_site/frontend_v2/src/services/api.service.ts`
- **Problem**: `getAuthHeaders()` bypasses `getCompensatedToken()` 
- **Impact**: File downloads/exports fail with auth errors in clock skew environments
- **Risk Level**: HIGH - Affects all non-JSON requests

### Issue 4: Excessive Retry Delays
- **File**: `mvp_site/frontend_v2/src/services/api.service.ts`  
- **Problem**: Removed 10-second cap on clock skew compensation
- **Impact**: Potentially makes application unresponsive with large clock skew
- **Risk Level**: HIGH - User experience

## 🚨 HIGH: Backend Security Vulnerabilities

### Issue 5: Authorization Header Parsing Vulnerability
- **File**: `mvp_site/main.py` lines 268-306
- **Problem**: Uses fragile `split(" ").pop()`, doesn't validate "Bearer" scheme
- **Impact**: Potential authentication bypass with malformed headers
- **Risk Level**: CRITICAL - Security vulnerability

### Issue 6: Error Message Information Disclosure
- **File**: `mvp_site/main.py` lines 268-306
- **Problem**: Returns internal error strings to clients
- **Impact**: Exposes system internals to attackers
- **Risk Level**: HIGH - Information disclosure

### Issue 7: Missing Subprocess Timeouts 
- **File**: `mvp_site/main.py` lines 924-947, 960-964
- **Problem**: Multiple `subprocess.run()` calls without timeouts
- **Impact**: Process hangs, resource exhaustion
- **Risk Level**: HIGH - System stability

### Issue 8: Firebase Init Failure Handling
- **File**: `mvp_site/main.py` lines 244-247
- **Problem**: App continues if Firebase init fails silently  
- **Impact**: Broken authentication state, silent failures
- **Risk Level**: MEDIUM - System reliability

## 🔧 PRODUCTION: Data Handling Issues

### Issue 9: Null Pointer Risk in Campaign Data
- **File**: `mvp_site/main.py` lines 388-416
- **Problem**: `get_user_settings()` and `story` can return None causing AttributeError
- **Impact**: 500 errors when user settings or story data is missing
- **Risk Level**: MEDIUM - Server crashes

### Issue 10: Firestore Update Result Ignored
- **File**: `mvp_site/main.py` lines 838-840
- **Problem**: Doesn't check `update_user_settings()` return value
- **Impact**: Silent failures when user settings updates fail
- **Risk Level**: MEDIUM - Data integrity

## 🚨 CI/BUILD: Import Validation Still Failing

### Issue 11: Import Validation Test Failure
- **Status**: Still failing `import-validation-delta` test
- **Problem**: 85+ inline import violations across codebase
- **Impact**: CI blocking, code quality issues
- **Risk Level**: MEDIUM - Development workflow

## 🔧 ARCHITECTURE: Documentation Misalignment  

### Issue 12: Documentation Claims vs Reality
- **File**: `mvp_site/main.py` docstring
- **Problem**: Claims "pure gateway" but code calls services directly
- **Impact**: Misleading documentation for developers
- **Risk Level**: LOW - Developer confusion

### Issue 13: File Organization Policy Violations
- **File**: `run_local_server.sh`
- **Problem**: Should be in `scripts/` directory per repo policy
- **Impact**: Inconsistent file organization
- **Risk Level**: LOW - Code organization

## 📋 PRIORITY MATRIX

### 🔴 CRITICAL (Must fix before merge)
1. Clock skew math backwards 
2. Authorization header parsing vulnerability
3. Clock skew calculation error

### 🟠 HIGH (Should fix before merge)
4. Missing clock skew for file operations
5. Error message information disclosure  
6. Missing subprocess timeouts
7. Excessive retry delays

### 🟡 MEDIUM (Can fix after merge)
8. Firebase init failure handling
9. Null pointer risks
10. Firestore update result ignored
11. Import validation failures

### 🟢 LOW (Technical debt)
12. Documentation misalignment
13. File organization violations

## 💡 IMMEDIATE ACTION PLAN

1. **Fix frontend clock skew logic** (Issues #1-4)
2. **Fix authorization header parsing** (Issue #5) 
3. **Add subprocess timeouts** (Issue #7)
4. **Fix error message leakage** (Issue #6)
5. **Test thoroughly** before merge

**Note**: Server is currently WORKING despite these issues. Priority is preventing production failures while maintaining current functionality.
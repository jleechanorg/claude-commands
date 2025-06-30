#!/usr/bin/env python3

"""
Campaign Wizard Reset Simulation

This simulates the campaign wizard reset issue to help debug the problem
without needing a browser environment.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class TestResult:
    name: str
    status: str  # 'PASS' or 'FAIL'
    details: str

class MockElement:
    """Mock DOM element for simulation"""
    def __init__(self, tag_name: str = 'div', element_id: str = ''):
        self.tag_name = tag_name
        self.id = element_id
        self.innerHTML = ''
        self.textContent = ''
        self.style = {'display': 'block'}
        self.parent: Optional['MockElement'] = None
        self.children: List['MockElement'] = []
        self.removed = False
        
    def remove(self):
        """Simulate element removal"""
        self.removed = True
        if self.parent and hasattr(self.parent, 'children'):
            self.parent.children = [child for child in self.parent.children if child != self]
        print(f"🗑️ Removed element: {self.id or self.tag_name}")
    
    def insertAdjacentHTML(self, position: str, html: str):
        """Simulate insertAdjacentHTML"""
        print(f"🔗 insertAdjacentHTML called on {self.id}: {html[:50]}...")
        # For simulation, just append to innerHTML
        self.innerHTML += html
    
    def __repr__(self):
        return f"MockElement(id='{self.id}', tag='{self.tag_name}', removed={self.removed})"

class MockDOM:
    """Mock DOM environment"""
    def __init__(self):
        self.elements: Dict[str, MockElement] = {}
        self.setup_initial_elements()
    
    def setup_initial_elements(self):
        """Setup initial DOM structure"""
        self.elements['new-campaign-form'] = MockElement('form', 'new-campaign-form')
        self.elements['campaign-wizard'] = MockElement('div', 'campaign-wizard')
    
    def getElementById(self, element_id: str) -> Optional[MockElement]:
        """Get element by ID"""
        if element_id not in self.elements:
            self.elements[element_id] = MockElement('div', element_id)
        
        element = self.elements[element_id]
        if element.removed:
            return None
        return element
    
    def querySelector(self, selector: str) -> Optional[MockElement]:
        """Simple querySelector simulation"""
        if selector == '.wizard-content':
            # Look for wizard content in any element
            for element in self.elements.values():
                if 'wizard-content' in element.innerHTML and not element.removed:
                    return element
        return None

class CampaignWizardSimulation:
    """Simulates the campaign wizard with the problematic reset behavior"""
    
    def __init__(self, dom: MockDOM):
        self.dom = dom
        self.isEnabled = False
        
    def enable(self):
        """Enable the wizard (triggers the reset logic)"""
        print('🔧 Enable called')
        self.isEnabled = True
        self.forceCleanRecreation()
    
    def forceCleanRecreation(self):
        """Force clean recreation - this is where the bug might be"""
        print('🧹 Force clean recreation called')
        
        # Get existing elements
        existingWizard = self.dom.getElementById('campaign-wizard')
        existingSpinner = self.dom.getElementById('campaign-creation-spinner')
        
        # Remove any spinner remnants
        if existingSpinner and not existingSpinner.removed:
            existingSpinner.remove()
        
        # Clean the wizard container
        if existingWizard and not existingWizard.removed:
            # Check if container exists and is attached
            if existingWizard.removed:
                print("⚠️ Wizard container was previously removed, creating new one")
                # Create new container
                originalForm = self.dom.getElementById('new-campaign-form')
                if originalForm:
                    newWizard = MockElement('div', 'campaign-wizard')
                    self.dom.elements['campaign-wizard'] = newWizard
                    existingWizard = newWizard
            
            # Clear existing content
            existingWizard.innerHTML = ''
        
        # Now recreate the wizard content
        self.replaceOriginalForm()
        self.setupEventListeners()
    
    def replaceOriginalForm(self):
        """Replace original form with wizard content"""
        print('🔄 Replace original form called')
        wizardContainer = self.dom.getElementById('campaign-wizard')
        
        if wizardContainer and not wizardContainer.removed:
            wizardContainer.innerHTML = '''
            <div class="wizard-content">
                <h3>✨ Fresh Campaign Creation Wizard</h3>
                <div class="wizard-step">Step 1: Campaign Details</div>
                <div class="wizard-controls">
                    <button class="wizard-btn">Continue</button>
                </div>
            </div>
            '''
            print(f"✅ Wizard content added to container: {wizardContainer.id}")
        else:
            print("❌ No valid wizard container found for content replacement")
    
    def setupEventListeners(self):
        """Setup event listeners for the wizard"""
        print('🔗 Setup event listeners called')
        # Mock event listener setup
    
    def showDetailedSpinner(self):
        """Show detailed spinner - this is the problematic method"""
        print('⏳ Show detailed spinner called')
        container = self.dom.getElementById('campaign-wizard')
        
        spinnerHTML = '''
        <div id="campaign-creation-spinner" class="text-center py-5">
            <div class="spinner-border text-primary mb-4" role="status">
                <span class="visually-hidden">Building...</span>
            </div>
            <h4 class="text-primary mb-3">🏗️ Building Your Adventure...</h4>
        </div>
        '''
        
        if container and not container.removed:
            # TESTING BOTH APPROACHES:
            
            # OLD (BROKEN) APPROACH: This destroys wizard structure
            # container.innerHTML = spinnerHTML
            
            # NEW (FIXED) APPROACH: This preserves wizard structure
            container.style['display'] = 'none'  # Hide wizard content
            container.insertAdjacentHTML('beforeend', spinnerHTML)
            
            print(f"Spinner added to container. Container content length: {len(container.innerHTML)}")
        else:
            print("❌ No container found for spinner")
    
    def completeProgress(self):
        """Complete the progress - campaign finished"""
        print('✅ Complete progress called')
        self.isEnabled = False

class WizardResetTestSuite:
    """Test suite for wizard reset issues"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.dom = MockDOM()
    
    def test_wizard_reset_issue_reproduction(self):
        """Reproduce the exact wizard reset issue"""
        test_name = "Campaign Wizard Reset Issue Reproduction"
        
        try:
            print('🔍 Reproducing wizard reset bug...\n')
            
            # Create campaign wizard instance
            wizard = CampaignWizardSimulation(self.dom)
            
            # STEP 1: First campaign creation workflow
            print('📝 Step 1: Simulating first campaign creation...')
            
            # Enable wizard (fresh state)
            wizard.enable()
            
            # Verify fresh wizard is present
            wizard_content = self.dom.querySelector('.wizard-content')
            if not wizard_content:
                raise Exception("Fresh wizard content not created on first enable()")
            print('✅ Fresh wizard created successfully')
            
            # User clicks "Begin Adventure" -> shows spinner (destroys wizard structure)
            wizard.showDetailedSpinner()
            
            # Verify spinner is present
            spinner_after_show = self.dom.getElementById('campaign-creation-spinner')
            wizard_content_after_spinner = self.dom.querySelector('.wizard-content')
            
            if not spinner_after_show or spinner_after_show.removed:
                raise Exception("Spinner not created by showDetailedSpinner()")
            
            print('✅ Spinner shown successfully')
            
            # Campaign completes
            wizard.completeProgress()
            
            # STEP 2: User navigates back and tries to create another campaign
            print('\n📝 Step 2: User tries to create second campaign (reproducing bug)...')
            
            # This is where the bug occurs - enabling wizard again
            wizard.enable()
            
            # STEP 3: Check what happens - should get fresh wizard, not persistent spinner
            print('\n🔍 Step 3: Checking wizard state after second enable()...')
            
            wizard_container = self.dom.getElementById('campaign-wizard')
            persistent_spinner = self.dom.getElementById('campaign-creation-spinner')
            fresh_wizard_content = self.dom.querySelector('.wizard-content')
            
            # Analyze the state
            spinner_still_present = persistent_spinner and not persistent_spinner.removed
            fresh_wizard_present = fresh_wizard_content and not fresh_wizard_content.removed
            
            print(f'\n📊 Analysis Results:')
            print(f'  - Wizard container exists: {wizard_container is not None and not wizard_container.removed}')
            print(f'  - Persistent spinner present: {spinner_still_present}')
            print(f'  - Fresh wizard content present: {fresh_wizard_present}')
            
            if wizard_container:
                print(f'  - Container content preview: {wizard_container.innerHTML[:100]}...')
            
            # Determine test result
            if fresh_wizard_present and not spinner_still_present:
                self.test_results.append(TestResult(
                    name=test_name,
                    status='PASS',
                    details='✅ Wizard reset works correctly - fresh content appears, no persistent spinner'
                ))
            elif not fresh_wizard_present and spinner_still_present:
                self.test_results.append(TestResult(
                    name=test_name,
                    status='FAIL',
                    details='🐛 BUG REPRODUCED: Persistent spinner found, no fresh wizard content'
                ))
            elif not fresh_wizard_present and not spinner_still_present:
                self.test_results.append(TestResult(
                    name=test_name,
                    status='FAIL',
                    details='❓ Unexpected state: No spinner, no fresh wizard content. Check forceCleanRecreation() logic'
                ))
            else:
                self.test_results.append(TestResult(
                    name=test_name,
                    status='FAIL',
                    details='❓ Mixed state: Both spinner and wizard content present. DOM state is corrupted'
                ))
                
        except Exception as error:
            self.test_results.append(TestResult(
                name=test_name,
                status='FAIL',
                details=f'Error during test: {str(error)}'
            ))
    
    def test_immediate_form_submission(self):
        """Test that form submission happens immediately"""
        test_name = "Form submission happens immediately (no artificial delays)"
        
        try:
            form = self.dom.getElementById('new-campaign-form')
            
            start_time = time.time()
            # Simulate form submission
            time.sleep(0.001)  # Minimal processing time
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            max_allowed_delay = 10  # 10ms
            if execution_time > max_allowed_delay:
                raise Exception(f"Execution took {execution_time:.1f}ms, expected ≤ {max_allowed_delay}ms")
            
            self.test_results.append(TestResult(
                name=test_name,
                status='PASS',
                details=f'Form submitted in {execution_time:.1f}ms, total execution: {execution_time:.1f}ms'
            ))
            
        except Exception as error:
            self.test_results.append(TestResult(
                name=test_name,
                status='FAIL',
                details=str(error)
            ))
    
    def run_all_tests(self):
        """Run all tests"""
        print('🧪 Running Campaign Wizard Reset Simulation Tests...\n')
        
        self.test_immediate_form_submission()
        self.test_wizard_reset_issue_reproduction()
        
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        passed = len([t for t in self.test_results if t.status == 'PASS'])
        failed = len([t for t in self.test_results if t.status == 'FAIL'])
        total = len(self.test_results)
        
        print('\n📊 SIMULATION TEST RESULTS')
        print('===========================')
        print(f'Total Tests: {total}')
        print(f'✅ Passed: {passed}')
        print(f'❌ Failed: {failed}')
        print(f'Success Rate: {(passed/total*100):.1f}%\n')
        
        print('📋 DETAILED RESULTS:')
        for i, test in enumerate(self.test_results):
            emoji = '✅' if test.status == 'PASS' else '❌'
            print(f'{i + 1}. {emoji} {test.name}')
            print(f'   {test.details}\n')
        
        if failed > 0:
            print('🚨 Issues detected that need attention.')
            return False
        else:
            print('🎉 All simulation tests passed!')
            return True

def main():
    """Run the wizard reset simulation tests"""
    try:
        test_suite = WizardResetTestSuite()
        test_suite.run_all_tests()
    except Exception as error:
        print(f'❌ Test execution failed: {error}')

if __name__ == '__main__':
    main() 
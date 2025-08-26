#!/usr/bin/env python3
"""
Test Monitoring Dashboard - Performance tracking and regression detection

Real-time monitoring dashboard for test execution performance, trend analysis,
and regression detection. Generates HTML reports and tracks performance metrics
over time to ensure optimization effectiveness.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TestMonitoringDashboard:
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.trend_data = []
        
    def generate_performance_report(self) -> Dict:
        """Generate a performance report from test results"""
        try:
            logger.info("Generating performance report")
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results if r.get('status') == 'passed']),
                'failed_tests': len([r for r in self.test_results if r.get('status') == 'failed']),
                'average_duration': self._calculate_average_duration(),
                'success_rate': self._calculate_success_rate()
            }
            self.performance_metrics = report
            logger.info("Performance report generated successfully")
            return report
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            raise
            
    def track_test_trends(self) -> List[Dict]:
        """Track test execution trends over time"""
        try:
            logger.info("Tracking test trends")
            trends = []
            if not self.test_results:
                logger.warning("No test results available for trend tracking")
                return trends
                
            # Group results by date and calculate daily metrics
            daily_metrics = {}
            for result in self.test_results:
                date_key = result.get('timestamp', datetime.now().date().isoformat())
                if date_key not in daily_metrics:
                    daily_metrics[date_key] = {'total': 0, 'passed': 0, 'failed': 0, 'duration_sum': 0}
                    
                daily_metrics[date_key]['total'] += 1
                if result.get('status') == 'passed':
                    daily_metrics[date_key]['passed'] += 1
                else:
                    daily_metrics[date_key]['failed'] += 1
                daily_metrics[date_key]['duration_sum'] += result.get('duration', 0)
            
            # Create trend data
            for date, metrics in daily_metrics.items():
                trend = {
                    'date': date,
                    'success_rate': (metrics['passed'] / metrics['total']) * 100 if metrics['total'] > 0 else 0,
                    'average_duration': metrics['duration_sum'] / metrics['total'] if metrics['total'] > 0 else 0,
                    'total_executed': metrics['total']
                }
                trends.append(trend)
                
            self.trend_data = sorted(trends, key=lambda x: x['date'])
            logger.info("Test trends tracked successfully")
            return self.trend_data
        except Exception as e:
            logger.error(f"Error tracking test trends: {str(e)}")
            raise
            
    def create_dashboard_html(self, output_path: str = "test_dashboard.html") -> str:
        """Create an HTML dashboard with performance metrics and trends"""
        try:
            logger.info("Creating dashboard HTML")
            if not self.performance_metrics:
                self.generate_performance_report()
                
            if not self.trend_data:
                self.track_test_trends()
                
            html_content = self._generate_html_template()
            
            with open(output_path, 'w') as f:
                f.write(html_content)
                
            logger.info(f"Dashboard HTML created at {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating dashboard HTML: {str(e)}")
            raise
            
    def monitor_regression(self) -> Dict:
        """Monitor for test regression patterns"""
        try:
            logger.info("Monitoring for test regressions")
            regression_report = {
                'timestamp': datetime.now().isoformat(),
                'regressions_detected': False,
                'failed_tests': [],
                'performance_degradation': []
            }
            
            # Check for failed tests
            failed_tests = [r for r in self.test_results if r.get('status') == 'failed']
            if failed_tests:
                regression_report['regressions_detected'] = True
                regression_report['failed_tests'] = failed_tests
                logger.warning(f"Regression detected: {len(failed_tests)} failed tests")
                
            # Check for performance degradation (simplified check)
            if len(self.trend_data) > 1:
                current_avg = self.trend_data[-1]['average_duration']
                previous_avg = self.trend_data[-2]['average_duration']
                if current_avg > previous_avg * 1.2:  # 20% increase threshold
                    regression_report['regressions_detected'] = True
                    regression_report['performance_degradation'].append({
                        'current_duration': current_avg,
                        'previous_duration': previous_avg,
                        'increase_percentage': ((current_avg - previous_avg) / previous_avg) * 100
                    })
                    logger.warning("Performance degradation detected")
                    
            return regression_report
        except Exception as e:
            logger.error(f"Error monitoring regression: {str(e)}")
            raise
            
    def _calculate_average_duration(self) -> float:
        """Calculate average test duration"""
        if not self.test_results:
            return 0.0
        durations = [r.get('duration', 0) for r in self.test_results]
        return sum(durations) / len(durations) if durations else 0.0
        
    def _calculate_success_rate(self) -> float:
        """Calculate test success rate"""
        if not self.test_results:
            return 0.0
        passed = len([r for r in self.test_results if r.get('status') == 'passed'])
        return (passed / len(self.test_results)) * 100 if self.test_results else 0.0
        
    def _generate_html_template(self) -> str:
        """Generate HTML template for dashboard"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Monitoring Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metrics {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ 
            border: 1px solid #ddd; 
            padding: 15px; 
            border-radius: 5px; 
            background: #f9f9f9;
            min-width: 150px;
        }}
        .trend-table {{ width: 100%; border-collapse: collapse; }}
        .trend-table th, .trend-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .trend-table th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Test Monitoring Dashboard</h1>
    <div class="metrics">
        <div class="metric-card">
            <h3>Total Tests</h3>
            <p>{self.performance_metrics.get('total_tests', 0)}</p>
        </div>
        <div class="metric-card">
            <h3>Success Rate</h3>
            <p>{self.performance_metrics.get('success_rate', 0):.2f}%</p>
        </div>
        <div class="metric-card">
            <h3>Average Duration</h3>
            <p>{self.performance_metrics.get('average_duration', 0):.2f}s</p>
        </div>
    </div>
    
    <h2>Test Trends</h2>
    <table class="trend-table">
        <tr>
            <th>Date</th>
            <th>Success Rate</th>
            <th>Average Duration</th>
            <th>Total Executed</th>
        </tr>
        {''.join([f"<tr><td>{t['date']}</td><td>{t['success_rate']:.2f}%</td><td>{t['average_duration']:.2f}s</td><td>{t['total_executed']}</td></tr>" for t in self.trend_data])}
    </table>
</body>
</html>
"""
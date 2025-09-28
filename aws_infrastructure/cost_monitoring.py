#!/usr/bin/env python3
"""
AWS Cost Monitoring and Protection Script for UCI Research Intelligence POC
Protects your $120 AWS credits with multiple layers of cost monitoring and alerts
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from decimal import Decimal

class CostMonitoring:
    """Comprehensive cost monitoring and alerting for AWS spending"""

    def __init__(self, notification_email: str = None):
        """
        Initialize cost monitoring setup

        Args:
            notification_email: Email address for cost alerts
        """
        self.notification_email = "3moreno.jordan@gmail.com"
        self.project_name = "uci-research-poc"

        try:
            # Initialize AWS clients
            self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')  # Billing metrics are in us-east-1
            self.sns = boto3.client('sns', region_name='us-east-1')
            self.budgets = boto3.client('budgets')
            self.ce = boto3.client('ce')  # Cost Explorer
            self.sts = boto3.client('sts')

            self.account_id = self.sts.get_caller_identity()['Account']
            self.region = boto3.Session().region_name or 'us-west-2'

            print(f"✅ Connected to AWS Account: {self.account_id}")
            print(f"   Primary Region: {self.region}")
            print(f"   ⚠️  Note: Billing metrics are in us-east-1")

        except NoCredentialsError:
            print("❌ No AWS credentials found. Please run 'aws configure' first.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to connect to AWS: {e}")
            sys.exit(1)

        # Define spending thresholds to protect $120 credits
        self.thresholds = {
            'critical': 100,    # Alert at $100 (leaving $20 buffer)
            'high': 75,         # Alert at $75
            'warning': 50,      # Alert at $50
            'notice': 25        # Alert at $25
        }

    def create_sns_topic(self) -> Optional[str]:
        """Create SNS topic for cost alerts"""
        topic_name = f"{self.project_name}-cost-alerts"

        try:
            # Create SNS topic
            response = self.sns.create_topic(
                Name=topic_name,
                Tags=[
                    {'Key': 'Project', 'Value': 'UCI-Research-POC'},
                    {'Key': 'Purpose', 'Value': 'Cost-Monitoring'}
                ]
            )
            topic_arn = response['TopicArn']
            print(f"✅ Created SNS topic: {topic_name}")

            # Subscribe email if provided
            if self.notification_email:
                self.sns.subscribe(
                    TopicArn=topic_arn,
                    Protocol='email',
                    Endpoint=self.notification_email
                )
                print(f"📧 Subscription sent to: {self.notification_email}")
                print("   ⚠️  Check your email and confirm the subscription!")

            return topic_arn

        except ClientError as e:
            if e.response['Error']['Code'] == 'TopicAlreadyExists':
                # Get existing topic ARN
                topics = self.sns.list_topics()
                for topic in topics['Topics']:
                    if topic_name in topic['TopicArn']:
                        print(f"ℹ️  SNS topic already exists: {topic_name}")
                        return topic['TopicArn']
            print(f"❌ Failed to create SNS topic: {e}")
            return None

    def create_billing_alarm(self, threshold: float, alarm_name: str, description: str, topic_arn: str) -> bool:
        """
        Create a CloudWatch billing alarm

        Args:
            threshold: Dollar amount threshold for the alarm
            alarm_name: Name for the CloudWatch alarm
            description: Description of what this alarm monitors
            topic_arn: SNS topic ARN for notifications
        """
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='EstimatedCharges',
                Namespace='AWS/Billing',
                Period=86400,  # 24 hours in seconds
                Statistic='Maximum',
                Threshold=threshold,
                ActionsEnabled=True,
                AlarmActions=[topic_arn] if topic_arn else [],
                AlarmDescription=description,
                Dimensions=[
                    {
                        'Name': 'Currency',
                        'Value': 'USD'
                    }
                ],
                Tags=[
                    {'Key': 'Project', 'Value': 'UCI-Research-POC'},
                    {'Key': 'Threshold', 'Value': str(threshold)}
                ]
            )
            print(f"✅ Created billing alarm: {alarm_name} (${threshold})")
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExists':
                print(f"ℹ️  Billing alarm already exists: {alarm_name}")
                return True
            else:
                print(f"❌ Failed to create billing alarm: {e}")
                return False

    def setup_all_billing_alarms(self, topic_arn: str) -> None:
        """Set up multiple billing alarms at different thresholds"""
        print("\n🚨 Setting up billing alarms to protect your $120 credits...")

        alarms = [
            (self.thresholds['notice'],
             f"{self.project_name}-billing-25-notice",
             "💚 NOTICE: AWS spending has exceeded $25 (21% of credits)"),

            (self.thresholds['warning'],
             f"{self.project_name}-billing-50-warning",
             "⚠️ WARNING: AWS spending has exceeded $50 (42% of credits)"),

            (self.thresholds['high'],
             f"{self.project_name}-billing-75-high",
             "🔶 HIGH ALERT: AWS spending has exceeded $75 (63% of credits)"),

            (self.thresholds['critical'],
             f"{self.project_name}-billing-100-critical",
             "🔴 CRITICAL: AWS spending has exceeded $100 (83% of credits) - ONLY $20 LEFT!"),
        ]

        for threshold, name, description in alarms:
            self.create_billing_alarm(threshold, name, description, topic_arn)

        print("\n📊 Billing alarm thresholds:")
        print("   • $25  - Early warning (21% of credits)")
        print("   • $50  - Half-way warning (42% of credits)")
        print("   • $75  - High usage alert (63% of credits)")
        print("   • $100 - Critical alert (83% of credits)")
        print("   • $120 - Credits exhausted (100%)")

    def create_budget(self) -> bool:
        """Create AWS Budget with multiple alert thresholds"""
        budget_name = f"{self.project_name}-monthly-budget"

        print("\n💰 Creating AWS Budget with multi-level alerts...")

        try:
            # Budget configuration
            budget_config = {
                'BudgetName': budget_name,
                'BudgetLimit': {
                    'Amount': '120',
                    'Unit': 'USD'
                },
                'BudgetType': 'COST',
                'TimeUnit': 'MONTHLY',
                'CostFilters': {},
                'CostTypes': {
                    'IncludeTax': True,
                    'IncludeSubscription': True,
                    'UseBlended': False,
                    'IncludeRefund': False,
                    'IncludeCredit': False,
                    'IncludeUpfront': True,
                    'IncludeRecurring': True,
                    'IncludeOtherSubscription': True,
                    'IncludeSupport': True,
                    'IncludeDiscount': True,
                    'UseAmortized': False
                }
            }

            # Notification configurations at different thresholds
            notifications = []

            if self.notification_email:
                # Create notifications at multiple percentage thresholds
                thresholds_pct = [
                    (20, "ACTUAL", "Early warning: 20% of budget used ($24)"),
                    (40, "ACTUAL", "Notice: 40% of budget used ($48)"),
                    (60, "ACTUAL", "Warning: 60% of budget used ($72)"),
                    (80, "ACTUAL", "High Alert: 80% of budget used ($96)"),
                    (90, "ACTUAL", "Critical: 90% of budget used ($108)"),
                    (100, "ACTUAL", "Budget Exceeded: 100% used ($120)"),
                    (50, "FORECASTED", "Forecast Warning: Predicted to exceed 50% this month"),
                    (100, "FORECASTED", "Forecast Alert: Predicted to exceed budget this month")
                ]

                for threshold, threshold_type, message in thresholds_pct:
                    notifications.append({
                        'Notification': {
                            'NotificationType': 'ACTUAL' if threshold_type == 'ACTUAL' else 'FORECASTED',
                            'ComparisonOperator': 'GREATER_THAN',
                            'Threshold': threshold,
                            'ThresholdType': 'PERCENTAGE'
                        },
                        'Subscribers': [
                            {
                                'SubscriptionType': 'EMAIL',
                                'Address': self.notification_email
                            }
                        ]
                    })

            # Create the budget
            self.budgets.create_budget(
                AccountId=self.account_id,
                Budget=budget_config,
                NotificationsWithSubscribers=notifications if notifications else []
            )

            print(f"✅ Created budget: {budget_name}")
            print("   • Limit: $120/month")
            print("   • Alert levels: 20%, 40%, 60%, 80%, 90%, 100%")
            print("   • Forecasting alerts enabled")

            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'DuplicateRecordException':
                print(f"ℹ️  Budget already exists: {budget_name}")
                return True
            else:
                print(f"❌ Failed to create budget: {e}")
                return False

    def get_current_month_spend(self) -> Dict:
        """Get current month's AWS spending"""
        print("\n💵 Checking current month's spending...")

        # Get date range for current month
        today = datetime.now()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')

        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )

            # Calculate total cost
            total_cost = 0
            service_costs = {}

            for group in response['ResultsByTime'][0]['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0:
                    service_costs[service] = cost
                    total_cost += cost

            # Get credits remaining
            credits_remaining = 120 - total_cost
            days_in_month = 30
            days_elapsed = today.day
            daily_average = total_cost / days_elapsed if days_elapsed > 0 else 0
            projected_monthly = daily_average * days_in_month

            return {
                'total_cost': total_cost,
                'credits_remaining': credits_remaining,
                'service_costs': service_costs,
                'daily_average': daily_average,
                'projected_monthly': projected_monthly,
                'days_elapsed': days_elapsed,
                'start_date': start_date,
                'check_date': today.strftime('%Y-%m-%d %H:%M:%S')
            }

        except ClientError as e:
            print(f"❌ Failed to get cost data: {e}")
            return None

    def get_daily_costs(self, days: int = 7) -> List[Dict]:
        """Get daily costs for the last N days"""
        print(f"\n📈 Getting daily costs for last {days} days...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )

            daily_costs = []
            for result in response['ResultsByTime']:
                daily_costs.append({
                    'date': result['TimePeriod']['Start'],
                    'cost': float(result['Total']['UnblendedCost']['Amount'])
                })

            return daily_costs

        except ClientError as e:
            print(f"❌ Failed to get daily costs: {e}")
            return []

    # Removed daily cost alarm functionality - only keeping spending threshold alerts

    def print_cost_report(self, cost_data: Dict) -> None:
        """Print formatted cost report"""
        if not cost_data:
            return

        print("\n" + "="*60)
        print("💰 CURRENT MONTH AWS SPENDING REPORT")
        print("="*60)

        print(f"\n📊 Summary (as of {cost_data['check_date']}):")
        print(f"   Total Spent: ${cost_data['total_cost']:.2f}")
        print(f"   Credits Remaining: ${cost_data['credits_remaining']:.2f} of $120")
        print(f"   Days Elapsed: {cost_data['days_elapsed']}")
        print(f"   Daily Average: ${cost_data['daily_average']:.2f}")
        print(f"   Projected Monthly: ${cost_data['projected_monthly']:.2f}")

        # Status indicator
        percentage_used = (cost_data['total_cost'] / 120) * 100
        if percentage_used < 25:
            status = "✅ HEALTHY"
            status_color = "green"
        elif percentage_used < 50:
            status = "💚 GOOD"
            status_color = "yellow"
        elif percentage_used < 75:
            status = "⚠️  CAUTION"
            status_color = "orange"
        else:
            status = "🔴 CRITICAL"
            status_color = "red"

        print(f"\n   Status: {status} ({percentage_used:.1f}% of credits used)")

        # Budget burn rate analysis
        expected_percentage = (cost_data['days_elapsed'] / 30) * 100
        if percentage_used > expected_percentage:
            print(f"   ⚠️  Spending above expected rate ({expected_percentage:.1f}% expected)")
        else:
            print(f"   ✅ Spending within expected rate ({expected_percentage:.1f}% expected)")

        # Service breakdown
        if cost_data['service_costs']:
            print("\n💼 Cost by Service:")
            sorted_services = sorted(cost_data['service_costs'].items(),
                                    key=lambda x: x[1], reverse=True)
            for service, cost in sorted_services[:10]:  # Top 10 services
                print(f"   • {service}: ${cost:.2f}")

        # Recommendations
        print("\n💡 Recommendations:")
        if cost_data['projected_monthly'] > 120:
            overage = cost_data['projected_monthly'] - 120
            print(f"   🔴 REDUCE SPENDING: Projected to exceed budget by ${overage:.2f}")
            print("   • Review and terminate unused resources")
            print("   • Check for forgotten running instances")
            print("   • Enable auto-shutdown for development resources")
        elif cost_data['projected_monthly'] > 100:
            print("   ⚠️  Monitor closely - approaching credit limit")
            print("   • Review S3 storage and lifecycle policies")
            print("   • Consider using Spot instances for non-critical workloads")
        else:
            print("   ✅ Spending is under control")
            print("   • Continue monitoring daily")
            print("   • Review Cost Explorer for optimization opportunities")

    def setup_cost_anomaly_detection(self) -> bool:
        """Set up AWS Cost Anomaly Detection"""
        print("\n🔍 Setting up Cost Anomaly Detection...")

        try:
            # Note: Cost Anomaly Detection API is available through AWS Cost Explorer
            # This is a placeholder for the feature description
            print("ℹ️  Cost Anomaly Detection monitors for unusual spending patterns")
            print("   • Enable via AWS Console > Cost Management > Cost Anomaly Detection")
            print("   • AI-powered detection of unusual spending")
            print("   • Free feature that helps prevent surprise charges")

            return True

        except Exception as e:
            print(f"ℹ️  Cost Anomaly Detection note: {e}")
            return False

    def create_emergency_shutdown_script(self) -> None:
        """Create emergency shutdown script to stop all resources"""
        script_content = '''#!/usr/bin/env python3
"""
EMERGENCY AWS RESOURCE SHUTDOWN
Use this if costs are spiraling out of control
"""

import boto3
import sys

def emergency_shutdown():
    print("🚨 EMERGENCY SHUTDOWN INITIATED")

    response = input("This will STOP all EC2, RDS, and expensive services. Type 'SHUTDOWN' to confirm: ")
    if response != 'SHUTDOWN':
        print("Cancelled.")
        return

    # Stop all EC2 instances
    ec2 = boto3.client('ec2')
    try:
        instances = ec2.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running':
                    ec2.stop_instances(InstanceIds=[instance['InstanceId']])
                    print(f"Stopped EC2: {instance['InstanceId']}")
    except Exception as e:
        print(f"EC2 stop failed: {e}")

    # Delete NAT gateways (expensive!)
    try:
        nats = ec2.describe_nat_gateways()
        for nat in nats['NatGateways']:
            if nat['State'] == 'available':
                ec2.delete_nat_gateway(NatGatewayId=nat['NatGatewayId'])
                print(f"Deleted NAT Gateway: {nat['NatGatewayId']}")
    except Exception as e:
        print(f"NAT Gateway deletion failed: {e}")

    print("✅ Emergency shutdown complete")
    print("Check AWS Console for any remaining resources")

if __name__ == "__main__":
    emergency_shutdown()
'''

        with open('emergency_shutdown.py', 'w') as f:
            f.write(script_content)

        print("\n🚨 Created emergency_shutdown.py")
        print("   Use only if costs are out of control!")

    def save_configuration(self) -> None:
        """Save monitoring configuration"""
        config = {
            'account_id': self.account_id,
            'thresholds': self.thresholds,
            'notification_email': self.notification_email,
            'created_date': datetime.now().isoformat()
        }

        with open('cost_monitoring_config.json', 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n📄 Configuration saved to: cost_monitoring_config.json")

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("UCI RESEARCH INTELLIGENCE - COST MONITORING SETUP")
    print("="*60)
    print("\n💵 Protecting your $120 AWS credits...")

    # Get email for notifications
    email = input("\n📧 Enter email for cost alerts (or press Enter to skip): ").strip()

    if not email:
        print("⚠️  No email provided. SNS notifications will not be configured.")
        print("   You can still monitor costs via AWS Console.")
        response = input("Continue without email notifications? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return

    # Initialize monitoring
    monitor = CostMonitoring(notification_email=email)

    # Create SNS topic
    topic_arn = None
    if email:
        topic_arn = monitor.create_sns_topic()
        if topic_arn:
            input("\n⏸️  Press Enter after confirming the SNS email subscription...")

    # Set up billing alarms
    if topic_arn:
        monitor.setup_all_billing_alarms(topic_arn)

    # Create budget
    monitor.create_budget()

    # Daily spending alarm removed - only threshold alerts active

    # Get current spending
    cost_data = monitor.get_current_month_spend()
    if cost_data:
        monitor.print_cost_report(cost_data)

    # Get daily costs
    daily_costs = monitor.get_daily_costs(7)
    if daily_costs:
        print("\n📊 Last 7 days spending:")
        for day in daily_costs:
            print(f"   {day['date']}: ${day['cost']:.2f}")

    # Set up anomaly detection
    monitor.setup_cost_anomaly_detection()

    # Create emergency shutdown script
    monitor.create_emergency_shutdown_script()

    # Save configuration
    monitor.save_configuration()

    # Final summary
    print("\n" + "="*60)
    print("✅ COST MONITORING SETUP COMPLETE")
    print("="*60)

    print("\n🛡️ Protection Layers Activated:")
    print("   1. CloudWatch Billing Alarms ($25, $50, $75, $100)")
    print("   2. AWS Budget with percentage-based alerts")
    print("   3. Forecasting alerts for predicted overages")
    if email:
        print(f"   4. Email notifications to: {email}")

    print("\n📋 Next Steps:")
    print("   1. Check email and confirm SNS subscription")
    print("   2. Review AWS Cost Explorer daily")
    print("   3. Set up auto-shutdown for dev resources")
    print("   4. Tag all resources for cost allocation")
    print("   5. Run 'python cost_monitoring.py' weekly to check spending")

    print("\n⚠️  Important Commands:")
    print("   • Check spending: python cost_monitoring.py --check")
    print("   • Emergency stop: python emergency_shutdown.py")
    print("   • AWS Console: https://console.aws.amazon.com/cost-management/")

    print("\n💡 Your $120 credits are now protected with multiple safeguards!")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AWS Cost Monitoring for UCI Research")
    parser.add_argument('--check', action='store_true', help='Check current spending only')
    parser.add_argument('--email', help='Email address for notifications')

    args = parser.parse_args()

    if args.check:
        # Just check current spending
        monitor = CostMonitoring()
        cost_data = monitor.get_current_month_spend()
        if cost_data:
            monitor.print_cost_report(cost_data)

        daily_costs = monitor.get_daily_costs(7)
        if daily_costs:
            print("\n📊 Last 7 days spending:")
            total_week = 0
            for day in daily_costs:
                print(f"   {day['date']}: ${day['cost']:.2f}")
                total_week += day['cost']
            print(f"   Weekly Total: ${total_week:.2f}")
    else:
        main()
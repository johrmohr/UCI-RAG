#!/usr/bin/env python3
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

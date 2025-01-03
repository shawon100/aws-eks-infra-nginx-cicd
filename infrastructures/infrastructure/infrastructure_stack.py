
import os
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_eks as eks,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

class InfrastructureStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Create S3 bucket
        s3_bucket = s3.Bucket(self, id="bucket2",  bucket_name="arcidan-bucket")

        # The code that defines your stack goes here
        eks_role = iam.Role(self, "eksadmin", assumed_by=iam.ServicePrincipal(service='ec2.amazonaws.com'),
                            role_name='eks-cluster-role', managed_policies=
                            [iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='AdministratorAccess')])

        eks_instance_profile = iam.CfnInstanceProfile(self, 'instanceprofile',
                                                      roles=[eks_role.role_name],
                                                      instance_profile_name='eks-cluster-role')

        cluster = eks.Cluster(self, 'dev', cluster_name='dev-env',
                              version=eks.KubernetesVersion.V1_28,
                              default_capacity=0,
                              masters_role=eks_role)

        nodegroup = cluster.add_nodegroup_capacity('eks-nodegroup',
                                                   instance_types=[ec2.InstanceType('t3.medium')],
                                                   disk_size=50,
                                                   min_size=1,
                                                   max_size=1,
                                                   desired_size=1)
                                                   

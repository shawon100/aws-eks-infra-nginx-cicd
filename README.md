# Infrastructure Provisioning and Deployment

## Table of Contents
- [Infrastructure-as-Code Script](#infrastructure-as-code-script)
  - [Prerequisites](#prerequisites)
  - [Steps to Run](#steps-to-run)
- [Deploying the Helm Chart](#deploying-the-helm-chart)
  - [Steps to Deploy](#steps-to-deploy)
- [How the CI/CD Pipeline Works](#cicd-pipeline)
  - [Pipeline Steps](#Steps-Breakdown)

## Infrastructure-as-Code Script

This section describes how to use the AWS CDK to provision an Amazon EKS cluster with a single node and an Amazon S3 bucket.

### Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) installed and configured.
- [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) installed.
- Python 3.6+ installed.
- Docker installed.

### Steps to Run

1. **Clone the Repository**

   Clone the repository to your local machine:

   ```sh
   git clone https://github.com/shawon100/aws-eks-infra-nginx-cicd.git
   cd aws-eks-infra-nginx-cicd/infrastructures
   ```
2. **Install Virtual Env & Dependencies**


   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Bootstrap the CDK**


   ```sh
   cdk bootstrap
   ```

4. **Deploy the Infrastructure**


   ```sh
   cdk synth
   cdk deploy

   ```
5. **Update Kube Config**

    ```sh
    aws eks --region us-east-1 update-kubeconfig --name dev-env --role-arn arn:aws:iam::AccountNumber:role/eks-cluster-role
    ```
    Note: If you are facing any access issue go to the eks-cluster-role and update the Trust relationship by adding your aws cdk user arn (Added trust-policy.json)


## Deploying the Helm Chart

This section describes how to deploy an NGINX container on the provisioned EKS cluster using Helm.

### Prerequisites

- Helm installed.
- kubectl installed.
- Ensure your kubeconfig is configured to access the EKS cluster.

### Steps to Deploy

1. **Switch to Deployment Folder**

   Go to deployment folder of the repository

   ```sh
   cd deployment
   ```
2. **Install the Nginx Chart**

   ```sh
   helm install nginx-release nginx 
   ```

3. **Check the Pod**

   ```sh
   kubectl get po 
   ```

3. **Get the Loadbalancer URL**

   ```sh
   kubectl get svc
   ```
4. **Allow Inbound Rules**

   Go to your EKS security group and Allow HTTP port 80 to access the URL


## CI/CD Pipeline

This CI/CD pipeline automates the process of building a Docker image using a Dockerfile, pushing it to Amazon ECR, and deploying the application to an Amazon EKS cluster. It's located on cicd/.github/workflows/deployment.yml

### Trigger
The pipeline is triggered on a `push` event to the `main` branch.

### Steps Breakdown

1. **Checkout the Code**
   - The pipeline uses `actions/checkout@v2` to pull the latest code from the repository.

   ```yaml
   - name: Checkout
     uses: actions/checkout@v2
   ```
2. **Configure AWS Credentials**

   Configures AWS credentials using aws-actions configure-aws-credentials@v1. This step uses Github secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION) to authenticate with AWS.

   ```yaml
   - name: Configure AWS credentials
     uses: aws-actions/configure-aws-credentials@v1
     with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ secrets.AWS_REGION }}
    ```

3. **Login to Amazon ECR**

    Logs in to Amazon Elastic Container Registry (ECR) using aws-actions/amazon-ecr-login@v1.

    ```yaml
    - name: Login to Amazon ECR
    id: login-ecr
    uses: aws-actions/amazon-ecr-login@v1
    ```
4. **Build, Tag, and Push the Docker Image**

   This step builds a Docker image, tags it with the latest commit SHA, and pushes it to Amazon ECR.

   ```yaml
   - name: Build, tag, and push the image to Amazon ECR
     id: build-image
     env:
       ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
       ECR_REPOSITORY: cloudageskill
     run: |
       docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$GITHUB_SHA .
       docker push $ECR_REGISTRY/$ECR_REPOSITORY:$GITHUB_SHA
    ```

5. **Update kubeconfig**

   Updates the `kubeconfig` file to allow `kubectl` to access the Amazon EKS cluster.

   ```yaml
   - name: Update kube config
     run: aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION --role-arn $EKS_ROLE
   ```

6. **Deploy to EKS**

   Updates the container image reference in the Kubernetes deployment manifest and applies it to the EKS cluster using `kubectl`.

   ```yaml
   - name: Deploy to EKS
     env:
       ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
       IMAGE_TAG: ${{ steps.commit.outputs.short }}
     run: |
       sed -i.bak "s|DOCKER_IMAGE|$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG|g" manifests/app-deployment.yaml && \
       kubectl apply -f manifests/app-deployment.yaml
       kubectl apply -f manifests/app-service.yaml
    ```




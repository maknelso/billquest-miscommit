# BillQuest Miscommit

A web application for analyzing and visualizing AWS billing data, with a focus on identifying miscommitted resources.

## Project Structure

- `backend/`: Contains the AWS CDK infrastructure and Lambda functions
- `frontend/`: Contains the React/TypeScript frontend application
- `data/`: Contains sample data files for testing

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- AWS CLI configured with appropriate credentials
- AWS CDK installed globally (`npm install -g aws-cdk`)

### Backend Setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Deploy the CDK stack
cd backend
cdk deploy
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Development

- Run `npm run lint` in the frontend directory to lint the TypeScript code
- Run `npm run lint:cfn` in the backend directory to lint the CloudFormation templates

## Configuration

Environment-specific configuration is stored in `backend/config/config.py`. To switch between environments:

```bash
# For development (default)
export ENVIRONMENT=dev

# For production
export ENVIRONMENT=prod
```
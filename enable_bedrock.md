# Enable AWS Bedrock Claude Haiku Access

## Quick Setup Instructions

### 1. Open AWS Console
Go to: https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/modelaccess

### 2. Request Model Access
- Click "Manage model access" button
- In the Anthropic section, check:
  - ✅ Claude 3 Haiku
  - ✅ Claude 3.5 Haiku (optional, newer)
- Click "Request model access"
- Wait for "Access granted" status (usually instant)

### 3. Test Access
Run this command to verify:
```bash
python -c "
import boto3, json
client = boto3.client('bedrock-runtime', region_name='us-west-2')
response = client.invoke_model(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 10,
        'messages': [{'role': 'user', 'content': 'test'}]
    })
)
print('✅ Claude Haiku is working!')
"
```

### 4. Run the RAG System
```bash
python rag_pipeline/rag_system.py
```

## Troubleshooting

If you get "Access Denied" after requesting:
1. Wait 1-2 minutes for propagation
2. Make sure you're in the correct region (us-west-2)
3. Check if your account has Bedrock enabled in the region

## Alternative Regions
If us-west-2 doesn't work, try:
- us-east-1 (N. Virginia)
- eu-west-1 (Ireland)

Update the region in rag_system.py:
```python
pipeline = RAGPipeline(aws_region="us-east-1")
```
"""Check dataset image field."""
from datasets import load_dataset

dataset = load_dataset('cambridgeltl/vsr_random', split='test')
print('First example:')
example = dataset[0]
for key, value in example.items():
    if key == 'image':
        print(f'  {key}: {type(value)} - {str(value)[:100]}')
    else:
        print(f'  {key}: {value}')

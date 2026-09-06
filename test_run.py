import sys
import os
sys.path.insert(0, r'C:\Users\parth\OneDrive\Documents\Default Project\face-id-blockchain-verify')
os.chdir(r'C:\Users\parth\OneDrive\Documents\Default Project\face-id-blockchain-verify')

from app.search import DemoSearchProvider
provider = DemoSearchProvider()
results = provider.search('demo/subject1.jpg')
for r in results:
    print(f"URL: {r['url']}, Title: {r['title']}, Platform: {r.get('platform','N/A')}")
print('Search provider works!')

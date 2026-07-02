import os
thresh=100*1024*1024
big=[]
for root,dirs,files in os.walk('.'):
    for f in files:
        p=os.path.join(root,f)
        try:
            s=os.path.getsize(p)
        except OSError:
            continue
        if s>thresh:
            big.append((s,p))
big.sort(reverse=True)
for s,p in big:
    print(f"{p}\t{s/1024/1024:.2f} MB")
print(f"Found {len(big)} files > {thresh} bytes")

from chonkie import SemanticChunker


text = """
The RTX 4070 is a graphics card from NVIDIA.
It has 12GB of VRAM.
It uses the Ada Lovelace architecture.
The RTX 4070 is designed for gaming and creative workloads.
It performs particularly well at 1440p resolution.

Our store offers free shipping for orders above $100.
Standard delivery usually takes between 3 and 5 business days.
Express delivery is also available in selected regions.
Customers can track their orders using the tracking number.

Customers can pay using Visa or Mastercard.
PayPal is also supported.
All online payments are processed through a secure payment system.

Customers can return eligible products within 30 days.
Products must be returned in acceptable condition.
Refunds are processed after the returned product is inspected.

The store provides a two-year warranty for selected products.
Warranty coverage depends on the manufacturer and product category.
Customers should contact support if they experience a hardware problem.
"""


chunker = SemanticChunker(
    chunk_size=2048,
)

chunks = chunker(text)

print(f"Number of chunks: {len(chunks)}")

for index, chunk in enumerate(chunks):
    print()
    print("=" * 60)
    print(f"CHUNK {index}")
    print("=" * 60)
    print(chunk.text)
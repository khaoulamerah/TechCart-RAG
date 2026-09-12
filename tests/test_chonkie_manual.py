from chonkie import SemanticChunker


text = """
The RTX 4070 has 12GB of VRAM.
It is based on the NVIDIA Ada Lovelace architecture.
The GPU is suitable for gaming at 1440p.

Our store offers free shipping for orders above $100.
Orders are usually delivered within 3 to 5 business days.

Customers can pay using Visa, Mastercard, or PayPal.
We also support secure online payments.
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
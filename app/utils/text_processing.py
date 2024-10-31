def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into chunks of specified size with overlap
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        
        # If this isn't the last chunk, try to break at a space
        if end < text_length:
            # Look for the last space within the chunk
            while end > start and text[end] != ' ':
                end -= 1
            if end == start:  # No spaces found, force break at chunk_size
                end = start + chunk_size

        chunks.append(text[start:end].strip())
        start = end - overlap  # Move start position accounting for overlap

    return chunks 
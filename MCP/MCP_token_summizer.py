import tiktoken
from langchain_cerebras import ChatCerebras
import os

class TextSummarizer:
    def __init__(self, api_key, max_context=65000, chunk_size=50000, model="llama-3.3-70b"):
        """
        Initialize the summarizer with Cerebras API via LangChain
        
        Args:
            api_key: Cerebras API key
            max_context: Maximum context length (default 65000 tokens)
            chunk_size: Size of chunks to process at once (default 50000 tokens)
            model: Cerebras model to use (default "llama-3.3-70b")
        """
        self.llm = ChatCerebras(
            model=model,
            api_key=api_key,
            temperature=0.3  # Lower temperature for more consistent summaries
        )
        self.max_context = max_context
        self.chunk_size = chunk_size
        # Using cl100k_base encoding (GPT-4 tokenizer) as approximation
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text):
        """Count the number of tokens in a text string"""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text, chunk_size):
        """
        Split text into chunks based on token count
        
        Args:
            text: Input text to chunk
            chunk_size: Maximum tokens per chunk
            
        Returns:
            List of text chunks
        """
        tokens = self.encoding.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
        
        return chunks
    
    def summarize_chunk(self, text):
        """
        Summarize a single chunk of text using Cerebras API via LangChain
        
        Args:
            text: Text to summarize
            
        Returns:
            Summarized text
        """
        messages = [
            (
                "system",
                "You are a helpful assistant that creates concise, comprehensive summaries while preserving key information and important details."
            ),
            (
                "human",
                f"Please provide a detailed summary of the following text, maintaining all crucial information:\n\n{text}"
            )
        ]
        
        ai_msg = self.llm.invoke(messages)
        return ai_msg.content
    
    def summarize_file(self, input_file, output_file=None):
        """
        Read a text file and summarize it progressively until under max_context
        
        Args:
            input_file: Path to input text file
            output_file: Path to save summary (optional)
            
        Returns:
            Final summarized text
        """
        # Read the input file
        print(f"Reading file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        initial_tokens = self.count_tokens(text)
        print(f"Initial token count: {initial_tokens:,} tokens")
        
        # If already under max_context, no summarization needed
        if initial_tokens <= self.max_context:
            print("Text is already under the context limit. No summarization needed.")
            return text
        
        # Progressive summarization
        current_text = text
        iteration = 1
        
        while self.count_tokens(current_text) > self.max_context:
            print(f"\n--- Iteration {iteration} ---")
            current_tokens = self.count_tokens(current_text)
            print(f"Current token count: {current_tokens:,} tokens")
            
            # Split into chunks
            chunks = self.chunk_text(current_text, self.chunk_size)
            print(f"Split into {len(chunks)} chunks")
            
            # Summarize each chunk
            summaries = []
            for i, chunk in enumerate(chunks, 1):
                chunk_tokens = self.count_tokens(chunk)
                print(f"  Summarizing chunk {i}/{len(chunks)} ({chunk_tokens:,} tokens)...")
                summary = self.summarize_chunk(chunk)
                summaries.append(summary)
                summary_tokens = self.count_tokens(summary)
                print(f"    Summary: {summary_tokens:,} tokens")
            
            # Combine all summaries
            current_text = "\n\n".join(summaries)
            combined_tokens = self.count_tokens(current_text)
            print(f"Combined summaries: {combined_tokens:,} tokens")
            
            iteration += 1
        
        final_tokens = self.count_tokens(current_text)
        print(f"\n✓ Final summary: {final_tokens:,} tokens (under {self.max_context:,} limit)")
        print(f"Compression ratio: {(1 - final_tokens/initial_tokens)*100:.1f}% reduction")
        
        # Save to output file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(current_text)
            print(f"Summary saved to: {output_file}")
        
        return current_text


# Example usage
if __name__ == "__main__":
    # Get API key from environment variable or replace with your key
    API_KEY = os.getenv("CEREBRAS_API_KEY", "your-api-key-here")
    
    # Initialize summarizer
    summarizer = TextSummarizer(
        api_key=API_KEY,
        max_context=65000,  # Maximum tokens for final summary
        chunk_size=50000,   # Process 50k tokens at a time
        model="llama-3.3-70b"  # Cerebras model
    )
    
    # Summarize a file
    input_file = "input.txt"  # Replace with your input file path
    output_file = "summary.txt"  # Where to save the summary
    
    try:
        summary = summarizer.summarize_file(input_file, output_file)
        print("\n" + "="*50)
        print("SUMMARY PREVIEW:")
        print("="*50)
        print(summary[:500] + "..." if len(summary) > 500 else summary)
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
    except Exception as e:
        print(f"Error: {e}")
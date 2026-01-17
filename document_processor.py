"""
Document Processor
Handles document processing, chunking, and metadata extraction
"""

import os
import json
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema


class DocumentProcessor:
    """Processes documents for vector storage"""
    
    def __init__(self, chunk_size: int = 3000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize Gemini for metadata extraction
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4
        )
        
        # Define output schema for metadata extraction
        self.response_schemas = [
            ResponseSchema(
                name="overarching_theme",
                description='Summarize the main theme(s) discussed in the "Overarching Theme" section.'
            ),
            ResponseSchema(
                name="recurring_topics",
                description='List the recurring topics mentioned in the "Common Threads" section as an array of strings.',
                type="list"
            ),
            ResponseSchema(
                name="pain_points",
                description='Summarize the user\'s frustrations or challenges mentioned in the "Pain Points" section as an array of strings.',
                type="list"
            ),
            ResponseSchema(
                name="analytical_insights",
                description='Extract a list of key analytical observations from the "Analytical Insights" section, including shifts in tone or behavior.',
                type="list"
            ),
            ResponseSchema(
                name="conclusion",
                description="Summarize the conclusions drawn about the user's threads and their overall focus."
            ),
            ResponseSchema(
                name="keywords",
                description='Generate a list of 10 keywords that capture the essence of the document (e.g., "askNostr," "decentralization," "spam filtering").',
                type="list"
            )
        ]
        
        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        return self.text_splitter.split_text(text)
    
    async def extract_metadata(self, text: str) -> Dict:
        """
        Extract metadata from document using Gemini
        
        Args:
            text: Document text
            
        Returns:
            Dictionary containing extracted metadata
        """
        try:
            # Create prompt
            format_instructions = self.output_parser.get_format_instructions()
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert extraction algorithm.
Only extract relevant information from the text.
If you do not know the value of an attribute asked to extract, you may omit the attribute's value.

{format_instructions}"""),
                ("human", "{text}")
            ])
            
            # Format the prompt
            formatted_prompt = prompt.format_messages(
                format_instructions=format_instructions,
                text=text[:50000]  # Limit text length for API
            )
            
            # Get response from Gemini
            response = await self.llm.ainvoke(formatted_prompt)
            
            # Parse the response
            try:
                metadata = self.output_parser.parse(response.content)
            except Exception as parse_error:
                print(f"Error parsing metadata, using fallback: {parse_error}")
                # Fallback: try to extract JSON from response
                metadata = self._fallback_parse(response.content)
            
            # Ensure all fields are present with defaults
            default_metadata = {
                "overarching_theme": "",
                "recurring_topics": [],
                "pain_points": [],
                "analytical_insights": [],
                "conclusion": "",
                "keywords": []
            }
            
            default_metadata.update(metadata)
            return default_metadata
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {
                "overarching_theme": "",
                "recurring_topics": [],
                "pain_points": [],
                "analytical_insights": [],
                "conclusion": "",
                "keywords": []
            }
    
    def _fallback_parse(self, content: str) -> Dict:
        """
        Fallback parser for when structured parsing fails
        
        Args:
            content: Response content
            
        Returns:
            Parsed metadata dictionary
        """
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Return empty metadata if all parsing fails
        return {}
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            import PyPDF2
            
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """
        Extract text from DOCX file
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        try:
            import docx
            
            doc = docx.Document(docx_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            return text
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""

import os
import json
import base64
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
import PyPDF2
from pdf2image import convert_from_path
import io
import openai
from anthropic import Anthropic
from .models import PitchDeckAnalysis


@shared_task
def analyze_deck(analysis_id):
    """Analyze a pitch deck using AI."""
    try:
        analysis = PitchDeckAnalysis.objects.get(id=analysis_id)
        analysis.status = 'processing'
        analysis.save()
        
        # Convert PDF to images
        images = convert_pdf_to_images(analysis.deck_file.path)
        
        # Get AI analysis
        if settings.ANALYSIS_SETTINGS['AI_PROVIDER'] == 'openai':
            result = analyze_with_openai(images)
        elif settings.ANALYSIS_SETTINGS['AI_PROVIDER'] == 'anthropic':
            result = analyze_with_anthropic(images)
        else:
            raise ValueError(f"Unknown AI provider: {settings.ANALYSIS_SETTINGS['AI_PROVIDER']}")
        
        # Save results
        analysis.analysis_result = result
        analysis.status = 'completed'
        analysis.save()
        
    except Exception as e:
        analysis = PitchDeckAnalysis.objects.get(id=analysis_id)
        analysis.status = 'failed'
        analysis.error_message = str(e)
        analysis.save()
        raise


def convert_pdf_to_images(pdf_path):
    """Convert PDF pages to base64 encoded images."""
    images = []
    
    # Convert PDF pages to images
    pdf_images = convert_from_path(pdf_path, dpi=150)
    
    for i, image in enumerate(pdf_images):
        # Convert PIL image to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        images.append({
            'slide_number': i + 1,
            'image_base64': img_str
        })
    
    return images


def analyze_with_openai(images):
    """Analyze deck using OpenAI GPT-4 Vision."""
    openai.api_key = settings.ANALYSIS_SETTINGS['OPENAI_API_KEY']
    
    system_prompt = get_system_prompt()
    
    # Prepare messages with images
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add user message with all images
    content = [{"type": "text", "text": "Please analyze this pitch deck slide by slide."}]
    
    for img_data in images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_data['image_base64']}"
            }
        })
    
    messages.append({
        "role": "user",
        "content": content
    })
    
    # Make API call
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=messages,
        max_tokens=4096,
        temperature=0.7
    )
    
    # Parse JSON response
    result_text = response.choices[0].message.content
    return json.loads(result_text)


def analyze_with_anthropic(images):
    """Analyze deck using Anthropic Claude 3."""
    client = Anthropic(api_key=settings.ANALYSIS_SETTINGS['ANTHROPIC_API_KEY'])
    
    system_prompt = get_system_prompt()
    
    # Prepare content with images
    content = "Please analyze this pitch deck slide by slide.\n\n"
    
    for img_data in images:
        content += f"Slide {img_data['slide_number']}:\n"
        content += f"<image>{img_data['image_base64']}</image>\n\n"
    
    # Make API call
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        temperature=0.7,
        system=system_prompt,
        messages=[
            {"role": "user", "content": content}
        ]
    )
    
    # Parse JSON response
    result_text = response.content[0].text
    return json.loads(result_text)


def get_system_prompt():
    """Get the system prompt for AI analysis."""
    return """You are an expert venture capital analyst specializing in early-stage startups. Your task is to analyze a pitch deck, provided as a series of slide images. Provide concise, constructive, and actionable feedback.

Your response MUST be in a valid JSON format. Do not include any text outside of the JSON object.

The JSON structure should be as follows:
{
  "overall_summary": {
    "score": <integer, 1-100>,
    "key_strengths": "<A 2-3 sentence summary of what the deck does well.>",
    "major_weaknesses": "<A 2-3 sentence summary of the biggest areas for improvement.>"
  },
  "slide_by_slide_analysis": [
    {
      "slide_number": <integer>,
      "identified_topic": "<e.g., 'Problem', 'Solution', 'Team', 'Market Size', 'Not Clear'>",
      "design_score": <integer, 1-10>,
      "clarity_score": <integer, 1-10>,
      "feedback": "<Specific feedback on this slide's content, clarity, and design. Be direct and helpful.>",
      "suggestion": "<One key actionable suggestion for this slide.>"
    }
  ],
  "missing_elements": [
    "<List of key topics typically found in a pitch deck that were not identified, e.g., 'Financial Projections', 'Competitive Analysis'>"
  ],
  "investor_readiness": {
    "score": <integer, 1-10>,
    "recommendation": "<One paragraph recommendation on whether this deck is ready for investors and what the key next steps should be.>"
  }
}"""


@shared_task
def delete_old_pitch_decks():
    """Delete pitch deck files older than retention period."""
    retention_days = settings.ANALYSIS_SETTINGS['FILE_RETENTION_DAYS']
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    # Find analyses with files older than retention period
    old_analyses = PitchDeckAnalysis.objects.filter(
        created_at__lt=cutoff_date,
        file_deleted_at__isnull=True,
        deck_file__isnull=False
    )
    
    for analysis in old_analyses:
        try:
            # Delete the file
            if analysis.deck_file and default_storage.exists(analysis.deck_file.name):
                default_storage.delete(analysis.deck_file.name)
            
            # Mark as deleted but keep the analysis record
            analysis.file_deleted_at = timezone.now()
            analysis.save()
            
        except Exception as e:
            print(f"Error deleting file for analysis {analysis.id}: {str(e)}")
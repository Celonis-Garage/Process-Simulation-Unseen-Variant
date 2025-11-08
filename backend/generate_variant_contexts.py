"""
Generate descriptive contexts for all process variants using LLM.
This script analyzes each unique variant and creates a business context description.
"""

import json
import os
import sys
from pathlib import Path
from collections import Counter
from groq import Groq
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from real_data_loader import RealDataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_all_variants(data_loader):
    """Extract all unique process variants from the event log."""
    variants = []
    variant_counts = {}
    
    # Group events by order_id
    grouped = data_loader.df_events.groupby('order_id')
    
    for order_id, events_df in grouped:
        # Sort by timestamp
        events_df = events_df.sort_values('timestamp')
        
        # Get event sequence
        event_sequence = events_df['event_name'].tolist()
        variant_tuple = tuple(event_sequence)
        
        if variant_tuple not in variant_counts:
            variant_counts[variant_tuple] = 0
        variant_counts[variant_tuple] += 1
    
    # Convert to list with counts
    for variant, count in variant_counts.items():
        variants.append({
            'variant': list(variant),
            'count': count,
            'percentage': (count / len(grouped)) * 100
        })
    
    # Sort by count (descending)
    variants.sort(key=lambda x: x['count'], reverse=True)
    
    return variants


def extract_keywords_from_context(client, context, variant):
    """Extract key phrases/keywords from the generated context."""
    
    keywords_prompt = f"""Extract 5-8 key phrases or keywords that users might use to search for this process variant.

Context: {context}

Event Sequence: {', '.join(variant[:5])}{'...' if len(variant) > 5 else ''}

Return ONLY a comma-separated list of keywords/phrases.
Focus on: business scenarios, order types, key characteristics, common user descriptions.

Examples of good keywords:
- "standard order", "happy path", "normal fulfillment"
- "rejected order", "credit failure", "order denial"
- "discount", "promotion", "price reduction"
- "return", "refund", "customer return"
- "quick order", "simple process", "basic flow"

Your keywords (comma-separated only, no explanations):"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a keyword extraction specialist. Extract only relevant keywords, nothing else."},
                {"role": "user", "content": keywords_prompt}
            ],
            temperature=0.2,
            max_tokens=100
        )
        
        keywords_text = response.choices[0].message.content.strip()
        # Clean and split keywords
        keywords = [k.strip().strip('"').strip("'") for k in keywords_text.split(',')]
        keywords = [k for k in keywords if k and len(k) > 2]  # Remove empty or very short
        
        return keywords[:8]  # Limit to 8 keywords
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return []


def generate_context_for_variant(client, variant_data, variant_index, total_variants):
    """Generate business context for a single variant using LLM."""
    
    variant = variant_data['variant']
    count = variant_data['count']
    percentage = variant_data['percentage']
    
    prompt = f"""You are analyzing an Order-to-Cash (O2C) process variant.

Process Variant #{variant_index + 1} of {total_variants}:
Frequency: {count} cases ({percentage:.1f}% of all orders)

Event Sequence:
{chr(10).join([f"{i+1}. {event}" for i, event in enumerate(variant)])}

Based on this event sequence, generate a concise business context description that:
1. Describes what type of order scenario this represents
2. Identifies key characteristics (e.g., standard flow, has discount, includes returns, rejected order, etc.)
3. Mentions any deviations from a typical O2C process
4. Suggests what business situation would lead to this process flow

Respond with ONLY a 2-3 sentence description. Be specific and business-focused.

Example format:
"This represents a standard order fulfillment process where a customer order is received, validated, approved, and successfully fulfilled through warehouse picking, packing, shipping, and invoicing. This is the most common happy path with no deviations or exceptions."

Your description:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a business process analyst specializing in Order-to-Cash processes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        context = response.choices[0].message.content.strip()
        return context
        
    except Exception as e:
        logger.error(f"Error generating context for variant {variant_index + 1}: {str(e)}")
        return f"Process variant with {len(variant)} steps occurring in {percentage:.1f}% of cases."


def main():
    """Main function to generate contexts for all variants."""
    
    # Load environment
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        logger.error("GROQ_API_KEY not found in environment variables")
        return
    
    client = Groq(api_key=api_key)
    
    # Load data
    logger.info("Loading O2C event data...")
    data_loader = RealDataLoader()
    
    # Get all variants
    logger.info("Extracting process variants...")
    variants = get_all_variants(data_loader)
    logger.info(f"Found {len(variants)} unique process variants")
    
    # Generate contexts and keywords
    variant_contexts = []
    
    for i, variant_data in enumerate(variants):
        logger.info(f"Generating context for variant {i+1}/{len(variants)} ({variant_data['percentage']:.1f}% frequency)...")
        
        # Generate context description
        context = generate_context_for_variant(client, variant_data, i, len(variants))
        logger.info(f"  Context: {context[:100]}...")
        
        # Extract keywords from context
        logger.info(f"  Extracting keywords...")
        keywords = extract_keywords_from_context(client, context, variant_data['variant'])
        logger.info(f"  Keywords: {', '.join(keywords)}")
        
        variant_contexts.append({
            'variant_id': f"variant_{i+1}",
            'event_sequence': variant_data['variant'],
            'frequency_count': variant_data['count'],
            'frequency_percentage': round(variant_data['percentage'], 2),
            'context': context,
            'keywords': keywords,
            'is_most_frequent': (i == 0)
        })

    
    # Save to file
    output_path = Path(__file__).parent.parent / 'data' / 'variant_contexts.json'
    with open(output_path, 'w') as f:
        json.dump({
            'total_variants': len(variant_contexts),
            'total_cases': sum(v['frequency_count'] for v in variant_contexts),
            'variants': variant_contexts
        }, f, indent=2)
    
    logger.info(f"✅ Successfully generated contexts for {len(variant_contexts)} variants")
    logger.info(f"📁 Saved to: {output_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("VARIANT CONTEXTS SUMMARY")
    print("="*80)
    print(f"Total Variants: {len(variant_contexts)}")
    print(f"\nTop 5 Most Frequent Variants:")
    print("-"*80)
    for i, vc in enumerate(variant_contexts[:5]):
        print(f"\n{i+1}. Variant {vc['variant_id']} ({vc['frequency_percentage']}% of cases)")
        print(f"   Steps: {len(vc['event_sequence'])}")
        print(f"   Keywords: {', '.join(vc['keywords'])}")
        print(f"   Context: {vc['context']}")
    print("\n" + "="*80)


if __name__ == '__main__':
    main()


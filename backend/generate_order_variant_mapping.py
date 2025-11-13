"""
Generate mapping of orders to their variants and select one sample order per variant.
This creates a order_variant_mapping.csv file that maps each order to its variant.
"""

import json
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from real_data_loader import RealDataLoader

def generate_order_variant_mapping():
    """
    Map each order to its variant and select one representative sample per variant.
    """
    # Load data
    backend_dir = Path(__file__).parent
    data_dir = backend_dir.parent / 'data'
    data_file_path = str(data_dir / 'o2c_data_orders_only.xml')
    
    data_loader = RealDataLoader(data_file_path)
    
    # Load variant contexts to get the 8 known variants
    with open(data_dir / 'variant_contexts.json', 'r') as f:
        variant_contexts = json.load(f)
    
    print(f"📊 Found {variant_contexts['total_variants']} variants")
    print(f"📊 Total cases: {variant_contexts['total_cases']}")
    
    # Create variant ID to sequence mapping
    variant_sequences = {}
    for v in variant_contexts['variants']:
        variant_id = v['variant_id']
        event_seq = tuple(v['event_sequence'])
        variant_sequences[event_seq] = variant_id
    
    # Map each order to its variant
    order_variant_mapping = []
    variant_samples = {}  # Store sample orders per variant
    
    grouped = data_loader.df_events.groupby('order_id')
    
    for order_id, events_df in grouped:
        # Sort by timestamp
        events_df = events_df.sort_values('timestamp')
        
        # Get event sequence
        event_sequence = tuple(events_df['event_name'].tolist())
        
        # Find matching variant
        variant_id = variant_sequences.get(event_sequence, 'unknown')
        
        order_variant_mapping.append({
            'order_id': order_id,
            'variant_id': variant_id
        })
        
        # Store first order of each variant as sample
        if variant_id not in variant_samples and variant_id != 'unknown':
            variant_samples[variant_id] = order_id
    
    # Create DataFrame and save
    df_mapping = pd.DataFrame(order_variant_mapping)
    output_path = data_dir / 'order_variant_mapping.csv'
    df_mapping.to_csv(output_path, index=False)
    
    print(f"\n✅ Saved order-variant mapping to: {output_path}")
    print(f"📊 Total orders mapped: {len(df_mapping)}")
    print(f"📊 Variants found: {df_mapping['variant_id'].nunique()}")
    print(f"\nVariant distribution:")
    print(df_mapping['variant_id'].value_counts())
    
    # Save sample orders
    sample_orders = []
    for variant_id in sorted(variant_samples.keys(), key=lambda x: int(x.split('_')[1])):
        order_id = variant_samples[variant_id]
        
        # Get variant details
        variant_info = next((v for v in variant_contexts['variants'] if v['variant_id'] == variant_id), None)
        
        sample_orders.append({
            'variant_id': variant_id,
            'sample_order_id': order_id,
            'variant_name': ' → '.join(variant_info['event_sequence'][:3]) + '...' if variant_info else 'Unknown',
            'frequency_percentage': variant_info['frequency_percentage'] if variant_info else 0
        })
    
    df_samples = pd.DataFrame(sample_orders)
    samples_output_path = data_dir / 'variant_sample_orders.csv'
    df_samples.to_csv(samples_output_path, index=False)
    
    print(f"\n✅ Saved sample orders to: {samples_output_path}")
    print(f"\n📋 Sample orders (1 per variant):")
    for _, row in df_samples.iterrows():
        print(f"  {row['variant_id']}: Order {row['sample_order_id']} ({row['frequency_percentage']:.1f}% of orders)")
    
    return df_mapping, df_samples

if __name__ == '__main__':
    print("="*80)
    print("🔧 Generating Order-Variant Mapping")
    print("="*80)
    print()
    
    df_mapping, df_samples = generate_order_variant_mapping()
    
    print()
    print("="*80)
    print("✅ Mapping generation complete!")
    print("="*80)


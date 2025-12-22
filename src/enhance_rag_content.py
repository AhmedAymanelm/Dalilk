"""
Script to enhance rag_content with better semantic structure
"""
import json
import re

def extract_brand_model(name):
    """Extract brand and model from car name"""
    # Use the full name as-is since it's already in English
    # Just extract the year if present
    parts = name.split()
    brand = parts[0] if parts else ""
    
    # Find year (4 digits)
    year_match = re.search(r'\b(20\d{2})\b', name)
    if year_match:
        year_pos = name.index(year_match.group(1))
        model = name[len(brand):year_pos].strip()
    else:
        # Take everything after brand as model
        model = " ".join(parts[1:]) if len(parts) > 1 else ""
    
    return brand, model

def extract_price_number(price_str):
    """Extract numeric price from price string"""
    # Extract numbers from string like "Down payment 15%: 119,999 EGP"
    match = re.search(r'([\d,]+)\s*EGP', price_str)
    if match:
        return int(match.group(1).replace(',', ''))
    return 0

def generate_keywords(car):
    """Generate semantic keywords for better retrieval"""
    keywords = []
    specs = car.get('specs', {})
    
    # Brand and model
    brand, model = extract_brand_model(car.get('name', ''))
    if brand:
        keywords.append(brand)
    if model:
        keywords.append(model)
    
    # Key specs
    if specs.get('body_type'):
        keywords.append(specs['body_type'])
    if specs.get('fuel_type'):
        keywords.append(specs['fuel_type'])
    if specs.get('transmission'):
        keywords.append(specs['transmission'])
    if specs.get('drive_type'):
        keywords.append(specs['drive_type'])
    
    # Special features
    if specs.get('horsepower'):
        keywords.append(f"{specs['horsepower']} HP")
    if specs.get('seats'):
        keywords.append(f"{specs['seats']} seats")
    if specs.get('warranty_years'):
        keywords.append(f"{specs['warranty_years']} year warranty")
    
    return keywords

def generate_questions(car):
    """Generate questions this car data can answer"""
    brand, model = extract_brand_model(car.get('name', ''))
    specs = car.get('specs', {})
    questions = []
    
    if brand and model:
        questions.append(f"What is the price of {brand} {model}?")
        questions.append(f"Is {brand} {model} electric or petrol?")
        questions.append(f"What are the specs of {brand} {model}?")
        
        if specs.get('horsepower'):
            questions.append(f"How much horsepower does {brand} {model} have?")
        if specs.get('fuel_type'):
            fuel_ar = "كهربا" if specs['fuel_type'].lower() in ['electric', 'ev'] else "بنزين"
            questions.append(f"{brand} {model} {fuel_ar} ولا بنزين؟")
    
    return questions

def create_enhanced_rag_content(car):
    """Create enhanced RAG content with better semantic structure"""
    specs = car.get('specs', {})
    name = car.get('name', '')
    brand, model = extract_brand_model(name)
    price_num = extract_price_number(car.get('price', ''))
    
    # Summary (first line - most important for embedding)
    # Use the FULL car name as-is
    summary = name
    if specs.get('body_type'):
        summary += f" - {specs['body_type']}"
    if specs.get('fuel_type'):
        summary += f" {specs['fuel_type']}"
    if price_num > 0:
        summary += f" - {price_num:,} EGP"
    
    # Key features
    key_features = []
    if specs.get('transmission'):
        key_features.append(specs['transmission'])
    if specs.get('horsepower'):
        key_features.append(f"{specs['horsepower']} HP")
    if specs.get('seats'):
        key_features.append(f"{specs['seats']} seats")
    if specs.get('drive_type'):
        key_features.append(specs['drive_type'])
    if specs.get('warranty_years'):
        key_features.append(f"{specs['warranty_years']}yr warranty")
    
    # Build structured content
    lines = [
        f"# {summary}",
        f"Car Name: {name}",
        f"Price: {car.get('price', '')}",
        f"Rating: {car.get('rating', 'N/A')}/5"
    ]
    
    if key_features:
        lines.append(f"Key Features: {', '.join(key_features)}")
    
    # Keywords for semantic matching
    keywords = generate_keywords(car)
    if keywords:
        lines.append(f"Keywords: {', '.join(keywords)}")
    
    # Questions answered
    questions = generate_questions(car)
    if questions:
        lines.append(f"Answers: {' | '.join(questions[:3])}")  # Top 3 questions
    
    # Detailed specs
    lines.append("\nDetailed Specifications:")
    for key, value in specs.items():
        if value and value != "N/A":
            lines.append(f"  {key}: {value}")
    
    return "\n".join(lines)

def enhance_json_file(input_file, output_file):
    """Process JSON file and enhance rag_content"""
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        cars = json.load(f)
    
    print(f"Processing {len(cars)} cars...")
    for i, car in enumerate(cars):
        # Generate enhanced content
        enhanced_content = create_enhanced_rag_content(car)
        car['rag_content'] = enhanced_content
        
        # Add metadata for filtering
        brand, model = extract_brand_model(car.get('name', ''))
        specs = car.get('specs', {})
        
        car['metadata'] = {
            'brand': brand,
            'model': model,
            'fuel_type': specs.get('fuel_type', ''),
            'body_type': specs.get('body_type', ''),
            'transmission': specs.get('transmission', ''),
            'price_egp': extract_price_number(car.get('price', '')),
            'horsepower': int(specs.get('horsepower', 0)) if specs.get('horsepower') else 0,
            'seats': int(specs.get('seats', 0)) if specs.get('seats') else 0,
            'keywords': generate_keywords(car)
        }
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1} cars...")
    
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cars, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Done! Enhanced {len(cars)} cars")
    
    # Show example
    print("\n📝 Example enhanced content:")
    print("=" * 60)
    print(cars[0]['rag_content'][:500] + "...")
    print("=" * 60)

if __name__ == "__main__":
    input_file = "assets/files/default/lvATP97PZtHt_Data_clean_cars_english-1.json"
    output_file = "assets/files/default/enhanced_cars.json"
    
    enhance_json_file(input_file, output_file)

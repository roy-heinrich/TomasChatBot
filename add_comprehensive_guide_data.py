#!/usr/bin/env python3
"""
Add comprehensive makeup guide data to fix the "complete guide" query issue
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def add_comprehensive_guide_data():
    """Add comprehensive makeup guide data"""
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return
    
    try:
        # Create Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase")
        
        # Comprehensive makeup guide data
        guide_data = [
            {
                "keywords": "Give me a complete guide to your cosmetics",
                "response": "Welcome to our complete cosmetics guide! We offer a comprehensive range of beauty products including:\n\n**FACE:**\n- Foundation (30 shades, matte & dewy finishes)\n- Concealer (full coverage, color-correcting)\n- Powder (setting, translucent, pressed)\n- Blush (powder, cream, liquid)\n- Bronzer (matte, shimmer, contour)\n\n**EYES:**\n- Eyeshadow palettes (neutral, bold, seasonal)\n- Eyeliner (pencil, liquid, gel)\n- Mascara (volumizing, lengthening, waterproof)\n- Eyebrow products (pencils, gels, powders)\n\n**LIPS:**\n- Lipstick (matte, satin, glossy finishes)\n- Lip gloss (clear, tinted, plumping)\n- Lip liner (matching, nude, bold colors)\n- Lip balm (moisturizing, tinted, SPF)\n\n**SKINCARE:**\n- Cleansers (foaming, cream, oil-based)\n- Moisturizers (day, night, SPF)\n- Serums (anti-aging, brightening, hydrating)\n- Masks (clay, sheet, overnight)\n\nVisit our store for personalized recommendations and free consultations!"
            },
            {
                "keywords": "What cosmetics do you have?",
                "response": "We have a complete range of cosmetics including foundation, concealer, eyeshadow, eyeliner, mascara, lipstick, blush, bronzer, and skincare products. Our collection features both drugstore and high-end brands with options for all skin types and tones."
            },
            {
                "keywords": "Tell me about your makeup products",
                "response": "Our makeup collection includes everything you need for a complete beauty routine:\n\n**Base Products:** Foundation, concealer, powder, primer\n**Eye Products:** Eyeshadow palettes, eyeliner, mascara, eyebrow products\n**Lip Products:** Lipstick, lip gloss, lip liner, lip balm\n**Cheek Products:** Blush, bronzer, highlighter\n**Tools:** Brushes, sponges, applicators\n\nAll products are available in multiple shades and finishes to suit every preference and skin tone."
            },
            {
                "keywords": "What makeup brands do you carry?",
                "response": "We carry a variety of makeup brands including our own GlamourBot line, as well as popular brands like BeautyPro, GlowUp, StyleMax, and other quality cosmetics brands. We offer both affordable drugstore options and premium high-end products."
            },
            {
                "keywords": "Do you have makeup for beginners?",
                "response": "Yes! We have beginner-friendly makeup products and starter kits. Our neutral eyeshadow palettes, basic foundation shades, and simple lip colors are perfect for those new to makeup. We also offer free makeup consultations to help beginners learn application techniques."
            },
            {
                "keywords": "What makeup should I buy?",
                "response": "The best makeup for you depends on your skin type, tone, and personal style. We recommend starting with:\n\n**Essentials:**\n- Foundation or BB cream\n- Mascara\n- Lip color (lipstick or gloss)\n- Basic eyeshadow palette\n\n**For Beginners:**\n- Neutral color palette\n- Cream-based products (easier to blend)\n- Multi-purpose products\n\nVisit our store for a free consultation to find the perfect products for your needs!"
            },
            {
                "keywords": "How do I choose makeup?",
                "response": "Choosing the right makeup involves considering your skin type, undertone, and personal preferences:\n\n**Skin Type:**\n- Oily skin: Matte finishes, oil-free products\n- Dry skin: Hydrating formulas, cream products\n- Combination: Different products for different areas\n\n**Undertone:**\n- Warm: Yellow/golden undertones\n- Cool: Pink/blue undertones\n- Neutral: Balanced undertones\n\n**Personal Style:**\n- Natural: Neutral colors, minimal products\n- Bold: Bright colors, dramatic looks\n- Professional: Subtle, polished appearance\n\nOur beauty consultants can help you determine your skin type and undertone for the perfect match!"
            },
            {
                "keywords": "What is your best selling makeup?",
                "response": "Our best-selling makeup products include:\n\n**Top Sellers:**\n- Neutral eyeshadow palettes\n- Classic red lipstick\n- Volumizing mascara\n- Foundation in popular shades\n- Setting powder\n\n**Customer Favorites:**\n- Long-wear lipstick\n- Waterproof mascara\n- Cream blush\n- Highlighter\n- Eyebrow pencils\n\nThese products are consistently popular due to their quality, versatility, and great results. Ask our staff about current bestsellers!"
            },
            {
                "keywords": "Do you have makeup samples?",
                "response": "Yes! We provide free samples of foundation, skincare, and fragrance products. Samples are available in-store and with online orders over $50. This allows you to try products before purchasing to ensure the perfect match and formula for your skin."
            },
            {
                "keywords": "Can I try makeup before buying?",
                "response": "Absolutely! We encourage trying makeup before purchasing. We offer:\n\n- Free samples of foundation and skincare\n- Testers for all makeup products\n- Free makeup consultations\n- In-store application demos\n- Return policy for unused products\n\nOur beauty consultants can help you find the perfect products and show you application techniques."
            }
        ]
        
        # Insert the data
        result = supabase.table("chatbot_prompts").insert(guide_data).execute()
        
        if result.data:
            print(f"✅ Successfully added {len(result.data)} comprehensive guide records!")
            print("🎯 The 'complete guide' query should now work properly!")
        else:
            print("❌ Failed to insert guide data")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("💄 Adding Comprehensive Makeup Guide Data")
    print("=" * 50)
    add_comprehensive_guide_data()

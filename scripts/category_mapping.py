#!/usr/bin/env python3
"""
Category Mapping for Google Maps → Ethnicity Categories

Maps Google Maps restaurant categories to our existing ethnicity/country system.
"""

# Google Maps category → Our ethnicity category
# Based on common Google Maps restaurant type labels
GOOGLE_TO_ETHNICITY = {
    # East Asian - Chinese regional
    "chinese restaurant": "Chinese",
    "cantonese restaurant": "Cantonese",
    "dim sum restaurant": "Cantonese",
    "szechuan restaurant": "Sichuan",
    "sichuan restaurant": "Sichuan",
    "hunan restaurant": "Hunan",
    "shanghai restaurant": "Shanghainese",
    "shanghainese restaurant": "Shanghainese",
    "beijing restaurant": "Beijing",
    "hong kong style fast food restaurant": "Hong Kong",
    "hong kong restaurant": "Hong Kong",
    "chinese bakery": "Chinese Bakery",
    "taiwanese restaurant": "Taiwanese",
    "taiwanese noodle house": "Taiwanese",

    # East Asian - Japanese
    "japanese restaurant": "Japanese",
    "sushi restaurant": "Sushi",
    "ramen restaurant": "Ramen",
    "izakaya": "Japanese",
    "udon restaurant": "Japanese",
    "tempura restaurant": "Japanese",
    "teppanyaki restaurant": "Japanese",
    "yakitori restaurant": "Japanese",
    "japanese curry restaurant": "Japanese",
    "tonkatsu restaurant": "Japanese",
    "okonomiyaki restaurant": "Japanese",

    # East Asian - Korean
    "korean restaurant": "Korean",
    "korean bbq restaurant": "Korean BBQ",
    "korean fried chicken restaurant": "Korean",

    # East Asian - Other
    "vietnamese restaurant": "Vietnamese",
    "pho restaurant": "Vietnamese",
    "banh mi shop": "Vietnamese",
    "thai restaurant": "Thai",
    "laotian restaurant": "Laotian",

    # Southeast Asian
    "filipino restaurant": "Filipino",
    "indonesian restaurant": "Indonesian",
    "malaysian restaurant": "Malaysian",
    "singaporean restaurant": "Singaporean",
    "burmese restaurant": "Burmese",
    "cambodian restaurant": "Cambodian",
    "tibetan restaurant": "Tibetan",

    # South Asian
    "indian restaurant": "Indian",
    "south indian restaurant": "South Indian",
    "north indian restaurant": "North Indian",
    "punjabi restaurant": "Punjabi",
    "gujarati restaurant": "Gujarati",
    "biryani restaurant": "Indian",
    "dosa restaurant": "South Indian",
    "pakistani restaurant": "Pakistani",
    "bangladeshi restaurant": "Bangladeshi",
    "nepalese restaurant": "Nepalese",
    "sri lankan restaurant": "Sri Lankan",
    "afghan restaurant": "Afghan",

    # Middle Eastern / North African
    "middle eastern restaurant": "Middle Eastern (Unspecified)",
    "lebanese restaurant": "Lebanese",
    "syrian restaurant": "Syrian",
    "turkish restaurant": "Turkish",
    "persian restaurant": "Persian",
    "iranian restaurant": "Persian",
    "israeli restaurant": "Israeli",
    "moroccan restaurant": "Moroccan",
    "egyptian restaurant": "Egyptian",
    "yemeni restaurant": "Yemeni",
    "palestinian restaurant": "Palestinian",
    "jordanian restaurant": "Jordanian",
    "iraqi restaurant": "Iraqi",
    "armenian restaurant": "Armenian",
    "georgian restaurant": "Georgian",
    "azerbaijani restaurant": "Azerbaijani",
    "uzbek restaurant": "Uzbek",
    "falafel restaurant": "Middle Eastern (Unspecified)",
    "shawarma restaurant": "Middle Eastern (Unspecified)",
    "kebab restaurant": "Middle Eastern (Unspecified)",
    "hummus restaurant": "Middle Eastern (Unspecified)",

    # European - Southern
    "italian restaurant": "Italian",
    "pizza restaurant": "Pizza",
    "pizzeria": "Pizza",
    "neapolitan pizza restaurant": "Neapolitan Pizza",
    "sicilian restaurant": "Sicilian",
    "tuscan restaurant": "Tuscan",
    "french restaurant": "French",
    "bistro": "French",
    "brasserie": "French",
    "spanish restaurant": "Spanish",
    "tapas restaurant": "Spanish Tapas",
    "tapas bar": "Spanish Tapas",
    "basque restaurant": "Basque",
    "catalan restaurant": "Catalan",
    "portuguese restaurant": "Portuguese",
    "greek restaurant": "Greek",

    # European - Central/Eastern
    "german restaurant": "German",
    "austrian restaurant": "Austrian",
    "swiss restaurant": "Swiss",
    "polish restaurant": "Polish",
    "russian restaurant": "Russian",
    "ukrainian restaurant": "Ukrainian",
    "hungarian restaurant": "Hungarian",
    "czech restaurant": "Czech",
    "romanian restaurant": "Romanian",
    "serbian restaurant": "Serbian",
    "croatian restaurant": "Croatian",
    "bosnian restaurant": "Bosnian",
    "bulgarian restaurant": "Bulgarian",

    # European - Northern/Western
    "british restaurant": "British",
    "irish restaurant": "Irish",
    "scottish restaurant": "Scottish",
    "belgian restaurant": "Belgian",
    "dutch restaurant": "Dutch",
    "scandinavian restaurant": "Scandinavian",
    "swedish restaurant": "Swedish",
    "danish restaurant": "Danish",
    "norwegian restaurant": "Norwegian",
    "finnish restaurant": "Finnish",
    "icelandic restaurant": "Icelandic",
    "mediterranean restaurant": "Mediterranean (Unspecified)",

    # Latin American / Caribbean
    "mexican restaurant": "Mexican",
    "taqueria": "Mexican",
    "tex-mex restaurant": "Tex-Mex",
    "oaxacan restaurant": "Oaxacan",
    "yucatecan restaurant": "Yucatecan",
    "cuban restaurant": "Cuban",
    "puerto rican restaurant": "Puerto Rican",
    "dominican restaurant": "Dominican",
    "jamaican restaurant": "Jamaican",
    "trinidadian restaurant": "Trinidadian",
    "haitian restaurant": "Haitian",
    "guyanese restaurant": "Guyanese",
    "caribbean restaurant": "Caribbean (Unspecified)",
    "brazilian restaurant": "Brazilian",
    "brazilian steakhouse": "Brazilian Steakhouse",
    "churrascaria": "Brazilian Steakhouse",
    "peruvian restaurant": "Peruvian",
    "ceviche restaurant": "Peruvian",
    "colombian restaurant": "Colombian",
    "argentine restaurant": "Argentinian",
    "argentinian restaurant": "Argentinian",
    "argentine steakhouse": "Argentinian Steakhouse",
    "venezuelan restaurant": "Venezuelan",
    "chilean restaurant": "Chilean",
    "ecuadorian restaurant": "Ecuadorian",
    "bolivian restaurant": "Bolivian",
    "uruguayan restaurant": "Uruguayan",
    "paraguayan restaurant": "Paraguayan",
    "salvadoran restaurant": "Salvadoran",
    "guatemalan restaurant": "Guatemalan",
    "honduran restaurant": "Honduran",
    "nicaraguan restaurant": "Nicaraguan",
    "costa rican restaurant": "Costa Rican",
    "panamanian restaurant": "Panamanian",
    "latin american restaurant": "Latin American (Unspecified)",
    "south american restaurant": "Latin American (Unspecified)",
    "central american restaurant": "Latin American (Unspecified)",

    # African
    "ethiopian restaurant": "Ethiopian",
    "eritrean restaurant": "Eritrean",
    "nigerian restaurant": "Nigerian",
    "ghanaian restaurant": "Ghanaian",
    "senegalese restaurant": "Senegalese",
    "ivorian restaurant": "Ivorian",
    "cameroonian restaurant": "Cameroonian",
    "somali restaurant": "Somali",
    "kenyan restaurant": "Kenyan",
    "ugandan restaurant": "Ugandan",
    "tanzanian restaurant": "Tanzanian",
    "south african restaurant": "South African",
    "african restaurant": "African (Unspecified)",
    "west african restaurant": "West African",
    "east african restaurant": "East African",
    "north african restaurant": "North African",

    # American / Regional
    "american restaurant": "American",
    "new american restaurant": "New American",
    "soul food restaurant": "Soul Food",
    "southern restaurant": "Southern",
    "cajun restaurant": "Cajun",
    "creole restaurant": "Creole",
    "cajun creole restaurant": "Cajun-Creole",
    "bbq restaurant": "BBQ",
    "barbecue restaurant": "BBQ",
    "texas bbq": "Texas BBQ",
    "smokehouse": "BBQ",
    "diner": "Diner",
    "steakhouse": "Steakhouse",
    "seafood restaurant": "Seafood",
    "oyster bar": "Seafood",
    "fish & chips restaurant": "Fish & Chips",
    "hamburger restaurant": "Burgers",
    "burger restaurant": "Burgers",
    "hot dog restaurant": "Hot Dogs",
    "sandwich shop": "Sandwiches",
    "deli": "Deli",
    "delicatessen": "Deli",

    # Jewish
    "jewish restaurant": "Jewish",
    "kosher restaurant": "Kosher",
    "jewish deli": "Jewish Deli",

    # Asian Fusion / General
    "asian restaurant": "Asian (Unspecified)",
    "asian fusion restaurant": "Asian Fusion",
    "pan-asian restaurant": "Pan-Asian",
    "noodle shop": "Noodles",

    # Bars & Pubs
    "bar": "Bar",
    "cocktail bar": "Cocktail Bar",
    "wine bar": "Wine Bar",
    "sports bar": "Sports Bar",
    "pub": "Pub",
    "irish pub": "Irish Pub",
    "british pub": "British Pub",
    "gastropub": "Gastropub",
    "bar & grill": "Bar & Grill",
    "beer hall": "Beer Hall",
    "beer garden": "Beer Garden",
    "brewery": "Brewery",
    "brewpub": "Brewpub",

    # Cafes & Bakeries
    "cafe": "Cafe",
    "coffee shop": "Coffee Shop",
    "tea house": "Tea House",
    "bubble tea store": "Bubble Tea",
    "bakery": "Bakery",
    "pastry shop": "Pastry Shop",
    "patisserie": "Patisserie",
    "dessert shop": "Dessert Shop",
    "ice cream shop": "Ice Cream",
    "donut shop": "Donuts",
    "bagel shop": "Bagels",

    # Brunch & Breakfast
    "brunch restaurant": "Brunch",
    "breakfast restaurant": "Breakfast",
    "pancake restaurant": "Pancakes",

    # Health & Special Diet
    "vegetarian restaurant": "Vegetarian",
    "vegan restaurant": "Vegan",
    "health food restaurant": "Health Food",
    "juice bar": "Juice Bar",
    "salad shop": "Salads",
    "acai shop": "Acai",

    # Food Trucks & Street Food
    "food truck": "Food Truck",
    "street food restaurant": "Street Food",

    # Generic (less useful but still captured)
    "restaurant": None,  # Too generic to map
    "fast food restaurant": "Fast Food",
    "family restaurant": None,
    "fine dining restaurant": "Fine Dining",
    "buffet restaurant": "Buffet",
    "food court": None,
    "catering service": None,
}


def map_google_category(google_category):
    """
    Map a Google Maps category to our ethnicity system.

    Args:
        google_category: The category string from Google Maps (e.g., "Mexican restaurant")

    Returns:
        The mapped ethnicity category, or None if no mapping found
    """
    if not google_category:
        return None

    # Normalize the category
    normalized = google_category.lower().strip()

    # Direct lookup
    if normalized in GOOGLE_TO_ETHNICITY:
        return GOOGLE_TO_ETHNICITY[normalized]

    # Try partial matches (for categories like "Fine Mexican restaurant")
    for google_cat, ethnicity in GOOGLE_TO_ETHNICITY.items():
        if google_cat in normalized:
            return ethnicity

    # Try extracting the cuisine type
    # Pattern: "<adjective> <cuisine> restaurant"
    import re
    match = re.search(r'(\w+)\s+restaurant', normalized)
    if match:
        cuisine_word = match.group(1)
        # Check if this word maps to a known cuisine
        test_key = f"{cuisine_word} restaurant"
        if test_key in GOOGLE_TO_ETHNICITY:
            return GOOGLE_TO_ETHNICITY[test_key]

    return None


def get_improvement_stats(scraped_results):
    """
    Calculate statistics on how much the Google data improves our categorization.

    Args:
        scraped_results: List of scraped restaurant results

    Returns:
        Dictionary with improvement statistics
    """
    stats = {
        'total': len(scraped_results),
        'found': 0,
        'confident_matches': 0,
        'improved': 0,
        'already_specific': 0,
        'no_improvement': 0,
        'category_distribution': {}
    }

    for result in scraped_results:
        if not result.get('found'):
            continue

        stats['found'] += 1

        if result.get('confident_match'):
            stats['confident_matches'] += 1

        original = result.get('original_category', '')
        google_cat = result.get('google_category', '')
        mapped = map_google_category(google_cat)

        # Track category distribution
        if mapped:
            stats['category_distribution'][mapped] = stats['category_distribution'].get(mapped, 0) + 1

        # Check if this improves the categorization
        if 'Unspecified' in original:
            if mapped and 'Unspecified' not in mapped:
                stats['improved'] += 1
            else:
                stats['no_improvement'] += 1
        else:
            stats['already_specific'] += 1

    return stats


# Location-based categories (countries, ethnicities, cities, regions)
# These are PREFERRED over food-type categories
LOCATION_BASED_CATEGORIES = {
    # East Asian - Countries
    "Chinese", "Japanese", "Korean", "Vietnamese", "Thai",
    "Filipino", "Indonesian", "Malaysian", "Singaporean",
    "Burmese", "Cambodian", "Laotian", "Tibetan", "Taiwanese",

    # East Asian - Regional
    "Cantonese", "Sichuan", "Hunan", "Shanghainese", "Beijing",
    "Hong Kong",

    # South Asian - Countries
    "Indian", "Pakistani", "Bangladeshi", "Nepalese", "Sri Lankan", "Afghan",

    # South Asian - Regional
    "South Indian", "North Indian", "Punjabi", "Gujarati",

    # Middle Eastern / North African - Countries
    "Lebanese", "Syrian", "Turkish", "Persian", "Israeli",
    "Moroccan", "Egyptian", "Yemeni", "Palestinian", "Jordanian",
    "Iraqi", "Armenian", "Georgian", "Azerbaijani", "Uzbek",

    # European - Countries
    "Italian", "French", "Spanish", "Portuguese", "Greek",
    "German", "Austrian", "Swiss", "Polish", "Russian", "Ukrainian",
    "Hungarian", "Czech", "Romanian", "Serbian", "Croatian",
    "Bosnian", "Bulgarian", "British", "Irish", "Scottish",
    "Belgian", "Dutch", "Swedish", "Danish", "Norwegian",
    "Finnish", "Icelandic",

    # European - Regional
    "Neapolitan Pizza", "Sicilian", "Tuscan", "Basque", "Catalan",
    "Scandinavian",

    # Latin American / Caribbean - Countries
    "Mexican", "Cuban", "Puerto Rican", "Dominican", "Jamaican",
    "Trinidadian", "Haitian", "Guyanese", "Brazilian", "Peruvian",
    "Colombian", "Argentinian", "Venezuelan", "Chilean", "Ecuadorian",
    "Bolivian", "Uruguayan", "Paraguayan", "Salvadoran", "Guatemalan",
    "Honduran", "Nicaraguan", "Costa Rican", "Panamanian",

    # Latin American - Regional
    "Oaxacan", "Yucatecan", "Tex-Mex",

    # African - Countries
    "Ethiopian", "Eritrean", "Nigerian", "Ghanaian", "Senegalese",
    "Ivorian", "Cameroonian", "Somali", "Kenyan", "Ugandan",
    "Tanzanian", "South African",

    # American / Regional
    "American", "New American", "Southern", "Cajun", "Creole",
    "Cajun-Creole", "Texas BBQ",

    # Ethnicity-based
    "Jewish", "Kosher", "Jewish Deli", "Soul Food",

    # Unspecified but location-based
    "Caribbean (Unspecified)", "Latin American (Unspecified)",
    "Middle Eastern (Unspecified)", "African (Unspecified)",
    "West African", "East African", "North African",
    "Mediterranean (Unspecified)", "Asian (Unspecified)",
    "Asian Fusion", "Pan-Asian",
}

# Food-type categories (dishes, venues, diet styles)
# These are LOWER priority than location-based categories
FOOD_TYPE_CATEGORIES = {
    # Dish-specific
    "Sushi", "Ramen", "Pizza", "Noodles", "BBQ", "Burgers",
    "Seafood", "Steakhouse", "Korean BBQ", "Brazilian Steakhouse",
    "Argentinian Steakhouse", "Hot Dogs", "Sandwiches", "Deli",
    "Fish & Chips",

    # Venue-type
    "Bar", "Cocktail Bar", "Wine Bar", "Sports Bar", "Pub",
    "Irish Pub", "British Pub", "Gastropub", "Bar & Grill",
    "Beer Hall", "Beer Garden", "Brewery", "Brewpub",
    "Cafe", "Coffee Shop", "Tea House", "Bubble Tea",
    "Bistro", "Brasserie", "Diner",

    # Bakery/Dessert
    "Bakery", "Chinese Bakery", "Pastry Shop", "Patisserie",
    "Dessert Shop", "Ice Cream", "Donuts", "Bagels",

    # Meal-type
    "Brunch", "Breakfast", "Pancakes",

    # Diet/style
    "Vegetarian", "Vegan", "Health Food", "Juice Bar",
    "Salads", "Acai", "Fast Food", "Fine Dining", "Buffet",

    # Other
    "Food Truck", "Street Food", "Spanish Tapas",
}

# Mapping from specific categories to their immediate parent category
# This supports multi-level hierarchies (e.g., Cantonese -> Chinese -> Asian)
# Categories not in this dict are considered top-level categories
SPECIFIC_TO_GENERAL = {
    # ============================================================
    # ASIAN (top-level) - Geographic hierarchy
    # ============================================================

    # Chinese regional → Chinese
    "Cantonese": "Chinese",
    "Sichuan": "Chinese",
    "Hunan": "Chinese",
    "Shanghainese": "Chinese",
    "Beijing": "Chinese",
    "Hong Kong": "Chinese",
    "Taiwanese": "Chinese",
    "Chinese Bakery": "Chinese",

    # Chinese → Asian (mid-level)
    "Chinese": "Asian",

    # Japanese dish-types → Japanese
    "Sushi": "Japanese",
    "Ramen": "Japanese",

    # Japanese → Asian (mid-level)
    "Japanese": "Asian",

    # Korean specific → Korean
    "Korean BBQ": "Korean",

    # Korean → Asian (mid-level)
    "Korean": "Asian",

    # Indian regional → Indian
    "South Indian": "Indian",
    "North Indian": "Indian",
    "Punjabi": "Indian",
    "Gujarati": "Indian",

    # Indian → South Asian (mid-level)
    "Indian": "South Asian",

    # South Asian countries → South Asian
    "Pakistani": "South Asian",
    "Bangladeshi": "South Asian",
    "Nepalese": "South Asian",
    "Sri Lankan": "South Asian",
    "Afghan": "South Asian",

    # South Asian → Asian (mid-level)
    "South Asian": "Asian",

    # Southeast Asian countries → Southeast Asian
    "Filipino": "Southeast Asian",
    "Indonesian": "Southeast Asian",
    "Malaysian": "Southeast Asian",
    "Singaporean": "Southeast Asian",
    "Burmese": "Southeast Asian",
    "Cambodian": "Southeast Asian",
    "Laotian": "Southeast Asian",
    "Tibetan": "Southeast Asian",
    "Vietnamese": "Southeast Asian",
    "Thai": "Southeast Asian",

    # Southeast Asian → Asian (mid-level)
    "Southeast Asian": "Asian",

    # Asian unspecified and fusion
    "Asian (Unspecified)": "Asian",
    "Asian Fusion": "Asian",
    "Pan-Asian": "Asian",
    "Chinese-Japanese": "Asian",
    "Chinese-Cuban": "Asian",

    # Southeast Asian unspecified → Southeast Asian
    "Southeast Asian (Unspecified)": "Southeast Asian",

    # ============================================================
    # WESTERN EUROPEAN (top-level)
    # ============================================================

    # English subcategories → English
    "Fish & Chips": "English",
    "British": "English",
    "British Pub": "English",

    # English → Western European
    "English": "Western European",

    # Irish/Scottish → Western European
    "Irish": "Western European",
    "Irish Pub": "Western European",
    "Scottish": "Western European",

    # French → Western European
    "French": "Western European",
    "Bistro": "French",
    "Brasserie": "French",
    "Patisserie": "French",

    # Spanish subcategories → Spanish
    "Basque": "Spanish",
    "Catalan": "Spanish",
    "Spanish Tapas": "Spanish",
    "Tapas": "Spanish",

    # Spanish → Western European
    "Spanish": "Western European",

    # Italian regional → Italian
    "Sicilian": "Italian",
    "Tuscan": "Italian",

    # Italian → Western European
    "Italian": "Western European",

    # Pizza → Pizza Shop (Pizza Shop is now a top-level category)
    "Pizza": "Pizza Shop",
    "Neapolitan Pizza": "Pizza Shop",

    # Portuguese/Greek → Western European
    "Portuguese": "Western European",
    "Greek": "Western European",

    # Belgian/Dutch → Western European
    "Belgian": "Western European",
    "Dutch": "Western European",

    # German/Austrian/Swiss → Western European
    "German": "Western European",
    "Austrian": "Western European",
    "Swiss": "Western European",

    # Scandinavian → Western European
    "Swedish": "Western European",
    "Danish": "Western European",
    "Norwegian": "Western European",
    "Finnish": "Western European",
    "Icelandic": "Western European",
    "Scandinavian": "Western European",

    # Continental European → Western European
    "Continental European": "Western European",

    # Mediterranean → Western European
    "Mediterranean": "Western European",
    "Mediterranean (Unspecified)": "Western European",

    # ============================================================
    # EASTERN EUROPEAN (top-level)
    # ============================================================

    "Polish": "Eastern European",
    "Russian": "Eastern European",
    "Ukrainian": "Eastern European",
    "Hungarian": "Eastern European",
    "Czech": "Eastern European",
    "Romanian": "Eastern European",
    "Serbian": "Eastern European",
    "Croatian": "Eastern European",
    "Bosnian": "Eastern European",
    "Bulgarian": "Eastern European",
    "Moldovan": "Eastern European",
    "Eastern European (Unspecified)": "Eastern European",

    # ============================================================
    # MIDDLE EASTERN (top-level)
    # ============================================================

    "Lebanese": "Middle Eastern",
    "Syrian": "Middle Eastern",
    "Turkish": "Middle Eastern",
    "Persian": "Middle Eastern",
    "Iranian": "Middle Eastern",
    "Israeli": "Middle Eastern",
    "Moroccan": "Middle Eastern",
    "Egyptian": "Middle Eastern",
    "Yemeni": "Middle Eastern",
    "Palestinian": "Middle Eastern",
    "Jordanian": "Middle Eastern",
    "Iraqi": "Middle Eastern",
    "Armenian": "Middle Eastern",
    "Georgian": "Middle Eastern",
    "Azerbaijani": "Middle Eastern",
    "Uzbek": "Middle Eastern",
    "Cypriot": "Middle Eastern",
    "Middle Eastern (Unspecified)": "Middle Eastern",

    # ============================================================
    # AFRICAN (top-level)
    # ============================================================

    "Ethiopian": "African",
    "Eritrean": "African",
    "Nigerian": "African",
    "Ghanaian": "African",
    "Senegalese": "African",
    "Ivorian": "African",
    "Cameroonian": "African",
    "Somali": "African",
    "Kenyan": "African",
    "Ugandan": "African",
    "Tanzanian": "African",
    "South African": "African",
    "West African": "African",
    "East African": "African",
    "North African": "African",
    "African (Unspecified)": "African",

    # ============================================================
    # LATIN AMERICAN (top-level)
    # ============================================================

    # Mexican regional → Mexican
    "Tex-Mex": "Mexican",
    "Oaxacan": "Mexican",
    "Yucatecan": "Mexican",

    # Mexican → Latin American
    "Mexican": "Latin American",

    # Other Latin American countries
    "Brazilian": "Latin American",
    "Peruvian": "Latin American",
    "Colombian": "Latin American",
    "Argentinian": "Latin American",
    "Venezuelan": "Latin American",
    "Chilean": "Latin American",
    "Ecuadorian": "Latin American",
    "Bolivian": "Latin American",
    "Uruguayan": "Latin American",
    "Paraguayan": "Latin American",
    "Salvadoran": "Latin American",
    "Guatemalan": "Latin American",
    "Honduran": "Latin American",
    "Nicaraguan": "Latin American",
    "Costa Rican": "Latin American",
    "Panamanian": "Latin American",
    "Brazilian Steakhouse": "Latin American",
    "Argentinian Steakhouse": "Latin American",
    "Latin American (Unspecified)": "Latin American",

    # ============================================================
    # CARIBBEAN (top-level)
    # ============================================================

    "Jamaican": "Caribbean",
    "Trinidadian": "Caribbean",
    "Haitian": "Caribbean",
    "Guyanese": "Caribbean",
    "Cuban": "Caribbean",
    "Puerto Rican": "Caribbean",
    "Dominican": "Caribbean",
    "Caribbean (Unspecified)": "Caribbean",

    # ============================================================
    # AMERICAN (top-level)
    # ============================================================

    # Traditional American regional
    "Southern": "American",
    "Cajun": "American",
    "Creole": "American",
    "Cajun-Creole": "American",
    "Soul Food": "American",
    "Texas BBQ": "American",
    "New American": "American",
    "BBQ": "American",
    "Steakhouse": "American",

    # Food types under American
    "Juice Bar": "American",
    "Diner": "American",
    "Brunch": "American",
    "Breakfast": "American",
    "Burgers": "American",
    "Health Food": "American",
    "Vegan": "American",
    "Vegetarian": "American",
    "Seafood": "American",
    "Hotel Food": "American",
    "Bar & Grill": "American",
    "Deli": "American",
    "Hot Dogs": "American",
    "Sandwiches": "American",
    "Salads": "American",
    "Acai": "American",
    "Pancakes": "American",
    "Fine Dining": "American",
    "Southwestern": "American",
    "Buffet": "American",
    "Hawaiian": "American",
    "Fast Food": "American",

    # ============================================================
    # BAR (top-level)
    # ============================================================

    "Sports Bar": "Bar",
    "Wine Bar": "Bar",
    "Cocktail Bar": "Bar",
    "Pub": "Bar",
    "Gastropub": "Bar",
    "Beer Hall": "Bar",
    "Beer Garden": "Bar",
    "Brewery": "Bar",
    "Brewpub": "Bar",

    # ============================================================
    # JEWISH/KOSHER (top-level)
    # ============================================================

    "Kosher": "Jewish/Kosher",
    "Jewish": "Jewish/Kosher",
    "Jewish Deli": "Jewish/Kosher",

    # ============================================================
    # CAFE (top-level)
    # ============================================================

    "Coffee Shop": "Cafe",
    "Tea House": "Cafe",
    "Bubble Tea": "Cafe",

    # ============================================================
    # BAKERY (top-level)
    # ============================================================

    "Pastry Shop": "Bakery",
    "Dessert Shop": "Bakery",
    "Ice Cream": "Bakery",
    "Donuts": "Bakery",
    "Bagels": "Bakery",
}


def is_location_based(category):
    """
    Return True if category is location/ethnicity-based, False if food-type.

    Args:
        category: The category string to check

    Returns:
        True if location-based, False otherwise
    """
    if not category:
        return False
    return category in LOCATION_BASED_CATEGORIES


def get_general_category(specific_cat):
    """
    Get the immediate parent category for a specific category.

    Args:
        specific_cat: The specific category (e.g., "Cantonese", "Jamaican")

    Returns:
        The immediate parent category (e.g., "Chinese", "Caribbean"),
        or the category itself if it's already a top-level category.
    """
    if not specific_cat:
        return None
    return SPECIFIC_TO_GENERAL.get(specific_cat, specific_cat)


def get_top_level_category(category):
    """
    Get the top-level parent category by traversing the hierarchy.

    Args:
        category: Any category (e.g., "Cantonese", "Chinese", "Asian")

    Returns:
        The top-level parent category (e.g., "Asian" for "Cantonese"),
        or the category itself if it's already top-level.
    """
    if not category:
        return None

    current = category
    visited = set()  # Prevent infinite loops

    while current in SPECIFIC_TO_GENERAL and current not in visited:
        visited.add(current)
        current = SPECIFIC_TO_GENERAL[current]

    return current


def get_category_chain(category):
    """
    Get the full hierarchy chain from specific to top-level.

    Args:
        category: Any category (e.g., "Cantonese")

    Returns:
        List from specific to general (e.g., ["Cantonese", "Chinese", "Asian"])
    """
    if not category:
        return []

    chain = [category]
    visited = set()

    current = category
    while current in SPECIFIC_TO_GENERAL and current not in visited:
        visited.add(current)
        parent = SPECIFIC_TO_GENERAL[current]
        chain.append(parent)
        current = parent

    return chain


def determine_final_categories(original_cat, google_cat_mapped):
    """
    Determine both specific and general final categories.

    Priority for specific category:
    1. Google category if location-based
    2. Original category if location-based (and Google is not)
    3. Google category (even if food-type)
    4. Original category (fallback)

    Args:
        original_cat: Original category from DOHMH data
        google_cat_mapped: Mapped category from Google data

    Returns:
        tuple: (final_cat_specific, final_cat_general)
    """
    # Determine the specific category
    if google_cat_mapped and is_location_based(google_cat_mapped):
        final_specific = google_cat_mapped
    elif original_cat and is_location_based(original_cat):
        final_specific = original_cat
    elif google_cat_mapped:
        final_specific = google_cat_mapped
    else:
        final_specific = original_cat

    # Determine the general category from the specific one
    final_general = get_general_category(final_specific)

    return final_specific, final_general


# Keep old function name for backwards compatibility
def determine_final_category(original_cat, google_cat_mapped):
    """Backwards compatible wrapper - returns only specific category."""
    specific, _ = determine_final_categories(original_cat, google_cat_mapped)
    return specific


if __name__ == '__main__':
    # Test the mapping
    test_categories = [
        "Mexican restaurant",
        "Cuban restaurant",
        "Jamaican restaurant",
        "Caribbean restaurant",
        "Restaurant",
        "Cafe",
        "Fine dining Lebanese restaurant",
        "Sushi restaurant",
        "Ethiopian restaurant",
    ]

    print("Category Mapping Tests:")
    print("-" * 50)
    for cat in test_categories:
        mapped = map_google_category(cat)
        print(f"  {cat:40} -> {mapped}")

    print("\n" + "=" * 70)
    print("Dual Category Tests (Specific + General):")
    print("=" * 70)

    test_final = [
        ("Japanese", "Ramen"),        # Specific: Japanese, General: Japanese
        ("Japanese", "Sushi"),        # Specific: Japanese, General: Japanese
        ("Chinese", "Cantonese"),     # Specific: Cantonese, General: Chinese
        ("Chinese", "Hong Kong"),     # Specific: Hong Kong, General: Chinese
        ("Mediterranean (Unspecified)", "Israeli"),  # Specific: Israeli, General: Middle Eastern
        ("Bar", "Bar"),               # Specific: Bar, General: Bar
        ("American", "Vegan"),        # Specific: American, General: American
        ("Asian (Unspecified)", "Korean"),  # Specific: Korean, General: Korean
        (None, "Mexican"),            # Specific: Mexican, General: Mexican
        ("Italian", None),            # Specific: Italian, General: Italian
        ("Mexican", "Oaxacan"),       # Specific: Oaxacan, General: Mexican
        ("Caribbean (Unspecified)", "Jamaican"),  # Specific: Jamaican, General: Caribbean
        ("Indian", "Punjabi"),        # Specific: Punjabi, General: Indian
        ("Vietnamese", "Vietnamese"), # Specific: Vietnamese, General: Southeast Asian
    ]

    print(f"  {'Original':<25} {'Google':<15} {'Specific':<20} {'General':<20}")
    print("  " + "-" * 80)
    for original, google in test_final:
        specific, general = determine_final_categories(original, google)
        print(f"  {str(original):<25} {str(google):<15} {str(specific):<20} {str(general):<20}")
